from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import torch
from PIL import Image, ImageDraw

CLASS_LABELS: List[str] = ["dots", "irregular", "lines", "mixed"]
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


@dataclass
class ProjectPaths:
    project_dir: Path
    cnn_script: Path
    cnn_weights: Path
    unet_script: Path
    unet_weights: Path
    voronoi_script: Path
    colorwheel_script: Path


def resolve_project_paths(project_dir: str | Path) -> ProjectPaths:
    project = Path(project_dir).expanduser().resolve()
    return ProjectPaths(
        project_dir=project,
        cnn_script=project / "1.cnn_inference 1.py",
        cnn_weights=project / "cnn_rgb_classifier.pth",
        unet_script=project / "2.segmentation.py",
        unet_weights=project / "best_quality_unet.pt",
        voronoi_script=project / "2.voronoi.py",
        colorwheel_script=project / "3.colorwheel.py",
    )


def default_project_dir() -> Path:
    # Place this evaluation folder directly inside AFM_Web-main/.
    return Path(__file__).resolve().parents[1]


def import_module_from_path(name: str, path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing Python module: {path}")
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def is_git_lfs_pointer(path: str | Path) -> bool:
    p = Path(path)
    if not p.exists() or not p.is_file():
        return False
    try:
        head = p.read_bytes()[:200]
    except OSError:
        return False
    return head.startswith(b"version https://git-lfs.github.com/spec/v1")


def ensure_real_model_file(path: str | Path) -> None:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Model file not found: {p}")
    if is_git_lfs_pointer(p):
        text = p.read_text(encoding="utf-8", errors="replace")
        raise RuntimeError(
            f"{p.name} is only a Git LFS pointer, not the real model weights.\n"
            "From the repository root, run:\n"
            "  git lfs install\n"
            "  git lfs pull\n"
            "Then confirm the model file is tens or hundreds of MB, not ~130 bytes.\n\n"
            f"Pointer contents:\n{text}"
        )


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def choose_device(requested: str = "auto") -> torch.device:
    requested = requested.lower().strip()
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but torch.cuda.is_available() is False.")
    return torch.device(requested)


def _extract_state_dict(checkpoint: Any) -> Dict[str, torch.Tensor]:
    if isinstance(checkpoint, dict):
        for key in ("model_state_dict", "state_dict", "model"):
            value = checkpoint.get(key)
            if isinstance(value, dict):
                checkpoint = value
                break
    if not isinstance(checkpoint, dict):
        raise TypeError("CNN checkpoint does not contain a state dictionary.")

    cleaned: Dict[str, torch.Tensor] = {}
    for key, value in checkpoint.items():
        if not torch.is_tensor(value):
            continue
        clean_key = key[7:] if key.startswith("module.") else key
        cleaned[clean_key] = value
    if not cleaned:
        raise ValueError("No tensor weights were found in the CNN checkpoint.")
    return cleaned


def load_cnn(project_dir: str | Path, device: torch.device):
    paths = resolve_project_paths(project_dir)
    ensure_real_model_file(paths.cnn_weights)
    cnn_mod = import_module_from_path("cnn_evaluation_backend", paths.cnn_script)

    model = cnn_mod.DeeperCNN(num_classes=4, in_channels=3)
    # weights_only=False is needed for some older PyTorch checkpoints.
    checkpoint = torch.load(
        str(paths.cnn_weights), map_location=device, weights_only=False
    )
    state_dict = _extract_state_dict(checkpoint)
    model.load_state_dict(state_dict, strict=True)
    model.to(device)
    model.eval()
    return cnn_mod, model, paths


def load_unet(project_dir: str | Path, device: torch.device):
    paths = resolve_project_paths(project_dir)
    ensure_real_model_file(paths.unet_weights)
    unet_mod = import_module_from_path("unet_evaluation_backend", paths.unet_script)
    model, img_size, resolved_device = unet_mod.load_model(
        str(paths.unet_weights), device=str(device)
    )
    return unet_mod, model, int(img_size), torch.device(resolved_device), paths


def run_cnn_prediction(
    cnn_mod,
    model,
    image_path: str | Path,
    device: torch.device,
) -> Dict[str, Any]:
    return cnn_mod.predict_image(
        model,
        image_path=str(image_path),
        class_labels=CLASS_LABELS,
        image_size=217,
        in_channels=3,
        device=device,
    )


def discover_classification_images(test_dir: str | Path) -> List[Tuple[Path, str]]:
    test_root = Path(test_dir).expanduser().resolve()
    if not test_root.exists():
        raise FileNotFoundError(f"Test directory not found: {test_root}")

    items: List[Tuple[Path, str]] = []
    folder_map = {p.name.lower(): p for p in test_root.iterdir() if p.is_dir()}
    missing = [label for label in CLASS_LABELS if label not in folder_map]
    if missing:
        raise ValueError(
            f"Missing class folders in {test_root}: {', '.join(missing)}. "
            f"Expected exactly: {', '.join(CLASS_LABELS)}"
        )

    for label in CLASS_LABELS:
        folder = folder_map[label]
        for path in sorted(folder.rglob("*"), key=lambda p: p.as_posix().lower()):
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                items.append((path, label))
    if not items:
        raise ValueError(f"No images found under {test_root}")
    return items


def parse_bool(value: Any, default: bool = True) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "include"}


def load_manifest(manifest_path: Optional[str | Path]) -> Dict[str, Dict[str, Any]]:
    if not manifest_path:
        return {}
    p = Path(manifest_path)
    if not p.exists():
        raise FileNotFoundError(f"Manifest not found: {p}")
    rows: Dict[str, Dict[str, Any]] = {}
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"relative_path"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Manifest is missing columns: {sorted(missing)}")
        for row in reader:
            rel = str(row.get("relative_path", "")).replace("\\", "/").strip()
            if not rel:
                continue
            row["include_in_primary"] = parse_bool(
                row.get("include_in_primary"), default=True
            )
            rows[rel] = row
    return rows


def relative_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def write_csv(path: str | Path, rows: Sequence[Dict[str, Any]], fieldnames=None) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        if not rows:
            raise ValueError(f"Cannot infer CSV columns for empty rows: {p}")
        fieldnames = list(rows[0].keys())
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def runtime_metadata(device: torch.device) -> Dict[str, Any]:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "device": str(device),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_name": (
            torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
        ),
    }


def synchronize(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def image_metadata(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    with Image.open(p) as im:
        rgb = np.asarray(im.convert("RGB"), dtype=np.float32)
        mean_rgb = rgb.mean(axis=(0, 1))
        channel_spread = float(np.std(rgb, axis=2).mean())
        return {
            "width": int(im.width),
            "height": int(im.height),
            "image_mode": im.mode,
            "mean_red": float(mean_rgb[0]),
            "mean_green": float(mean_rgb[1]),
            "mean_blue": float(mean_rgb[2]),
            "mean_channel_spread": channel_spread,
            "file_size_bytes": int(p.stat().st_size),
            "sha256": sha256_file(p),
        }


def make_contact_sheet(
    items: Sequence[Tuple[Path, str]],
    output_path: str | Path,
    thumb_size: int = 180,
    columns: int = 5,
) -> None:
    if not items:
        raise ValueError("No items supplied for contact sheet.")
    label_height = 34
    rows = int(np.ceil(len(items) / columns))
    sheet = Image.new(
        "RGB",
        (columns * thumb_size, rows * (thumb_size + label_height)),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    for idx, (path, label) in enumerate(items):
        with Image.open(path) as opened:
            im = opened.convert("RGB")
        im.thumbnail((thumb_size, thumb_size))
        tile = Image.new("RGB", (thumb_size, thumb_size), "white")
        tile.paste(im, ((thumb_size - im.width) // 2, (thumb_size - im.height) // 2))
        x = (idx % columns) * thumb_size
        y = (idx // columns) * (thumb_size + label_height)
        sheet.paste(tile, (x, y))
        text = f"{label}/{path.name}"
        draw.text((x + 4, y + thumb_size + 4), text[:42], fill="black")
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
