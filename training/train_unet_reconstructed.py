#!/usr/bin/env python3
"""Reconstructed reference trainer for the AFM Balanced U-Net.

The published checkpoint retains substantial training metadata, allowing the
architecture, input size, optimizer, learning rate, weight decay, planned epoch
count, and checkpoint schema to be recovered. The original script and exact
Albumentations recipe were lost. This program therefore provides a transparent,
compatible reference implementation rather than pretending to be the exact
historical source.

Expected dataset layout::

    DATASET_ROOT/
      images/       # may contain class subdirectories
      masks/        # matching relative paths; ``name_mask.png`` is accepted

Original AFM images are not distributed with the repository.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import random
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence

import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision.transforms import functional as TF
from torchvision.transforms.functional import InterpolationMode

ROOT = Path(__file__).resolve().parents[1]
BACKEND_UNET = ROOT / "backend" / "2.segmentation.py"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


@dataclass(frozen=True)
class Pair:
    image: Path
    mask: Path


def load_unet_class():
    spec = importlib.util.spec_from_file_location("afm_unet_inference", BACKEND_UNET)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import U-Net definition from {BACKEND_UNET}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.BalancedUNet


def sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def seed_everything(seed: int, deterministic: bool = True) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def find_mask(mask_root: Path, relative_image: Path) -> Path | None:
    parent = mask_root / relative_image.parent
    candidates: list[Path] = []
    for extension in IMAGE_EXTENSIONS:
        candidates.extend(
            [
                parent / f"{relative_image.stem}{extension}",
                parent / f"{relative_image.stem}_mask{extension}",
            ]
        )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def collect_pairs(images_dir: Path, masks_dir: Path) -> list[Pair]:
    image_paths = sorted(
        path
        for path in images_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not image_paths:
        raise ValueError(f"No images found in {images_dir}")
    pairs: list[Pair] = []
    missing: list[str] = []
    for image in image_paths:
        relative = image.relative_to(images_dir)
        mask = find_mask(masks_dir, relative)
        if mask is None:
            missing.append(relative.as_posix())
        else:
            pairs.append(Pair(image=image, mask=mask))
    if missing:
        preview = ", ".join(missing[:10])
        raise FileNotFoundError(
            f"Missing masks for {len(missing)} image(s), including: {preview}"
        )
    if len(pairs) < 2:
        raise ValueError("At least two image/mask pairs are required")
    return pairs


def split_pairs(
    pairs: Sequence[Pair], validation_fraction: float, seed: int
) -> tuple[list[Pair], list[Pair]]:
    if not 0.0 < validation_fraction < 1.0:
        raise ValueError("validation_fraction must be between 0 and 1")
    shuffled = list(pairs)
    random.Random(seed).shuffle(shuffled)
    n_validation = max(1, int(round(len(shuffled) * validation_fraction)))
    n_validation = min(n_validation, len(shuffled) - 1)
    return shuffled[n_validation:], shuffled[:n_validation]


class PairedSegmentationDataset(Dataset):
    def __init__(
        self,
        pairs: Sequence[Pair],
        image_size: int,
        augmentation: str,
        positive_pixels: str,
    ):
        self.pairs = list(pairs)
        self.image_size = image_size
        self.augmentation = augmentation
        self.positive_pixels = positive_pixels

    def __len__(self) -> int:
        return len(self.pairs)

    def __getitem__(self, index: int):
        pair = self.pairs[index]
        with Image.open(pair.image) as opened:
            image = opened.convert("L")
        with Image.open(pair.mask) as opened:
            mask = opened.convert("L")

        image = TF.resize(
            image,
            [self.image_size, self.image_size],
            interpolation=InterpolationMode.BILINEAR,
            antialias=True,
        )
        mask = TF.resize(
            mask,
            [self.image_size, self.image_size],
            interpolation=InterpolationMode.NEAREST,
        )

        if self.augmentation == "geometric":
            if random.random() < 0.5:
                image = TF.hflip(image)
                mask = TF.hflip(mask)
            if random.random() < 0.5:
                image = TF.vflip(image)
                mask = TF.vflip(mask)
            turns = random.randint(0, 3)
            if turns:
                angle = 90 * turns
                image = TF.rotate(image, angle, interpolation=InterpolationMode.BILINEAR)
                mask = TF.rotate(mask, angle, interpolation=InterpolationMode.NEAREST)

        image_tensor = TF.to_tensor(image)  # divide by 255, one grayscale channel
        mask_array = np.asarray(mask, dtype=np.uint8)
        if self.positive_pixels == "white":
            target = (mask_array >= 128).astype(np.float32)
        else:
            target = (mask_array < 128).astype(np.float32)
        target_tensor = torch.from_numpy(target).unsqueeze(0)
        return image_tensor, target_tensor


class DiceLoss(nn.Module):
    def __init__(self, smooth: float = 1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        probabilities = torch.sigmoid(logits)
        probabilities = probabilities.flatten(start_dim=1)
        target = target.flatten(start_dim=1)
        intersection = (probabilities * target).sum(dim=1)
        denominator = probabilities.sum(dim=1) + target.sum(dim=1)
        dice = (2.0 * intersection + self.smooth) / (denominator + self.smooth)
        return 1.0 - dice.mean()


class CombinedLoss(nn.Module):
    """Inferred reference form: alpha * BCE + beta * Dice loss.

    The checkpoint names the loss ``CombinedLoss`` with alpha=0.2 and beta=0.8
    but does not serialize the original Python implementation. This common form
    is therefore explicitly identified as an inference.
    """

    def __init__(self, alpha: float = 0.2, beta: float = 0.8):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.bce = nn.BCEWithLogitsLoss()
        self.dice = DiceLoss()

    def forward(self, logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        return self.alpha * self.bce(logits, target) + self.beta * self.dice(
            logits, target
        )


def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    optimizer: torch.optim.Optimizer | None,
) -> float:
    training = optimizer is not None
    model.train(training)
    total_loss = 0.0
    total_examples = 0
    context = torch.enable_grad() if training else torch.no_grad()
    with context:
        for images, targets in loader:
            images = images.to(device, non_blocking=True)
            targets = targets.to(device, non_blocking=True)
            if training:
                optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            loss = criterion(logits, targets)
            if training:
                loss.backward()
                optimizer.step()
            batch_size = images.shape[0]
            total_loss += float(loss.item()) * batch_size
            total_examples += batch_size
    return total_loss / total_examples


def verify_checkpoint(checkpoint_path: Path, device: torch.device) -> None:
    checkpoint = torch.load(
        checkpoint_path, map_location=device, weights_only=False
    )
    required = {
        "model_state_dict",
        "model_config",
        "optimizer_state",
        "epoch",
        "train_loss",
        "val_loss",
        "train_losses",
        "val_losses",
        "training_config",
        "preprocessing",
        "metadata",
    }
    missing = required.difference(checkpoint)
    if missing:
        raise KeyError(f"Checkpoint is missing keys: {sorted(missing)}")
    config = checkpoint["model_config"]
    BalancedUNet = load_unet_class()
    model = BalancedUNet(
        in_channels=config["in_channels"],
        num_classes=config["num_classes"],
        base_channels=config.get("base_channels", 48),
        num_convs_per_block=config.get("num_convs_per_block", 2),
        kernel_size=config.get("kernel_size", 3),
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.eval()
    image_size = int(config.get("img_size", 256))
    with torch.no_grad():
        output = model(torch.zeros(1, config["in_channels"], image_size, image_size, device=device))
    expected = (1, config["num_classes"], image_size, image_size)
    if tuple(output.shape) != expected:
        raise RuntimeError(f"Unexpected output shape {tuple(output.shape)} != {expected}")
    print("U-Net checkpoint verification passed")
    print(f"path: {checkpoint_path}")
    print(f"sha256: {sha256(checkpoint_path)}")
    print(f"model_config: {json.dumps(config, sort_keys=True)}")
    print(f"training_config: {json.dumps(checkpoint['training_config'], sort_keys=True)}")
    print(f"output shape: {tuple(output.shape)}")


def train(args: argparse.Namespace) -> None:
    seed_everything(args.seed, deterministic=not args.allow_nondeterministic)
    device = torch.device(
        "cuda"
        if args.device == "auto" and torch.cuda.is_available()
        else ("cpu" if args.device == "auto" else args.device)
    )
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")

    pairs = collect_pairs(args.images_dir, args.masks_dir)
    train_pairs, validation_pairs = split_pairs(
        pairs, args.validation_fraction, args.seed
    )
    train_dataset = PairedSegmentationDataset(
        train_pairs, args.image_size, args.augmentation, args.positive_pixels
    )
    validation_dataset = PairedSegmentationDataset(
        validation_pairs, args.image_size, "none", args.positive_pixels
    )
    generator = torch.Generator().manual_seed(args.seed)
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.workers,
        pin_memory=device.type == "cuda",
        generator=generator,
    )
    validation_loader = DataLoader(
        validation_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.workers,
        pin_memory=device.type == "cuda",
    )

    BalancedUNet = load_unet_class()
    model = BalancedUNet(
        in_channels=1,
        num_classes=1,
        base_channels=args.base_channels,
        num_convs_per_block=args.num_convs_per_block,
        kernel_size=args.kernel_size,
    ).to(device)
    criterion = CombinedLoss(alpha=args.loss_alpha, beta=args.loss_beta)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    best_validation_loss = float("inf")
    stale_epochs = 0
    train_losses: list[float] = []
    validation_losses: list[float] = []

    for epoch in range(1, args.epochs + 1):
        epoch_start = time.perf_counter()
        train_loss = run_epoch(model, train_loader, criterion, device, optimizer)
        validation_loss = run_epoch(
            model, validation_loader, criterion, device, optimizer=None
        )
        train_losses.append(train_loss)
        validation_losses.append(validation_loss)
        elapsed = time.perf_counter() - epoch_start
        print(
            f"epoch {epoch:03d}/{args.epochs:03d} "
            f"train_loss={train_loss:.6f} val_loss={validation_loss:.6f} "
            f"time={elapsed:.1f}s"
        )

        if validation_loss < best_validation_loss:
            best_validation_loss = validation_loss
            stale_epochs = 0
            checkpoint = {
                "model_state_dict": model.state_dict(),
                "model_config": {
                    "in_channels": 1,
                    "num_classes": 1,
                    "img_size": args.image_size,
                    "base_channels": args.base_channels,
                    "num_convs_per_block": args.num_convs_per_block,
                    "kernel_size": args.kernel_size,
                    "model_type": "BalancedUNet",
                },
                "optimizer_state": optimizer.state_dict(),
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": validation_loss,
                "train_losses": list(train_losses),
                "val_losses": list(validation_losses),
                "training_config": {
                    "batch_size": args.batch_size,
                    "learning_rate": args.learning_rate,
                    "epochs": args.epochs,
                    "img_size": args.image_size,
                    "optimizer": "AdamW",
                    "loss_function": "CombinedLoss",
                    "loss_alpha": args.loss_alpha,
                    "loss_beta": args.loss_beta,
                    "weight_decay": args.weight_decay,
                    "validation_fraction": args.validation_fraction,
                    "seed": args.seed,
                    "positive_pixels": args.positive_pixels,
                    "reconstruction_status": "reference_not_historical_original",
                },
                "preprocessing": {
                    "normalization": "divide_by_255",
                    "resize_method": "bilinear_for_images_nearest_for_masks",
                    "grayscale": True,
                    "augmentation": args.augmentation,
                    "clahe_applied": False,
                },
                "metadata": {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "device": str(device),
                    "pytorch_version": torch.__version__,
                    "cuda_available": torch.cuda.is_available(),
                    "python_version": platform.python_version(),
                    "provenance": "reconstructed_reference_trainer_not_historical_original",
                    "loss_formula_note": (
                        "CombinedLoss implementation is inferred as alpha*BCEWithLogits + beta*Dice."
                    ),
                },
            }
            torch.save(checkpoint, args.output)
        else:
            stale_epochs += 1
            if args.patience > 0 and stale_epochs >= args.patience:
                print(f"early stopping after {epoch} epochs")
                break

    record = {
        "provenance": "reconstructed_reference_trainer_not_historical_original",
        "architecture_source": str(BACKEND_UNET.relative_to(ROOT)),
        "dataset_images_dir": str(args.images_dir.resolve()),
        "dataset_masks_dir": str(args.masks_dir.resolve()),
        "pair_count": len(pairs),
        "train_count": len(train_pairs),
        "validation_count": len(validation_pairs),
        "output_checkpoint": str(args.output),
        "output_sha256": sha256(args.output),
        "important_note": (
            "The original source and exact Albumentations recipe were unavailable. "
            "Serialized checkpoint metadata was used wherever possible; remaining details "
            "are explicitly reconstructed reference choices."
        ),
    }
    record_path = args.output.with_suffix(args.output.suffix + ".training.json")
    record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"saved best checkpoint: {args.output}")
    print(f"saved training record: {record_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path)
    parser.add_argument("--images-dir", type=Path)
    parser.add_argument("--masks-dir", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "models" / "best_quality_unet_retrained.pt",
    )
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--base-channels", type=int, default=48)
    parser.add_argument("--num-convs-per-block", type=int, default=2)
    parser.add_argument("--kernel-size", type=int, default=3)
    parser.add_argument("--validation-fraction", type=float, default=0.20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--weight-decay", type=float, default=1e-3)
    parser.add_argument("--loss-alpha", type=float, default=0.2)
    parser.add_argument("--loss-beta", type=float, default=0.8)
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument(
        "--augmentation", choices=["none", "geometric"], default="geometric"
    )
    parser.add_argument(
        "--positive-pixels",
        choices=["white", "black"],
        default="white",
        help=(
            "Pixels mapped to target 1. The published inference contract writes sigmoid-positive "
            "pixels as white, so white is the compatibility default."
        ),
    )
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--allow-nondeterministic", action="store_true")
    parser.add_argument(
        "--verify-checkpoint",
        type=Path,
        help="Verify schema and architecture compatibility of a checkpoint and exit.",
    )
    args = parser.parse_args()
    if args.verify_checkpoint is None:
        if args.dataset_dir:
            args.images_dir = args.images_dir or args.dataset_dir / "images"
            args.masks_dir = args.masks_dir or args.dataset_dir / "masks"
        if args.images_dir is None or args.masks_dir is None:
            parser.error(
                "Provide --dataset-dir or both --images-dir and --masks-dir unless --verify-checkpoint is used"
            )
    return args


def main() -> int:
    args = parse_args()
    if args.verify_checkpoint is not None:
        device = torch.device(
            "cuda"
            if args.device == "auto" and torch.cuda.is_available()
            else ("cpu" if args.device == "auto" else args.device)
        )
        verify_checkpoint(args.verify_checkpoint.expanduser().resolve(), device)
        return 0
    args.images_dir = args.images_dir.expanduser().resolve()
    args.masks_dir = args.masks_dir.expanduser().resolve()
    args.output = args.output.expanduser().resolve()
    train(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
