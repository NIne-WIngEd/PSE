# Reproducibility guide

## 1. Retrieve model weights

```bash
git lfs install
git lfs pull
```

Verify hashes against `models/README.md`.

## 2. Install Python dependencies

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

## 3. Run repository checks

```bash
python scripts/verify_repository.py
python scripts/smoke_test_backend.py
```

## 4. Run the application

Terminal 1:

```bash
python backend/app.py
```

Terminal 2:

```bash
cd frontend
npm ci
npm run lint
npm run build
npm run dev
```

## 5. Rerun experiments

Original AFM images are not in the repository. Place authorized images under `data/test/` or supply explicit image paths to the scripts under `experiments/`.

The saved raw outputs and publication packages allow verification of every reported value without rerunning the models.


## 6. Inspect the training contracts

The exact historical training source was unavailable. Verify that the submitted checkpoints are compatible with the reconstructed architecture contracts:

```bash
python training/train_cnn_reconstructed.py \
  --verify-checkpoint models/cnn_rgb_classifier.pth \
  --device cpu

python training/train_unet_reconstructed.py \
  --verify-checkpoint models/best_quality_unet.pt \
  --device cpu
```

For retraining with authorized source images, follow `training/README.md`. The reconstructed trainers are deliberately labeled as references; see `training/CHECKPOINT_PROVENANCE.md` for the precise recovery boundary.
