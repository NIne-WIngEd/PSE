#!/usr/bin/env python3
"""
Experiment 3: automated cold-start and warm-inference timing.

This script is tailored to the AFM project structure:

PSE-master/
├── AFM_Web-main/
│   ├── 1.cnn_inference 1.py
│   ├── 2.segmentation.py
│   ├── cnn_rgb_classifier.pth
│   └── best_quality_unet.pt
└── test/
    ├── dots/
    ├── lines/
    ├── mixed/
    └── irregular/

It produces:
- cold_start_timing.csv
- warm_inference_per_run.csv
- warm_inference_per_image.csv
- timing_summary.csv
- hardware_info.csv
- experiment_3_methodology.txt

Cold timing:
- Each cold run launches a completely fresh Python process.
- Both model files are imported and loaded from disk.
- The first CNN + U-Net pass is recorded separately.

Warm timing:
- Models remain loaded in one Python process.
- One unrecorded warm-up pass is performed.
- Every validation image is processed repeatedly.
- Per-image medians are used for the main runtime summary.

The U-Net timing includes:
- preprocessing,
- model inference,
- resizing/saving the predicted mask.

The CNN timing includes:
- opening and preprocessing the image,
- model inference,
- probability calculation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

PROCESS_START = time.perf_counter()

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
TRUE_VALUES = {"yes", "true", "1", "include", "included"}

CNN_SCRIPT_NAME = "1.cnn_inference 1.py"
UNET_SCRIPT_NAME = "2.segmentation.py"
CNN_MODEL_NAME = "cnn_rgb_classifier.pth"
UNET_MODEL_NAME = "best_quality_unet.pt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Measure AFM CNN/U-Net cold startup and warm inference times "
            "and generate publication-ready CSV files."
        )
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help=(
            "Repository root containing backend, models, and an optional local test directory. "
            "Default: current directory."
        ),
    )
    parser.add_argument(
        "--analysis-dir",
        default=None,
        help=(
            "Directory containing the Python analysis modules. Default: <project-dir>/backend."
        ),
    )
    parser.add_argument(
        "--test-dir",
        default="test",
        help="Validation image directory, relative to project-dir unless absolute.",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help=(
            "Optional CSV containing relative_path. Rows marked yes in "
            "include_in_primary or include_in_evaluation are used. "
            "Without a manifest, every supported image under test-dir is used."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default="evaluation_outputs/experiment_3_timing",
        help="Directory for CSV and text outputs.",
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default="auto",
        help="Execution device. Default: auto.",
    )
    parser.add_argument(
        "--cold-runs",
        type=int,
        default=5,
        help="Number of fresh-process cold-start runs. Default: 5.",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=5,
        help="Warm repetitions per image. Default: 5.",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=0,
        help="Limit images for a test run. Use 0 for all images.",
    )
    parser.add_argument(
        "--keep-warm-masks",
        action="store_true",
        help="Keep masks generated during warm timing.",
    )
    parser.add_argument(
        "--skip-cold",
        action="store_true",
        help="Skip fresh-process cold-start measurements.",
    )
    parser.add_argument(
        "--skip-warm",
        action="store_true",
        help="Skip warm per-image measurements.",
    )

    # Internal worker arguments. Users should not call these directly.
    parser.add_argument("--_cold-worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--_sample-image", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--_worker-json", default=None, help=argparse.SUPPRESS)

    return parser.parse_args()


def resolve_path(base: Path, value: str | Path | None) -> Path | None:
    if value is None:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def find_analysis_dir(project_dir: Path, explicit: str | None) -> Path:
    if explicit:
        candidate = resolve_path(project_dir, explicit)
        assert candidate is not None
        return candidate

    candidates = [
        project_dir / "backend",
        project_dir,
    ]
    for candidate in candidates:
        if (
            (candidate / CNN_SCRIPT_NAME).exists()
            and (candidate / UNET_SCRIPT_NAME).exists()
        ):
            return candidate.resolve()

    raise FileNotFoundError(
        "Could not locate the backend analysis modules automatically. "
        "Pass --analysis-dir explicitly."
    )


def ensure_real_model_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")

    head = path.read_bytes()[:200]
    if b"version https://git-lfs.github.com/spec" in head:
        raise RuntimeError(
            f"{path.name} is a Git LFS pointer, not the actual model. "
            "Run `git lfs pull` in the repository before timing."
        )

    if path.stat().st_size < 10_000:
        raise RuntimeError(
            f"{path.name} is unexpectedly small ({path.stat().st_size} bytes). "
            "Confirm that the real trained weights are present."
        )


def import_module_from_file(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create import specification for {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_torch_device(torch_module, requested: str):
    if requested == "cuda":
        if not torch_module.cuda.is_available():
            raise RuntimeError("--device cuda was requested, but CUDA is unavailable.")
        return torch_module.device("cuda")
    if requested == "cpu":
        return torch_module.device("cpu")
    return torch_module.device(
        "cuda" if torch_module.cuda.is_available() else "cpu"
    )


def synchronize_cuda(torch_module, device) -> None:
    if getattr(device, "type", str(device)) == "cuda":
        torch_module.cuda.synchronize()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def supported_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in TRUE_VALUES


def choose_include_column(fieldnames: list[str] | None) -> str | None:
    if not fieldnames:
        return None
    for candidate in (
        "include_in_evaluation",
        "include_in_primary",
        "include",
    ):
        if candidate in fieldnames:
            return candidate
    return None


def load_images(
    project_dir: Path,
    test_dir: Path,
    manifest_path: Path | None,
    max_images: int,
) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []

    if manifest_path is not None:
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        with manifest_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames or "relative_path" not in reader.fieldnames:
                raise ValueError(
                    "Manifest must contain a `relative_path` column."
                )

            include_column = choose_include_column(reader.fieldnames)
            for row in reader:
                if include_column and not truthy(row.get(include_column, "")):
                    continue

                relative = Path(row["relative_path"])
                candidates = [
                    relative if relative.is_absolute() else test_dir / relative,
                    relative if relative.is_absolute() else project_dir / relative,
                ]
                image_path = next(
                    (candidate.resolve() for candidate in candidates if candidate.exists()),
                    None,
                )
                if image_path is None:
                    raise FileNotFoundError(
                        f"Manifest image not found: {row['relative_path']}"
                    )
                if not supported_image(image_path):
                    continue

                try:
                    relative_to_test = image_path.relative_to(test_dir).as_posix()
                except ValueError:
                    relative_to_test = row["relative_path"]

                class_label = (
                    row.get("true_label")
                    or row.get("class_label")
                    or Path(relative_to_test).parts[0]
                ).strip().lower()

                records.append(
                    {
                        "relative_path": relative_to_test,
                        "class_label": class_label,
                        "image_path": str(image_path),
                    }
                )
    else:
        if not test_dir.exists():
            raise FileNotFoundError(f"Test directory not found: {test_dir}")
        for image_path in sorted(test_dir.rglob("*")):
            if not supported_image(image_path):
                continue
            relative = image_path.relative_to(test_dir)
            class_label = relative.parts[0].lower() if len(relative.parts) > 1 else ""
            records.append(
                {
                    "relative_path": relative.as_posix(),
                    "class_label": class_label,
                    "image_path": str(image_path.resolve()),
                }
            )

    # Deduplicate while preserving order.
    deduplicated: list[dict[str, str]] = []
    seen: set[str] = set()
    for record in records:
        key = str(Path(record["image_path"]).resolve())
        if key not in seen:
            deduplicated.append(record)
            seen.add(key)

    if max_images > 0:
        deduplicated = deduplicated[:max_images]

    if not deduplicated:
        raise RuntimeError("No validation images were selected.")

    return deduplicated


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"Cannot write empty CSV: {path}")
    columns = fieldnames or list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def percentile(values: list[float], q: float) -> float:
    if not values:
        return math.nan
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


def descriptive_row(
    measurement: str,
    values: Iterable[float],
    unit: str,
    notes: str,
) -> dict[str, Any]:
    values_list = [float(value) for value in values]
    if not values_list:
        return {
            "measurement": measurement,
            "unit": unit,
            "n": 0,
            "mean": "",
            "standard_deviation": "",
            "median": "",
            "q1": "",
            "q3": "",
            "minimum": "",
            "maximum": "",
            "throughput_images_per_second_from_median": "",
            "notes": notes,
        }

    median_value = statistics.median(values_list)
    throughput = (
        1000.0 / median_value
        if unit == "ms" and median_value > 0
        else ""
    )

    return {
        "measurement": measurement,
        "unit": unit,
        "n": len(values_list),
        "mean": statistics.fmean(values_list),
        "standard_deviation": (
            statistics.stdev(values_list) if len(values_list) > 1 else 0.0
        ),
        "median": median_value,
        "q1": percentile(values_list, 0.25),
        "q3": percentile(values_list, 0.75),
        "minimum": min(values_list),
        "maximum": max(values_list),
        "throughput_images_per_second_from_median": throughput,
        "notes": notes,
    }


def median(values: list[float]) -> float:
    return float(statistics.median(values))


def mean(values: list[float]) -> float:
    return float(statistics.fmean(values))


def stdev(values: list[float]) -> float:
    return float(statistics.stdev(values)) if len(values) > 1 else 0.0


def cold_worker(args: argparse.Namespace) -> int:
    if not args._sample_image or not args._worker_json:
        raise ValueError("Cold worker requires sample image and output JSON.")

    worker_json = Path(args._worker_json).resolve()
    sample_image = Path(args._sample_image).resolve()
    project_dir = Path(args.project_dir).expanduser().resolve()
    analysis_dir = find_analysis_dir(project_dir, args.analysis_dir)

    cnn_script = analysis_dir / CNN_SCRIPT_NAME
    unet_script = analysis_dir / UNET_SCRIPT_NAME
    model_dir = project_dir / "models"
    cnn_weights = model_dir / CNN_MODEL_NAME
    unet_weights = model_dir / UNET_MODEL_NAME

    try:
        ensure_real_model_file(cnn_weights)
        ensure_real_model_file(unet_weights)

        dependency_start = time.perf_counter()
        import torch
        dependency_end = time.perf_counter()

        module_start = time.perf_counter()
        cnn_mod = import_module_from_file("cnn_timing_worker", cnn_script)
        unet_mod = import_module_from_file("unet_timing_worker", unet_script)
        module_end = time.perf_counter()

        device = resolve_torch_device(torch, args.device)

        cnn_load_start = time.perf_counter()
        cnn_model = cnn_mod.load_model(
            str(cnn_weights),
            in_channels=3,
            device=device,
        )
        synchronize_cuda(torch, device)
        cnn_load_end = time.perf_counter()

        unet_load_start = time.perf_counter()
        unet_model, unet_img_size, unet_device = unet_mod.load_model(
            str(unet_weights),
            device=str(device),
        )
        synchronize_cuda(torch, device)
        unet_load_end = time.perf_counter()

        model_ready = time.perf_counter()

        with tempfile.TemporaryDirectory(prefix="afm_cold_worker_") as temp_dir:
            mask_path = Path(temp_dir) / "first_mask.png"

            synchronize_cuda(torch, device)
            pipeline_start = time.perf_counter()

            cnn_start = time.perf_counter()
            cnn_result = cnn_mod.predict_image(
                cnn_model,
                str(sample_image),
                in_channels=3,
                device=device,
            )
            synchronize_cuda(torch, device)
            cnn_end = time.perf_counter()

            preprocess_start = time.perf_counter()
            tensor, original_size = unet_mod.preprocess_image(
                str(sample_image),
                img_size=unet_img_size,
                denoise=0,
                sharpen=0,
                invert=False,
            )
            preprocess_end = time.perf_counter()

            synchronize_cuda(torch, unet_device)
            unet_inference_start = time.perf_counter()
            predicted_mask = unet_mod.predict_mask(
                unet_model,
                tensor,
                unet_device,
                threshold=0.5,
            )
            synchronize_cuda(torch, unet_device)
            unet_inference_end = time.perf_counter()

            save_start = time.perf_counter()
            unet_mod.save_mask(
                predicted_mask,
                str(mask_path),
                original_size,
            )
            save_end = time.perf_counter()

            synchronize_cuda(torch, device)
            pipeline_end = time.perf_counter()

        payload = {
            "status": "ok",
            "resolved_device": str(device),
            "dependency_import_ms": (dependency_end - dependency_start) * 1000,
            "analysis_module_import_ms": (module_end - module_start) * 1000,
            "cnn_model_load_ms": (cnn_load_end - cnn_load_start) * 1000,
            "unet_model_load_ms": (unet_load_end - unet_load_start) * 1000,
            "cold_model_ready_ms": (model_ready - PROCESS_START) * 1000,
            "first_cnn_ms": (cnn_end - cnn_start) * 1000,
            "first_unet_preprocess_ms": (preprocess_end - preprocess_start) * 1000,
            "first_unet_inference_ms": (
                unet_inference_end - unet_inference_start
            ) * 1000,
            "first_unet_save_ms": (save_end - save_start) * 1000,
            "first_unet_total_ms": (
                (preprocess_end - preprocess_start)
                + (unet_inference_end - unet_inference_start)
                + (save_end - save_start)
            ) * 1000,
            "first_pipeline_ms": (pipeline_end - pipeline_start) * 1000,
            "predicted_class": cnn_result["predicted_class"],
            "confidence": cnn_result["confidence"],
        }
    except Exception as exc:
        payload = {
            "status": "error",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        }

    worker_json.parent.mkdir(parents=True, exist_ok=True)
    worker_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 0 if payload["status"] == "ok" else 1


def run_cold_measurements(
    args: argparse.Namespace,
    project_dir: Path,
    analysis_dir: Path,
    sample_image: Path,
    output_dir: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for run_number in range(1, args.cold_runs + 1):
        print(f"[Cold] fresh process {run_number}/{args.cold_runs}")
        with tempfile.TemporaryDirectory(prefix="afm_cold_parent_") as temp_dir:
            json_path = Path(temp_dir) / "worker_result.json"
            command = [
                sys.executable,
                str(Path(__file__).resolve()),
                "--_cold-worker",
                "--project-dir",
                str(project_dir),
                "--analysis-dir",
                str(analysis_dir),
                "--device",
                args.device,
                "--_sample-image",
                str(sample_image),
                "--_worker-json",
                str(json_path),
            ]

            wall_start = time.perf_counter()
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
            wall_end = time.perf_counter()

            if not json_path.exists():
                raise RuntimeError(
                    "Cold worker did not create its result file.\n"
                    f"Return code: {completed.returncode}\n"
                    f"STDOUT:\n{completed.stdout}\n"
                    f"STDERR:\n{completed.stderr}"
                )

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            row = {
                "run": run_number,
                "device_requested": args.device,
                "resolved_device": payload.get("resolved_device", ""),
                "dependency_import_ms": payload.get("dependency_import_ms", ""),
                "analysis_module_import_ms": payload.get(
                    "analysis_module_import_ms", ""
                ),
                "cnn_model_load_ms": payload.get("cnn_model_load_ms", ""),
                "unet_model_load_ms": payload.get("unet_model_load_ms", ""),
                "cold_model_ready_ms": payload.get("cold_model_ready_ms", ""),
                "first_cnn_ms": payload.get("first_cnn_ms", ""),
                "first_unet_preprocess_ms": payload.get(
                    "first_unet_preprocess_ms", ""
                ),
                "first_unet_inference_ms": payload.get(
                    "first_unet_inference_ms", ""
                ),
                "first_unet_save_ms": payload.get("first_unet_save_ms", ""),
                "first_unet_total_ms": payload.get("first_unet_total_ms", ""),
                "first_pipeline_ms": payload.get("first_pipeline_ms", ""),
                "predicted_class": payload.get("predicted_class", ""),
                "confidence": payload.get("confidence", ""),
                "fresh_process_wall_ms": (wall_end - wall_start) * 1000,
                "status": payload.get("status", "error"),
                "error_type": payload.get("error_type", ""),
                "error_message": payload.get("error_message", ""),
            }
            rows.append(row)

            if row["status"] != "ok":
                raise RuntimeError(
                    f"Cold run {run_number} failed: "
                    f"{row['error_type']}: {row['error_message']}"
                )

    write_csv(output_dir / "cold_start_timing.csv", rows)
    return rows


def load_models_for_warm(analysis_dir: Path, model_dir: Path, device_requested: str):
    dependency_start = time.perf_counter()
    import torch
    dependency_end = time.perf_counter()

    cnn_script = analysis_dir / CNN_SCRIPT_NAME
    unet_script = analysis_dir / UNET_SCRIPT_NAME
    cnn_weights = model_dir / CNN_MODEL_NAME
    unet_weights = model_dir / UNET_MODEL_NAME

    ensure_real_model_file(cnn_weights)
    ensure_real_model_file(unet_weights)

    module_start = time.perf_counter()
    cnn_mod = import_module_from_file("cnn_timing_warm", cnn_script)
    unet_mod = import_module_from_file("unet_timing_warm", unet_script)
    module_end = time.perf_counter()

    device = resolve_torch_device(torch, device_requested)

    cnn_load_start = time.perf_counter()
    cnn_model = cnn_mod.load_model(
        str(cnn_weights),
        in_channels=3,
        device=device,
    )
    synchronize_cuda(torch, device)
    cnn_load_end = time.perf_counter()

    unet_load_start = time.perf_counter()
    unet_model, unet_img_size, unet_device = unet_mod.load_model(
        str(unet_weights),
        device=str(device),
    )
    synchronize_cuda(torch, device)
    unet_load_end = time.perf_counter()

    load_details = {
        "dependency_import_ms": (dependency_end - dependency_start) * 1000,
        "analysis_module_import_ms": (module_end - module_start) * 1000,
        "cnn_model_load_ms": (cnn_load_end - cnn_load_start) * 1000,
        "unet_model_load_ms": (unet_load_end - unet_load_start) * 1000,
        "resolved_device": str(device),
    }

    return (
        torch,
        cnn_mod,
        unet_mod,
        cnn_model,
        unet_model,
        unet_img_size,
        unet_device,
        device,
        load_details,
    )


def run_one_warm_pass(
    torch_module,
    cnn_mod,
    unet_mod,
    cnn_model,
    unet_model,
    unet_img_size,
    unet_device,
    device,
    image_path: Path,
    mask_path: Path,
) -> dict[str, Any]:
    synchronize_cuda(torch_module, device)
    pipeline_start = time.perf_counter()

    cnn_start = time.perf_counter()
    cnn_result = cnn_mod.predict_image(
        cnn_model,
        str(image_path),
        in_channels=3,
        device=device,
    )
    synchronize_cuda(torch_module, device)
    cnn_end = time.perf_counter()

    preprocess_start = time.perf_counter()
    tensor, original_size = unet_mod.preprocess_image(
        str(image_path),
        img_size=unet_img_size,
        denoise=0,
        sharpen=0,
        invert=False,
    )
    preprocess_end = time.perf_counter()

    synchronize_cuda(torch_module, unet_device)
    unet_inference_start = time.perf_counter()
    predicted_mask = unet_mod.predict_mask(
        unet_model,
        tensor,
        unet_device,
        threshold=0.5,
    )
    synchronize_cuda(torch_module, unet_device)
    unet_inference_end = time.perf_counter()

    save_start = time.perf_counter()
    unet_mod.save_mask(
        predicted_mask,
        str(mask_path),
        original_size,
    )
    save_end = time.perf_counter()

    synchronize_cuda(torch_module, device)
    pipeline_end = time.perf_counter()

    unet_preprocess_ms = (preprocess_end - preprocess_start) * 1000
    unet_inference_ms = (unet_inference_end - unet_inference_start) * 1000
    unet_save_ms = (save_end - save_start) * 1000

    return {
        "cnn_total_ms": (cnn_end - cnn_start) * 1000,
        "unet_preprocess_ms": unet_preprocess_ms,
        "unet_inference_ms": unet_inference_ms,
        "unet_save_ms": unet_save_ms,
        "unet_total_ms": (
            unet_preprocess_ms + unet_inference_ms + unet_save_ms
        ),
        "pipeline_total_ms": (pipeline_end - pipeline_start) * 1000,
        "predicted_class": cnn_result["predicted_class"],
        "confidence": cnn_result["confidence"],
    }


def run_warm_measurements(
    args: argparse.Namespace,
    analysis_dir: Path,
    image_records: list[dict[str, str]],
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    (
        torch_module,
        cnn_mod,
        unet_mod,
        cnn_model,
        unet_model,
        unet_img_size,
        unet_device,
        device,
        load_details,
    ) = load_models_for_warm(analysis_dir, project_dir / "models", args.device)

    warm_mask_dir = output_dir / "warm_generated_masks"
    warm_mask_dir.mkdir(parents=True, exist_ok=True)

    # One unrecorded pass before any warm measurements.
    warmup_record = image_records[0]
    warmup_path = Path(warmup_record["image_path"])
    warmup_mask = warm_mask_dir / "_warmup_mask.png"
    print(f"[Warm-up] {warmup_record['relative_path']} (discarded)")
    run_one_warm_pass(
        torch_module,
        cnn_mod,
        unet_mod,
        cnn_model,
        unet_model,
        unet_img_size,
        unet_device,
        device,
        warmup_path,
        warmup_mask,
    )

    per_run_rows: list[dict[str, Any]] = []

    for image_index, record in enumerate(image_records, start=1):
        image_path = Path(record["image_path"])
        print(
            f"[Warm] image {image_index}/{len(image_records)}: "
            f"{record['relative_path']}"
        )

        for repeat in range(1, args.repeats + 1):
            mask_path = (
                warm_mask_dir
                / record["class_label"]
                / f"{image_path.stem}_repeat_{repeat}_mask.png"
            )
            result = run_one_warm_pass(
                torch_module,
                cnn_mod,
                unet_mod,
                cnn_model,
                unet_model,
                unet_img_size,
                unet_device,
                device,
                image_path,
                mask_path,
            )

            per_run_rows.append(
                {
                    "relative_path": record["relative_path"],
                    "class_label": record["class_label"],
                    "image_sha256": sha256_file(image_path),
                    "repeat": repeat,
                    "device": str(device),
                    "cnn_total_ms": result["cnn_total_ms"],
                    "unet_preprocess_ms": result["unet_preprocess_ms"],
                    "unet_inference_ms": result["unet_inference_ms"],
                    "unet_save_ms": result["unet_save_ms"],
                    "unet_total_ms": result["unet_total_ms"],
                    "pipeline_total_ms": result["pipeline_total_ms"],
                    "predicted_class": result["predicted_class"],
                    "confidence": result["confidence"],
                }
            )

    write_csv(output_dir / "warm_inference_per_run.csv", per_run_rows)

    timing_fields = [
        "cnn_total_ms",
        "unet_preprocess_ms",
        "unet_inference_ms",
        "unet_save_ms",
        "unet_total_ms",
        "pipeline_total_ms",
    ]

    per_image_rows: list[dict[str, Any]] = []
    for record in image_records:
        matching = [
            row
            for row in per_run_rows
            if row["relative_path"] == record["relative_path"]
        ]
        summary: dict[str, Any] = {
            "relative_path": record["relative_path"],
            "class_label": record["class_label"],
            "image_sha256": matching[0]["image_sha256"],
            "repeats": len(matching),
            "device": matching[0]["device"],
            "predicted_class": matching[0]["predicted_class"],
            "confidence_median": median(
                [float(row["confidence"]) for row in matching]
            ),
        }

        for field in timing_fields:
            values = [float(row[field]) for row in matching]
            base = field.removesuffix("_ms")
            summary[f"{base}_median_ms"] = median(values)
            summary[f"{base}_mean_ms"] = mean(values)
            summary[f"{base}_sd_ms"] = stdev(values)
            summary[f"{base}_min_ms"] = min(values)
            summary[f"{base}_max_ms"] = max(values)

        summary["pipeline_throughput_images_per_second"] = (
            1000.0 / summary["pipeline_total_median_ms"]
            if summary["pipeline_total_median_ms"] > 0
            else ""
        )
        per_image_rows.append(summary)

    write_csv(output_dir / "warm_inference_per_image.csv", per_image_rows)

    if not args.keep_warm_masks:
        shutil.rmtree(warm_mask_dir, ignore_errors=True)

    return per_run_rows, per_image_rows, load_details


def collect_hardware_info(device_requested: str, resolved_device: str) -> dict[str, Any]:
    import torch

    gpu_name = ""
    gpu_memory_bytes: int | str = ""
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        try:
            gpu_memory_bytes = torch.cuda.get_device_properties(0).total_memory
        except Exception:
            gpu_memory_bytes = ""

    try:
        import psutil
        ram_bytes: int | str = psutil.virtual_memory().total
        cpu_physical_cores: int | str = psutil.cpu_count(logical=False) or ""
        cpu_logical_cores: int | str = psutil.cpu_count(logical=True) or ""
    except Exception:
        ram_bytes = ""
        cpu_physical_cores = ""
        cpu_logical_cores = os.cpu_count() or ""

    return {
        "timestamp_local": time.strftime("%Y-%m-%d %H:%M:%S"),
        "operating_system": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_physical_cores": cpu_physical_cores,
        "cpu_logical_cores": cpu_logical_cores,
        "ram_bytes": ram_bytes,
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "pytorch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_runtime_version": torch.version.cuda or "",
        "gpu_name": gpu_name,
        "gpu_memory_bytes": gpu_memory_bytes,
        "device_requested": device_requested,
        "device_used": resolved_device,
    }


def build_summary(
    cold_rows: list[dict[str, Any]],
    warm_per_image: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = []

    if cold_rows:
        summary_rows.extend(
            [
                descriptive_row(
                    "Cold model-ready time",
                    [float(row["cold_model_ready_ms"]) for row in cold_rows],
                    "ms",
                    (
                        "Fresh Python process; imports, model construction, "
                        "weight loading, and device transfer. Interpreter launch "
                        "overhead is not included."
                    ),
                ),
                descriptive_row(
                    "Cold CNN model load",
                    [float(row["cnn_model_load_ms"]) for row in cold_rows],
                    "ms",
                    "Fresh-process CNN construction and weight loading.",
                ),
                descriptive_row(
                    "Cold U-Net model load",
                    [float(row["unet_model_load_ms"]) for row in cold_rows],
                    "ms",
                    "Fresh-process U-Net construction and checkpoint loading.",
                ),
                descriptive_row(
                    "First CNN inference after cold start",
                    [float(row["first_cnn_ms"]) for row in cold_rows],
                    "ms",
                    "First image after model loading; not included in warm averages.",
                ),
                descriptive_row(
                    "First U-Net total after cold start",
                    [float(row["first_unet_total_ms"]) for row in cold_rows],
                    "ms",
                    "First U-Net preprocessing, inference, resize, and mask save.",
                ),
                descriptive_row(
                    "First combined pipeline after cold start",
                    [float(row["first_pipeline_ms"]) for row in cold_rows],
                    "ms",
                    "First CNN + U-Net pass after model loading.",
                ),
                descriptive_row(
                    "Fresh-process wall time",
                    [float(row["fresh_process_wall_ms"]) for row in cold_rows],
                    "ms",
                    (
                        "Diagnostic end-to-end subprocess time including interpreter "
                        "launch, model readiness, first inference, and process exit."
                    ),
                ),
            ]
        )

    if warm_per_image:
        summary_rows.extend(
            [
                descriptive_row(
                    "Warm CNN per image",
                    [
                        float(row["cnn_total_median_ms"])
                        for row in warm_per_image
                    ],
                    "ms",
                    "Distribution of per-image medians after one discarded warm-up pass.",
                ),
                descriptive_row(
                    "Warm U-Net preprocessing per image",
                    [
                        float(row["unet_preprocess_median_ms"])
                        for row in warm_per_image
                    ],
                    "ms",
                    "Image opening, grayscale conversion, resize, and tensor creation.",
                ),
                descriptive_row(
                    "Warm U-Net inference per image",
                    [
                        float(row["unet_inference_median_ms"])
                        for row in warm_per_image
                    ],
                    "ms",
                    "Forward pass and binary thresholding; CUDA synchronized when used.",
                ),
                descriptive_row(
                    "Warm U-Net mask save per image",
                    [
                        float(row["unet_save_median_ms"])
                        for row in warm_per_image
                    ],
                    "ms",
                    "Resize to original dimensions and PNG save.",
                ),
                descriptive_row(
                    "Warm U-Net total per image",
                    [
                        float(row["unet_total_median_ms"])
                        for row in warm_per_image
                    ],
                    "ms",
                    "Preprocessing + inference + resize/save.",
                ),
                descriptive_row(
                    "Warm CNN + U-Net pipeline per image",
                    [
                        float(row["pipeline_total_median_ms"])
                        for row in warm_per_image
                    ],
                    "ms",
                    (
                        "Combined classifier and segmentation path. "
                        "Downstream Voronoi/color-wheel analysis is not included."
                    ),
                ),
            ]
        )

    return summary_rows


def write_methodology(
    output_dir: Path,
    args: argparse.Namespace,
    image_records: list[dict[str, str]],
    analysis_dir: Path,
    test_dir: Path,
    manifest_path: Path | None,
) -> None:
    class_counts: dict[str, int] = {}
    for record in image_records:
        class_counts[record["class_label"]] = (
            class_counts.get(record["class_label"], 0) + 1
        )

    text = f"""Experiment 3 cold/warm timing methodology
==========================================

Project analysis directory:
{analysis_dir}

Validation image directory:
{test_dir}

Manifest:
{manifest_path if manifest_path else "Not supplied; all images were discovered recursively."}

Images timed:
{len(image_records)}

Class distribution:
{json.dumps(class_counts, indent=2)}

Device request:
{args.device}

Cold-start runs:
{0 if args.skip_cold else args.cold_runs}

Warm repetitions per image:
{0 if args.skip_warm else args.repeats}

Cold-start definition:
Each cold run was executed in a fresh Python process. The cold model-ready
measurement starts near the beginning of the worker script and ends after both
trained models have been imported, constructed, loaded, transferred to the
selected device, synchronized, and placed in evaluation mode. The first CNN
and U-Net pass was then measured separately. Fresh-process wall time is retained
only as a diagnostic because it also includes the first inference and process
shutdown.

Warm-timing definition:
Both trained models remained loaded in one Python process. One complete pass
was run and discarded as a warm-up. Each validation image was then processed
{args.repeats} times. The median of those repetitions was treated as that
image's principal runtime observation.

CNN scope:
Image opening, RGB conversion, resize to 217 x 217, tensor creation, device
transfer, forward pass, softmax, and prediction formatting.

U-Net scope:
Image opening, grayscale conversion, resize to the trained input dimensions,
tensor creation, device transfer, forward pass, sigmoid/thresholding, resizing
the mask to the original image dimensions, and PNG saving.

CUDA:
When CUDA was used, torch.cuda.synchronize() was called around measured GPU
segments so asynchronous execution did not produce falsely short runtimes.

Important limitation:
The warm combined-pipeline value covers CNN classification plus U-Net
segmentation. Voronoi and color-wheel analysis should be timed separately in
the downstream portion of Experiment 3.
"""
    (output_dir / "experiment_3_methodology.txt").write_text(
        text, encoding="utf-8"
    )


def main() -> int:
    args = parse_args()

    if args._cold_worker:
        return cold_worker(args)

    if args.cold_runs < 1 and not args.skip_cold:
        raise ValueError("--cold-runs must be at least 1.")
    if args.repeats < 1 and not args.skip_warm:
        raise ValueError("--repeats must be at least 1.")
    if args.skip_cold and args.skip_warm:
        raise ValueError("Both cold and warm timing were skipped.")

    project_dir = Path(args.project_dir).expanduser().resolve()
    analysis_dir = find_analysis_dir(project_dir, args.analysis_dir)
    test_dir = resolve_path(project_dir, args.test_dir)
    assert test_dir is not None
    manifest_path = resolve_path(project_dir, args.manifest)
    output_dir = resolve_path(project_dir, args.output_dir)
    assert output_dir is not None
    output_dir.mkdir(parents=True, exist_ok=True)

    model_dir = project_dir / "models"
    cnn_weights = model_dir / CNN_MODEL_NAME
    unet_weights = model_dir / UNET_MODEL_NAME
    ensure_real_model_file(cnn_weights)
    ensure_real_model_file(unet_weights)

    image_records = load_images(
        project_dir=project_dir,
        test_dir=test_dir,
        manifest_path=manifest_path,
        max_images=args.max_images,
    )

    print(f"Analysis directory: {analysis_dir}")
    print(f"Test directory: {test_dir}")
    print(f"Images selected: {len(image_records)}")
    print(f"Output directory: {output_dir}")

    sample_image = Path(image_records[0]["image_path"])
    cold_rows: list[dict[str, Any]] = []
    warm_per_run: list[dict[str, Any]] = []
    warm_per_image: list[dict[str, Any]] = []
    resolved_device = args.device

    if not args.skip_cold:
        cold_rows = run_cold_measurements(
            args=args,
            project_dir=project_dir,
            analysis_dir=analysis_dir,
            sample_image=sample_image,
            output_dir=output_dir,
        )
        if cold_rows:
            resolved_device = cold_rows[0]["resolved_device"]

    warm_load_details: dict[str, Any] = {}
    if not args.skip_warm:
        warm_per_run, warm_per_image, warm_load_details = run_warm_measurements(
            args=args,
            analysis_dir=analysis_dir,
            image_records=image_records,
            output_dir=output_dir,
        )
        resolved_device = warm_load_details["resolved_device"]
        write_csv(
            output_dir / "warm_session_model_load.csv",
            [warm_load_details],
        )

    summary_rows = build_summary(cold_rows, warm_per_image)
    if summary_rows:
        write_csv(output_dir / "timing_summary.csv", summary_rows)

    hardware_info = collect_hardware_info(args.device, str(resolved_device))
    write_csv(output_dir / "hardware_info.csv", [hardware_info])

    run_metadata = {
        "project_dir": str(project_dir),
        "analysis_dir": str(analysis_dir),
        "test_dir": str(test_dir),
        "manifest": str(manifest_path) if manifest_path else "",
        "image_count": len(image_records),
        "cold_runs": 0 if args.skip_cold else args.cold_runs,
        "warm_repeats": 0 if args.skip_warm else args.repeats,
        "device_requested": args.device,
        "device_used": str(resolved_device),
        "cnn_model": str(cnn_weights),
        "cnn_model_sha256": sha256_file(cnn_weights),
        "unet_model": str(unet_weights),
        "unet_model_sha256": sha256_file(unet_weights),
        "cnn_script_sha256": sha256_file(analysis_dir / CNN_SCRIPT_NAME),
        "unet_script_sha256": sha256_file(analysis_dir / UNET_SCRIPT_NAME),
        "threshold": 0.5,
        "warmup_passes_discarded": 0 if args.skip_warm else 1,
    }
    write_csv(output_dir / "run_metadata.csv", [run_metadata])

    write_methodology(
        output_dir=output_dir,
        args=args,
        image_records=image_records,
        analysis_dir=analysis_dir,
        test_dir=test_dir,
        manifest_path=manifest_path,
    )

    print("\nTiming complete.")
    print(f"Results saved to: {output_dir}")
    for filename in (
        "cold_start_timing.csv",
        "warm_inference_per_run.csv",
        "warm_inference_per_image.csv",
        "timing_summary.csv",
        "hardware_info.csv",
        "run_metadata.csv",
        "experiment_3_methodology.txt",
    ):
        path = output_dir / filename
        if path.exists():
            print(f"  - {path.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
