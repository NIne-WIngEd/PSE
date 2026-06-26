#!/usr/bin/env python3
"""Reconstructed reference trainer for the four-class AFM CNN.

This program reproduces the *architecture*, class ordering, input shape,
preprocessing contract, and checkpoint format required by
``models/cnn_rgb_classifier.pth``. The historical training notebook was lost,
so optimizer/split/augmentation defaults in this file are documented reference
choices, not a claim about the exact procedure used for the published weights.

Expected dataset layout::

    DATASET_ROOT/
      dots/
      irregular/
      lines/
      mixed/

Original AFM images are intentionally not distributed with the repository.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import random
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

ROOT = Path(__file__).resolve().parents[1]
BACKEND_CNN = ROOT / "backend" / "1.cnn_inference 1.py"
CLASS_NAMES = ("dots", "irregular", "lines", "mixed")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


@dataclass(frozen=True)
class Sample:
    path: Path
    label: int


def load_cnn_class():
    spec = importlib.util.spec_from_file_location("afm_cnn_inference", BACKEND_CNN)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import CNN definition from {BACKEND_CNN}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DeeperCNN


def seed_everything(seed: int, deterministic: bool = True) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_samples(dataset_dir: Path) -> list[Sample]:
    samples: list[Sample] = []
    for label, class_name in enumerate(CLASS_NAMES):
        class_dir = dataset_dir / class_name
        if not class_dir.exists():
            raise FileNotFoundError(
                f"Missing class directory: {class_dir}. "
                f"Required classes are: {', '.join(CLASS_NAMES)}"
            )
        class_files = sorted(
            path
            for path in class_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        )
        if len(class_files) < 2:
            raise ValueError(
                f"Class '{class_name}' contains {len(class_files)} image(s); "
                "at least two are required for a train/validation split."
            )
        samples.extend(Sample(path=path, label=label) for path in class_files)
    return samples


def stratified_split(
    samples: Sequence[Sample], validation_fraction: float, seed: int
) -> tuple[list[Sample], list[Sample]]:
    if not 0.0 < validation_fraction < 1.0:
        raise ValueError("validation_fraction must be between 0 and 1")

    by_label: dict[int, list[Sample]] = defaultdict(list)
    for sample in samples:
        by_label[sample.label].append(sample)

    rng = random.Random(seed)
    train: list[Sample] = []
    validation: list[Sample] = []
    for label in range(len(CLASS_NAMES)):
        group = list(by_label[label])
        rng.shuffle(group)
        n_validation = max(1, int(round(len(group) * validation_fraction)))
        n_validation = min(n_validation, len(group) - 1)
        validation.extend(group[:n_validation])
        train.extend(group[n_validation:])

    rng.shuffle(train)
    rng.shuffle(validation)
    return train, validation


def build_transform(image_size: int, augmentation: str):
    operations: list[object] = [transforms.Resize((image_size, image_size))]
    if augmentation == "basic":
        operations.extend(
            [
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomVerticalFlip(p=0.5),
                transforms.RandomRotation(degrees=15),
            ]
        )
    operations.append(transforms.ToTensor())
    return transforms.Compose(operations)


class AFMClassificationDataset(Dataset):
    def __init__(self, samples: Sequence[Sample], image_size: int, augmentation: str):
        self.samples = list(samples)
        self.transform = build_transform(image_size, augmentation)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int):
        sample = self.samples[index]
        with Image.open(sample.path) as opened:
            image = opened.convert("RGB")
        return self.transform(image), sample.label


def evaluate(model: nn.Module, loader: DataLoader, criterion, device: torch.device):
    model.eval()
    total_loss = 0.0
    total_correct = 0
    total_examples = 0
    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)
            logits = model(images)
            loss = criterion(logits, labels)
            batch_size = labels.shape[0]
            total_loss += float(loss.item()) * batch_size
            total_correct += int((logits.argmax(dim=1) == labels).sum().item())
            total_examples += batch_size
    return total_loss / total_examples, total_correct / total_examples


def verify_checkpoint(checkpoint_path: Path, device: torch.device) -> None:
    DeeperCNN = load_cnn_class()
    model = DeeperCNN(num_classes=4, in_channels=3)
    state = torch.load(checkpoint_path, map_location=device, weights_only=True)
    if not isinstance(state, dict):
        raise TypeError("Expected a plain state_dict checkpoint")
    model.load_state_dict(state, strict=True)
    model.to(device).eval()
    with torch.no_grad():
        output = model(torch.zeros(1, 3, 217, 217, device=device))
    if tuple(output.shape) != (1, 4):
        raise RuntimeError(f"Unexpected output shape: {tuple(output.shape)}")
    print("CNN checkpoint verification passed")
    print(f"path: {checkpoint_path}")
    print(f"sha256: {sha256(checkpoint_path)}")
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

    samples = collect_samples(args.dataset_dir)
    train_samples, validation_samples = stratified_split(
        samples, args.validation_fraction, args.seed
    )
    train_dataset = AFMClassificationDataset(
        train_samples, args.image_size, args.augmentation
    )
    validation_dataset = AFMClassificationDataset(
        validation_samples, args.image_size, "none"
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

    DeeperCNN = load_cnn_class()
    model = DeeperCNN(num_classes=4, in_channels=3).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    best_validation_loss = float("inf")
    best_epoch = 0
    stale_epochs = 0
    history: list[dict[str, float | int]] = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        seen = 0
        epoch_start = time.perf_counter()
        for images, labels in train_loader:
            images = images.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            batch_size = labels.shape[0]
            running_loss += float(loss.item()) * batch_size
            correct += int((logits.argmax(dim=1) == labels).sum().item())
            seen += batch_size

        train_loss = running_loss / seen
        train_accuracy = correct / seen
        validation_loss, validation_accuracy = evaluate(
            model, validation_loader, criterion, device
        )
        elapsed = time.perf_counter() - epoch_start
        history.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "train_accuracy": train_accuracy,
                "validation_loss": validation_loss,
                "validation_accuracy": validation_accuracy,
                "elapsed_seconds": elapsed,
            }
        )
        print(
            f"epoch {epoch:03d}/{args.epochs:03d} "
            f"train_loss={train_loss:.6f} train_acc={train_accuracy:.4f} "
            f"val_loss={validation_loss:.6f} val_acc={validation_accuracy:.4f} "
            f"time={elapsed:.1f}s"
        )

        if validation_loss < best_validation_loss:
            best_validation_loss = validation_loss
            best_epoch = epoch
            stale_epochs = 0
            # Historical checkpoint is a plain state_dict, so preserve that format.
            torch.save(model.state_dict(), args.output)
        else:
            stale_epochs += 1
            if args.patience > 0 and stale_epochs >= args.patience:
                print(f"early stopping after {epoch} epochs")
                break

    metadata = {
        "provenance": "reconstructed_reference_trainer_not_historical_original",
        "architecture_source": str(BACKEND_CNN.relative_to(ROOT)),
        "class_names": list(CLASS_NAMES),
        "image_size": args.image_size,
        "input_channels": 3,
        "preprocessing": "RGB -> resize -> ToTensor; no normalization",
        "dataset_dir": str(args.dataset_dir.resolve()),
        "dataset_count": len(samples),
        "train_count": len(train_samples),
        "validation_count": len(validation_samples),
        "validation_fraction": args.validation_fraction,
        "seed": args.seed,
        "augmentation": args.augmentation,
        "optimizer": "AdamW",
        "learning_rate": args.learning_rate,
        "weight_decay": args.weight_decay,
        "loss": "CrossEntropyLoss",
        "batch_size": args.batch_size,
        "epochs_requested": args.epochs,
        "best_epoch": best_epoch,
        "best_validation_loss": best_validation_loss,
        "output_checkpoint": str(args.output),
        "output_sha256": sha256(args.output),
        "history": history,
        "important_note": (
            "The original training notebook was unavailable. Architecture, class order, "
            "input size, preprocessing, and plain-state_dict save format match the published "
            "model contract; split, augmentation, optimizer, and other defaults are reconstructed."
        ),
    }
    metadata_path = args.output.with_suffix(args.output.suffix + ".training.json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"saved best checkpoint: {args.output}")
    print(f"saved training record: {metadata_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        help="Directory containing dots/, irregular/, lines/, and mixed/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "models" / "cnn_rgb_classifier_retrained.pth",
    )
    parser.add_argument("--image-size", type=int, default=217)
    parser.add_argument("--validation-fraction", type=float, default=0.20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--patience", type=int, default=15)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--augmentation", choices=["none", "basic"], default="none")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--allow-nondeterministic", action="store_true")
    parser.add_argument(
        "--verify-checkpoint",
        type=Path,
        help="Verify architecture compatibility of an existing checkpoint and exit.",
    )
    args = parser.parse_args()
    if args.verify_checkpoint is None and args.dataset_dir is None:
        parser.error("--dataset-dir is required unless --verify-checkpoint is used")
    return args


def main() -> int:
    args = parse_args()
    if args.verify_checkpoint is not None:
        device = torch.device(
            "cuda"
            if args.device == "auto" and torch.cuda.is_available()
            else ("cpu" if args.device == "auto" else args.device)
        )
        verify_checkpoint(args.verify_checkpoint.resolve(), device)
        return 0
    args.dataset_dir = args.dataset_dir.expanduser().resolve()
    args.output = args.output.expanduser().resolve()
    train(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
