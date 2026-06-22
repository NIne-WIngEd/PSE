from __future__ import annotations

import argparse
import math
import time
from pathlib import Path
from typing import Any, Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    balanced_accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
    matthews_corrcoef,
    precision_recall_fscore_support,
)

from common import (
    CLASS_LABELS,
    choose_device,
    default_project_dir,
    discover_classification_images,
    image_metadata,
    load_cnn,
    load_manifest,
    relative_posix,
    run_cnn_prediction,
    runtime_metadata,
    sha256_file,
    synchronize,
    write_csv,
    write_json,
)


def wilson_interval(correct: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        return (float("nan"), float("nan"))
    p = correct / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def expected_calibration_error(conf: np.ndarray, correct: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0
    for lower, upper in zip(edges[:-1], edges[1:]):
        if upper == 1.0:
            mask = (conf >= lower) & (conf <= upper)
        else:
            mask = (conf >= lower) & (conf < upper)
        if not np.any(mask):
            continue
        bin_acc = correct[mask].mean()
        bin_conf = conf[mask].mean()
        ece += mask.mean() * abs(bin_acc - bin_conf)
    return float(ece)


def compute_metrics(df: pd.DataFrame, output_dir: Path, prefix: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    y_true = df["true_label"].astype(str).to_numpy()
    y_pred = df["predicted_label"].astype(str).to_numpy()
    confidence = df["confidence"].astype(float).to_numpy()
    correct = (y_true == y_pred).astype(int)

    accuracy = accuracy_score(y_true, y_pred)
    balanced = balanced_accuracy_score(y_true, y_pred)
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=CLASS_LABELS, average="macro", zero_division=0
    )
    weighted_p, weighted_r, weighted_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=CLASS_LABELS, average="weighted", zero_division=0
    )
    per_p, per_r, per_f1, per_support = precision_recall_fscore_support(
        y_true, y_pred, labels=CLASS_LABELS, average=None, zero_division=0
    )

    n = len(df)
    n_correct = int(correct.sum())
    ci_low, ci_high = wilson_interval(n_correct, n)
    summary = {
        "evaluation_name": prefix,
        "n_images": n,
        "n_correct": n_correct,
        "accuracy": float(accuracy),
        "accuracy_95_ci_low_wilson": float(ci_low),
        "accuracy_95_ci_high_wilson": float(ci_high),
        "balanced_accuracy": float(balanced),
        "macro_precision": float(macro_p),
        "macro_recall": float(macro_r),
        "macro_f1": float(macro_f1),
        "weighted_precision": float(weighted_p),
        "weighted_recall": float(weighted_r),
        "weighted_f1": float(weighted_f1),
        "matthews_correlation_coefficient": float(matthews_corrcoef(y_true, y_pred)),
        "cohen_kappa": float(cohen_kappa_score(y_true, y_pred, labels=CLASS_LABELS)),
        "mean_confidence": float(confidence.mean()),
        "mean_confidence_correct": float(confidence[correct == 1].mean()) if np.any(correct == 1) else None,
        "mean_confidence_incorrect": float(confidence[correct == 0].mean()) if np.any(correct == 0) else None,
        "expected_calibration_error_10_bins": expected_calibration_error(confidence, correct, bins=10),
    }

    per_rows: List[Dict[str, Any]] = []
    for idx, label in enumerate(CLASS_LABELS):
        class_mask = y_true == label
        class_conf = confidence[class_mask]
        class_correct = correct[class_mask]
        per_rows.append({
            "class": label,
            "support": int(per_support[idx]),
            "precision": float(per_p[idx]),
            "recall": float(per_r[idx]),
            "f1_score": float(per_f1[idx]),
            "mean_confidence": float(class_conf.mean()) if len(class_conf) else None,
            "class_accuracy": float(class_correct.mean()) if len(class_correct) else None,
        })

    cm = confusion_matrix(y_true, y_pred, labels=CLASS_LABELS)
    cm_norm = confusion_matrix(y_true, y_pred, labels=CLASS_LABELS, normalize="true")

    write_json(output_dir / f"{prefix}_summary_metrics.json", summary)
    write_csv(output_dir / f"{prefix}_summary_metrics.csv", [summary])
    write_csv(output_dir / f"{prefix}_per_class_metrics.csv", per_rows)
    pd.DataFrame(cm, index=CLASS_LABELS, columns=CLASS_LABELS).to_csv(
        output_dir / f"{prefix}_confusion_matrix_counts.csv"
    )
    pd.DataFrame(cm_norm, index=CLASS_LABELS, columns=CLASS_LABELS).to_csv(
        output_dir / f"{prefix}_confusion_matrix_normalized.csv"
    )

    # Count confusion matrix.
    fig, ax = plt.subplots(figsize=(7, 6))
    ConfusionMatrixDisplay(cm, display_labels=CLASS_LABELS).plot(
        ax=ax, values_format="d", colorbar=False
    )
    ax.set_title(f"Confusion matrix: {prefix}")
    fig.tight_layout()
    fig.savefig(output_dir / f"{prefix}_confusion_matrix_counts.png", dpi=300)
    plt.close(fig)

    # Normalized confusion matrix.
    fig, ax = plt.subplots(figsize=(7, 6))
    ConfusionMatrixDisplay(cm_norm, display_labels=CLASS_LABELS).plot(
        ax=ax, values_format=".2f", colorbar=False
    )
    ax.set_title(f"Normalized confusion matrix: {prefix}")
    fig.tight_layout()
    fig.savefig(output_dir / f"{prefix}_confusion_matrix_normalized.png", dpi=300)
    plt.close(fig)

    # Per-class metrics.
    metric_df = pd.DataFrame(per_rows).set_index("class")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    metric_df[["precision", "recall", "f1_score"]].plot(kind="bar", ax=ax)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_xlabel("True class")
    ax.set_title(f"Per-class classification metrics: {prefix}")
    ax.tick_params(axis="x", rotation=0)
    fig.tight_layout()
    fig.savefig(output_dir / f"{prefix}_per_class_metrics.png", dpi=300)
    plt.close(fig)

    # Confidence distribution.
    fig, ax = plt.subplots(figsize=(8, 5.5))
    bins = np.linspace(0, 1, 11)
    ax.hist(confidence[correct == 1], bins=bins, alpha=0.7, label="Correct")
    if np.any(correct == 0):
        ax.hist(confidence[correct == 0], bins=bins, alpha=0.7, label="Incorrect")
    ax.set_xlabel("Top-class probability (confidence)")
    ax.set_ylabel("Number of images")
    ax.set_title(f"Prediction confidence: {prefix}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / f"{prefix}_confidence_histogram.png", dpi=300)
    plt.close(fig)

    # Reliability diagram.
    edges = np.linspace(0, 1, 11)
    bin_conf, bin_acc, bin_count = [], [], []
    for lower, upper in zip(edges[:-1], edges[1:]):
        mask = (confidence >= lower) & (confidence < upper)
        if upper == 1.0:
            mask = (confidence >= lower) & (confidence <= upper)
        if np.any(mask):
            bin_conf.append(float(confidence[mask].mean()))
            bin_acc.append(float(correct[mask].mean()))
            bin_count.append(int(mask.sum()))
    write_csv(
        output_dir / f"{prefix}_calibration_bins.csv",
        [
            {"mean_confidence": c, "empirical_accuracy": a, "count": n_bin}
            for c, a, n_bin in zip(bin_conf, bin_acc, bin_count)
        ],
        fieldnames=["mean_confidence", "empirical_accuracy", "count"],
    )
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    ax.plot([0, 1], [0, 1], linestyle="--", label="Perfect calibration")
    if bin_conf:
        ax.plot(bin_conf, bin_acc, marker="o", label="Model")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Mean predicted confidence")
    ax.set_ylabel("Observed accuracy")
    ax.set_title(f"Reliability diagram: {prefix}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / f"{prefix}_reliability_diagram.png", dpi=300)
    plt.close(fig)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Experiment 1: independent CNN classification evaluation."
    )
    parser.add_argument("--project-dir", type=Path, default=default_project_dir())
    parser.add_argument("--test-dir", type=Path, default=None)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    args = parser.parse_args()

    project = args.project_dir.expanduser().resolve()
    test_dir = (args.test_dir or project / "test").expanduser().resolve()
    output_dir = (
        args.output_dir or project / "evaluation_outputs" / "experiment_1_classification"
    ).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    device = choose_device(args.device)
    manifest = load_manifest(args.manifest)
    items = discover_classification_images(test_dir)
    cnn_mod, model, paths = load_cnn(project, device)

    rows: List[Dict[str, Any]] = []
    print(f"Evaluating {len(items)} images on {device}...")

    # One warm-up pass reduces one-time framework overhead in timing values.
    first_path = items[0][0]
    _ = run_cnn_prediction(cnn_mod, model, first_path, device)
    synchronize(device)

    for index, (image_path, true_label) in enumerate(items, start=1):
        rel = relative_posix(image_path, test_dir)
        manifest_row = manifest.get(rel, {})
        include_primary = bool(manifest_row.get("include_in_primary", True))
        evaluation_subset = str(
            manifest_row.get("evaluation_subset", "external_unreviewed")
        )

        synchronize(device)
        start = time.perf_counter()
        prediction = run_cnn_prediction(cnn_mod, model, image_path, device)
        synchronize(device)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        probs = prediction["probabilities"]
        pred = str(prediction["predicted_class"]).lower()
        confidence = float(prediction["confidence"])
        meta = image_metadata(image_path)
        row = {
            "relative_path": rel,
            "filename": image_path.name,
            "true_label": true_label,
            "predicted_label": pred,
            "confidence": confidence,
            "confidence_percent": confidence * 100.0,
            "dots_probability": float(probs.get("dots", 0.0)),
            "irregular_probability": float(probs.get("irregular", 0.0)),
            "lines_probability": float(probs.get("lines", 0.0)),
            "mixed_probability": float(probs.get("mixed", 0.0)),
            "correct": pred == true_label,
            "inference_time_ms": elapsed_ms,
            "include_in_primary": include_primary,
            "evaluation_subset": evaluation_subset,
            "source_reference": manifest_row.get("source_reference", ""),
            "source_group_id": manifest_row.get("source_group_id", ""),
            "sample_id": manifest_row.get("sample_id", ""),
            "color_domain_review": manifest_row.get("color_domain_review", ""),
            "label_review_status": manifest_row.get("label_review_status", ""),
            "manifest_notes": manifest_row.get("notes", ""),
            "width": meta["width"],
            "height": meta["height"],
            "image_mode": meta["image_mode"],
            "image_sha256": meta["sha256"],
        }
        rows.append(row)
        print(
            f"[{index:03d}/{len(items):03d}] {rel}: true={true_label}, "
            f"pred={pred}, confidence={confidence:.4f}"
        )

    df = pd.DataFrame(rows)
    df.to_csv(output_dir / "cnn_predictions_all.csv", index=False)
    primary_df = df[df["include_in_primary"] == True].copy()  # noqa: E712
    primary_df.to_csv(output_dir / "cnn_predictions_primary.csv", index=False)
    errors = df[df["correct"] == False].sort_values(  # noqa: E712
        "confidence", ascending=False
    )
    errors.to_csv(output_dir / "classification_errors_all.csv", index=False)

    class_counts = (
        df.groupby(["true_label", "include_in_primary"], dropna=False)
        .size()
        .reset_index(name="images")
    )
    class_counts.to_csv(output_dir / "dataset_class_counts.csv", index=False)

    all_summary = compute_metrics(df, output_dir, "all_external")
    primary_summary = None
    if len(primary_df):
        primary_summary = compute_metrics(primary_df, output_dir, "primary")

    # Optional subset-specific summaries, useful for same-domain vs cross-color analysis.
    subset_summaries = []
    for subset_name, subset_df in df.groupby("evaluation_subset"):
        if len(subset_df) < 2:
            continue
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(subset_name))
        summary = compute_metrics(subset_df, output_dir / "subsets", f"subset_{safe}")
        subset_summaries.append(summary)
    if subset_summaries:
        write_csv(output_dir / "subset_summary_metrics.csv", subset_summaries)

    metadata = runtime_metadata(device)
    metadata.update({
        "project_dir": str(project),
        "test_dir": str(test_dir),
        "manifest": str(args.manifest.resolve()) if args.manifest else None,
        "cnn_model": str(paths.cnn_weights),
        "cnn_model_sha256": sha256_file(paths.cnn_weights),
        "cnn_script": str(paths.cnn_script),
        "cnn_script_sha256": sha256_file(paths.cnn_script),
        "class_order": CLASS_LABELS,
        "preprocessing": "RGB -> resize 217x217 -> ToTensor; no normalization",
        "all_external_summary": all_summary,
        "primary_summary": primary_summary,
    })
    write_json(output_dir / "run_metadata.json", metadata)

    print(f"\nExperiment 1 complete: {output_dir}")
    print(f"All images: {len(df)}")
    print(f"Primary images: {len(primary_df)}")
    print(f"Primary accuracy: {primary_summary['accuracy']:.4f}" if primary_summary else "")


if __name__ == "__main__":
    main()
