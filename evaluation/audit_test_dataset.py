from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image

from common import (
    CLASS_LABELS,
    default_project_dir,
    discover_classification_images,
    image_metadata,
    make_contact_sheet,
    relative_posix,
    write_csv,
    write_json,
)


def average_hash(path: Path, size: int = 16) -> np.ndarray:
    with Image.open(path) as im:
        arr = np.asarray(im.convert("L").resize((size, size)), dtype=np.float32)
    return arr > arr.mean()


def hamming_distance(a: np.ndarray, b: np.ndarray) -> int:
    return int(np.count_nonzero(a != b))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit the AFM classification test folder before formal evaluation."
    )
    parser.add_argument(
        "--project-dir", type=Path, default=default_project_dir(),
        help="Path to AFM_Web-main."
    )
    parser.add_argument(
        "--test-dir", type=Path, default=None,
        help="Classification test folder. Defaults to <project-dir>/test."
    )
    parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="Audit output folder. Defaults to <project-dir>/evaluation_outputs/test_audit."
    )
    parser.add_argument(
        "--near-duplicate-distance", type=int, default=4,
        help="Maximum 16x16 average-hash Hamming distance to flag near duplicates."
    )
    args = parser.parse_args()

    project = args.project_dir.expanduser().resolve()
    test_dir = (args.test_dir or project / "test").expanduser().resolve()
    output_dir = (
        args.output_dir or project / "evaluation_outputs" / "test_audit"
    ).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    items = discover_classification_images(test_dir)
    refs_dir = project / "Cnn_classifier_test"

    reference_hashes: Dict[str, List[Path]] = {}
    if refs_dir.exists():
        for p in refs_dir.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
                digest = hashlib.sha256(p.read_bytes()).hexdigest()
                reference_hashes.setdefault(digest, []).append(p)

    inventory: List[dict] = []
    class_counts = {label: 0 for label in CLASS_LABELS}
    hashes: Dict[str, np.ndarray] = {}

    for path, label in items:
        rel = relative_posix(path, test_dir)
        class_counts[label] += 1
        meta = image_metadata(path)
        exact_refs = reference_hashes.get(meta["sha256"], [])
        flags: List[str] = []
        if exact_refs:
            flags.append("exact_duplicate_of_development_example")
        if min(meta["width"], meta["height"]) < 217:
            flags.append("smaller_than_cnn_input")
        aspect_ratio = max(meta["width"], meta["height"]) / max(1, min(meta["width"], meta["height"]))
        if aspect_ratio >= 1.25:
            flags.append("substantial_aspect_ratio_change_on_resize")

        inventory.append({
            "relative_path": rel,
            "true_label": label,
            **meta,
            "exact_reference_match": "; ".join(
                str(p.relative_to(project).as_posix()) for p in exact_refs
            ),
            "aspect_ratio_long_to_short": aspect_ratio,
            "automatic_flags": "; ".join(flags),
            "include_in_primary": "no" if exact_refs else "yes",
            "evaluation_subset": "development_example" if exact_refs else "external_unreviewed",
            "label_review_status": "pending",
            "color_domain_review": "pending",
            "source_reference": "",
            "source_group_id": "",
            "sample_id": "",
            "acquisition_mode": "",
            "scan_size_micrometers": "",
            "notes": "",
        })
        hashes[rel] = average_hash(path)

    duplicate_rows: List[dict] = []
    for i in range(len(inventory)):
        for j in range(i + 1, len(inventory)):
            a = inventory[i]
            b = inventory[j]
            if a["sha256"] == b["sha256"]:
                duplicate_rows.append({
                    "path_a": a["relative_path"],
                    "path_b": b["relative_path"],
                    "relationship": "exact_duplicate",
                    "hash_distance": 0,
                })
                continue
            dist = hamming_distance(
                hashes[a["relative_path"]], hashes[b["relative_path"]]
            )
            if dist <= args.near_duplicate_distance:
                duplicate_rows.append({
                    "path_a": a["relative_path"],
                    "path_b": b["relative_path"],
                    "relationship": "near_duplicate_candidate",
                    "hash_distance": dist,
                })

    count_rows = [
        {"class": label, "images": class_counts[label]} for label in CLASS_LABELS
    ]
    count_rows.append({"class": "total", "images": sum(class_counts.values())})

    write_csv(output_dir / "dataset_inventory_and_manifest.csv", inventory)
    write_csv(output_dir / "class_counts.csv", count_rows)
    write_csv(
        output_dir / "duplicate_candidates.csv",
        duplicate_rows,
        fieldnames=["path_a", "path_b", "relationship", "hash_distance"],
    )
    make_contact_sheet(items, output_dir / "test_contact_sheet.png")

    summary = {
        "test_dir": str(test_dir),
        "total_images": len(items),
        "class_counts": class_counts,
        "images_flagged_as_development_duplicates": sum(
            bool(row["exact_reference_match"]) for row in inventory
        ),
        "images_smaller_than_217_pixels": sum(
            "smaller_than_cnn_input" in row["automatic_flags"] for row in inventory
        ),
        "images_with_aspect_ratio_at_least_1_25": sum(
            "substantial_aspect_ratio_change_on_resize" in row["automatic_flags"]
            for row in inventory
        ),
        "duplicate_candidate_pairs": len(duplicate_rows),
        "important_note": (
            "Automatic checks cannot verify scientific labels or whether color palettes "
            "match the training domain. Review label_review_status and color_domain_review "
            "manually before freezing the formal test set."
        ),
    }
    write_json(output_dir / "audit_summary.json", summary)

    print(f"Audit complete: {output_dir}")
    print(f"Total images: {len(items)}")
    for label in CLASS_LABELS:
        print(f"  {label}: {class_counts[label]}")
    print(
        "Review dataset_inventory_and_manifest.csv, then copy it to "
        "evaluation/test_manifest.csv after finalizing include_in_primary and subset labels."
    )


if __name__ == "__main__":
    main()
