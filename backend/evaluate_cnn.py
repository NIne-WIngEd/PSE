#!/usr/bin/env python3
"""Evaluate the final four-class CNN on a class-folder dataset.

Expected data layout::

    DATA_DIR/
      dots/
      irregular/
      lines/
      mixed/

The script uses the same 217 x 217 RGB preprocessing and class order as the
production backend. Original AFM images are intentionally not distributed in
this repository; provide an authorized local dataset with the layout above.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    matthews_corrcoef,
    precision_recall_fscore_support,
)

CLASS_LABELS = ["dots", "irregular", "lines", "mixed"]
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, help="Dataset with one subfolder per class.")
    parser.add_argument(
        "--model-path",
        default=str(repo_root / "models" / "cnn_rgb_classifier.pth"),
        help="Path to the final CNN state dictionary.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(repo_root / "runtime" / "cnn_evaluation"),
        help="Directory for predictions and summary files.",
    )
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    return parser.parse_args()


def import_inference_module(path: Path):
    spec = importlib.util.spec_from_file_location("cnn_inference", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import CNN inference module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but torch.cuda.is_available() is False.")
    return torch.device(requested)


def ensure_real_model(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    head = path.read_bytes()[:200]
    if b"version https://git-lfs.github.com/spec/v1" in head:
        raise RuntimeError(
            f"{path} is a Git LFS pointer. Run `git lfs install` and `git lfs pull`."
        )


def discover_images(data_dir: Path) -> list[tuple[Path, str]]:
    records: list[tuple[Path, str]] = []
    for label in CLASS_LABELS:
        folder = data_dir / label
        if not folder.is_dir():
            raise FileNotFoundError(f"Missing class folder: {folder}")
        for path in sorted(folder.rglob("*")):
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                records.append((path, label))
    if not records:
        raise ValueError(f"No supported images found under {data_dir}")
    return records


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("No rows to write.")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    backend_dir = Path(__file__).resolve().parent
    data_dir = Path(args.data_dir).expanduser().resolve()
    model_path = Path(args.model_path).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    ensure_real_model(model_path)
    device = choose_device(args.device)
    cnn = import_inference_module(backend_dir / "1.cnn_inference 1.py")
    model = cnn.load_model(str(model_path), in_channels=3, device=device)

    prediction_rows: list[dict[str, Any]] = []
    for image_path, true_label in discover_images(data_dir):
        start = time.perf_counter()
        result = cnn.predict_image(
            model,
            str(image_path),
            class_labels=CLASS_LABELS,
            image_size=217,
            in_channels=3,
            device=device,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        predicted = str(result["predicted_class"])
        probabilities = result.get("probabilities", {})
        prediction_rows.append(
            {
                "relative_path": image_path.relative_to(data_dir).as_posix(),
                "true_label": true_label,
                "predicted_label": predicted,
                "confidence": float(result["confidence"]),
                "prob_dots": float(probabilities.get("dots", 0.0)),
                "prob_irregular": float(probabilities.get("irregular", 0.0)),
                "prob_lines": float(probabilities.get("lines", 0.0)),
                "prob_mixed": float(probabilities.get("mixed", 0.0)),
                "correct": predicted == true_label,
                "prediction_time_ms": elapsed_ms,
            }
        )

    y_true = np.array([row["true_label"] for row in prediction_rows])
    y_pred = np.array([row["predicted_label"] for row in prediction_rows])
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=CLASS_LABELS,
        average=None,
        zero_division=0,
    )
    macro_f1 = precision_recall_fscore_support(
        y_true, y_pred, labels=CLASS_LABELS, average="macro", zero_division=0
    )[2]

    summary = {
        "n_images": int(len(prediction_rows)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(macro_f1),
        "matthews_correlation_coefficient": float(matthews_corrcoef(y_true, y_pred)),
        "class_order": CLASS_LABELS,
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=CLASS_LABELS).tolist(),
        "per_class": {
            label: {
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(f1[index]),
                "support": int(support[index]),
            }
            for index, label in enumerate(CLASS_LABELS)
        },
        "device": str(device),
        "model_path": str(model_path.relative_to(repo_root))
        if model_path.is_relative_to(repo_root)
        else str(model_path),
    }

    write_csv(output_dir / "cnn_predictions.csv", prediction_rows)
    (output_dir / "cnn_evaluation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print(json.dumps(summary, indent=2))
    print(f"Predictions: {output_dir / 'cnn_predictions.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
