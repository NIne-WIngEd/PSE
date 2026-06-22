from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.metrics import accuracy_score, f1_score

from common import (
    CLASS_LABELS,
    choose_device,
    default_project_dir,
    discover_classification_images,
    load_cnn,
    load_manifest,
    relative_posix,
    run_cnn_prediction,
    write_csv,
    write_json,
)


def create_variants(source: Path) -> Dict[str, Image.Image]:
    with Image.open(source) as opened:
        original = opened.convert("RGB")
    gray = original.convert("L")
    gray_arr = np.asarray(gray, dtype=np.float32) / 255.0

    variants: Dict[str, Image.Image] = {
        "original": original,
        "grayscale_rgb": gray.convert("RGB"),
        "inverted_grayscale_rgb": Image.fromarray(
            (255 - np.asarray(gray, dtype=np.uint8)), mode="L"
        ).convert("RGB"),
    }

    for cmap_name in ("magma", "viridis", "inferno"):
        cmap = plt.get_cmap(cmap_name)
        rgba = cmap(gray_arr)
        rgb = (rgba[:, :, :3] * 255).astype(np.uint8)
        variants[cmap_name] = Image.fromarray(rgb, mode="RGB")
    return variants


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Experiment 1B: rendering/color sensitivity stress test. "
            "This is a robustness analysis, not a replacement for the primary benchmark."
        )
    )
    parser.add_argument("--project-dir", type=Path, default=default_project_dir())
    parser.add_argument("--test-dir", type=Path, default=None)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    parser.add_argument(
        "--save-variants", action="store_true",
        help="Keep generated color variants. Otherwise temporary files are removed."
    )
    args = parser.parse_args()

    project = args.project_dir.expanduser().resolve()
    test_dir = (args.test_dir or project / "test").expanduser().resolve()
    output_dir = (
        args.output_dir or project / "evaluation_outputs" / "experiment_1b_color_robustness"
    ).expanduser().resolve()
    variants_dir = output_dir / "rendered_variants"
    variants_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(args.manifest)
    items = discover_classification_images(test_dir)
    device = choose_device(args.device)
    cnn_mod, model, _ = load_cnn(project, device)

    rows: List[Dict[str, Any]] = []
    original_predictions: Dict[str, str] = {}

    for index, (image_path, true_label) in enumerate(items, start=1):
        rel = relative_posix(image_path, test_dir)
        manifest_row = manifest.get(rel, {})
        if not bool(manifest_row.get("include_in_primary", True)):
            continue

        variants = create_variants(image_path)
        image_variant_dir = variants_dir / image_path.parent.name / image_path.stem
        image_variant_dir.mkdir(parents=True, exist_ok=True)

        for variant_name, image in variants.items():
            variant_path = image_variant_dir / f"{variant_name}.png"
            image.save(variant_path)
            result = run_cnn_prediction(cnn_mod, model, variant_path, device)
            probs = result["probabilities"]
            pred = str(result["predicted_class"]).lower()
            if variant_name == "original":
                original_predictions[rel] = pred
            rows.append({
                "relative_path": rel,
                "true_label": true_label,
                "variant": variant_name,
                "predicted_label": pred,
                "confidence": float(result["confidence"]),
                "dots_probability": float(probs.get("dots", 0.0)),
                "irregular_probability": float(probs.get("irregular", 0.0)),
                "lines_probability": float(probs.get("lines", 0.0)),
                "mixed_probability": float(probs.get("mixed", 0.0)),
                "correct": pred == true_label,
            })
        print(f"[{index:03d}/{len(items):03d}] {rel}")

    df = pd.DataFrame(rows)
    df["same_prediction_as_original"] = df.apply(
        lambda row: row["predicted_label"] == original_predictions[row["relative_path"]],
        axis=1,
    )
    df.to_csv(output_dir / "color_robustness_predictions.csv", index=False)

    summary_rows: List[Dict[str, Any]] = []
    for variant, group in df.groupby("variant"):
        summary_rows.append({
            "variant": variant,
            "n_images": len(group),
            "accuracy": float(accuracy_score(group["true_label"], group["predicted_label"])),
            "macro_f1": float(
                f1_score(
                    group["true_label"], group["predicted_label"],
                    labels=CLASS_LABELS, average="macro", zero_division=0
                )
            ),
            "mean_confidence": float(group["confidence"].mean()),
            "prediction_consistency_with_original": float(
                group["same_prediction_as_original"].mean()
            ),
        })
    write_csv(output_dir / "color_robustness_summary.csv", summary_rows)

    summary_df = pd.DataFrame(summary_rows).set_index("variant")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    summary_df[["accuracy", "macro_f1", "prediction_consistency_with_original"]].plot(
        kind="bar", ax=ax
    )
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_xlabel("Rendering variant")
    ax.set_title("CNN sensitivity to AFM rendering/color transformations")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(output_dir / "color_robustness_summary.png", dpi=300)
    plt.close(fig)

    changed = df[(df["variant"] != "original") & (~df["same_prediction_as_original"])]
    changed.to_csv(output_dir / "prediction_changes_from_original.csv", index=False)

    write_json(output_dir / "interpretation_note.json", {
        "purpose": (
            "This experiment measures sensitivity to display rendering and colormap changes "
            "while approximately preserving spatial morphology."
        ),
        "limitation": (
            "The transformations operate on already-rendered RGB images, not raw AFM height data. "
            "Results should be described as a stress test, not proof of acquisition-domain generalization."
        ),
    })

    if not args.save_variants:
        import shutil
        shutil.rmtree(variants_dir, ignore_errors=True)

    print(f"Color robustness experiment complete: {output_dir}")


if __name__ == "__main__":
    main()
