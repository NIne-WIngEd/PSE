#!/usr/bin/env python3
"""
Experiment 3B: downstream AFM analysis timing.

Measures Voronoi and ColorWheel runtimes separately after U-Net masks have
already been generated. This isolates downstream computation from CNN/U-Net
timing.

Routing matches the Flask application:
- dots      -> Voronoi
- lines     -> ColorWheel
- mixed     -> Voronoi + ColorWheel
- irregular -> no downstream analysis

Outputs:
- downstream_timing_per_run.csv
- downstream_timing_per_image.csv
- downstream_timing_summary.csv
- downstream_routing_summary.csv
- downstream_failures.csv (only if failures occur)
- downstream_methodology.txt
- downstream_run_metadata.csv
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import math
import os
import platform
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
TRUE_VALUES = {"yes", "true", "1", "include", "included"}

UNET_SCRIPT_NAME = "2.segmentation.py"
UNET_MODEL_NAME = "best_quality_unet.pt"
VORONOI_SCRIPT_NAME = "2.voronoi.py"
COLORWHEEL_SCRIPT_NAME = "3.colorwheel.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Time Voronoi and ColorWheel downstream AFM analysis."
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Repository root containing backend, models, and an optional local test directory.",
    )
    parser.add_argument(
        "--analysis-dir",
        default=None,
        help="Directory containing analysis modules. Default: <project-dir>/backend.",
    )
    parser.add_argument(
        "--test-dir",
        default="test",
        help="Validation image folder relative to project-dir unless absolute.",
    )
    parser.add_argument(
        "--manifest",
        default="cnn_predictions_primary_reviewed.csv",
        help=(
            "Final classification CSV containing relative_path and predicted_label. "
            "Rows marked true in include_in_primary/include_in_evaluation are retained."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default="evaluation_outputs/experiment_3_downstream",
        help="Directory for timing outputs.",
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default="auto",
        help="Device used only to generate U-Net masks before timing.",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=3,
        help="Downstream repetitions per applicable image. Default: 3.",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=0,
        help="Limit images for a quick test. Use 0 for all images.",
    )
    parser.add_argument(
        "--keep-generated-outputs",
        action="store_true",
        help="Keep all Voronoi/ColorWheel output files. Default: delete after timing.",
    )
    parser.add_argument(
        "--keep-predicted-masks",
        action="store_true",
        help="Keep U-Net masks generated before downstream timing.",
    )
    return parser.parse_args()


def resolve_path(base: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def find_analysis_dir(project_dir: Path, explicit: str | None) -> Path:
    if explicit:
        candidate = resolve_path(project_dir, explicit)
    else:
        candidates = [project_dir / "backend", project_dir]
        candidate = next(
            (
                path
                for path in candidates
                if (path / UNET_SCRIPT_NAME).exists()
                and (path / VORONOI_SCRIPT_NAME).exists()
                and (path / COLORWHEEL_SCRIPT_NAME).exists()
            ),
            None,
        )
        if candidate is None:
            raise FileNotFoundError(
                "Could not locate backend analysis modules. Pass --analysis-dir explicitly."
            )

    required = [
        UNET_SCRIPT_NAME,
        VORONOI_SCRIPT_NAME,
        COLORWHEEL_SCRIPT_NAME,
    ]
    missing = [name for name in required if not (candidate / name).exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing required files in {candidate}: {', '.join(missing)}"
        )
    return candidate.resolve()


def ensure_real_model_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    head = path.read_bytes()[:200]
    if b"version https://git-lfs.github.com/spec" in head:
        raise RuntimeError(
            f"{path.name} is a Git LFS pointer. Run `git lfs pull` first."
        )
    if path.stat().st_size < 10_000:
        raise RuntimeError(
            f"{path.name} is unexpectedly small. Confirm real weights are present."
        )


def import_module_from_file(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in TRUE_VALUES


def load_manifest_records(
    manifest_path: Path,
    test_dir: Path,
    max_images: int,
) -> list[dict[str, str]]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with manifest_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fields = reader.fieldnames or []

        if "relative_path" not in fields:
            raise ValueError("Manifest must contain relative_path.")
        if "predicted_label" not in fields:
            raise ValueError(
                "Manifest must contain predicted_label from the finalized "
                "classification experiment."
            )

        include_column = next(
            (
                name
                for name in (
                    "include_in_evaluation",
                    "include_in_primary",
                    "include",
                )
                if name in fields
            ),
            None,
        )

        records: list[dict[str, str]] = []
        for row in reader:
            if include_column and not truthy(row.get(include_column, "")):
                continue

            relative = Path(row["relative_path"])
            image_path = (
                relative if relative.is_absolute() else test_dir / relative
            ).resolve()

            if not image_path.exists():
                raise FileNotFoundError(
                    f"Image listed in manifest was not found: {image_path}"
                )
            if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            predicted = str(row["predicted_label"]).strip().lower()
            if predicted not in {"dots", "lines", "mixed", "irregular"}:
                raise ValueError(
                    f"Unsupported predicted label `{predicted}` for "
                    f"{row['relative_path']}"
                )

            true_label = str(
                row.get("true_label", relative.parts[0])
            ).strip().lower()

            records.append(
                {
                    "relative_path": relative.as_posix(),
                    "true_label": true_label,
                    "predicted_label": predicted,
                    "image_path": str(image_path),
                }
            )

    if max_images > 0:
        records = records[:max_images]

    if not records:
        raise RuntimeError("No images were selected.")
    return records


def routing_for(predicted_label: str) -> tuple[bool, bool, str]:
    if predicted_label == "dots":
        return True, False, "voronoi"
    if predicted_label == "lines":
        return False, True, "colorwheel"
    if predicted_label == "mixed":
        return True, True, "voronoi+colorwheel"
    if predicted_label == "irregular":
        return False, False, "none"
    raise ValueError(f"Unsupported predicted label: {predicted_label}")


def write_csv(
    path: Path,
    rows: list[dict[str, Any]],
    fieldnames: list[str] | None = None,
) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = fieldnames or list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return ordered[low]
    fraction = position - low
    return ordered[low] + fraction * (ordered[high] - ordered[low])


def summarize_values(
    component: str,
    values: list[float],
    notes: str,
) -> dict[str, Any]:
    return {
        "component": component,
        "n_images": len(values),
        "mean_ms": statistics.fmean(values),
        "standard_deviation_ms": (
            statistics.stdev(values) if len(values) > 1 else 0.0
        ),
        "median_ms": statistics.median(values),
        "q1_ms": percentile(values, 0.25),
        "q3_ms": percentile(values, 0.75),
        "minimum_ms": min(values),
        "maximum_ms": max(values),
        "throughput_per_second_from_median": (
            1000.0 / statistics.median(values)
            if statistics.median(values) > 0
            else ""
        ),
        "notes": notes,
    }


def load_unet(analysis_dir: Path, model_dir: Path, requested_device: str):
    import torch

    unet_mod = import_module_from_file(
        "unet_downstream_timing",
        analysis_dir / UNET_SCRIPT_NAME,
    )
    device = choose_device(torch, requested_device)
    model, img_size, model_device = unet_mod.load_model(
        str(model_dir / UNET_MODEL_NAME),
        device=str(device),
    )
    synchronize(torch, model_device)
    return torch, unet_mod, model, img_size, model_device


def generate_predicted_masks(
    records: list[dict[str, str]],
    analysis_dir: Path,
    model_dir: Path,
    requested_device: str,
    mask_root: Path,
) -> tuple[dict[str, Path], str]:
    torch_module, unet_mod, model, img_size, model_device = load_unet(
        analysis_dir, model_dir, requested_device
    )

    # One discarded U-Net warm-up.
    first = Path(records[0]["image_path"])
    tensor, original_size = unet_mod.preprocess_image(
        str(first),
        img_size=img_size,
        denoise=0,
        sharpen=0,
        invert=False,
    )
    _ = unet_mod.predict_mask(model, tensor, model_device, threshold=0.5)
    synchronize(torch_module, model_device)

    masks: dict[str, Path] = {}
    for index, record in enumerate(records, start=1):
        image_path = Path(record["image_path"])
        mask_path = (
            mask_root
            / record["predicted_label"]
            / f"{image_path.stem}_predicted_mask.png"
        )
        mask_path.parent.mkdir(parents=True, exist_ok=True)

        tensor, original_size = unet_mod.preprocess_image(
            str(image_path),
            img_size=img_size,
            denoise=0,
            sharpen=0,
            invert=False,
        )
        predicted_mask = unet_mod.predict_mask(
            model,
            tensor,
            model_device,
            threshold=0.5,
        )
        synchronize(torch_module, model_device)
        unet_mod.save_mask(predicted_mask, str(mask_path), original_size)
        masks[record["relative_path"]] = mask_path

        print(
            f"[Mask {index:03d}/{len(records):03d}] "
            f"{record['relative_path']}"
        )

    return masks, str(model_device)


def quiet_timed_call(function) -> tuple[float, Any]:
    # Suppress extensive diagnostic printing so terminal I/O does not inflate
    # computational timing.
    sink = io.StringIO()
    start = time.perf_counter()
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        result = function()
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return elapsed_ms, result


def stage_mask(source_mask: Path, run_dir: Path) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    staged = run_dir / "predicted_mask.png"
    shutil.copy2(source_mask, staged)
    return staged


def warm_downstream(
    records: list[dict[str, str]],
    masks: dict[str, Path],
    vor_mod,
    cw_mod,
    warmup_root: Path,
) -> None:
    vor_record = next(
        (
            record
            for record in records
            if routing_for(record["predicted_label"])[0]
        ),
        None,
    )
    cw_record = next(
        (
            record
            for record in records
            if routing_for(record["predicted_label"])[1]
        ),
        None,
    )

    if vor_record:
        run_dir = warmup_root / "voronoi"
        staged = stage_mask(
            masks[vor_record["relative_path"]],
            run_dir,
        )
        quiet_timed_call(
            lambda: vor_mod.run_voronoi_analysis(
                image_path=str(staged),
                image_size=1.0,
                output_dir=str(run_dir / "voronoi_outputs"),
                threshold_edge=0.025,
                max_size=1024,
            )
        )

    if cw_record:
        run_dir = warmup_root / "colorwheel"
        staged = stage_mask(
            masks[cw_record["relative_path"]],
            run_dir,
        )
        quiet_timed_call(
            lambda: cw_mod.analyze_image(
                image_path=str(staged),
                output_dir=str(run_dir / "colorwheel_output"),
                num_clusters=8,
            )
        )

    shutil.rmtree(warmup_root, ignore_errors=True)


def run_downstream_timing(
    records: list[dict[str, str]],
    masks: dict[str, Path],
    analysis_dir: Path,
    output_dir: Path,
    repeats: int,
    keep_outputs: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    # The local module directory must be importable because 2.voronoi.py imports
    # voronoi_mask_pipeline and voronoi_v7 by module name.
    if str(analysis_dir) not in sys.path:
        sys.path.insert(0, str(analysis_dir))

    module_import_start = time.perf_counter()
    vor_mod = import_module_from_file(
        "voronoi_downstream_timing",
        analysis_dir / VORONOI_SCRIPT_NAME,
    )
    cw_mod = import_module_from_file(
        "colorwheel_downstream_timing",
        analysis_dir / COLORWHEEL_SCRIPT_NAME,
    )
    module_import_ms = (time.perf_counter() - module_import_start) * 1000.0

    runtime_root = output_dir / "runtime_outputs"
    runtime_root.mkdir(parents=True, exist_ok=True)

    warm_downstream(
        records,
        masks,
        vor_mod,
        cw_mod,
        runtime_root / "_discarded_warmup",
    )

    per_run_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []

    for image_index, record in enumerate(records, start=1):
        run_voronoi, run_colorwheel, route = routing_for(
            record["predicted_label"]
        )
        print(
            f"[Downstream {image_index:03d}/{len(records):03d}] "
            f"{record['relative_path']} -> {route}"
        )

        if route == "none":
            per_run_rows.append(
                {
                    "relative_path": record["relative_path"],
                    "true_label": record["true_label"],
                    "predicted_label": record["predicted_label"],
                    "routing": route,
                    "repeat": 0,
                    "voronoi_ms": "",
                    "voronoi_status": "not_applicable",
                    "voronoi_ran_analysis": "",
                    "colorwheel_ms": "",
                    "colorwheel_status": "not_applicable",
                    "downstream_total_ms": 0.0,
                    "overall_status": "completed_no_downstream",
                }
            )
            continue

        for repeat in range(1, repeats + 1):
            run_dir = (
                runtime_root
                / record["predicted_label"]
                / Path(record["relative_path"]).stem
                / f"repeat_{repeat}"
            )
            staged_mask = stage_mask(
                masks[record["relative_path"]],
                run_dir,
            )

            voronoi_ms: float | str = ""
            voronoi_status = "not_applicable"
            voronoi_ran_analysis: bool | str = ""
            colorwheel_ms: float | str = ""
            colorwheel_status = "not_applicable"
            total_ms = 0.0
            overall_status = "completed"

            if run_voronoi:
                try:
                    voronoi_ms, result = quiet_timed_call(
                        lambda: vor_mod.run_voronoi_analysis(
                            image_path=str(staged_mask),
                            image_size=1.0,
                            output_dir=str(run_dir / "voronoi_outputs"),
                            threshold_edge=0.025,
                            max_size=1024,
                        )
                    )
                    total_ms += float(voronoi_ms)
                    if isinstance(result, dict):
                        voronoi_ran_analysis = bool(
                            result.get("ran_voronoi", False)
                        )
                        if voronoi_ran_analysis:
                            voronoi_status = "completed"
                        else:
                            reason = str(result.get("reason", "skipped"))
                            voronoi_status = f"skipped: {reason}"
                    elif result is None:
                        voronoi_status = "failed: returned_none"
                        overall_status = "partial_or_failed"
                    else:
                        voronoi_status = "completed_unexpected_result_type"
                except Exception as exc:
                    voronoi_status = (
                        f"failed: {type(exc).__name__}: {exc}"
                    )
                    overall_status = "partial_or_failed"
                    failure_rows.append(
                        {
                            "relative_path": record["relative_path"],
                            "predicted_label": record["predicted_label"],
                            "repeat": repeat,
                            "component": "voronoi",
                            "error_type": type(exc).__name__,
                            "error_message": str(exc),
                        }
                    )

            if run_colorwheel:
                try:
                    colorwheel_ms, _ = quiet_timed_call(
                        lambda: cw_mod.analyze_image(
                            image_path=str(staged_mask),
                            output_dir=str(run_dir / "colorwheel_output"),
                            num_clusters=8,
                        )
                    )
                    total_ms += float(colorwheel_ms)
                    colorwheel_status = "completed"
                except Exception as exc:
                    colorwheel_status = (
                        f"failed: {type(exc).__name__}: {exc}"
                    )
                    overall_status = "partial_or_failed"
                    failure_rows.append(
                        {
                            "relative_path": record["relative_path"],
                            "predicted_label": record["predicted_label"],
                            "repeat": repeat,
                            "component": "colorwheel",
                            "error_type": type(exc).__name__,
                            "error_message": str(exc),
                        }
                    )

            per_run_rows.append(
                {
                    "relative_path": record["relative_path"],
                    "true_label": record["true_label"],
                    "predicted_label": record["predicted_label"],
                    "routing": route,
                    "repeat": repeat,
                    "voronoi_ms": voronoi_ms,
                    "voronoi_status": voronoi_status,
                    "voronoi_ran_analysis": voronoi_ran_analysis,
                    "colorwheel_ms": colorwheel_ms,
                    "colorwheel_status": colorwheel_status,
                    "downstream_total_ms": total_ms,
                    "overall_status": overall_status,
                }
            )

            if not keep_outputs:
                shutil.rmtree(run_dir, ignore_errors=True)

    write_csv(output_dir / "downstream_timing_per_run.csv", per_run_rows)
    if failure_rows:
        write_csv(output_dir / "downstream_failures.csv", failure_rows)

    # Build one row per image from successful numerical timings.
    per_image_rows: list[dict[str, Any]] = []
    for record in records:
        route = routing_for(record["predicted_label"])[2]
        matching = [
            row
            for row in per_run_rows
            if row["relative_path"] == record["relative_path"]
        ]

        if route == "none":
            per_image_rows.append(
                {
                    "relative_path": record["relative_path"],
                    "true_label": record["true_label"],
                    "predicted_label": record["predicted_label"],
                    "routing": route,
                    "repeats_expected": 0,
                    "successful_repeats": 1,
                    "voronoi_median_ms": "",
                    "voronoi_mean_ms": "",
                    "voronoi_sd_ms": "",
                    "colorwheel_median_ms": "",
                    "colorwheel_mean_ms": "",
                    "colorwheel_sd_ms": "",
                    "downstream_total_median_ms": 0.0,
                    "downstream_total_mean_ms": 0.0,
                    "downstream_total_sd_ms": 0.0,
                    "status": "completed_no_downstream",
                }
            )
            continue

        successful = [
            row
            for row in matching
            if row["overall_status"] == "completed"
        ]

        def numeric_values(field: str) -> list[float]:
            values = []
            for row in successful:
                value = row[field]
                if value not in ("", None):
                    values.append(float(value))
            return values

        vor_values = numeric_values("voronoi_ms")
        cw_values = numeric_values("colorwheel_ms")
        total_values = numeric_values("downstream_total_ms")

        def describe(values: list[float]):
            if not values:
                return "", "", ""
            return (
                statistics.median(values),
                statistics.fmean(values),
                statistics.stdev(values) if len(values) > 1 else 0.0,
            )

        vor_median, vor_mean, vor_sd = describe(vor_values)
        cw_median, cw_mean, cw_sd = describe(cw_values)
        total_median, total_mean, total_sd = describe(total_values)

        per_image_rows.append(
            {
                "relative_path": record["relative_path"],
                "true_label": record["true_label"],
                "predicted_label": record["predicted_label"],
                "routing": route,
                "repeats_expected": repeats,
                "successful_repeats": len(successful),
                "voronoi_median_ms": vor_median,
                "voronoi_mean_ms": vor_mean,
                "voronoi_sd_ms": vor_sd,
                "colorwheel_median_ms": cw_median,
                "colorwheel_mean_ms": cw_mean,
                "colorwheel_sd_ms": cw_sd,
                "downstream_total_median_ms": total_median,
                "downstream_total_mean_ms": total_mean,
                "downstream_total_sd_ms": total_sd,
                "status": (
                    "completed"
                    if len(successful) == repeats
                    else "incomplete_or_failed"
                ),
            }
        )

    write_csv(
        output_dir / "downstream_timing_per_image.csv",
        per_image_rows,
    )

    # Save module import time separately; it is not a per-image runtime.
    write_csv(
        output_dir / "downstream_module_import.csv",
        [
            {
                "voronoi_and_colorwheel_module_import_ms": module_import_ms,
                "reporting_note": (
                    "One-time process initialization; exclude from warm "
                    "per-image downstream runtime."
                ),
            }
        ],
    )

    return per_run_rows, per_image_rows


def build_summaries(
    records: list[dict[str, str]],
    per_run_rows: list[dict[str, Any]],
    per_image_rows: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    completed_images = [
        row
        for row in per_image_rows
        if row["status"] in {"completed", "completed_no_downstream"}
    ]

    vor_values = [
        float(row["voronoi_median_ms"])
        for row in completed_images
        if row["voronoi_median_ms"] not in ("", None)
    ]
    cw_values = [
        float(row["colorwheel_median_ms"])
        for row in completed_images
        if row["colorwheel_median_ms"] not in ("", None)
    ]
    routed_total_values = [
        float(row["downstream_total_median_ms"])
        for row in completed_images
        if row["routing"] != "none"
        and row["downstream_total_median_ms"] not in ("", None)
    ]
    all_total_values = [
        float(row["downstream_total_median_ms"])
        for row in completed_images
        if row["downstream_total_median_ms"] not in ("", None)
    ]

    summary_rows: list[dict[str, Any]] = []
    if vor_values:
        summary_rows.append(
            summarize_values(
                "Voronoi analysis",
                vor_values,
                "Applicable images routed as dots or mixed; per-image medians.",
            )
        )
    if cw_values:
        summary_rows.append(
            summarize_values(
                "ColorWheel analysis",
                cw_values,
                "Applicable images routed as lines or mixed; per-image medians.",
            )
        )
    if routed_total_values:
        summary_rows.append(
            summarize_values(
                "Downstream total among routed images",
                routed_total_values,
                "Irregular images excluded because no downstream rule is applied.",
            )
        )
    if all_total_values:
        summary_rows.append(
            summarize_values(
                "Downstream total across all 50 images",
                all_total_values,
                "Irregular images contribute 0 ms because no downstream analysis is run.",
            )
        )

    write_csv(
        output_dir / "downstream_timing_summary.csv",
        summary_rows,
    )

    routing_counts: dict[str, int] = {}
    predicted_counts: dict[str, int] = {}
    for record in records:
        route = routing_for(record["predicted_label"])[2]
        routing_counts[route] = routing_counts.get(route, 0) + 1
        predicted_counts[record["predicted_label"]] = (
            predicted_counts.get(record["predicted_label"], 0) + 1
        )

    routing_rows = []
    for route in ("voronoi", "colorwheel", "voronoi+colorwheel", "none"):
        routing_rows.append(
            {
                "routing": route,
                "n_images": routing_counts.get(route, 0),
            }
        )
    for label in ("dots", "lines", "mixed", "irregular"):
        routing_rows.append(
            {
                "routing": f"predicted_class:{label}",
                "n_images": predicted_counts.get(label, 0),
            }
        )
    write_csv(
        output_dir / "downstream_routing_summary.csv",
        routing_rows,
    )


def write_methodology(
    output_dir: Path,
    records: list[dict[str, str]],
    repeats: int,
    device_used: str,
    keep_outputs: bool,
) -> None:
    text = f"""Experiment 3B downstream timing methodology
================================================

Images:
{len(records)} images from the finalized external validation set.

Routing:
- Predicted dots: Voronoi
- Predicted lines: ColorWheel
- Predicted mixed: Voronoi followed by ColorWheel
- Predicted irregular: no downstream analysis

Routing source:
The finalized predicted_label values from the Experiment 1 reviewed manifest.

U-Net masks:
A predicted mask was generated once for every image before downstream timing.
Mask-generation time was excluded because CNN/U-Net timing was already measured
separately in Experiment 3A.

Warm-up:
One Voronoi call and one ColorWheel call were executed and discarded before
recorded downstream timings.

Repetitions:
{repeats} repetitions per applicable image.

Timing:
time.perf_counter() was used. Each repetition included the complete downstream
function, including its file-generating outputs. Output deletion occurred only
after the timer stopped. Diagnostic console output was suppressed during timed
calls to prevent terminal rendering from inflating computational runtime.

Voronoi parameters:
- image_size = 1.0
- threshold_edge = 0.025
- max_size = 1024

ColorWheel parameters:
- num_clusters = 8

Device used to generate masks:
{device_used}

Generated downstream outputs retained:
{keep_outputs}

Interpretation:
Module import time is recorded separately and should not be added to each image.
The principal downstream result is the distribution of per-image median runtimes.
"""
    (output_dir / "downstream_methodology.txt").write_text(
        text, encoding="utf-8"
    )


def main() -> int:
    args = parse_args()
    if args.repeats < 1:
        raise ValueError("--repeats must be at least 1.")

    project_dir = Path(args.project_dir).expanduser().resolve()
    analysis_dir = find_analysis_dir(project_dir, args.analysis_dir)
    test_dir = resolve_path(project_dir, args.test_dir)
    manifest_path = resolve_path(project_dir, args.manifest)
    output_dir = resolve_path(project_dir, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_dir = project_dir / "models"
    ensure_real_model_file(model_dir / UNET_MODEL_NAME)

    records = load_manifest_records(
        manifest_path,
        test_dir,
        args.max_images,
    )

    print(f"Analysis directory: {analysis_dir}")
    print(f"Images selected: {len(records)}")
    print(f"Downstream repetitions: {args.repeats}")
    print(f"Output directory: {output_dir}")

    mask_root = output_dir / "generated_predicted_masks"
    masks, device_used = generate_predicted_masks(
        records,
        analysis_dir,
        model_dir,
        args.device,
        mask_root,
    )

    per_run_rows, per_image_rows = run_downstream_timing(
        records,
        masks,
        analysis_dir,
        output_dir,
        args.repeats,
        args.keep_generated_outputs,
    )

    build_summaries(
        records,
        per_run_rows,
        per_image_rows,
        output_dir,
    )

    metadata = {
        "timestamp_local": time.strftime("%Y-%m-%d %H:%M:%S"),
        "operating_system": platform.platform(),
        "python_version": platform.python_version(),
        "project_dir": str(project_dir),
        "analysis_dir": str(analysis_dir),
        "test_dir": str(test_dir),
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "image_count": len(records),
        "repeats": args.repeats,
        "routing_basis": "finalized Experiment 1 predicted_label",
        "device_for_mask_generation": device_used,
        "unet_model_sha256": sha256_file(model_dir / UNET_MODEL_NAME),
        "voronoi_script_sha256": sha256_file(
            analysis_dir / VORONOI_SCRIPT_NAME
        ),
        "colorwheel_script_sha256": sha256_file(
            analysis_dir / COLORWHEEL_SCRIPT_NAME
        ),
        "threshold": 0.5,
        "voronoi_threshold_edge": 0.025,
        "voronoi_max_size": 1024,
        "colorwheel_num_clusters": 8,
        "warmup_calls_discarded": 2,
    }
    write_csv(
        output_dir / "downstream_run_metadata.csv",
        [metadata],
    )

    write_methodology(
        output_dir,
        records,
        args.repeats,
        device_used,
        args.keep_generated_outputs,
    )

    if not args.keep_predicted_masks:
        shutil.rmtree(mask_root, ignore_errors=True)

    print("\nDownstream timing complete.")
    for filename in (
        "downstream_timing_per_run.csv",
        "downstream_timing_per_image.csv",
        "downstream_timing_summary.csv",
        "downstream_routing_summary.csv",
        "downstream_failures.csv",
        "downstream_module_import.csv",
        "downstream_run_metadata.csv",
        "downstream_methodology.txt",
    ):
        path = output_dir / filename
        if path.exists():
            print(f"  - {path.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
