from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

from common import (
    IMAGE_EXTENSIONS,
    choose_device,
    default_project_dir,
    load_unet,
    runtime_metadata,
    sha256_file,
    synchronize,
    write_csv,
    write_json,
)


def find_mask(mask_root: Path, image_root: Path, image_path: Path) -> Optional[Path]:
    rel = image_path.relative_to(image_root)
    base = mask_root / rel.parent / rel.stem
    for ext in (".png", ".tif", ".tiff", ".jpg", ".jpeg"):
        candidate = base.with_suffix(ext)
        if candidate.exists():
            return candidate
    return None


def binary_metrics(gt: np.ndarray, pred: np.ndarray) -> Dict[str, float]:
    gt = gt.astype(bool)
    pred = pred.astype(bool)
    tp = int(np.logical_and(gt, pred).sum())
    tn = int(np.logical_and(~gt, ~pred).sum())
    fp = int(np.logical_and(~gt, pred).sum())
    fn = int(np.logical_and(gt, ~pred).sum())
    eps = 1e-12
    dice = (2 * tp) / (2 * tp + fp + fn + eps)
    iou = tp / (tp + fp + fn + eps)
    precision = tp / (tp + fp + eps)
    recall = tp / (tp + fn + eps)
    specificity = tn / (tn + fp + eps)
    accuracy = (tp + tn) / (tp + tn + fp + fn + eps)
    return {
        "dice": float(dice),
        "iou": float(iou),
        "pixel_precision": float(precision),
        "pixel_recall": float(recall),
        "specificity": float(specificity),
        "pixel_accuracy": float(accuracy),
        "true_positive_pixels": tp,
        "true_negative_pixels": tn,
        "false_positive_pixels": fp,
        "false_negative_pixels": fn,
    }


def bootstrap_ci(values: np.ndarray, seed: int = 2026, n_boot: int = 5000) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    if len(values) < 2:
        value = float(values.mean()) if len(values) else float("nan")
        return value, value
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        sample = rng.choice(values, size=len(values), replace=True)
        means[i] = sample.mean()
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def make_comparison_sheet(
    original_path: Path,
    gt: np.ndarray,
    pred: np.ndarray,
    output_path: Path,
    tile_size: int = 320,
) -> None:
    with Image.open(original_path) as opened:
        original = opened.convert("RGB")
    gt_img = Image.fromarray((gt.astype(np.uint8) * 255), mode="L").convert("RGB")
    pred_img = Image.fromarray((pred.astype(np.uint8) * 255), mode="L").convert("RGB")
    disagreement = np.logical_xor(gt.astype(bool), pred.astype(bool))
    disagreement_img = Image.fromarray((disagreement.astype(np.uint8) * 255), mode="L").convert("RGB")

    panels = [
        ("Original", original),
        ("Ground-truth mask", gt_img),
        ("Predicted mask", pred_img),
        ("Disagreement", disagreement_img),
    ]
    label_h = 34
    sheet = Image.new("RGB", (4 * tile_size, tile_size + label_h), "white")
    draw = ImageDraw.Draw(sheet)
    for i, (label, image) in enumerate(panels):
        image = image.copy()
        image.thumbnail((tile_size, tile_size))
        tile = Image.new("RGB", (tile_size, tile_size), "white")
        tile.paste(image, ((tile_size - image.width) // 2, (tile_size - image.height) // 2))
        sheet.paste(tile, (i * tile_size, 0))
        draw.text((i * tile_size + 6, tile_size + 6), label, fill="black")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Experiment 2: quantitative U-Net segmentation validation."
    )
    parser.add_argument("--project-dir", type=Path, default=default_project_dir())
    parser.add_argument(
        "--images-dir", type=Path, default=None,
        help="Defaults to <project-dir>/segmentation_test/images."
    )
    parser.add_argument(
        "--masks-dir", type=Path, default=None,
        help="Defaults to <project-dir>/segmentation_test/masks."
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--invert-ground-truth", action="store_true")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    args = parser.parse_args()

    project = args.project_dir.expanduser().resolve()
    images_dir = (
        args.images_dir or project / "segmentation_test" / "images"
    ).expanduser().resolve()
    masks_dir = (
        args.masks_dir or project / "segmentation_test" / "masks"
    ).expanduser().resolve()
    output_dir = (
        args.output_dir or project / "evaluation_outputs" / "experiment_2_segmentation"
    ).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not images_dir.exists() or not masks_dir.exists():
        raise FileNotFoundError(
            "Segmentation validation requires manually reviewed ground-truth masks.\n"
            f"Expected images in: {images_dir}\n"
            f"Expected masks in:  {masks_dir}\n"
            "Use matching relative paths and stems, for example:\n"
            "  segmentation_test/images/dots/sample_01.png\n"
            "  segmentation_test/masks/dots/sample_01.png"
        )

    image_paths = sorted(
        p for p in images_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not image_paths:
        raise ValueError(f"No images found in {images_dir}")

    device = choose_device(args.device)
    unet_mod, model, img_size, resolved_device, paths = load_unet(project, device)

    rows: List[Dict[str, Any]] = []
    predicted_dir = output_dir / "predicted_masks"
    comparison_dir = output_dir / "comparison_sheets"

    for index, image_path in enumerate(image_paths, start=1):
        mask_path = find_mask(masks_dir, images_dir, image_path)
        if mask_path is None:
            print(f"Skipping without matching mask: {image_path.relative_to(images_dir)}")
            continue

        tensor, original_size = unet_mod.preprocess_image(
            str(image_path), img_size=img_size, denoise=0, sharpen=0, invert=False
        )
        synchronize(resolved_device)
        start = time.perf_counter()
        tensor = tensor.to(resolved_device)
        with __import__("torch").no_grad():
            logits = model(tensor)
            probabilities = __import__("torch").sigmoid(logits).squeeze().cpu().numpy()
        synchronize(resolved_device)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        if probabilities.ndim != 2:
            raise ValueError(
                f"Expected one 2D probability map for {image_path.name}, got {probabilities.shape}"
            )
        pred_small = probabilities >= args.threshold
        pred_img = Image.fromarray((pred_small.astype(np.uint8) * 255), mode="L")
        pred_img = pred_img.resize(original_size, Image.Resampling.NEAREST)
        pred = np.asarray(pred_img) > 127

        with Image.open(mask_path) as opened:
            gt_img = opened.convert("L").resize(original_size, Image.Resampling.NEAREST)
        gt = np.asarray(gt_img) > 127
        if args.invert_ground_truth:
            gt = ~gt

        metrics = binary_metrics(gt, pred)
        rel = image_path.relative_to(images_dir)
        save_path = predicted_dir / rel.with_suffix(".png")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        pred_img.save(save_path)
        comparison_path = comparison_dir / rel.with_suffix(".png")
        make_comparison_sheet(image_path, gt, pred, comparison_path)

        rows.append({
            "relative_path": rel.as_posix(),
            "image_path": str(image_path),
            "ground_truth_mask_path": str(mask_path),
            "predicted_mask_path": str(save_path),
            "threshold": args.threshold,
            "prediction_time_ms": elapsed_ms,
            "ground_truth_foreground_fraction": float(gt.mean()),
            "predicted_foreground_fraction": float(pred.mean()),
            **metrics,
        })
        print(
            f"[{index:03d}/{len(image_paths):03d}] {rel.as_posix()} "
            f"Dice={metrics['dice']:.4f}, IoU={metrics['iou']:.4f}"
        )

    if not rows:
        raise RuntimeError("No image/mask pairs were evaluated.")

    df = pd.DataFrame(rows)
    df.to_csv(output_dir / "segmentation_per_image_metrics.csv", index=False)

    metric_names = [
        "dice", "iou", "pixel_precision", "pixel_recall", "specificity", "pixel_accuracy"
    ]
    summary_rows: List[Dict[str, Any]] = []
    for metric in metric_names:
        values = df[metric].to_numpy(dtype=float)
        ci_low, ci_high = bootstrap_ci(values)
        summary_rows.append({
            "metric": metric,
            "n_images": len(values),
            "mean": float(values.mean()),
            "standard_deviation": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
            "median": float(np.median(values)),
            "minimum": float(values.min()),
            "maximum": float(values.max()),
            "mean_95_ci_low_bootstrap": ci_low,
            "mean_95_ci_high_bootstrap": ci_high,
        })
    write_csv(output_dir / "segmentation_summary_metrics.csv", summary_rows)

    summary_df = pd.DataFrame(summary_rows).set_index("metric")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    summary_df["mean"].plot(kind="bar", yerr=summary_df["standard_deviation"], ax=ax, capsize=4)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Mean score")
    ax.set_xlabel("Metric")
    ax.set_title("U-Net segmentation performance")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(output_dir / "segmentation_summary_metrics.png", dpi=300)
    plt.close(fig)

    metadata = runtime_metadata(resolved_device)
    metadata.update({
        "project_dir": str(project),
        "images_dir": str(images_dir),
        "masks_dir": str(masks_dir),
        "threshold": args.threshold,
        "invert_ground_truth": args.invert_ground_truth,
        "unet_model": str(paths.unet_weights),
        "unet_model_sha256": sha256_file(paths.unet_weights),
        "unet_script": str(paths.unet_script),
        "unet_script_sha256": sha256_file(paths.unet_script),
        "n_evaluated": len(df),
    })
    write_json(output_dir / "run_metadata.json", metadata)
    print(f"Segmentation experiment complete: {output_dir}")


if __name__ == "__main__":
    main()
