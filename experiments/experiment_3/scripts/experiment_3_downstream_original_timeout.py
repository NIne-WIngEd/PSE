#!/usr/bin/env python3
"""
Experiment 3B downstream timing using the repository's ORIGINAL ColorWheel.

This script does not replace or edit app.py or 3.colorwheel.py.

It:
- reads the supplied 49-image Experiment 3 manifest;
- generates one U-Net mask per included image before downstream timing;
- times Voronoi in-process;
- runs the original ColorWheel in an isolated subprocess;
- terminates a ColorWheel repetition after the configured timeout;
- logs failures/timeouts and continues to the next image;
- writes raw, per-image, summary, routing, failure, and methodology files.
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
import platform
import shutil
import statistics
import subprocess
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
COLORWHEEL_SCRIPT_NAME = "3.colorwheel_before_fix.py"
WORKER_NAME = "colorwheel_original_worker.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Timeout-safe timing of the original downstream AFM pipeline."
    )
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--analysis-dir", default=None)
    parser.add_argument("--test-dir", default="test")
    parser.add_argument(
        "--manifest",
        default="cnn_predictions_primary_reviewed_exp3_49.csv",
    )
    parser.add_argument(
        "--output-dir",
        default="evaluation_outputs/experiment_3_downstream_original_49",
    )
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--max-images", type=int, default=0)
    parser.add_argument("--colorwheel-timeout-seconds", type=float, default=120.0)
    parser.add_argument("--num-clusters", type=int, default=8)
    parser.add_argument("--keep-generated-outputs", action="store_true")
    parser.add_argument("--keep-predicted-masks", action="store_true")
    return parser.parse_args()


def resolve_path(base: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    return (base / path).resolve() if not path.is_absolute() else path.resolve()


def import_module_from_file(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_analysis_dir(project_dir: Path, explicit: str | None) -> Path:
    candidates = (
        [resolve_path(project_dir, explicit)]
        if explicit
        else [project_dir / "backend", project_dir]
    )
    required = [
        UNET_SCRIPT_NAME,
        VORONOI_SCRIPT_NAME,
        COLORWHEEL_SCRIPT_NAME,
    ]
    for candidate in candidates:
        if all((candidate / name).exists() for name in required):
            return candidate.resolve()
    raise FileNotFoundError(
        "Could not find the backend directory containing the U-Net, Voronoi, "
        "and archived pre-fix ColorWheel modules."
    )


def ensure_real_model(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    head = path.read_bytes()[:200]
    if b"version https://git-lfs.github.com/spec" in head or path.stat().st_size < 10000:
        raise RuntimeError(f"{path.name} does not appear to contain real weights.")


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
) -> list[dict[str, str]]:
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        if "relative_path" not in fields or "predicted_label" not in fields:
            raise ValueError("Manifest must contain relative_path and predicted_label.")

        include_column = next(
            (
                name
                for name in ("include_in_evaluation", "include_in_primary", "include")
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
                raise FileNotFoundError(f"Image not found: {image_path}")
            if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            predicted = str(row["predicted_label"]).strip().lower()
            if predicted not in {"dots", "lines", "mixed", "irregular"}:
                raise ValueError(f"Unsupported predicted label: {predicted}")

            records.append(
                {
                    "relative_path": relative.as_posix(),
                    "true_label": str(
                        row.get("true_label", relative.parts[0])
                    ).strip().lower(),
                    "predicted_label": predicted,
                    "confidence": str(row.get("confidence", "")),
                    "image_path": str(image_path),
                }
            )

    if max_images > 0:
        records = records[:max_images]
    if not records:
        raise RuntimeError("No images selected.")
    return records


def route_for(label: str) -> tuple[bool, bool, str]:
    if label == "dots":
        return True, False, "voronoi"
    if label == "lines":
        return False, True, "colorwheel"
    if label == "mixed":
        return True, True, "voronoi+colorwheel"
    return False, False, "none"


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


def generate_masks(
    records: list[dict[str, str]],
    analysis_dir: Path,
    model_dir: Path,
    requested_device: str,
    mask_root: Path,
) -> tuple[dict[str, Path], str]:
    import torch

    unet = import_module_from_file(
        "unet_original_downstream_timing",
        analysis_dir / UNET_SCRIPT_NAME,
    )
    device = choose_device(torch, requested_device)
    model, image_size, model_device = unet.load_model(
        str(model_dir / UNET_MODEL_NAME),
        device=str(device),
    )
    synchronize(torch, model_device)

    # Discard one warm-up pass.
    first = Path(records[0]["image_path"])
    tensor, original_size = unet.preprocess_image(
        str(first),
        img_size=image_size,
        denoise=0,
        sharpen=0,
        invert=False,
    )
    _ = unet.predict_mask(model, tensor, model_device, threshold=0.5)
    synchronize(torch, model_device)

    masks: dict[str, Path] = {}
    for index, record in enumerate(records, start=1):
        image_path = Path(record["image_path"])
        mask_path = (
            mask_root
            / record["predicted_label"]
            / f"{image_path.stem}_predicted_mask.png"
        )
        mask_path.parent.mkdir(parents=True, exist_ok=True)

        tensor, original_size = unet.preprocess_image(
            str(image_path),
            img_size=image_size,
            denoise=0,
            sharpen=0,
            invert=False,
        )
        prediction = unet.predict_mask(
            model,
            tensor,
            model_device,
            threshold=0.5,
        )
        synchronize(torch, model_device)
        unet.save_mask(prediction, str(mask_path), original_size)
        masks[record["relative_path"]] = mask_path
        print(f"[Mask {index:03d}/{len(records):03d}] {record['relative_path']}")

    return masks, str(model_device)


def quiet_timed_call(function):
    sink = io.StringIO()
    start = time.perf_counter()
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        result = function()
    return (time.perf_counter() - start) * 1000.0, result


def stage_mask(source: Path, run_dir: Path) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    staged = run_dir / "predicted_mask.png"
    shutil.copy2(source, staged)
    return staged


def run_original_colorwheel(
    worker_path: Path,
    colorwheel_module: Path,
    image_path: Path,
    output_dir: Path,
    timeout_seconds: float,
    num_clusters: int,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    result_json = output_dir / "_worker_result.json"

    command = [
        sys.executable,
        str(worker_path),
        "--module",
        str(colorwheel_module),
        "--image",
        str(image_path),
        "--output-dir",
        str(output_dir),
        "--result-json",
        str(result_json),
        "--num-clusters",
        str(num_clusters),
    ]

    wall_start = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "elapsed_ms": "",
            "worker_wall_ms": (time.perf_counter() - wall_start) * 1000.0,
            "error_type": "TimeoutExpired",
            "error_message": (
                f"Original ColorWheel exceeded {timeout_seconds:.1f} seconds."
            ),
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        }

    wall_ms = (time.perf_counter() - wall_start) * 1000.0

    if not result_json.exists():
        return {
            "status": "failed",
            "elapsed_ms": "",
            "worker_wall_ms": wall_ms,
            "error_type": "MissingWorkerResult",
            "error_message": (
                f"Worker returned code {completed.returncode} without JSON."
            ),
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }

    payload = json.loads(result_json.read_text(encoding="utf-8"))
    payload["worker_wall_ms"] = wall_ms
    payload["stdout"] = completed.stdout
    payload["stderr"] = completed.stderr
    return payload


def median_or_blank(values: list[float]):
    return statistics.median(values) if values else ""


def mean_or_blank(values: list[float]):
    return statistics.fmean(values) if values else ""


def sd_or_blank(values: list[float]):
    if not values:
        return ""
    return statistics.stdev(values) if len(values) > 1 else 0.0


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


def summarize(component: str, values: list[float], note: str) -> dict[str, Any]:
    med = statistics.median(values)
    return {
        "component": component,
        "n_images": len(values),
        "mean_ms": statistics.fmean(values),
        "standard_deviation_ms": (
            statistics.stdev(values) if len(values) > 1 else 0.0
        ),
        "median_ms": med,
        "q1_ms": percentile(values, 0.25),
        "q3_ms": percentile(values, 0.75),
        "minimum_ms": min(values),
        "maximum_ms": max(values),
        "throughput_per_second_from_median": 1000.0 / med if med > 0 else "",
        "notes": note,
    }


def main() -> int:
    args = parse_args()
    if args.repeats < 1:
        raise ValueError("--repeats must be at least 1.")

    script_dir = Path(__file__).resolve().parent
    worker_path = script_dir / WORKER_NAME
    if not worker_path.exists():
        raise FileNotFoundError(
            f"Place {WORKER_NAME} beside this timing script."
        )

    project_dir = Path(args.project_dir).expanduser().resolve()
    analysis_dir = find_analysis_dir(project_dir, args.analysis_dir)
    test_dir = resolve_path(project_dir, args.test_dir)
    manifest_path = resolve_path(project_dir, args.manifest)
    output_dir = resolve_path(project_dir, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_dir = project_dir / "models"
    ensure_real_model(model_dir / UNET_MODEL_NAME)

    records = load_records(
        manifest_path,
        test_dir,
        args.max_images,
    )

    print(f"Analysis directory: {analysis_dir}")
    print(f"Images selected: {len(records)}")
    print(f"Downstream repetitions: {args.repeats}")
    print(f"Original ColorWheel timeout: {args.colorwheel_timeout_seconds:.1f} s")
    print(f"Output directory: {output_dir}")

    mask_root = output_dir / "generated_predicted_masks"
    masks, device_used = generate_masks(
        records,
        analysis_dir,
        model_dir,
        args.device,
        mask_root,
    )

    if str(analysis_dir) not in sys.path:
        sys.path.insert(0, str(analysis_dir))
    import_start = time.perf_counter()
    voronoi = import_module_from_file(
        "voronoi_original_downstream_timing",
        analysis_dir / VORONOI_SCRIPT_NAME,
    )
    voronoi_import_ms = (time.perf_counter() - import_start) * 1000.0

    write_csv(
        output_dir / "downstream_module_import.csv",
        [{
            "voronoi_module_import_ms": voronoi_import_ms,
            "colorwheel_import_note": (
                "Original ColorWheel imported inside every isolated worker; "
                "worker wall time is recorded separately."
            ),
        }],
    )

    runtime_root = output_dir / "runtime_outputs"
    per_run: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for image_index, record in enumerate(records, start=1):
        run_voronoi, run_colorwheel, route = route_for(
            record["predicted_label"]
        )
        print(
            f"[Downstream {image_index:03d}/{len(records):03d}] "
            f"{record['relative_path']} -> {route}"
        )

        if route == "none":
            per_run.append({
                "relative_path": record["relative_path"],
                "true_label": record["true_label"],
                "predicted_label": record["predicted_label"],
                "confidence": record["confidence"],
                "routing": route,
                "repeat": 0,
                "voronoi_ms": "",
                "voronoi_status": "not_applicable",
                "colorwheel_analysis_ms": "",
                "colorwheel_worker_wall_ms": "",
                "colorwheel_status": "not_applicable",
                "downstream_total_ms": 0.0,
                "overall_status": "completed_no_downstream",
            })
            continue

        for repeat in range(1, args.repeats + 1):
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
            colorwheel_ms: float | str = ""
            colorwheel_wall_ms: float | str = ""
            voronoi_status = "not_applicable"
            colorwheel_status = "not_applicable"
            downstream_total_ms = 0.0
            overall_status = "completed"

            if run_voronoi:
                try:
                    voronoi_ms, result = quiet_timed_call(
                        lambda: voronoi.run_voronoi_analysis(
                            image_path=str(staged_mask),
                            image_size=1.0,
                            output_dir=str(run_dir / "voronoi_outputs"),
                            threshold_edge=0.025,
                            max_size=1024,
                        )
                    )
                    downstream_total_ms += float(voronoi_ms)
                    if result is None:
                        voronoi_status = "failed: returned_none"
                        overall_status = "partial_or_failed"
                    elif isinstance(result, dict) and not result.get(
                        "ran_voronoi", False
                    ):
                        voronoi_status = (
                            f"skipped: {result.get('reason', 'unknown')}"
                        )
                    else:
                        voronoi_status = "completed"
                except Exception as exc:
                    voronoi_status = (
                        f"failed: {type(exc).__name__}: {exc}"
                    )
                    overall_status = "partial_or_failed"
                    failures.append({
                        "relative_path": record["relative_path"],
                        "predicted_label": record["predicted_label"],
                        "repeat": repeat,
                        "component": "voronoi",
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    })

            if run_colorwheel:
                result = run_original_colorwheel(
                    worker_path=worker_path,
                    colorwheel_module=analysis_dir / COLORWHEEL_SCRIPT_NAME,
                    image_path=staged_mask,
                    output_dir=run_dir / "colorwheel_output",
                    timeout_seconds=args.colorwheel_timeout_seconds,
                    num_clusters=args.num_clusters,
                )
                colorwheel_wall_ms = result.get("worker_wall_ms", "")
                if result.get("status") == "completed":
                    colorwheel_ms = float(result["elapsed_ms"])
                    downstream_total_ms += colorwheel_ms
                    colorwheel_status = "completed"
                else:
                    overall_status = "partial_or_failed"
                    colorwheel_status = (
                        f"{result.get('status')}: "
                        f"{result.get('error_type', '')}: "
                        f"{result.get('error_message', '')}"
                    )
                    failures.append({
                        "relative_path": record["relative_path"],
                        "predicted_label": record["predicted_label"],
                        "repeat": repeat,
                        "component": "colorwheel",
                        "error_type": result.get(
                            "error_type",
                            result.get("status", "failed"),
                        ),
                        "error_message": result.get("error_message", ""),
                    })

            per_run.append({
                "relative_path": record["relative_path"],
                "true_label": record["true_label"],
                "predicted_label": record["predicted_label"],
                "confidence": record["confidence"],
                "routing": route,
                "repeat": repeat,
                "voronoi_ms": voronoi_ms,
                "voronoi_status": voronoi_status,
                "colorwheel_analysis_ms": colorwheel_ms,
                "colorwheel_worker_wall_ms": colorwheel_wall_ms,
                "colorwheel_status": colorwheel_status,
                "downstream_total_ms": downstream_total_ms,
                "overall_status": overall_status,
            })

            if not args.keep_generated_outputs:
                shutil.rmtree(run_dir, ignore_errors=True)

    write_csv(output_dir / "downstream_timing_per_run.csv", per_run)
    if failures:
        write_csv(output_dir / "downstream_failures.csv", failures)

    # Per-image aggregation.
    per_image: list[dict[str, Any]] = []
    for record in records:
        route = route_for(record["predicted_label"])[2]
        image_rows = [
            row for row in per_run
            if row["relative_path"] == record["relative_path"]
        ]
        successful = [
            row for row in image_rows
            if row["overall_status"] in {
                "completed",
                "completed_no_downstream",
            }
        ]

        def values(field: str) -> list[float]:
            result = []
            for row in successful:
                value = row.get(field)
                if value not in ("", None):
                    result.append(float(value))
            return result

        vor = values("voronoi_ms")
        color = values("colorwheel_analysis_ms")
        wall = values("colorwheel_worker_wall_ms")
        total = values("downstream_total_ms")

        per_image.append({
            "relative_path": record["relative_path"],
            "true_label": record["true_label"],
            "predicted_label": record["predicted_label"],
            "routing": route,
            "repeats_expected": 0 if route == "none" else args.repeats,
            "successful_repeats": len(successful),
            "voronoi_median_ms": median_or_blank(vor),
            "voronoi_mean_ms": mean_or_blank(vor),
            "voronoi_sd_ms": sd_or_blank(vor),
            "colorwheel_analysis_median_ms": median_or_blank(color),
            "colorwheel_analysis_mean_ms": mean_or_blank(color),
            "colorwheel_analysis_sd_ms": sd_or_blank(color),
            "colorwheel_worker_wall_median_ms": median_or_blank(wall),
            "downstream_total_median_ms": median_or_blank(total),
            "downstream_total_mean_ms": mean_or_blank(total),
            "downstream_total_sd_ms": sd_or_blank(total),
            "status": (
                "completed_no_downstream"
                if route == "none"
                else "completed"
                if len(successful) == args.repeats
                else "incomplete_or_failed"
            ),
        })

    write_csv(output_dir / "downstream_timing_per_image.csv", per_image)

    # Summary only uses images with complete expected repetitions.
    complete = [
        row for row in per_image
        if row["status"] in {"completed", "completed_no_downstream"}
    ]

    vor_values = [
        float(row["voronoi_median_ms"])
        for row in complete
        if row["voronoi_median_ms"] not in ("", None)
    ]
    color_values = [
        float(row["colorwheel_analysis_median_ms"])
        for row in complete
        if row["colorwheel_analysis_median_ms"] not in ("", None)
    ]
    routed_total_values = [
        float(row["downstream_total_median_ms"])
        for row in complete
        if row["routing"] != "none"
        and row["downstream_total_median_ms"] not in ("", None)
    ]
    all_total_values = [
        float(row["downstream_total_median_ms"])
        for row in complete
        if row["downstream_total_median_ms"] not in ("", None)
    ]

    summary_rows: list[dict[str, Any]] = []
    if vor_values:
        summary_rows.append(summarize(
            "Voronoi analysis",
            vor_values,
            "Complete applicable images only; image-level medians.",
        ))
    if color_values:
        summary_rows.append(summarize(
            "Original ColorWheel analysis",
            color_values,
            (
                "Complete applicable images only; excludes worker startup "
                "and timed-out/failed images."
            ),
        ))
    if routed_total_values:
        summary_rows.append(summarize(
            "Downstream total among routed images",
            routed_total_values,
            "Complete routed images only.",
        ))
    if all_total_values:
        summary_rows.append(summarize(
            "Downstream total across included Experiment 3B images",
            all_total_values,
            "No-downstream irregular cases contribute 0 ms.",
        ))
    write_csv(output_dir / "downstream_timing_summary.csv", summary_rows)

    routing_counts: dict[str, int] = {}
    for record in records:
        route = route_for(record["predicted_label"])[2]
        routing_counts[route] = routing_counts.get(route, 0) + 1

    routing_rows = [
        {"routing": route, "n_images": routing_counts.get(route, 0)}
        for route in ("voronoi", "colorwheel", "voronoi+colorwheel", "none")
    ]
    write_csv(output_dir / "downstream_routing_summary.csv", routing_rows)

    metadata = [{
        "timestamp_local": time.strftime("%Y-%m-%d %H:%M:%S"),
        "operating_system": platform.platform(),
        "python_version": platform.python_version(),
        "image_count": len(records),
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "analysis_dir": str(analysis_dir),
        "original_app_and_colorwheel_preserved": True,
        "repeats": args.repeats,
        "colorwheel_timeout_seconds": args.colorwheel_timeout_seconds,
        "colorwheel_num_clusters_argument": args.num_clusters,
        "important_colorwheel_note": (
            "Original implementation internally hardcodes four masks even "
            "when num_clusters=8 is passed."
        ),
        "device_for_mask_generation": device_used,
        "unet_model_sha256": sha256_file(model_dir / UNET_MODEL_NAME),
        "colorwheel_script_sha256": sha256_file(
            analysis_dir / COLORWHEEL_SCRIPT_NAME
        ),
    }]
    write_csv(output_dir / "downstream_run_metadata.csv", metadata)

    methodology = f"""Experiment 3B downstream timing — original pipeline
===================================================

Included images:
{len(records)}

Manifest:
{manifest_path}

Excluded case:
irregular/irregular_06.jpeg was excluded from Experiment 3B downstream runtime
only because the original full-resolution ColorWheel did not complete within
15 minutes on that 1254 x 1254 low-confidence misrouted image. It remains in
Experiments 1 and 2.

Code:
The repository's original app.py and 3.colorwheel.py were preserved. No image
resizing, K-means replacement, or connected-component optimization was applied.

Timeout:
Every original ColorWheel repetition ran in an isolated Python subprocess with
a {args.colorwheel_timeout_seconds:.1f}-second timeout. A timeout was recorded
as a technical failure and the experiment continued.

Repetitions:
{args.repeats} per applicable included image.

Routing:
- predicted dots -> Voronoi
- predicted lines -> ColorWheel
- predicted mixed -> Voronoi + ColorWheel
- predicted irregular -> no downstream analysis

Mask generation:
Predicted U-Net masks were generated once before downstream timing. Their
generation time is excluded because neural timing was measured in Experiment
3A.

Important limitation:
The original ColorWheel implementation calls KMeans on all image pixels, uses
large Python pixel/BFS loops, and internally hardcodes four color masks despite
receiving num_clusters=8. Therefore, downstream timing is conditional on cases
that finish within the timeout. Report the excluded case and any additional
timeouts transparently.
"""
    (output_dir / "downstream_methodology.txt").write_text(
        methodology,
        encoding="utf-8",
    )

    if not args.keep_predicted_masks:
        shutil.rmtree(mask_root, ignore_errors=True)

    print("\nExperiment 3B timing complete.")
    print(f"Included images: {len(records)}")
    print(f"Failures/timeouts: {len(failures)}")
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
