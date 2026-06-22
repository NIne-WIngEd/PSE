from __future__ import annotations

import argparse
import csv
import statistics
import time
from pathlib import Path
from typing import Any, Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common import (
    choose_device,
    default_project_dir,
    discover_classification_images,
    import_module_from_path,
    load_cnn,
    load_manifest,
    load_unet,
    relative_posix,
    run_cnn_prediction,
    synchronize,
    write_csv,
    write_json,
)


def timed_call(func, device, repeats: int):
    values = []
    result = None
    for _ in range(repeats):
        synchronize(device)
        start = time.perf_counter()
        result = func()
        synchronize(device)
        values.append((time.perf_counter() - start) * 1000.0)
    return result, values


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Experiment 3: automated pipeline timing and optional manual comparison."
    )
    parser.add_argument("--project-dir", type=Path, default=default_project_dir())
    parser.add_argument("--test-dir", type=Path, default=None)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--manual-timing-csv", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--max-images", type=int, default=20)
    parser.add_argument(
        "--include-downstream", action="store_true",
        help="Also time Voronoi/ColorWheel file-generating analysis once per image."
    )
    args = parser.parse_args()

    project = args.project_dir.expanduser().resolve()
    test_dir = (args.test_dir or project / "test").expanduser().resolve()
    output_dir = (
        args.output_dir or project / "evaluation_outputs" / "experiment_3_timing"
    ).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    device = choose_device(args.device)
    manifest = load_manifest(args.manifest)
    items = discover_classification_images(test_dir)
    selected = []
    for path, label in items:
        rel = relative_posix(path, test_dir)
        if bool(manifest.get(rel, {}).get("include_in_primary", True)):
            selected.append((path, label))
    if args.max_images > 0:
        # Keep the original deterministic class/path order for reproducibility.
        selected = selected[: args.max_images]

    load_start = time.perf_counter()
    cnn_mod, cnn_model, paths = load_cnn(project, device)
    cnn_load_ms = (time.perf_counter() - load_start) * 1000.0

    load_start = time.perf_counter()
    unet_mod, unet_model, unet_img_size, unet_device, _ = load_unet(project, device)
    unet_load_ms = (time.perf_counter() - load_start) * 1000.0

    vor_mod = cw_mod = None
    if args.include_downstream:
        vor_mod = import_module_from_path("voronoi_timing_backend", paths.voronoi_script)
        cw_mod = import_module_from_path("colorwheel_timing_backend", paths.colorwheel_script)

    # Warm both neural-network models once.
    first = selected[0][0]
    _ = run_cnn_prediction(cnn_mod, cnn_model, first, device)
    tensor, _ = unet_mod.preprocess_image(str(first), img_size=unet_img_size)
    _ = unet_mod.predict_mask(unet_model, tensor, unet_device, threshold=0.5)

    rows: List[Dict[str, Any]] = []
    runtime_root = output_dir / "runtime_outputs"
    runtime_root.mkdir(parents=True, exist_ok=True)

    for index, (image_path, true_label) in enumerate(selected, start=1):
        rel = relative_posix(image_path, test_dir)

        prediction, cnn_times = timed_call(
            lambda: run_cnn_prediction(cnn_mod, cnn_model, image_path, device),
            device,
            max(1, args.repeats),
        )

        tensor, original_size = unet_mod.preprocess_image(
            str(image_path), img_size=unet_img_size, denoise=0, sharpen=0, invert=False
        )
        mask, unet_times = timed_call(
            lambda: unet_mod.predict_mask(
                unet_model, tensor, unet_device, threshold=0.5
            ),
            unet_device,
            max(1, args.repeats),
        )

        item_dir = runtime_root / image_path.parent.name / image_path.stem
        item_dir.mkdir(parents=True, exist_ok=True)
        mask_path = item_dir / "predicted_mask.png"
        unet_mod.save_mask(mask, str(mask_path), original_size)

        raw_pred = str(prediction["predicted_class"]).lower()
        # This exactly mirrors the current Flask app's routing behavior.
        routing_label = "mixed" if raw_pred == "irregular" else raw_pred
        downstream_ms = None
        downstream_status = "not_requested"

        if args.include_downstream:
            start = time.perf_counter()
            try:
                if routing_label in ("dots", "mixed"):
                    vor_mod.run_voronoi_analysis(
                        image_path=str(mask_path),
                        image_size=1.0,
                        output_dir=str(item_dir / "voronoi_outputs"),
                        threshold_edge=0.025,
                        max_size=1024,
                    )
                if routing_label in ("lines", "mixed"):
                    cw_mod.analyze_image(
                        image_path=str(mask_path),
                        output_dir=str(item_dir / "colorwheel_output"),
                        num_clusters=8,
                    )
                downstream_status = "completed"
            except Exception as exc:
                downstream_status = f"failed: {type(exc).__name__}: {exc}"
            downstream_ms = (time.perf_counter() - start) * 1000.0

        cnn_median = statistics.median(cnn_times)
        unet_median = statistics.median(unet_times)
        neural_total = cnn_median + unet_median
        full_total = neural_total + (downstream_ms or 0.0)
        rows.append({
            "relative_path": rel,
            "true_label": true_label,
            "predicted_label_raw": raw_pred,
            "routing_label_used_by_app": routing_label,
            "cnn_time_ms_median": cnn_median,
            "cnn_time_ms_mean": statistics.mean(cnn_times),
            "unet_time_ms_median": unet_median,
            "unet_time_ms_mean": statistics.mean(unet_times),
            "neural_pipeline_time_ms": neural_total,
            "downstream_time_ms": downstream_ms,
            "downstream_status": downstream_status,
            "full_automated_time_ms": full_total,
            "repeats_for_cnn_and_unet": max(1, args.repeats),
        })
        print(
            f"[{index:03d}/{len(selected):03d}] {rel}: "
            f"CNN={cnn_median:.1f} ms, U-Net={unet_median:.1f} ms, "
            f"full={full_total:.1f} ms"
        )

    df = pd.DataFrame(rows)
    df.to_csv(output_dir / "automated_timing_per_image.csv", index=False)

    timing_columns = [
        "cnn_time_ms_median", "unet_time_ms_median",
        "neural_pipeline_time_ms", "full_automated_time_ms"
    ]
    summary_rows = []
    for column in timing_columns:
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        summary_rows.append({
            "timing_component": column,
            "n_images": len(values),
            "mean_ms": float(values.mean()),
            "median_ms": float(values.median()),
            "standard_deviation_ms": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
            "minimum_ms": float(values.min()),
            "maximum_ms": float(values.max()),
        })
    summary_rows.extend([
        {"timing_component": "cnn_model_load", "n_images": 1, "mean_ms": cnn_load_ms,
         "median_ms": cnn_load_ms, "standard_deviation_ms": 0.0,
         "minimum_ms": cnn_load_ms, "maximum_ms": cnn_load_ms},
        {"timing_component": "unet_model_load", "n_images": 1, "mean_ms": unet_load_ms,
         "median_ms": unet_load_ms, "standard_deviation_ms": 0.0,
         "minimum_ms": unet_load_ms, "maximum_ms": unet_load_ms},
    ])
    write_csv(output_dir / "automated_timing_summary.csv", summary_rows)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    df[["cnn_time_ms_median", "unet_time_ms_median", "full_automated_time_ms"]].plot(
        kind="box", ax=ax
    )
    ax.set_ylabel("Time (ms)")
    ax.set_title("Automated AFM pipeline timing")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(output_dir / "automated_timing_boxplot.png", dpi=300)
    plt.close(fig)

    # Create a blank manual-timing template when one was not supplied.
    template_path = output_dir / "manual_timing_template.csv"
    template_rows = [
        {
            "relative_path": row["relative_path"],
            "true_label": row["true_label"],
            "analyst_id": "",
            "manual_time_seconds": "",
            "manual_workflow_definition": "",
            "notes": "",
        }
        for row in rows
    ]
    write_csv(template_path, template_rows)

    if args.manual_timing_csv:
        manual = pd.read_csv(args.manual_timing_csv)
        required = {"relative_path", "manual_time_seconds"}
        if not required.issubset(manual.columns):
            raise ValueError(
                f"Manual timing CSV must contain columns: {sorted(required)}"
            )
        merged = df.merge(manual, on="relative_path", how="inner")
        merged["automated_time_seconds"] = merged["full_automated_time_ms"] / 1000.0
        merged["speedup_factor"] = (
            merged["manual_time_seconds"] / merged["automated_time_seconds"]
        )
        merged["time_saved_seconds"] = (
            merged["manual_time_seconds"] - merged["automated_time_seconds"]
        )
        merged.to_csv(output_dir / "manual_vs_automated_per_image.csv", index=False)
        comparison_summary = {
            "n_images": int(len(merged)),
            "mean_manual_seconds": float(merged["manual_time_seconds"].mean()),
            "mean_automated_seconds": float(merged["automated_time_seconds"].mean()),
            "median_speedup_factor": float(merged["speedup_factor"].median()),
            "mean_time_saved_seconds": float(merged["time_saved_seconds"].mean()),
        }
        write_json(output_dir / "manual_vs_automated_summary.json", comparison_summary)

        fig, ax = plt.subplots(figsize=(7.5, 5.5))
        pd.DataFrame({
            "Manual": merged["manual_time_seconds"],
            "Automated": merged["automated_time_seconds"],
        }).plot(kind="box", ax=ax)
        ax.set_ylabel("Time per image (seconds)")
        ax.set_title("Manual versus automated AFM analysis time")
        fig.tight_layout()
        fig.savefig(output_dir / "manual_vs_automated_boxplot.png", dpi=300)
        plt.close(fig)

    write_json(output_dir / "timing_protocol.json", {
        "device": str(device),
        "cnn_model_load_ms": cnn_load_ms,
        "unet_model_load_ms": unet_load_ms,
        "cnn_and_unet_repeats": max(1, args.repeats),
        "warmup_performed": True,
        "downstream_included": args.include_downstream,
        "n_images": len(df),
        "important_reporting_note": (
            "Report model-loading time separately from warm per-image inference. "
            "The deployed Flask app loads both models once at startup."
        ),
    })
    print(f"Timing experiment complete: {output_dir}")
    print(f"Manual timing template: {template_path}")


if __name__ == "__main__":
    main()
