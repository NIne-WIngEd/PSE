# Final verification report

Verification date: 2026-06-26

## Tested environment

- Operating system: Linux reviewer-build environment
- Python: 3.13.5
- Node.js: 22.16.0
- npm: 10.9.2
- PyTorch: 2.10.0+cpu
- torchvision: 0.25.0+cpu

Exact Python package versions are listed in `environment/requirements-lock.txt`. The frontend dependency graph is locked by `frontend/package-lock.json`.

## Repository integrity

Command:

```bash
python scripts/verify_repository.py
```

Result: passed.

Verified items:

- required source, documentation, result, and model files are present;
- CNN and U-Net file sizes and SHA-256 hashes match the submitted checkpoints;
- 50 manual ground-truth masks and 50 predicted masks are present and hash-verified;
- no exact copy of any raw validation AFM image is present;
- the Experiment 4 redacted archive contains no raw case-study image file and includes a redaction record;
- reconstructed training entry points and provenance disclosures are present;
- all Python source files compile;
- stale build products and cache directories are absent.

## Backend smoke test

Command:

```bash
python scripts/smoke_test_backend.py
```

Result: passed.

The test generated a synthetic image outside the distributed dataset, loaded both submitted model checkpoints on CPU, exercised the Flask health endpoint, submitted the synthetic image to the upload endpoint, and confirmed that a class prediction and segmentation mask were returned.

## CNN evaluation entry point

`backend/evaluate_cnn.py` was executed successfully on a temporary synthetic four-class folder dataset. The numerical accuracy on synthetic patterns is not scientifically meaningful; this check verifies the corrected dictionary-based inference API, class-folder discovery, CSV output, and JSON summary generation.

## Training checkpoint contracts

Commands:

```bash
python training/train_cnn_reconstructed.py \
  --verify-checkpoint models/cnn_rgb_classifier.pth \
  --device cpu

python training/train_unet_reconstructed.py \
  --verify-checkpoint models/best_quality_unet.pt \
  --device cpu
```

Results: passed.

- CNN output shape: `(1, 4)` for a `(1, 3, 217, 217)` input.
- U-Net output shape: `(1, 1, 256, 256)` for a `(1, 1, 256, 256)` input.
- Both checkpoints loaded strictly against the production architecture definitions.

The exact historical training scripts were lost. The included trainers are transparent compatible reconstructions, not falsely labeled originals. See `training/CHECKPOINT_PROVENANCE.md`.

## Frontend

Commands:

```bash
cd frontend
npm ci
npm run lint
NEXT_TELEMETRY_DISABLED=1 npm run build
```

Results:

- dependency installation completed;
- npm audit reported 0 vulnerabilities;
- ESLint passed with 0 errors and 0 warnings;
- Next.js production build completed successfully;
- TypeScript validation completed successfully;
- all static routes were generated;
- the build did not require downloading Google fonts.

`node_modules/` and `.next/` were removed after verification and are intentionally excluded from the repository.

## Data-distribution boundary

The repository intentionally excludes original AFM training and validation images. It includes manual masks, predicted masks, derived figures, raw machine-readable experiment outputs, final model weights, and a redacted Experiment 4 output archive. Publication figures may contain selected AFM image panels because they are derived manuscript figures; standalone raw source images are not redistributed.

## Reproducibility scope

The reported predictions, segmentation metrics, bootstrap intervals, runtime analyses, ColorWheel comparison, and end-to-end case-study outputs are reproducible from the submitted final weights and preserved raw evaluation files. Bit-for-bit regeneration of the submitted weights from the unavailable historical training code is not claimed.
