# Training

The exact historical training scripts were lost. This directory contains transparent **reconstructed reference trainers**, not falsely relabeled originals.

## Files

- `train_cnn_reconstructed.py` — reproduces the published CNN architecture, class order, 217 × 217 RGB input contract, no-normalization inference preprocessing, and plain-state-dictionary checkpoint format.
- `train_unet_reconstructed.py` — reproduces the published Balanced U-Net architecture and checkpoint schema and uses all hyperparameters preserved inside the submitted checkpoint.
- `CHECKPOINT_PROVENANCE.md` — precise boundary between recovered facts and unknown historical details.
- `checkpoint_provenance.json` — machine-readable provenance and serialized U-Net metadata.

## Verify the submitted weights

From the repository root:

```bash
python training/train_cnn_reconstructed.py \
  --verify-checkpoint models/cnn_rgb_classifier.pth \
  --device cpu

python training/train_unet_reconstructed.py \
  --verify-checkpoint models/best_quality_unet.pt \
  --device cpu
```

## Reference CNN training

Expected authorized dataset layout:

```text
DATASET_ROOT/
├── dots/
├── irregular/
├── lines/
└── mixed/
```

Run:

```bash
python training/train_cnn_reconstructed.py \
  --dataset-dir /path/to/authorized/classification_dataset \
  --output models/cnn_rgb_classifier_retrained.pth
```

The script defaults to no augmentation because the original augmentation procedure is unknown. `--augmentation basic` enables paired orientation-preserving reference transforms.

## Reference U-Net training

Expected authorized dataset layout:

```text
DATASET_ROOT/
├── images/
└── masks/
```

Class subdirectories are allowed. A mask may match the image stem directly or use the suffix `_mask`.

Run:

```bash
python training/train_unet_reconstructed.py \
  --dataset-dir /path/to/authorized/segmentation_dataset \
  --output models/best_quality_unet_retrained.pt
```

The reconstructed U-Net defaults use every hyperparameter preserved in the submitted checkpoint. The exact historical Albumentations transforms and `CombinedLoss` source were unavailable; the implemented geometric augmentation and weighted BCE-plus-Dice formula are explicitly documented in the source and output metadata.

## Important limitation

These scripts support compatible retraining and transparent inspection. They should not be described as the exact programs that generated the submitted weights. The preserved weights, inference code, evaluation code, masks, and raw output files remain sufficient to reproduce the reported validation results without retraining.
