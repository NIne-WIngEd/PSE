from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image, ImageDraw

from common import (
    choose_device,
    default_project_dir,
    import_module_from_path,
    load_cnn,
    load_unet,
    run_cnn_prediction,
    write_csv,
    write_json,
)


def read_cases(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Case-study manifest not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    required = {"relative_path", "true_label", "case_name", "include"}
    missing = required - set(rows[0].keys() if rows else [])
    if missing:
        raise ValueError(f"Case-study manifest is missing columns: {sorted(missing)}")
    return [
        row for row in rows
        if str(row.get("include", "yes")).strip().lower() in {"yes", "true", "1", "y"}
    ]


def find_image_candidates(result: Any) -> List[Path]:
    paths: List[Path] = []
    if isinstance(result, dict):
        for value in result.values():
            if isinstance(value, str):
                p = Path(value)
                if p.exists() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
                    paths.append(p)
            elif isinstance(value, dict):
                paths.extend(find_image_candidates(value))
            elif isinstance(value, (list, tuple)):
                for item in value:
                    if isinstance(item, str):
                        p = Path(item)
                        if p.exists() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
                            paths.append(p)
    unique: List[Path] = []
    seen = set()
    for p in paths:
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def make_sheet(panels: List[tuple[str, Path]], output_path: Path, tile_size: int = 320) -> None:
    if not panels:
        return
    columns = min(3, len(panels))
    rows = (len(panels) + columns - 1) // columns
    label_h = 38
    sheet = Image.new("RGB", (columns * tile_size, rows * (tile_size + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (label, path) in enumerate(panels):
        with Image.open(path) as opened:
            im = opened.convert("RGB")
        im.thumbnail((tile_size, tile_size))
        tile = Image.new("RGB", (tile_size, tile_size), "white")
        tile.paste(im, ((tile_size - im.width) // 2, (tile_size - im.height) // 2))
        x = (idx % columns) * tile_size
        y = (idx // columns) * (tile_size + label_h)
        sheet.paste(tile, (x, y))
        draw.text((x + 6, y + tile_size + 7), label[:48], fill="black")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Experiment 4: generate end-to-end AFM case-study artifacts."
    )
    parser.add_argument("--project-dir", type=Path, default=default_project_dir())
    parser.add_argument("--test-dir", type=Path, default=None)
    parser.add_argument("--cases-csv", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    args = parser.parse_args()

    project = args.project_dir.expanduser().resolve()
    test_dir = (args.test_dir or project / "test").expanduser().resolve()
    cases_csv = (
        args.cases_csv or Path(__file__).resolve().parent / "case_studies_template.csv"
    ).expanduser().resolve()
    output_dir = (
        args.output_dir or project / "evaluation_outputs" / "experiment_4_case_studies"
    ).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    device = choose_device(args.device)
    cnn_mod, cnn_model, paths = load_cnn(project, device)
    unet_mod, unet_model, unet_img_size, unet_device, _ = load_unet(project, device)
    vor_mod = import_module_from_path("voronoi_case_backend", paths.voronoi_script)
    cw_mod = import_module_from_path("colorwheel_case_backend", paths.colorwheel_script)

    cases = read_cases(cases_csv)
    summaries: List[Dict[str, Any]] = []

    for idx, case in enumerate(cases, start=1):
        rel = case["relative_path"].replace("\\", "/")
        image_path = test_dir / rel
        if not image_path.exists():
            raise FileNotFoundError(f"Case image not found: {image_path}")
        case_name = case["case_name"]
        safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in case_name)
        case_dir = output_dir / f"case_{idx:02d}_{safe_name}"
        case_dir.mkdir(parents=True, exist_ok=True)

        copied_original = case_dir / f"original{image_path.suffix.lower()}"
        shutil.copy2(image_path, copied_original)

        prediction = run_cnn_prediction(cnn_mod, cnn_model, image_path, device)
        raw_pred = str(prediction["predicted_class"]).lower()
        routing_label = "mixed" if raw_pred == "irregular" else raw_pred

        edited_mask_value = str(case.get("edited_mask_path", "")).strip()
        if edited_mask_value:
            edited = Path(edited_mask_value)
            if not edited.is_absolute():
                edited = project / edited
            if not edited.exists():
                raise FileNotFoundError(f"Edited mask not found: {edited}")
            mask_path = case_dir / "mask_used.png"
            shutil.copy2(edited, mask_path)
            mask_source = "edited_mask_from_case_manifest"
        else:
            tensor, original_size = unet_mod.preprocess_image(
                str(image_path), img_size=unet_img_size, denoise=0, sharpen=0, invert=False
            )
            mask = unet_mod.predict_mask(
                unet_model, tensor, unet_device, threshold=0.5
            )
            mask_path = case_dir / "mask_used.png"
            unet_mod.save_mask(mask, str(mask_path), original_size)
            mask_source = "automatic_unet"

        panels: List[tuple[str, Path]] = [
            ("Original AFM image", copied_original),
            (f"Segmentation mask ({mask_source})", mask_path),
        ]
        analysis_record: Dict[str, Any] = {}

        if routing_label in ("dots", "mixed"):
            try:
                vor_result = vor_mod.run_voronoi_analysis(
                    image_path=str(mask_path),
                    image_size=float(case.get("image_size_micrometers") or 1.0),
                    output_dir=str(case_dir / "voronoi_outputs"),
                    threshold_edge=0.025,
                    max_size=1024,
                )
                analysis_record["voronoi"] = vor_result
                selected = (vor_result or {}).get("selected_images", {}) if isinstance(vor_result, dict) else {}
                for label, key in [
                    ("Voronoi overlay", "voronoi_overlay"),
                    ("Morphology map", "morphology_map"),
                    ("Voronoi snapshot", "snapshot"),
                ]:
                    value = selected.get(key, "")
                    if value and Path(value).exists():
                        panels.append((label, Path(value)))
            except Exception as exc:
                analysis_record["voronoi_error"] = f"{type(exc).__name__}: {exc}"

        if routing_label in ("lines", "mixed"):
            try:
                cw_result = cw_mod.analyze_image(
                    image_path=str(mask_path),
                    output_dir=str(case_dir / "colorwheel_output"),
                    num_clusters=8,
                )
                analysis_record["colorwheel"] = cw_result
                if isinstance(cw_result, dict):
                    for label, key in [
                        ("Color-wheel orientation map", "color_wheel_image"),
                        ("One-phase map", "one_phase_image"),
                    ]:
                        value = cw_result.get(key, "")
                        if value and Path(value).exists():
                            panels.append((label, Path(value)))
            except Exception as exc:
                analysis_record["colorwheel_error"] = f"{type(exc).__name__}: {exc}"

        # Limit the publication sheet to the first six informative panels.
        make_sheet(panels[:6], case_dir / "case_study_figure.png")
        with (case_dir / "analysis_results.json").open("w", encoding="utf-8") as f:
            json.dump(analysis_record, f, indent=2, default=str)

        summary = {
            "case_name": case_name,
            "relative_path": rel,
            "true_label": case["true_label"].strip().lower(),
            "predicted_label_raw": raw_pred,
            "routing_label_used_by_current_app": routing_label,
            "confidence": float(prediction["confidence"]),
            "dots_probability": float(prediction["probabilities"].get("dots", 0.0)),
            "irregular_probability": float(prediction["probabilities"].get("irregular", 0.0)),
            "lines_probability": float(prediction["probabilities"].get("lines", 0.0)),
            "mixed_probability": float(prediction["probabilities"].get("mixed", 0.0)),
            "classification_correct": raw_pred == case["true_label"].strip().lower(),
            "mask_source": mask_source,
            "case_figure": str(case_dir / "case_study_figure.png"),
            "notes": case.get("notes", ""),
        }
        summaries.append(summary)
        print(
            f"[{idx:02d}/{len(cases):02d}] {case_name}: true={summary['true_label']}, "
            f"pred={raw_pred}, confidence={summary['confidence']:.4f}"
        )

    write_csv(output_dir / "case_study_summary.csv", summaries)
    write_json(output_dir / "case_study_protocol.json", {
        "cases_csv": str(cases_csv),
        "n_cases": len(summaries),
        "routing_note": (
            "The current Flask application maps a raw CNN prediction of 'irregular' to the "
            "'mixed' routing branch. This script records both labels so the manuscript does not "
            "hide that implementation choice."
        ),
        "reporting_note": (
            "Case studies illustrate workflow behavior. They must not replace the full test-set "
            "classification and segmentation metrics."
        ),
    })
    print(f"Case-study experiment complete: {output_dir}")


if __name__ == "__main__":
    main()
