# Checkpoint provenance and training-source status

The exact historical CNN and U-Net training programs were lost before this reviewer repository was assembled. This repository does **not** label reconstructed code as the original source.

## What is fully preserved

- Final production model architectures.
- Final trained weights and SHA-256 hashes.
- Final inference preprocessing and class ordering.
- All U-Net training metadata serialized inside `best_quality_unet.pt`.
- Evaluation scripts, raw result tables, masks, and publication outputs.
- Compatible reference trainers that create checkpoints consumable by the production inference code.

## CNN recovery boundary

`cnn_rgb_classifier.pth` is a plain PyTorch `state_dict`. The layer names and tensor shapes recover the complete `DeeperCNN` architecture. The production inference code also establishes RGB input, 217 × 217 resizing, `ToTensor`, and the class order `dots`, `irregular`, `lines`, `mixed`.

The checkpoint does not preserve the historical data split, augmentation, optimizer, learning rate, batch size, epoch count, or checkpoint-selection rule. `train_cnn_reconstructed.py` therefore uses transparent reference defaults and writes a sidecar training record. It saves a plain state dictionary so the resulting file is compatible with the production loader.

## U-Net recovery boundary

`best_quality_unet.pt` preserves the following information:

- `BalancedUNet`, one input channel, one output channel;
- input size 256;
- base channels 48;
- two convolutions per block;
- kernel size 3;
- batch size 8;
- AdamW, learning rate 5 × 10⁻⁵, weight decay 0.001;
- planned 100 epochs;
- `CombinedLoss`, alpha 0.2 and beta 0.8;
- grayscale input, divide-by-255 normalization, OpenCV linear resizing;
- Albumentations was used;
- checkpoint selected at epoch 33 with validation loss 0.2859746298.

The exact Albumentations recipe, split seed, and Python implementation of `CombinedLoss` were not serialized. `train_unet_reconstructed.py` uses a common inferred form, `0.2 × BCEWithLogitsLoss + 0.8 × DiceLoss`, and labels that formula as inferred in both code and output metadata.

## Reviewer interpretation

The included scripts make future training on an authorized external dataset executable and architecture-compatible. They do not prove bit-for-bit regeneration of the submitted weights. Inference, evaluation, reported metrics, mask audits, and end-to-end outputs are reproducible from the preserved final weights and raw results.
