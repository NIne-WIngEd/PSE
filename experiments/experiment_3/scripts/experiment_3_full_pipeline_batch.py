#!/usr/bin/env python3
"""
Experiment 3C: direct full-pipeline and batch timing.

The final pipeline is executed directly in one warm Python process:

    image file
      -> CNN classification
      -> U-Net segmentation and mask save
      -> routing by the fresh CNN prediction
      -> Voronoi and/or fixed full-resolution ColorWheel
      -> generated analysis files

Three complete batch repetitions provide:
- three end-to-end measurements for every image;
- three directly measured complete-batch runtimes;
- component-level runtime decomposition;
- batch throughput and per-image medians.

Excluded from the principal warm pipeline time:
- Python/backend startup;
- model loading;
- browser upload/network transfer;
- manual mask editing;
- PDF export.

Those are separate concerns. Model startup was already measured in Experiment 3A.
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
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
TRUE_VALUES = {"yes", "true", "1", "include", "included"}

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

COLORWHEEL_MAX_DIMENSION = 0
COLORWHEEL_ORIENTATION_MAX_DIMENSION = 1024
COLORWHEEL_NUM_CLUSTERS = 8
COLORWHEEL_MAX_FIT_SAMPLES = 10000
COLORWHEEL_MIN_COMPONENT_SIZE = 15
COLORWHEEL_RANDOM_STATE = 42


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Time the complete AFM pipeline and complete 50-image batches."
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Repository root containing backend, models, and an optional local test directory.",
    )
    parser.add_argument(
        "--analysis-dir",
        default=None,
        help="Directory containing analysis scripts. Default: <project-dir>/backend.",
    )
    parser.add_argument(
        "--test-dir",
        default="test",
        help="Validation image directory relative to project-dir unless absolute.",
    )
    parser.add_argument(
        "--manifest",
        default="cnn_predictions_primary_reviewed.csv",
        help="Final 50-image reviewed classification manifest.",
    )
    parser.add_argument(
        "--output-dir",
        default="evaluation_outputs/experiment_3_full_pipeline",
        help="Directory for timing outputs.",
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default="auto",
    )
    parser.add_argument(
        "--batch-repeats",
        type=int,
        default=3,
        help="Number of complete sequential batch runs. Default: 3.",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=0,
        help="Limit images for a setup test. Use 0 for all images.",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help=(
            "Select one image from each manifest-predicted route "
            "(dots, lines, mixed, irregular) and force one batch run."
        ),
    )
    parser.add_argument(
        "--skip-warmup",
        action="store_true",
        help="Skip the discarded route-specific warm-up passes.",
    )
    parser.add_argument(
        "--keep-last-batch-outputs",
        action="store_true",
        help="Keep generated masks and analysis files from the final batch only.",
    )
    parser.add_argument(
        "--low-confidence-threshold",
        type=float,
        default=0.60,
    )
    parser.add_argument(
        "--low-margin-threshold",
        type=float,
        default=0.10,
    )
    return parser.parse_args()


def resolve_path(base: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def find_analysis_dir(project_dir: Path, explicit: str | None) -> Path:
    candidates = (
        [resolve_path(project_dir, explicit)]
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
        "Could not locate the backend directory with all analysis modules."
    )


def ensure_real_model(path: Path) -> None:
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


def import_module_from_file(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_fixed_colorwheel(colorwheel_module) -> None:
    parameters = inspect.signature(colorwheel_module.analyze_image).parameters
    required = {
        "num_clusters",
        "max_dimension",
        "orientation_max_dimension",
        "max_fit_samples",
        "min_component_size",
    }
    missing = sorted(required.difference(parameters))
    if missing:
        raise RuntimeError(
            "The active backend/3.colorwheel.py is not the validated fixed "
            "full-resolution implementation. Missing parameters: "
            + ", ".join(missing)
        )


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in TRUE_VALUES


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_records(
    manifest_path: Path,
    test_dir: Path,
    max_images: int,
    smoke_test: bool,
) -> list[dict[str, Any]]:
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        required = {"relative_path", "true_label", "predicted_label"}
        missing = required.difference(fields)
        if missing:
            raise ValueError(
                "Manifest is missing required columns: " + ", ".join(sorted(missing))
            )

        include_column = next(
            (
                name
                for name in ("include_in_evaluation", "include_in_primary", "include")
                if name in fields
            ),
            None,
        )

        records: list[dict[str, Any]] = []
        for row in reader:
            if include_column and not truthy(row.get(include_column, "")):
                continue

            relative = Path(row["relative_path"])
            image_path = (
                relative if relative.is_absolute() else test_dir / relative
            ).resolve()

            if not image_path.exists():
                raise FileNotFoundError(f"Manifest image not found: {image_path}")
            if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            manifest_predicted = str(row["predicted_label"]).strip().lower()
            if manifest_predicted not in {"dots", "lines", "mixed", "irregular"}:
                raise ValueError(
                    f"Unsupported manifest predicted label `{manifest_predicted}` "
                    f"for {row['relative_path']}"
                )

            records.append(
                {
                    "relative_path": relative.as_posix(),
                    "true_label": str(row["true_label"]).strip().lower(),
                    "manifest_predicted_label": manifest_predicted,
                    "manifest_confidence": parse_optional_float(row.get("confidence")),
                    "image_path": str(image_path),
                    "image_sha256": (
                        str(row.get("image_sha256", "")).strip()
                        or sha256_file(image_path)
                    ),
                }
            )

    if smoke_test:
        selected: list[dict[str, Any]] = []
        for label in ("dots", "lines", "mixed", "irregular"):
            record = next(
                (
                    item
                    for item in records
                    if item["manifest_predicted_label"] == label
                ),
                None,
            )
            if record is None:
                raise RuntimeError(
                    f"Smoke test could not find manifest-predicted class: {label}"
                )
            selected.append(record)
        records = selected
    elif max_images > 0:
        records = records[:max_images]

    if not records:
        raise RuntimeError("No images selected.")
    return records


def parse_optional_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


def quiet_timed_call(function: Callable[[], Any]) -> tuple[float, Any]:
    """Time a call while suppressing diagnostic terminal output."""
    sink = io.StringIO()
    start = time.perf_counter()
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        result = function()
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return elapsed_ms, result


def route_for(label: str) -> tuple[bool, bool, str]:
    if label == "dots":
        return True, False, "voronoi"
    if label == "lines":
        return False, True, "colorwheel"
    if label == "mixed":
        return True, True, "voronoi+colorwheel"
    if label == "irregular":
        return False, False, "none"
    raise ValueError(f"Unsupported runtime predicted label: {label}")


def probability_details(cnn_result: dict[str, Any]) -> dict[str, Any]:
    probabilities = {
        str(key).lower(): float(value)
        for key, value in (cnn_result.get("probabilities") or {}).items()
    }
    ordered = sorted(
        probabilities.items(),
        key=lambda item: item[1],
        reverse=True,
    )
    top_probability = float(cnn_result.get("confidence", 0.0))
    if ordered:
        top_probability = ordered[0][1]
    second_probability = ordered[1][1] if len(ordered) > 1 else 0.0
    margin = top_probability - second_probability
    return {
        "probabilities": probabilities,
        "confidence": top_probability,
        "second_probability": second_probability,
        "confidence_margin": margin,
    }


def load_pipeline(analysis_dir: Path, model_dir: Path, requested_device: str):
    import torch

    module_import_start = time.perf_counter()
    cnn = import_module_from_file(
        "cnn_full_pipeline_timing",
        analysis_dir / CNN_SCRIPT_NAME,
    )
    unet = import_module_from_file(
        "unet_full_pipeline_timing",
        analysis_dir / UNET_SCRIPT_NAME,
    )

    if str(analysis_dir) not in sys.path:
        sys.path.insert(0, str(analysis_dir))

    voronoi = import_module_from_file(
        "voronoi_full_pipeline_timing",
        analysis_dir / VORONOI_SCRIPT_NAME,
    )
    colorwheel = import_module_from_file(
        "colorwheel_full_pipeline_timing",
        analysis_dir / COLORWHEEL_SCRIPT_NAME,
    )
    validate_fixed_colorwheel(colorwheel)
    module_import_ms = (time.perf_counter() - module_import_start) * 1000.0

    device = choose_device(torch, requested_device)

    model_load_start = time.perf_counter()
    cnn_model = cnn.load_model(
        str(model_dir / CNN_MODEL_NAME),
        in_channels=CNN_IN_CHANNELS,
        device=device,
    )
    synchronize(torch, device)

    unet_model, unet_image_size, unet_device = unet.load_model(
        str(model_dir / UNET_MODEL_NAME),
        device=str(device),
    )
    synchronize(torch, unet_device)
    model_load_ms = (time.perf_counter() - model_load_start) * 1000.0

    return {
        "torch": torch,
        "cnn_module": cnn,
        "unet_module": unet,
        "voronoi_module": voronoi,
        "colorwheel_module": colorwheel,
        "cnn_model": cnn_model,
        "unet_model": unet_model,
        "unet_image_size": unet_image_size,
        "unet_device": unet_device,
        "device": device,
        "module_import_ms": module_import_ms,
        "model_load_ms": model_load_ms,
    }


def process_one_image(
    pipeline: dict[str, Any],
    record: dict[str, Any],
    item_dir: Path,
) -> dict[str, Any]:
    torch_module = pipeline["torch"]
    cnn = pipeline["cnn_module"]
    unet = pipeline["unet_module"]
    voronoi = pipeline["voronoi_module"]
    colorwheel = pipeline["colorwheel_module"]
    device = pipeline["device"]
    unet_device = pipeline["unet_device"]

    image_path = Path(record["image_path"])

    synchronize(torch_module, device)
    pipeline_start = time.perf_counter()

    item_dir.mkdir(parents=True, exist_ok=True)

    # CNN classification, including image open/preprocessing and softmax.
    synchronize(torch_module, device)
    cnn_start = time.perf_counter()
    cnn_result = cnn.predict_image(
        pipeline["cnn_model"],
        str(image_path),
        image_size=CNN_IMAGE_SIZE,
        in_channels=CNN_IN_CHANNELS,
        device=device,
    )
    synchronize(torch_module, device)
    cnn_end = time.perf_counter()

    runtime_predicted = str(
        cnn_result.get("predicted_class", "unknown")
    ).strip().lower()
    if runtime_predicted not in {"dots", "lines", "mixed", "irregular"}:
        raise ValueError(
            f"Unexpected CNN prediction `{runtime_predicted}` for {image_path}"
        )

    probability_info = probability_details(cnn_result)
    run_voronoi, run_colorwheel, routing = route_for(runtime_predicted)

    # U-Net preprocessing.
    unet_preprocess_start = time.perf_counter()
    tensor, original_size = unet.preprocess_image(
        str(image_path),
        img_size=pipeline["unet_image_size"],
        denoise=0,
        sharpen=0,
        invert=False,
    )
    unet_preprocess_end = time.perf_counter()

    # U-Net inference.
    synchronize(torch_module, unet_device)
    unet_inference_start = time.perf_counter()
    predicted_mask = unet.predict_mask(
        pipeline["unet_model"],
        tensor,
        unet_device,
        threshold=UNET_THRESHOLD,
    )
    synchronize(torch_module, unet_device)
    unet_inference_end = time.perf_counter()

    # Mask resize/save.
    mask_path = item_dir / f"{image_path.stem}_predicted_mask.png"
    mask_save_start = time.perf_counter()
    unet.save_mask(predicted_mask, str(mask_path), original_size)
    mask_save_end = time.perf_counter()

    voronoi_ms: float | str = ""
    voronoi_status = "not_applicable"
    colorwheel_ms: float | str = ""
    colorwheel_status = "not_applicable"

    if run_voronoi:
        voronoi_dir = item_dir / "voronoi_outputs"
        voronoi_ms, voronoi_result = quiet_timed_call(
            lambda: voronoi.run_voronoi_analysis(
                image_path=str(mask_path),
                image_size=VORONOI_IMAGE_SIZE,
                output_dir=str(voronoi_dir),
                threshold_edge=VORONOI_THRESHOLD_EDGE,
                max_size=VORONOI_MAX_SIZE,
            )
        )
        if voronoi_result is None:
            voronoi_status = "failed_returned_none"
        elif isinstance(voronoi_result, dict) and not voronoi_result.get(
            "ran_voronoi", False
        ):
            voronoi_status = (
                "skipped_"
                + str(voronoi_result.get("reason", "unknown"))
                .strip()
                .replace(" ", "_")
            )
        else:
            voronoi_status = "completed"

    if run_colorwheel:
        colorwheel_dir = item_dir / "colorwheel_outputs"
        colorwheel_ms, colorwheel_result = quiet_timed_call(
            lambda: colorwheel.analyze_image(
                image_path=str(mask_path),
                output_dir=str(colorwheel_dir),
                num_clusters=COLORWHEEL_NUM_CLUSTERS,
                max_dimension=COLORWHEEL_MAX_DIMENSION,
                orientation_max_dimension=COLORWHEEL_ORIENTATION_MAX_DIMENSION,
                random_state=COLORWHEEL_RANDOM_STATE,
                max_fit_samples=COLORWHEEL_MAX_FIT_SAMPLES,
                min_component_size=COLORWHEEL_MIN_COMPONENT_SIZE,
            )
        )
        if not isinstance(colorwheel_result, dict):
            colorwheel_status = "failed_unexpected_result"
        else:
            expected_outputs = [
                Path(str(colorwheel_result.get("color_wheel_image", ""))),
                Path(str(colorwheel_result.get("one_phase_image", ""))),
            ]
            if all(path.exists() for path in expected_outputs):
                colorwheel_status = "completed"
            else:
                colorwheel_status = "failed_missing_primary_output"

    synchronize(torch_module, device)
    pipeline_end = time.perf_counter()

    unet_preprocess_ms = (
        unet_preprocess_end - unet_preprocess_start
    ) * 1000.0
    unet_inference_ms = (
        unet_inference_end - unet_inference_start
    ) * 1000.0
    unet_save_ms = (mask_save_end - mask_save_start) * 1000.0
    unet_total_ms = unet_preprocess_ms + unet_inference_ms + unet_save_ms

    return {
        "runtime_predicted_label": runtime_predicted,
        "routing": routing,
        "confidence": probability_info["confidence"],
        "second_probability": probability_info["second_probability"],
        "confidence_margin": probability_info["confidence_margin"],
        "probabilities_json": json.dumps(
            probability_info["probabilities"],
            sort_keys=True,
        ),
        "cnn_ms": (cnn_end - cnn_start) * 1000.0,
        "unet_preprocess_ms": unet_preprocess_ms,
        "unet_inference_ms": unet_inference_ms,
        "unet_save_ms": unet_save_ms,
        "unet_total_ms": unet_total_ms,
        "voronoi_ms": voronoi_ms,
        "voronoi_status": voronoi_status,
        "colorwheel_ms": colorwheel_ms,
        "colorwheel_status": colorwheel_status,
        "full_pipeline_ms": (pipeline_end - pipeline_start) * 1000.0,
        "mask_path": str(mask_path),
    }


def warm_up_pipeline(
    pipeline: dict[str, Any],
    records: list[dict[str, Any]],
    warmup_dir: Path,
) -> list[dict[str, Any]]:
    """Run and discard one full pass from each route represented in the set."""
    warmup_records: list[dict[str, Any]] = []
    for label in ("dots", "lines", "mixed", "irregular"):
        record = next(
            (
                item
                for item in records
                if item["manifest_predicted_label"] == label
            ),
            None,
        )
        if record is not None:
            warmup_records.append(record)

    warmup_rows = []
    for index, record in enumerate(warmup_records, start=1):
        print(
            f"[Warm-up {index}/{len(warmup_records)}] "
            f"{record['relative_path']} (discarded)"
        )
        result = process_one_image(
            pipeline,
            record,
            warmup_dir / f"route_{record['manifest_predicted_label']}",
        )
        warmup_rows.append({
            "relative_path": record["relative_path"],
            "manifest_predicted_label": record["manifest_predicted_label"],
            "runtime_predicted_label": result["runtime_predicted_label"],
            "routing": result["routing"],
            "full_pipeline_ms": result["full_pipeline_ms"],
        })

    shutil.rmtree(warmup_dir, ignore_errors=True)
    return warmup_rows


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


def describe(
    measurement: str,
    values: list[float],
    unit: str,
    notes: str,
) -> dict[str, Any]:
    median_value = statistics.median(values)
    throughput = ""
    if unit == "ms" and median_value > 0:
        throughput = 1000.0 / median_value
    return {
        "measurement": measurement,
        "unit": unit,
        "n": len(values),
        "mean": statistics.fmean(values),
        "standard_deviation": (
            statistics.stdev(values) if len(values) > 1 else 0.0
        ),
        "median": median_value,
        "q1": percentile(values, 0.25),
        "q3": percentile(values, 0.75),
        "minimum": min(values),
        "maximum": max(values),
        "throughput_per_second_from_median": throughput,
        "notes": notes,
    }


def aggregate_per_image(
    per_run_rows: list[dict[str, Any]],
    records: list[dict[str, Any]],
    expected_repeats: int,
) -> list[dict[str, Any]]:
    timing_fields = [
        "cnn_ms",
        "unet_preprocess_ms",
        "unet_inference_ms",
        "unet_save_ms",
        "unet_total_ms",
        "voronoi_ms",
        "colorwheel_ms",
        "full_pipeline_ms",
    ]

    output: list[dict[str, Any]] = []
    for record in records:
        matching = [
            row
            for row in per_run_rows
            if row["relative_path"] == record["relative_path"]
            and row["status"] == "completed"
        ]

        row_out: dict[str, Any] = {
            "relative_path": record["relative_path"],
            "true_label": record["true_label"],
            "manifest_predicted_label": record["manifest_predicted_label"],
            "runtime_predicted_label": (
                matching[0]["runtime_predicted_label"] if matching else ""
            ),
            "routing": matching[0]["routing"] if matching else "",
            "expected_batch_repeats": expected_repeats,
            "successful_batch_repeats": len(matching),
            "prediction_matches_manifest_all_runs": (
                all(
                    row["runtime_predicted_label"]
                    == record["manifest_predicted_label"]
                    for row in matching
                )
                if matching
                else False
            ),
            "confidence_median": (
                statistics.median(
                    [float(row["confidence"]) for row in matching]
                )
                if matching
                else ""
            ),
        }

        for field in timing_fields:
            values = [
                float(row[field])
                for row in matching
                if row[field] not in ("", None)
            ]
            base = field.removesuffix("_ms")
            if values:
                row_out[f"{base}_median_ms"] = statistics.median(values)
                row_out[f"{base}_mean_ms"] = statistics.fmean(values)
                row_out[f"{base}_sd_ms"] = (
                    statistics.stdev(values) if len(values) > 1 else 0.0
                )
                row_out[f"{base}_minimum_ms"] = min(values)
                row_out[f"{base}_maximum_ms"] = max(values)
            else:
                row_out[f"{base}_median_ms"] = ""
                row_out[f"{base}_mean_ms"] = ""
                row_out[f"{base}_sd_ms"] = ""
                row_out[f"{base}_minimum_ms"] = ""
                row_out[f"{base}_maximum_ms"] = ""

        row_out["status"] = (
            "completed"
            if len(matching) == expected_repeats
            else "incomplete_or_failed"
        )
        output.append(row_out)

    return output


def build_summaries(
    per_image_rows: list[dict[str, Any]],
    batch_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    complete = [
        row for row in per_image_rows if row["status"] == "completed"
    ]

    component_specs = [
        ("Warm CNN", "cnn_median_ms", "All completed images."),
        ("Warm U-Net total", "unet_total_median_ms", "All completed images."),
        (
            "Voronoi analysis",
            "voronoi_median_ms",
            "Only routes where Voronoi was applicable.",
        ),
        (
            "Fixed full-resolution ColorWheel",
            "colorwheel_median_ms",
            "Only routes where ColorWheel was applicable.",
        ),
        (
            "Direct complete pipeline",
            "full_pipeline_median_ms",
            (
                "Image read/classification, segmentation/mask save, and route-specific "
                "analysis/output generation."
            ),
        ),
    ]

    component_summary: list[dict[str, Any]] = []
    for label, field, note in component_specs:
        values = [
            float(row[field])
            for row in complete
            if row.get(field) not in ("", None)
        ]
        if values:
            component_summary.append(
                describe(label, values, "ms", note)
            )

    batch_values = [
        float(row["batch_total_seconds"])
        for row in batch_rows
        if row["status"] == "completed"
    ]
    batch_summary: list[dict[str, Any]] = []
    if batch_values:
        batch_summary.append(
            describe(
                "Complete validation batch",
                batch_values,
                "seconds",
                (
                    "Models remained loaded. Each run processed every selected image "
                    "sequentially and generated all route-specific output files."
                ),
            )
        )

    return component_summary, batch_summary


def build_route_summary(
    per_image_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    route_order = ["voronoi", "colorwheel", "voronoi+colorwheel", "none"]

    for route in route_order:
        matching = [
            row
            for row in per_image_rows
            if row["status"] == "completed" and row["routing"] == route
        ]
        if not matching:
            continue
        values = [
            float(row["full_pipeline_median_ms"])
            for row in matching
        ]
        rows.append({
            "routing": route,
            "n_images": len(values),
            "mean_full_pipeline_ms": statistics.fmean(values),
            "standard_deviation_ms": (
                statistics.stdev(values) if len(values) > 1 else 0.0
            ),
            "median_full_pipeline_ms": statistics.median(values),
            "q1_ms": percentile(values, 0.25),
            "q3_ms": percentile(values, 0.75),
            "minimum_ms": min(values),
            "maximum_ms": max(values),
        })

    return rows


def collect_hardware_info(
    device_requested: str,
    device_used: str,
) -> dict[str, Any]:
    import torch

    gpu_name = ""
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)

    try:
        import psutil
        ram_bytes: int | str = psutil.virtual_memory().total
        physical_cores: int | str = psutil.cpu_count(logical=False) or ""
        logical_cores: int | str = psutil.cpu_count(logical=True) or ""
    except Exception:
        ram_bytes = ""
        physical_cores = ""
        logical_cores = os.cpu_count() or ""

    return {
        "timestamp_local": time.strftime("%Y-%m-%d %H:%M:%S"),
        "operating_system": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_physical_cores": physical_cores,
        "cpu_logical_cores": logical_cores,
        "ram_bytes": ram_bytes,
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "pytorch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_runtime_version": torch.version.cuda or "",
        "gpu_name": gpu_name,
        "device_requested": device_requested,
        "device_used": device_used,
    }


def write_methodology(
    output_dir: Path,
    records: list[dict[str, Any]],
    args: argparse.Namespace,
    device_used: str,
) -> None:
    route_counts: dict[str, int] = {}
    for record in records:
        route = route_for(record["manifest_predicted_label"])[2]
        route_counts[route] = route_counts.get(route, 0) + 1

    text = f"""Experiment 3C direct full-pipeline and batch timing
=====================================================

Images:
{len(records)} images selected from the finalized reviewed manifest.

Complete batch repetitions:
{args.batch_repeats}

Execution state:
CNN and U-Net models were loaded once before the experiment and remained loaded
through all batch repetitions. Model loading was excluded from the warm
full-pipeline and batch measurements because startup was measured separately in
Experiment 3A.

Warm-up:
{"Skipped by command-line request." if args.skip_warmup else "One discarded complete pass was run for each represented route: dots, lines, mixed, and irregular."}

Direct per-image timing scope:
- output-directory creation;
- image opening and CNN preprocessing/inference;
- U-Net preprocessing/inference;
- resizing and saving the predicted mask;
- routing by the fresh CNN prediction;
- Voronoi and/or fixed full-resolution ColorWheel computation;
- generation and saving of downstream output files.

Excluded:
- browser/network upload time;
- manual mask review or editing;
- PDF export;
- model/backend startup.

Routing:
- predicted dots -> Voronoi
- predicted lines -> ColorWheel
- predicted mixed -> Voronoi + ColorWheel
- predicted irregular -> no downstream analysis

Manifest route counts before direct execution:
{json.dumps(route_counts, indent=2)}

Voronoi settings:
- image_size = {VORONOI_IMAGE_SIZE}
- threshold_edge = {VORONOI_THRESHOLD_EDGE}
- max_size = {VORONOI_MAX_SIZE}

Fixed full-resolution ColorWheel settings:
- max_dimension = {COLORWHEEL_MAX_DIMENSION} (0 = retain original resolution)
- orientation_max_dimension = {COLORWHEEL_ORIENTATION_MAX_DIMENSION}
- num_clusters = {COLORWHEEL_NUM_CLUSTERS}
- max_fit_samples = {COLORWHEEL_MAX_FIT_SAMPLES}
- min_component_size = {COLORWHEEL_MIN_COMPONENT_SIZE}
- random_state = {COLORWHEEL_RANDOM_STATE}

Timing:
time.perf_counter() was used. CUDA synchronization was applied when relevant.
Diagnostic output from Voronoi and ColorWheel was suppressed during measured
calls so terminal rendering did not inflate computation time.

Device:
{device_used}

Batch timing:
The batch timer began immediately before creation of the batch output directory
and stopped after the final image's route-specific output files were generated.
Output deletion occurred only after the timer stopped. The same loaded models
were reused across all complete batch repetitions.

Interpretation:
The principal per-image observation is the median direct full-pipeline runtime
across the complete batch repetitions. The principal batch observation is the
directly measured total duration of each complete batch run.
"""
    (output_dir / "full_pipeline_methodology.txt").write_text(
        text,
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()

    if args.batch_repeats < 1:
        raise ValueError("--batch-repeats must be at least 1.")
    if args.smoke_test:
        args.batch_repeats = 1

    project_dir = Path(args.project_dir).expanduser().resolve()
    analysis_dir = find_analysis_dir(project_dir, args.analysis_dir)
    test_dir = resolve_path(project_dir, args.test_dir)
    manifest_path = resolve_path(project_dir, args.manifest)
    output_dir = resolve_path(project_dir, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_dir = project_dir / "models"
    ensure_real_model(model_dir / CNN_MODEL_NAME)
    ensure_real_model(model_dir / UNET_MODEL_NAME)

    records = load_records(
        manifest_path,
        test_dir,
        args.max_images,
        args.smoke_test,
    )

    print(f"Analysis directory: {analysis_dir}")
    print(f"Images selected: {len(records)}")
    print(f"Complete batch repetitions: {args.batch_repeats}")
    print(f"Output directory: {output_dir}")
    print("Loading final pipeline once...")

    pipeline = load_pipeline(analysis_dir, model_dir, args.device)
    device_used = str(pipeline["device"])

    write_csv(
        output_dir / "full_pipeline_session_setup.csv",
        [{
            "module_import_ms": pipeline["module_import_ms"],
            "cnn_and_unet_model_load_ms": pipeline["model_load_ms"],
            "device": device_used,
            "reporting_note": (
                "One-time warm-session setup; excluded from direct warm pipeline "
                "and batch measurements."
            ),
        }],
    )

    warmup_rows: list[dict[str, Any]] = []
    if not args.skip_warmup:
        warmup_rows = warm_up_pipeline(
            pipeline,
            records,
            output_dir / "_discarded_warmup",
        )
        write_csv(
            output_dir / "discarded_warmup_runs.csv",
            warmup_rows,
        )

    runtime_root = output_dir / "runtime_outputs"
    per_run_rows: list[dict[str, Any]] = []
    batch_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    low_confidence_rows: list[dict[str, Any]] = []
    mismatch_rows: list[dict[str, Any]] = []

    for batch_repeat in range(1, args.batch_repeats + 1):
        batch_dir = runtime_root / f"batch_{batch_repeat}"
        if batch_dir.exists():
            shutil.rmtree(batch_dir)

        print(
            f"\n[Batch {batch_repeat}/{args.batch_repeats}] "
            f"starting {len(records)} images"
        )

        batch_start = time.perf_counter()
        completed_in_batch = 0
        failed_in_batch = 0
        batch_image_rows: list[dict[str, Any]] = []

        for position, record in enumerate(records, start=1):
            print(
                f"[Batch {batch_repeat} | {position:03d}/{len(records):03d}] "
                f"{record['relative_path']}"
            )
            item_dir = (
                batch_dir
                / f"{position:03d}_{Path(record['relative_path']).stem}"
            )

            try:
                result = process_one_image(
                    pipeline,
                    record,
                    item_dir,
                )

                row = {
                    "batch_repeat": batch_repeat,
                    "position_in_batch": position,
                    "relative_path": record["relative_path"],
                    "true_label": record["true_label"],
                    "manifest_predicted_label": record[
                        "manifest_predicted_label"
                    ],
                    "runtime_predicted_label": result[
                        "runtime_predicted_label"
                    ],
                    "prediction_matches_manifest": (
                        result["runtime_predicted_label"]
                        == record["manifest_predicted_label"]
                    ),
                    "routing": result["routing"],
                    "confidence": result["confidence"],
                    "second_probability": result["second_probability"],
                    "confidence_margin": result["confidence_margin"],
                    "probabilities_json": result["probabilities_json"],
                    "cnn_ms": result["cnn_ms"],
                    "unet_preprocess_ms": result["unet_preprocess_ms"],
                    "unet_inference_ms": result["unet_inference_ms"],
                    "unet_save_ms": result["unet_save_ms"],
                    "unet_total_ms": result["unet_total_ms"],
                    "voronoi_ms": result["voronoi_ms"],
                    "voronoi_status": result["voronoi_status"],
                    "colorwheel_ms": result["colorwheel_ms"],
                    "colorwheel_status": result["colorwheel_status"],
                    "full_pipeline_ms": result["full_pipeline_ms"],
                    "status": "completed",
                }
                per_run_rows.append(row)
                batch_image_rows.append(row)
                completed_in_batch += 1

                if not row["prediction_matches_manifest"]:
                    mismatch_rows.append({
                        "batch_repeat": batch_repeat,
                        "relative_path": record["relative_path"],
                        "manifest_predicted_label": record[
                            "manifest_predicted_label"
                        ],
                        "runtime_predicted_label": result[
                            "runtime_predicted_label"
                        ],
                        "confidence": result["confidence"],
                    })

                if (
                    result["confidence"] < args.low_confidence_threshold
                    or result["confidence_margin"] < args.low_margin_threshold
                ):
                    low_confidence_rows.append({
                        "batch_repeat": batch_repeat,
                        "relative_path": record["relative_path"],
                        "true_label": record["true_label"],
                        "runtime_predicted_label": result[
                            "runtime_predicted_label"
                        ],
                        "routing": result["routing"],
                        "confidence": result["confidence"],
                        "second_probability": result["second_probability"],
                        "confidence_margin": result["confidence_margin"],
                        "confidence_threshold": args.low_confidence_threshold,
                        "margin_threshold": args.low_margin_threshold,
                    })

            except Exception as exc:
                failed_in_batch += 1
                failure = {
                    "batch_repeat": batch_repeat,
                    "position_in_batch": position,
                    "relative_path": record["relative_path"],
                    "true_label": record["true_label"],
                    "manifest_predicted_label": record[
                        "manifest_predicted_label"
                    ],
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
                failures.append(failure)
                per_run_rows.append({
                    **failure,
                    "runtime_predicted_label": "",
                    "prediction_matches_manifest": False,
                    "routing": "",
                    "confidence": "",
                    "second_probability": "",
                    "confidence_margin": "",
                    "probabilities_json": "",
                    "cnn_ms": "",
                    "unet_preprocess_ms": "",
                    "unet_inference_ms": "",
                    "unet_save_ms": "",
                    "unet_total_ms": "",
                    "voronoi_ms": "",
                    "voronoi_status": "",
                    "colorwheel_ms": "",
                    "colorwheel_status": "",
                    "full_pipeline_ms": "",
                    "status": "failed",
                })
                print(
                    f"  FAILED: {type(exc).__name__}: {exc}",
                    file=sys.stderr,
                )

        batch_total_seconds = time.perf_counter() - batch_start
        sum_per_image_ms = sum(
            float(row["full_pipeline_ms"])
            for row in batch_image_rows
        )
        batch_status = (
            "completed"
            if failed_in_batch == 0 and completed_in_batch == len(records)
            else "incomplete_or_failed"
        )

        batch_rows.append({
            "batch_repeat": batch_repeat,
            "images_expected": len(records),
            "images_completed": completed_in_batch,
            "images_failed": failed_in_batch,
            "batch_total_seconds": batch_total_seconds,
            "batch_total_minutes": batch_total_seconds / 60.0,
            "images_per_second": (
                completed_in_batch / batch_total_seconds
                if batch_total_seconds > 0
                else ""
            ),
            "images_per_minute": (
                completed_in_batch * 60.0 / batch_total_seconds
                if batch_total_seconds > 0
                else ""
            ),
            "average_seconds_per_completed_image": (
                batch_total_seconds / completed_in_batch
                if completed_in_batch > 0
                else ""
            ),
            "sum_recorded_per_image_seconds": sum_per_image_ms / 1000.0,
            "batch_overhead_seconds": (
                batch_total_seconds - sum_per_image_ms / 1000.0
            ),
            "status": batch_status,
        })

        print(
            f"[Batch {batch_repeat}] {batch_status}: "
            f"{completed_in_batch}/{len(records)} images in "
            f"{batch_total_seconds / 60.0:.2f} min "
            f"({completed_in_batch * 60.0 / batch_total_seconds:.2f} images/min)"
        )

        should_keep = (
            args.keep_last_batch_outputs
            and batch_repeat == args.batch_repeats
        )
        if not should_keep:
            shutil.rmtree(batch_dir, ignore_errors=True)

        gc.collect()

    write_csv(
        output_dir / "full_pipeline_per_image_per_batch.csv",
        per_run_rows,
    )
    write_csv(
        output_dir / "full_pipeline_batch_timing.csv",
        batch_rows,
    )
    if failures:
        write_csv(
            output_dir / "full_pipeline_failures.csv",
            failures,
        )
    if low_confidence_rows:
        write_csv(
            output_dir / "full_pipeline_low_confidence_routes.csv",
            low_confidence_rows,
        )
    if mismatch_rows:
        write_csv(
            output_dir / "full_pipeline_prediction_mismatches.csv",
            mismatch_rows,
        )

    per_image_rows = aggregate_per_image(
        per_run_rows,
        records,
        args.batch_repeats,
    )
    write_csv(
        output_dir / "full_pipeline_per_image_summary.csv",
        per_image_rows,
    )

    component_summary, batch_summary = build_summaries(
        per_image_rows,
        batch_rows,
    )
    write_csv(
        output_dir / "full_pipeline_component_summary.csv",
        component_summary,
    )
    write_csv(
        output_dir / "full_pipeline_batch_summary.csv",
        batch_summary,
    )
    write_csv(
        output_dir / "full_pipeline_route_summary.csv",
        build_route_summary(per_image_rows),
    )

    prediction_match_count = sum(
        1
        for row in per_image_rows
        if row["prediction_matches_manifest_all_runs"]
    )

    hardware = collect_hardware_info(
        args.device,
        device_used,
    )
    write_csv(
        output_dir / "full_pipeline_hardware_info.csv",
        [hardware],
    )

    metadata = [{
        "timestamp_local": time.strftime("%Y-%m-%d %H:%M:%S"),
        "project_dir": str(project_dir),
        "analysis_dir": str(analysis_dir),
        "test_dir": str(test_dir),
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "image_count": len(records),
        "batch_repeats": args.batch_repeats,
        "successful_batch_runs": sum(
            1 for row in batch_rows if row["status"] == "completed"
        ),
        "failed_image_runs": len(failures),
        "images_matching_manifest_prediction_all_runs": prediction_match_count,
        "device": device_used,
        "cnn_model_sha256": sha256_file(model_dir / CNN_MODEL_NAME),
        "unet_model_sha256": sha256_file(model_dir / UNET_MODEL_NAME),
        "cnn_script_sha256": sha256_file(
            analysis_dir / CNN_SCRIPT_NAME
        ),
        "unet_script_sha256": sha256_file(
            analysis_dir / UNET_SCRIPT_NAME
        ),
        "voronoi_script_sha256": sha256_file(
            analysis_dir / VORONOI_SCRIPT_NAME
        ),
        "colorwheel_script_sha256": sha256_file(
            analysis_dir / COLORWHEEL_SCRIPT_NAME
        ),
        "unet_threshold": UNET_THRESHOLD,
        "voronoi_threshold_edge": VORONOI_THRESHOLD_EDGE,
        "voronoi_max_size": VORONOI_MAX_SIZE,
        "colorwheel_max_dimension": COLORWHEEL_MAX_DIMENSION,
        "colorwheel_orientation_max_dimension": (
            COLORWHEEL_ORIENTATION_MAX_DIMENSION
        ),
        "colorwheel_num_clusters": COLORWHEEL_NUM_CLUSTERS,
        "colorwheel_max_fit_samples": COLORWHEEL_MAX_FIT_SAMPLES,
        "colorwheel_min_component_size": COLORWHEEL_MIN_COMPONENT_SIZE,
        "colorwheel_random_state": COLORWHEEL_RANDOM_STATE,
        "route_specific_warmup_discarded": not args.skip_warmup,
        "keep_last_batch_outputs": args.keep_last_batch_outputs,
    }]
    write_csv(
        output_dir / "full_pipeline_run_metadata.csv",
        metadata,
    )

    write_methodology(
        output_dir,
        records,
        args,
        device_used,
    )

    print("\nExperiment 3C complete.")
    print(
        f"Successful complete batches: "
        f"{metadata[0]['successful_batch_runs']}/{args.batch_repeats}"
    )
    print(f"Failed image runs: {len(failures)}")
    print(f"Results: {output_dir}")

    for filename in (
        "full_pipeline_per_image_per_batch.csv",
        "full_pipeline_per_image_summary.csv",
        "full_pipeline_batch_timing.csv",
        "full_pipeline_component_summary.csv",
        "full_pipeline_batch_summary.csv",
        "full_pipeline_route_summary.csv",
        "full_pipeline_low_confidence_routes.csv",
        "full_pipeline_prediction_mismatches.csv",
        "full_pipeline_failures.csv",
        "full_pipeline_session_setup.csv",
        "full_pipeline_hardware_info.csv",
        "full_pipeline_run_metadata.csv",
        "full_pipeline_methodology.txt",
    ):
        path = output_dir / filename
        if path.exists():
            print(f"  - {path.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
