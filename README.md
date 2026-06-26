# AFM Morphology Analysis Platform

A reproducible software package for classifying, segmenting, and analyzing rendered atomic-force microscopy (AFM) images. The application combines a four-class CNN classifier, a binary U-Net segmenter, Voronoi analysis for dot-like structures, and ColorWheel orientation analysis for line-like structures.

## Publication status

This repository accompanies the AFM morphology software validation study. It contains the final application source, trained model weights, evaluation scripts, machine-readable results, publication tables and figures, and the complete externally verified manual and predicted mask sets used for segmentation validation.

The original AFM dataset images are **not redistributed** because the repository does not establish redistribution permission for every source image. Authorized users can supply their own images through the application or evaluation command-line interfaces.

## Pipeline

1. Load an AFM image.
2. Classify morphology as `dots`, `irregular`, `lines`, or `mixed`.
3. Generate a binary U-Net segmentation mask.
4. Route by the CNN prediction:
   - `dots` → Voronoi
   - `lines` → ColorWheel
   - `mixed` → Voronoi and ColorWheel
   - `irregular` → no morphology-specific downstream module
5. Return visual and numerical outputs through the Flask API and Next.js interface.

## Repository layout

```text
AFM_Morphology_Analysis_GitHub/
├── backend/                 Final Flask API and analysis modules
├── frontend/                Next.js user interface
├── models/                  Trained weights tracked with Git LFS
├── training/                Reconstructed compatible trainers and provenance notes
├── experiments/             Reproduction scripts and raw machine-readable results
│   ├── experiment_1/        CNN classification validation
│   ├── experiment_2/        U-Net segmentation validation
│   ├── experiment_3/        Runtime, batch, and ColorWheel validation
│   └── experiment_4/        End-to-end case studies
├── results/                 Final publication packages for Experiments 1–4
├── masks/                   50 manual ground-truth and 50 predicted masks
├── environment/             Tested pinned Python environment
├── scripts/                 Repository verification and backend smoke tests
├── docs/                    Data-availability and reproducibility notes
├── data/                    Dataset-access statement; no raw AFM images
└── runtime/                 Generated application outputs; ignored by Git
```

## Model weights and Git LFS

The two trained model files are large and are configured for Git LFS:

| File | Size | SHA-256 |
|---|---:|---|
| `models/cnn_rgb_classifier.pth` | 194,579,557 bytes | `dd309d7d0d6706f34b762b396b4142e2586f4859d27f5cb409b9093156bba256` |
| `models/best_quality_unet.pt` | 57,507,115 bytes | `18ecdf3b3c35408a467d0e7baab781dbdb88572a87c907c14f4ad01884b1be41` |

Clone and retrieve the weights with:

```bash
git lfs install
git clone <repository-url>
cd AFM_Morphology_Analysis_GitHub
git lfs pull
```

## Python environment

The tested environment is pinned in `environment/requirements-lock.txt`.

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The lock file records the tested CPU PyTorch stack. A platform-specific CUDA build may be installed separately when GPU execution is required.

## Run the backend

From the repository root:

```bash
python backend/app.py
```

Default endpoint:

```text
http://127.0.0.1:8050
```

Optional environment variables:

- `AFM_MODEL_DIR`: model directory; defaults to `models/`
- `AFM_RUNTIME_DIR`: generated-output directory; defaults to `runtime/`
- `AFM_DEVICE`: `auto`, `cpu`, or `cuda`
- `AFM_HOST`: backend host; defaults to `127.0.0.1`
- `AFM_PORT`: backend port; defaults to `8050`
- `FLASK_DEBUG`: enable Flask debug mode only for local development

Health check:

```bash
curl http://127.0.0.1:8050/api/health
```

## Run the frontend

The frontend was tested with Node.js 22.16.0 and npm 10.9.2.

```bash
cd frontend
npm ci
npm run lint
npm run build
npm run dev
```

The frontend uses `NEXT_PUBLIC_BACKEND_URL` when provided and otherwise connects to `http://127.0.0.1:8050`.

```bash
cp .env.example .env.local
```

Open:

```text
http://localhost:3000
```

The frontend uses local/system fonts, so the production build does not require downloading Google fonts.

## Validate the repository

Run static integrity checks:

```bash
python scripts/verify_repository.py
```

Run a complete CPU backend smoke test with a generated synthetic image:

```bash
python scripts/smoke_test_backend.py
```

The verification script checks model hashes, mask hashes and counts, Python compilation, removal of stale build artifacts, absence of exact raw AFM validation images, and Experiment 4 redaction.

A detailed record of the final backend, frontend, checkpoint-contract, and repository-integrity tests is provided in `docs/VERIFICATION_REPORT.md`. A SHA-256 manifest for all distributed files is provided as `FILE_MANIFEST.sha256`.

## Reproduce the experiments

Each experiment directory contains scripts, input manifests, raw outputs, and a README describing the validated protocol.

### Experiment 1 — classification

```text
experiments/experiment_1/
```

The finalized validation set contains 50 independently reviewed images. The principal result was 90.0% classification accuracy.

### Experiment 2 — segmentation

```text
experiments/experiment_2/
masks/
```

All 50 externally verified manual masks and all 50 predicted masks are included. The mask manifest contains the file mapping and SHA-256 hashes needed to reproduce the reported image-level metrics.

### Experiment 3 — runtime and ColorWheel validation

```text
experiments/experiment_3/scripts/
experiments/experiment_3/raw_results/
```

This directory contains cold/warm timing, fixed downstream timing, original censored ColorWheel timing, direct full-pipeline batch timing, and ColorWheel output-preservation results.

### Experiment 4 — end-to-end case studies

```text
experiments/experiment_4/
```

The raw AFM case images were removed from the public package. The redacted archive preserves generated masks, probability charts, JSON/CSV summaries, disagreement maps, route notes, and downstream outputs. Publication panels are retained as derived figures.

## Training and provenance

The exact historical CNN and U-Net training programs were lost before this reviewer repository was assembled. The repository therefore includes transparent **reconstructed reference trainers** rather than mislabeling recreated code as the original source.

- `training/train_cnn_reconstructed.py` reproduces the final CNN architecture, class order, 217 × 217 RGB input contract, inference preprocessing, and plain-state-dictionary checkpoint format.
- `training/train_unet_reconstructed.py` reproduces the final Balanced U-Net architecture and checkpoint schema and uses the hyperparameters serialized inside `best_quality_unet.pt`.
- `training/CHECKPOINT_PROVENANCE.md` separates facts recovered from the weights and production code from historically unknown training details.
- `training/checkpoint_provenance.json` provides the same provenance boundary in machine-readable form.

The submitted weights, inference code, evaluation scripts, masks, and raw outputs fully reproduce the reported validation results without retraining. The reconstructed trainers support compatible future training on an authorized external dataset, but they are not claimed to regenerate the submitted weights bit-for-bit.

## Final publication outputs

The authoritative final packages are under `results/`:

- `Experiment_1_Final_Publication`
- `Experiment_2_Final_Publication`
- `Experiment_3_Final_Publication`
- `Experiment_4_Final_Publication`

They include publication tables, figures, methodology bullets, captions, and supporting machine-readable data. Experiment 2 masks and Experiment 3 raw result files are stored separately in first-class repository directories to avoid duplicate large archives.

## Data availability

No original AFM validation or training images are redistributed in this repository. Manual annotations, predicted masks, derived figures, and machine-readable evaluation outputs are included. See `docs/DATA_AVAILABILITY.md`.

## Citation

Citation metadata is provided in `CITATION.cff`. Add the GitHub repository URL and archival DOI after those identifiers exist; no fabricated URL is included in this package.

## License

Source code is released under the MIT License. Model weights, derived results, and third-party input data may have separate provenance or usage constraints; users are responsible for verifying those constraints before redistribution.
