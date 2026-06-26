#!/usr/bin/env python3
"""Static integrity checks for the reviewer repository."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MODELS = {
    "models/cnn_rgb_classifier.pth": (
        194_579_557,
        "dd309d7d0d6706f34b762b396b4142e2586f4859d27f5cb409b9093156bba256",
    ),
    "models/best_quality_unet.pt": (
        57_507_115,
        "18ecdf3b3c35408a467d0e7baab781dbdb88572a87c907c14f4ad01884b1be41",
    ),
}
REQUIRED = [
    "README.md",
    "LICENSE",
    "CITATION.cff",
    ".gitignore",
    ".gitattributes",
    "requirements.txt",
    "environment/requirements-lock.txt",
    "backend/app.py",
    "backend/1.cnn_inference 1.py",
    "backend/2.segmentation.py",
    "backend/2.voronoi.py",
    "backend/3.colorwheel.py",
    "backend/3.colorwheel_before_fix.py",
    "backend/evaluate_cnn.py",
    "frontend/package.json",
    "frontend/package-lock.json",
    "training/train_cnn_reconstructed.py",
    "training/train_unet_reconstructed.py",
    "training/CHECKPOINT_PROVENANCE.md",
    "training/checkpoint_provenance.json",
    "masks/manifest.csv",
    "results/Experiment_1_Final_Publication/Experiment_1_Publication_Tables.xlsx",
    "results/Experiment_2_Final_Publication/Experiment_2_Publication_Tables.xlsx",
    "results/Experiment_3_Final_Publication/Experiment_3_Publication_Tables.xlsx",
    "results/Experiment_4_Final_Publication/Experiment_4_Publication_Tables.xlsx",
    "experiments/experiment_4/raw_results/experiment_4_end_to_end_results_redacted.zip",
]
DISALLOWED_NAMES = {
    ".next",
    "node_modules",
    "__pycache__",
    ".ipynb_checkpoints",
    "tempCodeRunnerFile.py",
    "PACKAGE_MANIFEST.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)
    print(f"FAIL: {message}")


def main() -> int:
    failures: list[str] = []

    for relative in REQUIRED:
        if not (ROOT / relative).exists():
            fail(f"Missing required path: {relative}", failures)

    for path in ROOT.rglob("*"):
        if path.name in DISALLOWED_NAMES:
            fail(f"Disallowed generated/stale path: {path.relative_to(ROOT)}", failures)

    for relative, (expected_size, expected_hash) in EXPECTED_MODELS.items():
        path = ROOT / relative
        if not path.exists():
            continue
        head = path.read_bytes()[:200]
        if b"version https://git-lfs.github.com/spec/v1" in head:
            fail(f"Unresolved Git LFS pointer: {relative}", failures)
            continue
        if path.stat().st_size != expected_size:
            fail(
                f"Unexpected size for {relative}: {path.stat().st_size} != {expected_size}",
                failures,
            )
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            fail(f"SHA-256 mismatch for {relative}: {actual_hash}", failures)

    manifest_path = ROOT / "masks" / "manifest.csv"
    if manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != 50:
            fail(f"Mask manifest has {len(rows)} rows; expected 50", failures)
        raw_image_hashes = {row["image_sha256"] for row in rows}
        for row in rows:
            label = row["class_label"]
            gt = ROOT / "masks" / "ground_truth" / label / Path(row["ground_truth_mask_path"]).name
            pred = ROOT / "masks" / "predicted" / label / Path(row["predicted_mask_path"]).name
            for path, expected in [
                (gt, row["ground_truth_mask_sha256"]),
                (pred, row["predicted_mask_sha256"]),
            ]:
                if not path.exists():
                    fail(f"Missing mask: {path.relative_to(ROOT)}", failures)
                elif sha256(path) != expected:
                    fail(f"Mask hash mismatch: {path.relative_to(ROOT)}", failures)

        gt_count = sum(1 for p in (ROOT / "masks" / "ground_truth").rglob("*") if p.is_file())
        pred_count = sum(1 for p in (ROOT / "masks" / "predicted").rglob("*") if p.is_file())
        if gt_count != 50:
            fail(f"Ground-truth mask count is {gt_count}; expected 50", failures)
        if pred_count != 50:
            fail(f"Predicted mask count is {pred_count}; expected 50", failures)

        # Detect exact copies of any raw validation image anywhere in the repository.
        image_extensions = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
        exact_raw_matches: list[str] = []
        for path in ROOT.rglob("*"):
            if path.is_file() and path.suffix.lower() in image_extensions:
                # Manual/predicted masks and publication figures are allowed, but none
                # should have the exact raw-image checksum.
                if sha256(path) in raw_image_hashes:
                    exact_raw_matches.append(path.relative_to(ROOT).as_posix())
        if exact_raw_matches:
            fail(
                "Exact raw AFM image files found: " + ", ".join(exact_raw_matches),
                failures,
            )

    redacted_zip = ROOT / "experiments" / "experiment_4" / "raw_results" / "experiment_4_end_to_end_results_redacted.zip"
    if redacted_zip.exists():
        with zipfile.ZipFile(redacted_zip) as archive:
            forbidden = [
                name
                for name in archive.namelist()
                if "/case_" in f"/{name}" and Path(name).name.startswith("original.")
            ]
            if forbidden:
                fail("Raw Experiment 4 case images remain in redacted ZIP", failures)
            if not any(name.endswith("REDACTION_RECORD.txt") for name in archive.namelist()):
                fail("Redacted Experiment 4 ZIP lacks REDACTION_RECORD.txt", failures)

    # The exact historical training source was lost. Require transparent,
    # architecture-compatible reference trainers plus an explicit provenance record.
    training_dir = ROOT / "training"
    cnn_trainer = training_dir / "train_cnn_reconstructed.py"
    unet_trainer = training_dir / "train_unet_reconstructed.py"
    provenance_json = training_dir / "checkpoint_provenance.json"
    disclosure = training_dir / "CHECKPOINT_PROVENANCE.md"
    for required_training_path in [cnn_trainer, unet_trainer, provenance_json, disclosure]:
        if not required_training_path.exists():
            fail(
                f"Missing reconstructed training/provenance file: {required_training_path.relative_to(ROOT)}",
                failures,
            )

    if provenance_json.exists():
        try:
            provenance = json.loads(provenance_json.read_text(encoding="utf-8"))
            if "exact historical scripts unavailable" not in provenance.get(
                "repository_training_status", ""
            ):
                fail("Training provenance does not disclose the missing historical source", failures)
            cnn_hash = provenance.get("cnn", {}).get("sha256")
            unet_hash = provenance.get("unet", {}).get("sha256")
            if cnn_hash != EXPECTED_MODELS["models/cnn_rgb_classifier.pth"][1]:
                fail("CNN hash mismatch in training provenance record", failures)
            if unet_hash != EXPECTED_MODELS["models/best_quality_unet.pt"][1]:
                fail("U-Net hash mismatch in training provenance record", failures)
        except Exception as exc:
            fail(f"Could not validate training provenance JSON: {exc}", failures)

    for trainer in [cnn_trainer, unet_trainer]:
        if trainer.exists():
            source = trainer.read_text(encoding="utf-8")
            if "not_historical_original" not in source:
                fail(
                    f"Trainer lacks explicit reconstructed-source disclosure: {trainer.relative_to(ROOT)}",
                    failures,
                )

    # Compile Python source text without generating __pycache__ directories.
    for path in ROOT.rglob("*.py"):
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")
        except Exception as exc:
            fail(f"Python compile failure in {path.relative_to(ROOT)}: {exc}", failures)

    if failures:
        print(f"\nRepository verification failed with {len(failures)} issue(s).")
        return 1

    print("Repository verification passed.")
    print("- required files present")
    print("- model hashes verified")
    print("- 50 ground-truth and 50 predicted masks verified")
    print("- no exact raw validation image files detected")
    print("- Experiment 4 redacted archive verified")
    print("- reconstructed training contracts and provenance verified")
    print("- Python sources compile")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
