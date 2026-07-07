# AFM Morphology Analysis Platform

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE) [![Citation](https://img.shields.io/badge/citation-CITATION.cff-informational.svg)](CITATION.cff)

A reproducible research-software platform for automated analysis of rendered Atomic Force Microscopy (AFM) images. The system combines deep-learning classification and segmentation with morphology-aware routing, Voronoi analysis, ColorWheel orientation analysis, interactive mask correction, batch processing, and PDF report generation.

> **Scope:** This repository evaluates and processes rendered AFM images. It does not operate directly on raw AFM height-data files.

---

## Overview

AFM morphology analysis often requires several disconnected manual steps: identifying morphology type, drawing or refining a binary mask, selecting an appropriate downstream analysis, reviewing the outputs, and assembling a report. This project integrates those steps into one browser-based workflow.

The application supports four morphology classes:

- `dots`
- `irregular`
- `lines`
- `mixed`

The prediction controls which downstream analysis is executed:

| Predicted class | Downstream route |
|---|---|
| `dots` | Voronoi analysis |
| `lines` | ColorWheel orientation analysis |
| `mixed` | Voronoi and ColorWheel analysis |
| `irregular` | No morphology-specific downstream module |

The user can review and edit the predicted mask before launching downstream analysis.

---

## Key capabilities

- Single-image and batch AFM-image upload
- Four-class CNN morphology classification
- Confidence scores and full class-probability output
- Binary U-Net segmentation
- Browser-based mask drawing and erasing
- Adjustable editing brush size
- Prediction-dependent analysis routing
- Voronoi analysis for dot-like structures
- ColorWheel orientation analysis for line-like structures
- Combined downstream processing for mixed morphologies
- Job-specific output storage
- Single-image and batch PDF export
- Flask REST API
- Next.js and TypeScript user interface
- Reproducible evaluation scripts and machine-readable results
- Externally verified manual and predicted segmentation masks
- Repository-integrity and backend smoke-test utilities

---

## End-to-end workflow

```text
AFM image
   │
   ├── CNN morphology classifier
   │      ├── dots
   │      ├── irregular
   │      ├── lines
   │      └── mixed
   │
   ├── U-Net binary segmentation
   │
   ├── Optional human mask correction
   │
   └── Morphology-aware routing
          ├── dots      → Voronoi
          ├── lines     → ColorWheel
          ├── mixed     → Voronoi + ColorWheel
          └── irregular → no downstream module
```

For each uploaded image, the backend returns the predicted class, confidence, class probabilities, predicted mask, and output URLs. After optional mask editing, the user can run the appropriate downstream analysis and export a report.

---

## Software architecture

### Backend

The backend is a Flask application responsible for:

- image upload and validation
- model loading
- CNN inference
- U-Net inference
- edited-mask handling
- routing to Voronoi and ColorWheel modules
- batch execution
- job-specific output management
- PDF report generation
- serving generated result files

Default backend address:

```text
http://127.0.0.1:8050
```

### Frontend

The frontend is a Next.js application written in TypeScript. It provides:

- drag-and-drop or file-picker upload
- batch navigation
- prediction and probability display
- mask preview
- interactive draw and erase tools
- brush-size control
- per-image and batch analysis
- result previews
- PDF export

Default frontend address:

```text
http://localhost:3000
```

---

## Core software modules

### CNN morphology classification

**Primary module:** `backend/1.cnn_inference 1.py`

This module defines the production classifier and exposes functions for:

- model construction
- checkpoint loading
- RGB preprocessing
- 217 × 217 image resizing
- four-class inference
- confidence and probability reporting

Class order:

```text
dots, irregular, lines, mixed
```

The production checkpoint is:

```text
models/cnn_rgb_classifier.pth
```

### U-Net segmentation

**Primary module:** `backend/2.segmentation.py`

This module defines the production binary segmentation architecture and includes:

- image preprocessing
- tensor conversion
- inference
- thresholding
- mask resizing
- binary-mask saving

The production checkpoint is:

```text
models/best_quality_unet.pt
```

The validated decision threshold is:

```text
0.5
```

### Voronoi analysis

**Primary modules:**

```text
backend/2.voronoi.py
backend/voronoi_v7.py
backend/voronoi_mask_pipeline.py
```

The Voronoi branch is used for `dots` and `mixed` predictions. Depending on the detected structure, outputs can include:

- dot-only masks
- Voronoi overlays
- morphology maps
- snapshots
- light- and dark-defect visualizations
- group-area summaries
- morphology statistics

Some images may produce only the available original and snapshot outputs when the conditions required for overlay or morphology-map generation are not met.

### ColorWheel orientation analysis

**Active implementation:**

```text
backend/3.colorwheel.py
```

The ColorWheel branch is used for `lines` and `mixed` predictions. It produces:

- `color_wheel_output.png`
- `one_phase_output.png`
- orientation-cluster masks
- filtered component masks
- grain-summary text files
- orientation metadata

Additional files:

```text
backend/3.colorwheel_before_fix.py
backend/colorwheel_worker.py
```

`3.colorwheel_before_fix.py` is the preserved historical baseline used in Experiment 3. `colorwheel_worker.py` executes the active implementation in a separate process so timing scripts can isolate failures and enforce time limits without freezing the main process.

---

## Backend API

The Flask application exposes the following primary routes:

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/health` | Backend and model health check |
| `POST` | `/api/upload` | Upload images and run classification and segmentation |
| `POST` | `/api/run-analysis` | Run downstream analysis for one item |
| `POST` | `/api/run-analysis-batch` | Run downstream analysis for a batch |
| `POST` | `/api/export-pdf` | Export one result as PDF |
| `POST` | `/api/export-pdf-batch` | Export a batch report |
| `GET` | `/job_file/<job_id>/<path>` | Serve job-specific generated files |

Generated files are stored under `runtime/` by default.

---

## Repository layout

```text
AFM_Morphology_Analysis_GitHub/
├── backend/                 Flask API and production analysis modules
├── frontend/                Next.js and TypeScript user interface, npm config, and Node version hint
├── models/                  Trained CNN and U-Net checkpoints
├── training/                Reconstructed compatible training scripts
├── experiments/             Reproduction scripts and raw experiment outputs
│   ├── experiment_1/        CNN classification validation
│   ├── experiment_2/        U-Net segmentation validation
│   ├── experiment_3/        Runtime, batch, and ColorWheel validation
│   └── experiment_4/        End-to-end workflow case studies
├── results/                 Final publication packages for Experiments 1–4
├── masks/                   Manual ground-truth and predicted masks
├── environment/             Tested pinned Python environment
├── scripts/                 Verification and smoke-test utilities
├── docs/                    Reproducibility and data-availability documents
├── data/                    Dataset-access statement; no raw AFM images
├── runtime/                 Generated application outputs; ignored by Git
├── CITATION.cff             Citation metadata
├── CONTRIBUTING.md          Contribution guidance
├── LICENSE                  GNU Affero General Public License v3 or later
├── FILE_MANIFEST.sha256     Distributed-file integrity manifest
└── README.md
```

Some production modules retain historical filenames, including spaces and numeric prefixes. These names are intentional, and the backend imports the modules by file path where necessary.

---

## Model weights and Git LFS

The trained checkpoints are distributed through Git LFS.

| File | Size | SHA-256 |
|---|---:|---|
| `models/cnn_rgb_classifier.pth` | 194,579,557 bytes | `dd309d7d0d6706f34b762b396b4142e2586f4859d27f5cb409b9093156bba256` |
| `models/best_quality_unet.pt` | 57,507,115 bytes | `18ecdf3b3c35408a467d0e7baab781dbdb88572a87c907c14f4ad01884b1be41` |

Clone the repository and retrieve the model files with:

```bash
git lfs install
git clone https://github.com/NIne-WIngEd/PSE.git
cd PSE
git lfs pull
```

Verify that the weights were downloaded rather than left as Git LFS pointer files:

```bash
git lfs ls-files
```

---

## Installation

### Prerequisites

- Python 3.13.x for the tested CPU environment
- Node.js 22 LTS recommended for the frontend
- npm 10.x recommended for the frontend
- Git LFS
- Windows, Linux, or macOS
- Optional CUDA-compatible GPU for accelerated PyTorch inference

The frontend includes `frontend/.nvmrc` and `frontend/.npmrc` to make cross-system setup more consistent. The `.nvmrc` file indicates the recommended Node.js major version, and `.npmrc` explicitly points npm to the public npm registry.

### Python environment

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux or macOS:

```bash
source .venv/bin/activate
```

Install the exact tested environment:

```bash
python -m pip install --upgrade pip
python -m pip install -r environment/requirements-lock.txt
```

A convenience dependency file is also available at `requirements.txt`. Use the lock file when exact reproducibility is required.

### Frontend dependencies

From the repository root:

```bash
cd frontend
npm install
```

For strict lockfile-based installation, `npm ci` can also be used when supported by the local Node/npm version:

```bash
npm ci
```

The frontend is intended to be installed from the public npm registry. The expected registry is:

```text
https://registry.npmjs.org/
```

You can confirm this with:

```bash
npm config get registry
```

The frontend uses local and system fonts. Its production build does not depend on downloading Google Fonts.

---

## Frontend Node.js troubleshooting

The frontend is recommended to run with Node.js 22 LTS and npm 10.x. Very new Node/npm combinations may occasionally produce npm-internal installation errors such as:

```text
npm error Exit handler never called!
```

If this occurs, switch to Node.js 22 LTS, remove `node_modules`, and reinstall with `npm install` from the `frontend` directory:

```bash
cd frontend
npm install
npm run build
```

On systems using `nvm`, run the following from the `frontend` directory:

```bash
nvm use
npm install
```

On Windows, use a Node version manager such as nvm-windows or install Node.js 22 LTS directly.

---

## Running the application

### 1. Start the backend

From the repository root:

```bash
python backend/app.py
```

Optional environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `AFM_MODEL_DIR` | `models/` | Model-checkpoint directory |
| `AFM_RUNTIME_DIR` | `runtime/` | Generated-output directory |
| `AFM_DEVICE` | `auto` | `auto`, `cpu`, or `cuda` |
| `AFM_HOST` | `127.0.0.1` | Flask host |
| `AFM_PORT` | `8050` | Flask port |
| `FLASK_DEBUG` | disabled | Local-development debugging |

Health check:

```bash
curl http://127.0.0.1:8050/api/health
```

### 2. Start the frontend

In a second terminal:

```bash
cd frontend
cp .env.example .env.local
npm run dev
```

On Windows PowerShell, the copy command can be written as:

```powershell
Copy-Item .env.example .env.local
```

The default backend URL is:

```text
http://127.0.0.1:8050
```

It can be changed in `.env.local` with:

```text
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8050
```

Open the interface at:

```text
http://localhost:3000
```

---

## Typical usage

1. Start the backend and frontend.
2. Open `http://localhost:3000`.
3. Upload one or more rendered AFM images.
4. Review the CNN prediction, confidence, and class probabilities.
5. Review the U-Net segmentation mask.
6. Draw or erase mask regions when correction is necessary.
7. Run downstream analysis.
8. Inspect the Voronoi and/or ColorWheel results selected by the predicted class.
9. Export a single-image or batch PDF report.

---

## Runtime outputs

Application-generated content is written to `runtime/`. Typical outputs include:

```text
runtime/
├── uploads/
├── results/
├── segmentation_output/
├── colorwheel_output/
└── job_<id>/
```

These files are generated during use and are excluded from version control. They should not be edited manually while a job is running.

---

## Validation study

This repository accompanies a four-part software-validation study.

### Experiment 1 — CNN classification

Location:

```text
experiments/experiment_1/
results/Experiment_1_Final_Publication/
```

Final 50-image results:

- Accuracy: **90.0%**
- Balanced accuracy: **88.93%**
- Macro F1: **89.43%**
- Matthews correlation coefficient: **0.859**

The finalized set contained 13 dots, 7 irregular, 20 lines, and 10 mixed images.

### Experiment 2 — U-Net segmentation

Location:

```text
experiments/experiment_2/
results/Experiment_2_Final_Publication/
masks/
```

Final 50-image image-level results:

- Mean Dice: **0.845**
- Mean IoU: **0.737**
- Mean precision: **0.858**
- Mean recall: **0.839**
- Mean specificity: **0.959**
- Mean pixel accuracy: **0.934**

All 50 externally verified manual masks and all 50 predicted masks are included. The original AFM images are not redistributed.

### Experiment 3 — runtime and ColorWheel validation

Location:

```text
experiments/experiment_3/
results/Experiment_3_Final_Publication/
```

The experiment includes:

- cold and warm CNN/U-Net timing
- fixed downstream timing
- original censored ColorWheel timing
- direct 50-image batch timing
- route-specific timing
- ColorWheel output-preservation analysis

The final sequential 50-image batch completed in a median of **450.637 seconds**, corresponding to **6.657 images per minute**. On the seven common completion cases, the fixed ColorWheel implementation was **26.4× faster by median runtime** than the censored historical baseline.

### Experiment 4 — end-to-end case studies

Location:

```text
experiments/experiment_4/
results/Experiment_4_Final_Publication/
```

Six fixed cases demonstrate:

- representative dots routing
- representative lines routing
- representative mixed routing
- representative irregular handling
- severe segmentation-error propagation
- high-confidence classification-driven routing failure

All six case-study executions completed without runtime failure.

---

## Reproducing the experiments

Each experiment directory includes:

- evaluation scripts
- input manifests
- raw machine-readable outputs
- methodology notes
- publication-ready figures and tables
- experiment-specific README documentation

The authoritative publication packages are:

```text
results/Experiment_1_Final_Publication/
results/Experiment_2_Final_Publication/
results/Experiment_3_Final_Publication/
results/Experiment_4_Final_Publication/
```

Experiment 2 masks and Experiment 3 raw outputs are stored as first-class repository content rather than duplicated inside every publication archive.

---

## Training-code provenance

The exact historical CNN and U-Net training scripts were lost before the reviewer repository was assembled. To avoid misrepresenting reconstructed code as the original training source, the repository includes compatible reference trainers with explicit provenance boundaries:

```text
training/train_cnn_reconstructed.py
training/train_unet_reconstructed.py
training/CHECKPOINT_PROVENANCE.md
training/checkpoint_provenance.json
```

The reconstructed scripts reproduce the final architectures, input contracts, class ordering, checkpoint formats, and all recoverable checkpoint metadata. They are suitable for compatible future training on an authorized dataset, but they are **not claimed to regenerate the submitted weights bit-for-bit**.

The included weights, inference code, masks, evaluation scripts, and raw results reproduce the reported validation results without retraining.

---

## Repository verification

Run the repository-integrity checks:

```bash
python scripts/verify_repository.py
```

Run the backend smoke test:

```bash
python scripts/smoke_test_backend.py
```

Validate the frontend:

```bash
cd frontend
npm install
npm run lint
npm run build
```

For strict lockfile-based verification, `npm ci` may be used instead of `npm install` when supported by the local Node/npm version.

The verification workflow checks:

- model-file hashes
- manual and predicted mask counts and hashes
- Python source compilation
- absence of stale cache and build artifacts
- absence of exact raw AFM validation images
- Experiment 4 redaction
- backend health
- backend upload and inference
- frontend linting
- frontend production build

A full verification record is available in:

```text
docs/VERIFICATION_REPORT.md
```

A SHA-256 file manifest is available in:

```text
FILE_MANIFEST.sha256
```

---

## Data availability

The original AFM training and validation images are not redistributed because the repository does not establish redistribution permission for every source image.

The public repository includes:

- trained model checkpoints
- inference code
- reconstructed training code
- evaluation scripts
- reviewed predictions
- manual ground-truth masks
- predicted masks
- raw machine-readable results
- derived figures
- publication tables
- redacted end-to-end outputs

Authorized users may run the software with their own AFM images or with separately obtained source data. See:

```text
docs/DATA_AVAILABILITY.md
```

---

## Known limitations

- The validation set is modest and should not be interpreted as establishing performance across every AFM instrument, material system, or rendering convention.
- The software was validated on rendered AFM images rather than raw height maps.
- Manual segmentation masks contain unavoidable annotation uncertainty.
- Binary overlap metrics do not fully measure boundary quality, topology, or downstream scientific error.
- CNN confidence is descriptive and was not established as a clinical or safety-critical uncertainty measure.
- The reconstructed trainers are compatible implementations, not the exact lost historical training scripts.
- The public repository does not contain the original AFM images.

---

## Citation

Citation metadata is provided in [`CITATION.cff`](CITATION.cff).

When using this repository in academic work, cite the associated software article and archived repository release once the final bibliographic information and DOI are available.

---

## Project governance and attribution

- [`LICENSE`](LICENSE): GNU AGPL v3 or later
- [`NOTICE`](NOTICE): copyright and attribution notice
- [`CITATION.cff`](CITATION.cff): academic citation metadata
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md): community, research-integrity, and anti-plagiarism policy
- [`CONTRIBUTING.md`](CONTRIBUTING.md): contribution requirements

---

## Author

**Mostakim Khan Rayan**  
Electrical & Computer Engineering  
Vanderbilt University 

**Mohammad Nabil Islam**  
Polymer Science & Engineering  
University of Southern Mississippi 

GitHub: [NIne-WIngEd](https://github.com/NIne-WIngEd)  
Repository: [NIne-WIngEd/PSE](https://github.com/NIne-WIngEd/PSE)

---

## Acknowledgments

This project was developed as part of an AFM morphology-analysis research workflow at Dr. Boran Ma's research lab. It combines machine learning, scientific image processing, and browser-based software engineering to make AFM analysis more consistent, reviewable, and reproducible.

Additional collaborators, laboratory acknowledgments, and funding information should be added to the associated manuscript and repository release where required.

---

## Contributing

Contributions are welcome. Review [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a pull request.

When reporting an issue, include:

- operating system
- Python version
- Node.js version
- CPU or GPU configuration
- exact reproduction command
- traceback or browser-console output
- whether the issue occurs on one image or a batch

Do not upload restricted or proprietary AFM images to a public issue.

---

## License

Unless a file states otherwise, the original source code and documentation in this repository are licensed under the **GNU Affero General Public License, version 3 or later** (`AGPL-3.0-or-later`). See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

In practical terms:

- commercial use is permitted;
- modified or redistributed versions must remain under the AGPL and include the corresponding source code;
- a modified version made available to users over a network must offer those users access to its corresponding source code, as required by AGPL section 13;
- copyright, license, attribution, and modification notices must be preserved;
- the AGPL does not permit false authorship, plagiarism, or removal of provenance.

Academic citation is requested through [`CITATION.cff`](CITATION.cff). Citation is an important research-integrity expectation, but it is separate from the legal conditions of the AGPL.

Model weights, masks, derived outputs, figures, tables, and third-party components may carry additional provenance or usage considerations. Original AFM source images are not redistributed. Users remain responsible for confirming that they have permission to use and redistribute their own input data and any third-party material.

When deploying a modified network-accessible version of the application, keep a visible link to the corresponding source code available to users.
