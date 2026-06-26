#!/usr/bin/env python3
"""
Experiment 4: end-to-end AFM case-study generator.

This script loads the final production CNN and U-Net once, then runs six fixed
case studies through the same prediction-dependent routing used by the
application:

dots -> Voronoi
lines -> fixed full-resolution ColorWheel
mixed -> Voronoi + fixed full-resolution ColorWheel
irregular -> no downstream module

Four cases are representative class-median examples. Two are retained failure
cases: Mixed_01 for severe under-segmentation and lines_01 for a high-confidence
classification/routing error.

The script creates:
- original, ground-truth, predicted-mask, and disagreement images;
- classifier probability charts;
- full downstream output folders;
- one publication panel per case;
- one combined six-case overview;
- CSV and JSON summaries;
- methodology and run metadata;
- a ZIP containing the complete Experiment 4 result folder.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import gc
import hashlib
import importlib.util
import inspect
import io
import json
import math
import os
import platform
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

CNN_SCRIPT_NAME = "1.cnn_inference 1.py"
UNET_SCRIPT_NAME = "2.segmentation.py"
VORONOI_SCRIPT_NAME = "2.voronoi.py"
COLORWHEEL_SCRIPT_NAME = "3.colorwheel.py"
CNN_MODEL_NAME = "cnn_rgb_classifier.pth"
UNET_MODEL_NAME = "best_quality_unet.pt"

CNN_IMAGE_SIZE = 217
CNN_IN_CHANNELS = 3
UNET_THRESHOLD = 0.5

VORONOI_IMAGE_SIZE = 1.0
VORONOI_THRESHOLD_EDGE = 0.025
VORONOI_MAX_SIZE = 1024

COLORWHEEL_NUM_CLUSTERS = 8
COLORWHEEL_MAX_DIMENSION = 0
COLORWHEEL_ORIENTATION_MAX_DIMENSION = 1024
COLORWHEEL_RANDOM_STATE = 42
COLORWHEEL_MAX_FIT_SAMPLES = 10000
COLORWHEEL_MIN_COMPONENT_SIZE = 15

CLASS_ORDER = ["dots", "irregular", "lines", "mixed"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--analysis-dir", default=None)
    parser.add_argument("--test-dir", default="test")
    parser.add_argument(
        "--case-manifest",
        default="Experiment_4_End_to_End_Case_Study/experiment_4_selected_cases.csv",
    )
    parser.add_argument(
        "--ground-truth-dir",
        default="Experiment_4_End_to_End_Case_Study/ground_truth_masks",
    )
    parser.add_argument(
        "--output-dir",
        default="evaluation_outputs/experiment_4_end_to_end",
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default="auto",
    )
    parser.add_argument(
        "--keep-intermediate-files",
        action="store_true",
        default=True,
        help="Retain complete downstream outputs. Enabled by default.",
    )
    return parser.parse_args()


def resolve(base: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def find_analysis_dir(project_dir: Path, explicit: str | None) -> Path:
    candidates = (
        [resolve(project_dir, explicit)]
        if explicit
        else [project_dir / "backend", project_dir]
    )
    required = [
        CNN_SCRIPT_NAME,
        UNET_SCRIPT_NAME,
        VORONOI_SCRIPT_NAME,
        COLORWHEEL_SCRIPT_NAME,
    ]
    for candidate in candidates:
        if all((candidate / name).exists() for name in required):
            return candidate.resolve()
    raise FileNotFoundError(
        "Could not find the backend directory containing all analysis modules."
    )


def ensure_real_model(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    head = path.read_bytes()[:200]
    if b"version https://git-lfs.github.com/spec" in head:
        raise RuntimeError(f"{path.name} is a Git LFS pointer. Run `git lfs pull`.")
    if path.stat().st_size < 10000:
        raise RuntimeError(f"{path.name} is unexpectedly small.")


def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def choose_device(torch_module, requested: str):
    if requested == "cuda":
        if not torch_module.cuda.is_available():
            raise RuntimeError("CUDA requested but unavailable.")
        return torch_module.device("cuda")
    if requested == "cpu":
        return torch_module.device("cpu")
    return torch_module.device(
        "cuda" if torch_module.cuda.is_available() else "cpu"
    )


def synchronize(torch_module, device) -> None:
    if getattr(device, "type", str(device)) == "cuda":
        torch_module.cuda.synchronize()


def validate_fixed_colorwheel(module) -> None:
    parameters = inspect.signature(module.analyze_image).parameters
    required = {
        "num_clusters",
        "max_dimension",
        "orientation_max_dimension",
        "random_state",
        "max_fit_samples",
        "min_component_size",
    }
    missing = required.difference(parameters)
    if missing:
        raise RuntimeError(
            "The active 3.colorwheel.py is not the validated fixed "
            "full-resolution implementation. Missing parameters: "
            + ", ".join(sorted(missing))
        )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def probability_details(result: dict[str, Any]) -> tuple[dict[str, float], float, float]:
    probabilities = {
        str(key).lower(): float(value)
        for key, value in (result.get("probabilities") or {}).items()
    }
    ordered = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
    confidence = float(result.get("confidence", ordered[0][1] if ordered else 0.0))
    margin = ordered[0][1] - ordered[1][1] if len(ordered) > 1 else confidence
    return probabilities, confidence, margin


def route_for(label: str) -> tuple[bool, bool, str]:
    if label == "dots":
        return True, False, "voronoi"
    if label == "lines":
        return False, True, "colorwheel"
    if label == "mixed":
        return True, True, "voronoi+colorwheel"
    if label == "irregular":
        return False, False, "none"
    raise ValueError(f"Unsupported predicted class: {label}")


def quiet_call(function):
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        return function()


def copy_image(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def disagreement_map(ground_truth_path: Path, prediction_path: Path, output_path: Path):
    gt = cv2.imread(str(ground_truth_path), cv2.IMREAD_GRAYSCALE)
    pred = cv2.imread(str(prediction_path), cv2.IMREAD_GRAYSCALE)
    if gt is None or pred is None:
        raise ValueError("Could not read ground-truth or predicted mask.")
    if gt.shape != pred.shape:
        pred = cv2.resize(pred, (gt.shape[1], gt.shape[0]), interpolation=cv2.INTER_NEAREST)

    gt_foreground = gt < 128
    pred_foreground = pred < 128

    rgb = np.zeros((*gt.shape, 3), dtype=np.uint8)
    rgb[gt_foreground & pred_foreground] = [0, 180, 0]       # TP green
    rgb[~gt_foreground & pred_foreground] = [220, 0, 0]      # FP red
    rgb[gt_foreground & ~pred_foreground] = [0, 80, 230]     # FN blue
    Image.fromarray(rgb).save(output_path)

    tp = int(np.sum(gt_foreground & pred_foreground))
    fp = int(np.sum(~gt_foreground & pred_foreground))
    fn = int(np.sum(gt_foreground & ~pred_foreground))
    tn = int(np.sum(~gt_foreground & ~pred_foreground))
    dice = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 1.0
    iou = tp / (tp + fp + fn) if (tp + fp + fn) else 1.0

    return {
        "tp_pixels": tp,
        "fp_pixels": fp,
        "fn_pixels": fn,
        "tn_pixels": tn,
        "dice_recomputed": dice,
        "iou_recomputed": iou,
    }


def create_probability_chart(
    probabilities: dict[str, float],
    output_path: Path,
    predicted_label: str,
) -> None:
    values = [probabilities.get(label, 0.0) for label in CLASS_ORDER]
    fig, ax = plt.subplots(figsize=(5.6, 4.0))
    positions = np.arange(len(CLASS_ORDER))
    ax.bar(positions, values)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Softmax probability")
    ax.set_title(f"CNN prediction: {predicted_label}")
    ax.set_xticks(positions)
    ax.set_xticklabels([label.capitalize() for label in CLASS_ORDER])
    ax.grid(axis="y", alpha=0.25)
    for position, value in zip(positions, values):
        ax.text(position, min(value + 0.025, 1.01), f"{value:.3f}", ha="center", fontsize=8)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def select_voronoi_images(result: dict[str, Any]) -> list[Path]:
    selected = result.get("selected_images") or {}
    preferred = [
        selected.get("voronoi_overlay"),
        selected.get("morphology_map"),
        selected.get("snapshot"),
        selected.get("original"),
    ]
    paths = [Path(value) for value in preferred if value and Path(value).exists()]
    return paths[:2]


def create_route_note(
    output_path: Path,
    predicted_label: str,
    true_label: str,
    expected_route: str,
) -> None:
    image = Image.new("RGB", (900, 650), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    lines = [
        "No downstream module executed",
        "",
        f"Fresh CNN prediction: {predicted_label}",
        f"Externally verified class: {true_label}",
        f"Executed route: none",
        f"Reference expected route: {expected_route}",
    ]
    if predicted_label == true_label == "irregular":
        lines.extend([
            "",
            "This is the intended behavior for irregular morphology.",
            "The pipeline terminates after segmentation.",
        ])
    elif predicted_label != true_label:
        lines.extend([
            "",
            "This is a classification-driven routing failure.",
            "The expected morphology-specific module was not executed.",
        ])

    y = 150
    for line in lines:
        draw.text((90, y), line, fill="black", font=font)
        y += 48
    image.save(output_path)


def fit_panel(image_path: Path, width: int = 520, height: int = 390) -> Image.Image:
    image = Image.open(image_path).convert("RGB")
    image = ImageOps.contain(image, (width - 24, height - 54))
    canvas = Image.new("RGB", (width, height), "white")
    x = (width - image.width) // 2
    y = 42 + (height - 42 - image.height) // 2
    canvas.paste(image, (x, y))
    return canvas


def create_case_panel(
    title: str,
    panels: list[tuple[str, Path]],
    output_png: Path,
    output_pdf: Path,
) -> None:
    columns = 3
    rows = math.ceil(len(panels) / columns)
    panel_width, panel_height = 520, 390
    title_height = 70
    canvas = Image.new(
        "RGB",
        (columns * panel_width, title_height + rows * panel_height),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text((24, 24), title, fill="black", font=font)

    for index, (label, path) in enumerate(panels):
        row = index // columns
        column = index % columns
        x = column * panel_width
        y = title_height + row * panel_height
        panel = fit_panel(path, panel_width, panel_height)
        canvas.paste(panel, (x, y))
        draw.text((x + 12, y + 12), label, fill="black", font=font)

    canvas.save(output_png, dpi=(300, 300))
    canvas.save(output_pdf, "PDF", resolution=300)


def create_overview(
    case_panel_paths: list[tuple[str, Path]],
    output_png: Path,
    output_pdf: Path,
) -> None:
    columns = 2
    rows = math.ceil(len(case_panel_paths) / columns)
    panel_w, panel_h = 760, 560
    canvas = Image.new("RGB", (columns * panel_w, rows * panel_h), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    for index, (label, path) in enumerate(case_panel_paths):
        image = Image.open(path).convert("RGB")
        image = ImageOps.contain(image, (panel_w - 30, panel_h - 50))
        row = index // columns
        column = index % columns
        x = column * panel_w
        y = row * panel_h
        canvas.paste(image, (x + (panel_w - image.width)//2, y + 36))
        draw.text((x + 12, y + 12), label, fill="black", font=font)

    canvas.save(output_png, dpi=(300, 300))
    canvas.save(output_pdf, "PDF", resolution=300)


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir).expanduser().resolve()
    analysis_dir = find_analysis_dir(project_dir, args.analysis_dir)
    test_dir = resolve(project_dir, args.test_dir)
    manifest_path = resolve(project_dir, args.case_manifest)
    ground_truth_dir = resolve(project_dir, args.ground_truth_dir)
    output_dir = resolve(project_dir, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_dir = project_dir / "models"
    ensure_real_model(model_dir / CNN_MODEL_NAME)
    ensure_real_model(model_dir / UNET_MODEL_NAME)

    records = read_csv(manifest_path)
    if len(records) != 6:
        raise RuntimeError(f"Expected 6 fixed case studies, found {len(records)}.")

    import torch

    cnn = import_module("exp4_cnn", analysis_dir / CNN_SCRIPT_NAME)
    unet = import_module("exp4_unet", analysis_dir / UNET_SCRIPT_NAME)

    if str(analysis_dir) not in sys.path:
        sys.path.insert(0, str(analysis_dir))

    voronoi = import_module("exp4_voronoi", analysis_dir / VORONOI_SCRIPT_NAME)
    colorwheel = import_module("exp4_colorwheel", analysis_dir / COLORWHEEL_SCRIPT_NAME)
    validate_fixed_colorwheel(colorwheel)

    device = choose_device(torch, args.device)
    cnn_model = cnn.load_model(
        str(model_dir / CNN_MODEL_NAME),
        in_channels=CNN_IN_CHANNELS,
        device=device,
    )
    unet_model, unet_image_size, unet_device = unet.load_model(
        str(model_dir / UNET_MODEL_NAME),
        device=str(device),
    )

    summary_rows: list[dict[str, Any]] = []
    case_panel_paths: list[tuple[str, Path]] = []
    failures: list[dict[str, Any]] = []

    for case_index, record in enumerate(records, start=1):
        case_id = record["case_id"]
        relative_path = Path(record["relative_path"])
        case_dir = output_dir / f"{case_id}_{relative_path.stem}"
        case_dir.mkdir(parents=True, exist_ok=True)

        print(f"[{case_index}/6] {case_id}: {record['relative_path']}")

        try:
            image_path = (test_dir / relative_path).resolve()
            if not image_path.exists():
                raise FileNotFoundError(image_path)

            gt_candidates = sorted(
                ground_truth_dir.glob(f"{case_id}_*_ground_truth.png")
            )
            if len(gt_candidates) != 1:
                raise RuntimeError(
                    f"Expected one ground-truth file for {case_id}, found {len(gt_candidates)}."
                )
            gt_source = gt_candidates[0]

            original_copy = copy_image(
                image_path,
                case_dir / f"original{image_path.suffix.lower()}",
            )
            gt_copy = copy_image(
                gt_source,
                case_dir / "ground_truth_mask.png",
            )

            case_start = time.perf_counter()

            synchronize(torch, device)
            cnn_start = time.perf_counter()
            cnn_result = cnn.predict_image(
                cnn_model,
                str(image_path),
                image_size=CNN_IMAGE_SIZE,
                in_channels=CNN_IN_CHANNELS,
                device=device,
            )
            synchronize(torch, device)
            cnn_ms = (time.perf_counter() - cnn_start) * 1000.0

            predicted_label = str(cnn_result["predicted_class"]).strip().lower()
            probabilities, confidence, confidence_margin = probability_details(cnn_result)
            run_voronoi, run_colorwheel, route = route_for(predicted_label)

            probability_chart = case_dir / "classification_probabilities.png"
            create_probability_chart(
                probabilities,
                probability_chart,
                predicted_label,
            )

            tensor, original_size = unet.preprocess_image(
                str(image_path),
                img_size=unet_image_size,
                denoise=0,
                sharpen=0,
                invert=False,
            )
            synchronize(torch, unet_device)
            unet_start = time.perf_counter()
            predicted_mask = unet.predict_mask(
                unet_model,
                tensor,
                unet_device,
                threshold=UNET_THRESHOLD,
            )
            synchronize(torch, unet_device)
            unet_inference_ms = (time.perf_counter() - unet_start) * 1000.0

            predicted_mask_path = case_dir / "predicted_mask.png"
            unet.save_mask(predicted_mask, str(predicted_mask_path), original_size)

            disagreement_path = case_dir / "disagreement_map.png"
            disagreement = disagreement_map(
                gt_copy,
                predicted_mask_path,
                disagreement_path,
            )

            voronoi_result: dict[str, Any] = {}
            voronoi_images: list[Path] = []
            voronoi_status = "not_applicable"
            voronoi_ms: float | str = ""

            if run_voronoi:
                start = time.perf_counter()
                voronoi_result = quiet_call(
                    lambda: voronoi.run_voronoi_analysis(
                        image_path=str(predicted_mask_path),
                        image_size=VORONOI_IMAGE_SIZE,
                        output_dir=str(case_dir / "voronoi_outputs"),
                        threshold_edge=VORONOI_THRESHOLD_EDGE,
                        max_size=VORONOI_MAX_SIZE,
                    )
                )
                voronoi_ms = (time.perf_counter() - start) * 1000.0
                if isinstance(voronoi_result, dict) and voronoi_result.get("ran_voronoi"):
                    voronoi_status = "completed"
                    voronoi_images = select_voronoi_images(voronoi_result)
                else:
                    voronoi_status = (
                        "skipped_"
                        + str(
                            (voronoi_result or {}).get(
                                "reason",
                                "no_output",
                            )
                        ).replace(" ", "_")
                    )

            colorwheel_result: dict[str, Any] = {}
            colorwheel_status = "not_applicable"
            colorwheel_ms: float | str = ""
            colorwheel_images: list[Path] = []

            if run_colorwheel:
                colorwheel_dir = case_dir / "colorwheel_outputs"
                start = time.perf_counter()
                colorwheel_result = quiet_call(
                    lambda: colorwheel.analyze_image(
                        image_path=str(predicted_mask_path),
                        output_dir=str(colorwheel_dir),
                        num_clusters=COLORWHEEL_NUM_CLUSTERS,
                        max_dimension=COLORWHEEL_MAX_DIMENSION,
                        orientation_max_dimension=COLORWHEEL_ORIENTATION_MAX_DIMENSION,
                        random_state=COLORWHEEL_RANDOM_STATE,
                        max_fit_samples=COLORWHEEL_MAX_FIT_SAMPLES,
                        min_component_size=COLORWHEEL_MIN_COMPONENT_SIZE,
                    )
                )
                colorwheel_ms = (time.perf_counter() - start) * 1000.0
                one_phase = Path(str(colorwheel_result.get("one_phase_image", "")))
                full_color = Path(str(colorwheel_result.get("color_wheel_image", "")))
                colorwheel_images = [
                    path for path in (one_phase, full_color) if path.exists()
                ]
                colorwheel_status = (
                    "completed" if len(colorwheel_images) == 2 else "failed_missing_output"
                )

            route_note_path = case_dir / "route_note.png"
            if route == "none":
                create_route_note(
                    route_note_path,
                    predicted_label,
                    record["true_label"],
                    record["expected_route"],
                )

            full_pipeline_ms = (time.perf_counter() - case_start) * 1000.0

            panel_items: list[tuple[str, Path]] = [
                ("Original AFM image", original_copy),
                ("Ground-truth mask", gt_copy),
                ("Predicted U-Net mask", predicted_mask_path),
                ("CNN class probabilities", probability_chart),
                ("Segmentation disagreement", disagreement_path),
            ]

            if route == "voronoi":
                if voronoi_images:
                    panel_items.append(("Voronoi overlay", voronoi_images[0]))
                if len(voronoi_images) > 1:
                    panel_items.append(("Voronoi morphology map", voronoi_images[1]))
            elif route == "colorwheel":
                if colorwheel_images:
                    panel_items.append(("ColorWheel one-phase output", colorwheel_images[0]))
                if len(colorwheel_images) > 1:
                    panel_items.append(("Full ColorWheel output", colorwheel_images[1]))
            elif route == "voronoi+colorwheel":
                if voronoi_images:
                    panel_items.append(("Voronoi overlay", voronoi_images[0]))
                if colorwheel_images:
                    panel_items.append(("ColorWheel one-phase output", colorwheel_images[0]))
            else:
                panel_items.append(("Routing outcome", route_note_path))

            panel_png = output_dir / f"Figure_Exp4_{case_index}_{case_id}.png"
            panel_pdf = output_dir / f"Figure_Exp4_{case_index}_{case_id}.pdf"
            title = (
                f"{record['case_role']} | true={record['true_label']} | "
                f"predicted={predicted_label} | route={route} | "
                f"Dice={disagreement['dice_recomputed']:.3f}"
            )
            create_case_panel(title, panel_items, panel_png, panel_pdf)
            case_panel_paths.append((record["case_role"], panel_png))

            summary = {
                **record,
                "fresh_predicted_label": predicted_label,
                "fresh_prediction_matches_reference": (
                    predicted_label == record["reference_predicted_label"]
                ),
                "fresh_prediction_correct": (
                    predicted_label == record["true_label"]
                ),
                "fresh_confidence": confidence,
                "fresh_confidence_margin": confidence_margin,
                "fresh_probabilities_json": json.dumps(probabilities, sort_keys=True),
                "executed_route": route,
                "route_matches_reference": route == record["expected_route"],
                "recomputed_dice": disagreement["dice_recomputed"],
                "recomputed_iou": disagreement["iou_recomputed"],
                "tp_pixels": disagreement["tp_pixels"],
                "tn_pixels": disagreement["tn_pixels"],
                "fp_pixels": disagreement["fp_pixels"],
                "fn_pixels": disagreement["fn_pixels"],
                "cnn_ms": cnn_ms,
                "unet_inference_ms": unet_inference_ms,
                "voronoi_status": voronoi_status,
                "voronoi_ms": voronoi_ms,
                "colorwheel_status": colorwheel_status,
                "colorwheel_ms": colorwheel_ms,
                "full_pipeline_ms": full_pipeline_ms,
                "case_directory": str(case_dir),
                "panel_png": str(panel_png),
                "status": "completed",
            }
            summary_rows.append(summary)

            (case_dir / "case_result.json").write_text(
                json.dumps(
                    {
                        **summary,
                        "voronoi_result": voronoi_result,
                        "colorwheel_result": colorwheel_result,
                    },
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )

        except Exception as exc:
            failures.append({
                "case_id": case_id,
                "relative_path": record["relative_path"],
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            })
            print(f"  FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)

        gc.collect()

    write_csv(output_dir / "experiment_4_case_summary.csv", summary_rows)
    if failures:
        write_csv(output_dir / "experiment_4_failures.csv", failures)

    overview_png = output_dir / "Figure_Exp4_0_Combined_Overview.png"
    overview_pdf = output_dir / "Figure_Exp4_0_Combined_Overview.pdf"
    if case_panel_paths:
        create_overview(case_panel_paths, overview_png, overview_pdf)

    metadata = [{
        "timestamp_local": time.strftime("%Y-%m-%d %H:%M:%S"),
        "project_dir": str(project_dir),
        "analysis_dir": str(analysis_dir),
        "test_dir": str(test_dir),
        "case_manifest": str(manifest_path),
        "case_manifest_sha256": sha256(manifest_path),
        "case_count_expected": 6,
        "case_count_completed": len(summary_rows),
        "case_count_failed": len(failures),
        "device": str(device),
        "python_version": platform.python_version(),
        "operating_system": platform.platform(),
        "pytorch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cnn_model_sha256": sha256(model_dir / CNN_MODEL_NAME),
        "unet_model_sha256": sha256(model_dir / UNET_MODEL_NAME),
        "cnn_script_sha256": sha256(analysis_dir / CNN_SCRIPT_NAME),
        "unet_script_sha256": sha256(analysis_dir / UNET_SCRIPT_NAME),
        "voronoi_script_sha256": sha256(analysis_dir / VORONOI_SCRIPT_NAME),
        "colorwheel_script_sha256": sha256(analysis_dir / COLORWHEEL_SCRIPT_NAME),
        "unet_threshold": UNET_THRESHOLD,
        "voronoi_threshold_edge": VORONOI_THRESHOLD_EDGE,
        "voronoi_max_size": VORONOI_MAX_SIZE,
        "colorwheel_num_clusters": COLORWHEEL_NUM_CLUSTERS,
        "colorwheel_max_dimension": COLORWHEEL_MAX_DIMENSION,
        "colorwheel_orientation_max_dimension": COLORWHEEL_ORIENTATION_MAX_DIMENSION,
        "colorwheel_max_fit_samples": COLORWHEEL_MAX_FIT_SAMPLES,
        "colorwheel_min_component_size": COLORWHEEL_MIN_COMPONENT_SIZE,
    }]
    write_csv(output_dir / "experiment_4_run_metadata.csv", metadata)

    methodology = f"""Experiment 4 end-to-end case-study methodology
================================================

Purpose:
Qualitatively demonstrate the complete final AFM analysis workflow and show how
representative successes and retained failure cases propagate through
prediction-dependent routing.

Fixed cases:
- representative dots: dots/dots_09.png
- representative lines: lines/lines_03.png
- representative mixed: mixed/Mixed_04.png
- representative irregular: irregular/irregular_03.png
- segmentation failure: mixed/Mixed_01.png
- classification/routing failure: lines/lines_01.png

Selection:
The four representative cases were the images nearest the class-specific median
Dice score in Experiment 2. Mixed_01 was the lowest segmentation score in the
50-image set. lines_01 was retained because the CNN predicted irregular for a
true line morphology with confidence greater than 0.9999.

Pipeline:
Original image -> CNN class prediction -> U-Net predicted mask -> route based on
the fresh CNN prediction -> Voronoi and/or fixed full-resolution ColorWheel.

Routing:
- dots -> Voronoi
- lines -> ColorWheel
- mixed -> Voronoi + ColorWheel
- irregular -> no downstream analysis

Segmentation comparison:
Externally verified manual masks were used only to create disagreement maps and
recompute Dice and IoU for the case-study panels. They did not influence
classification, segmentation, routing, or downstream analysis.

Disagreement colors:
- green = true-positive foreground
- red = false-positive foreground
- blue = false-negative foreground
- black = true-negative background

Downstream settings:
- Voronoi threshold_edge = {VORONOI_THRESHOLD_EDGE}
- Voronoi max_size = {VORONOI_MAX_SIZE}
- ColorWheel full-resolution output: max_dimension = {COLORWHEEL_MAX_DIMENSION}
- ColorWheel orientation_max_dimension = {COLORWHEEL_ORIENTATION_MAX_DIMENSION}
- ColorWheel clusters = {COLORWHEEL_NUM_CLUSTERS}
- ColorWheel max_fit_samples = {COLORWHEEL_MAX_FIT_SAMPLES}
- ColorWheel min_component_size = {COLORWHEEL_MIN_COMPONENT_SIZE}

Interpretation:
Experiment 4 is a qualitative end-to-end software demonstration, not a new
accuracy or runtime benchmark. Quantitative performance is reported in
Experiments 1–3. No manual mask correction was introduced during these cases.
"""
    (output_dir / "experiment_4_methodology.txt").write_text(
        methodology,
        encoding="utf-8",
    )

    readme = f"""EXPERIMENT 4 RESULTS
====================

Completed cases: {len(summary_rows)}/6
Failures: {len(failures)}

Primary outputs:
- experiment_4_case_summary.csv
- experiment_4_run_metadata.csv
- experiment_4_methodology.txt
- Figure_Exp4_0_Combined_Overview.png
- Figure_Exp4_1_case_01.png through Figure_Exp4_6_case_06.png
- one folder per case containing all original and downstream outputs

The result ZIP preserves all case folders and publication panels.
"""
    (output_dir / "README.txt").write_text(readme, encoding="utf-8")

    zip_path = output_dir.parent / "experiment_4_end_to_end_results.zip"
    zip_path.unlink(missing_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in output_dir.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(output_dir.parent))

    print("\nExperiment 4 complete.")
    print(f"Completed cases: {len(summary_rows)}/6")
    print(f"Failures: {len(failures)}")
    print(f"Results: {output_dir}")
    print(f"ZIP: {zip_path}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
