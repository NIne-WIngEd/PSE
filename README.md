# AFM Morphology Analysis Platform

An integrated software platform for automated analysis of Atomic Force Microscopy (AFM) micrographs using deep learning, morphology-aware routing, and image-processing pipelines.

The repository combines:

- **CNN-based morphology classification**
- **U-Net segmentation**
- **Voronoi analysis** for dot-like / mixed morphologies
- **Color-wheel orientation analysis** for line-like / mixed morphologies
- **Interactive batch review and mask editing**
- **PDF report export**
- **A Flask backend** and **Next.js frontend**

---

## Overview

AFM images often require manual interpretation to determine whether the surface morphology is dot-like, line-like, mixed, or irregular. This project automates that workflow by chaining several analysis stages into one browser-based tool.

Typical usage:

1. Upload one or more AFM images.
2. Run a trained CNN to predict morphology class.
3. Run a U-Net model to generate a segmentation mask.
4. Optionally edit the mask in the browser.
5. Route the image into morphology-specific analysis:
   - **Dots / Mixed** → Voronoi analysis
   - **Lines / Mixed** → Color-wheel orientation analysis
6. Review the results.
7. Export a PDF report for one image or the whole batch.

---

## Main Features

- Batch image upload
- CNN classification with confidence scores and class probabilities
- U-Net segmentation mask generation
- Human-in-the-loop mask editing using a browser canvas
- Morphology-specific downstream analysis
- Result previews and downloadable outputs
- Single-result and batch PDF export
- Flask API backend for analysis orchestration
- Next.js frontend for interactive use

---

## Repository Structure

```text
PSE-master/
├── AFM_Web-main/
│   ├── app.py
│   ├── 1.cnn_inference 1.py
│   ├── 2.segmentation.py
│   ├── 2.2.dansegmentation.py
│   ├── 2.voronoi.py
│   ├── 3.colorwheel.py
│   ├── voronoi_v7.py
│   ├── voronoi_mask_pipeline.py
│   ├── cnn_rgb_classifier.pth
│   ├── best_quality_unet.pt
│   ├── requirements.txt
│   ├── Cnn_classifier_test/
│   ├── colorwheel_output/
│   ├── colorwheel_temp/
│   ├── results/
│   ├── segmentation_output/
│   ├── uploads/
│   └── assets/
└── afm-frontend/
    ├── app/
    ├── package.json
    ├── package-lock.json
    ├── tailwind / Next.js config files
    └── README.md
```

### Important note

Several files use unusual names, such as:

- `1.cnn_inference 1.py`

Those filenames are intentional in this archive, and `app.py` imports them dynamically by path.

---

## Core Pipeline

### 1) CNN morphology classification

**File:** `AFM_Web-main/1.cnn_inference 1.py`

This script defines the morphology classifier and exposes helper functions for:

- loading the trained model
- preprocessing images
- running inference
- returning predicted class, confidence, and probabilities

The classifier uses four labels:

- `dots`
- `irregular`
- `lines`
- `mixed`

In the current backend, `irregular` is mapped to `mixed` for the UI workflow.

---

### 2) U-Net segmentation

**File:** `AFM_Web-main/2.segmentation.py`

This module defines a U-Net-style segmentation model and helper functions for:

- preprocessing input images
- predicting binary masks
- saving mask outputs to disk

The backend uses the generated mask as the input for the downstream morphology-specific analysis.

---

### 3) Voronoi analysis

**Files:**

- `AFM_Web-main/2.voronoi.py`
- `AFM_Web-main/voronoi_v7.py`
- `AFM_Web-main/voronoi_mask_pipeline.py`

This branch is used primarily for **dots** and **mixed** morphologies. It performs feature extraction and Voronoi-based quantification on the mask-derived structure.

Typical outputs include:

- Voronoi overlays
- morphology maps
- snapshots
- original/mask previews
- pixel-count / summary text files
- defect-related visualizations

---

### 4) Color-wheel orientation analysis

**File:** `AFM_Web-main/3.colorwheel.py`

This module analyzes **lines** and **mixed** morphologies using orientation-based processing and color-wheel visualization.

Typical outputs include:

- `color_wheel_output.png`
- `one_phase_output.png`
- orientation masks
- grain files and auxiliary TIFF outputs

The implementation can optionally use GPU acceleration if CuPy is available, but it also works with NumPy on CPU.

---

## Backend Application

### `AFM_Web-main/app.py`

This is the main backend for the project.

It is a **Flask API** that handles:

- batch upload
- CNN inference
- U-Net segmentation
- mask editing
- Voronoi and color-wheel routing
- PDF generation
- serving job-specific result files

### Backend workflow

For each uploaded image, the backend:

1. Saves the file inside a job folder
2. Runs CNN classification
3. Runs U-Net segmentation
4. Returns the predicted class, confidence, probabilities, and preview URLs
5. When analysis is triggered, routes the image to the proper downstream pipeline
6. Saves all outputs under a job-specific results directory

### Backend routes

- `GET /api/health`
- `POST /api/upload`
- `POST /api/run-analysis`
- `POST /api/run-analysis-batch`
- `POST /api/export-pdf`
- `POST /api/export-pdf-batch`
- `GET /job_file/<job_id>/<path:filename>`

### Backend runtime

By default the backend runs on:

```text
http://127.0.0.1:8050
```

---

## Frontend Application

### `afm-frontend/`

This is a **Next.js** frontend that provides the user interface for the backend.

It supports:

- file selection and batch upload
- switching between uploaded images in a job
- previewing CNN predictions and segmentation masks
- interactive mask editing with draw/erase tools
- changing brush size
- running analysis for the whole batch
- exporting PDFs

### Frontend runtime

By default the frontend runs on:

```text
http://localhost:3000
```

The frontend is configured to talk to the backend at:

```text
http://127.0.0.1:8050
```

---

## Output and Working Directories

The project writes analysis artifacts into local folders such as:

- `AFM_Web-main/uploads/`
- `AFM_Web-main/results/`
- `AFM_Web-main/segmentation_output/`
- `AFM_Web-main/colorwheel_output/`
- `AFM_Web-main/colorwheel_temp/`
- job-specific folders under `AFM_Web-main/results/job_<id>/`

These are runtime-generated outputs and generally should not be edited manually.

---

## Included Example / Test Assets

The repository contains example assets and generated results that demonstrate the pipeline output, including:

- `Cnn_classifier_test/`
- sample AFM images such as `dots.png`, `lines.png`, and `mixed.png`
- previously generated result folders inside `results/`
- example color-wheel and Voronoi outputs

These are useful for understanding the pipeline and for quick sanity checks.

---

## Requirements

### Python backend

The backend uses packages such as:

- `flask`
- `flask-cors`
- `reportlab`
- `Pillow`
- `numpy`
- `torch`
- `torchvision`
- `opencv-python`
- `scikit-image`
- `scikit-learn`
- `matplotlib`
- `pandas`
- `scipy`
- `networkx`

Install them with:

```bash
pip install -r AFM_Web-main/requirements.txt
```

### Frontend

The frontend uses:

- `next`
- `react`
- `react-dom`
- `tailwindcss`
- `typescript`

Install frontend dependencies with:

```bash
cd afm-frontend
npm install
```

---

## How to Run

### 1) Start the backend

From the `AFM_Web-main/` directory:

```bash
python app.py
```

This starts the Flask server on port `8050`.

### 2) Start the frontend

In a second terminal:

```bash
cd afm-frontend
npm run dev
```

Then open:

```text
http://localhost:3000
```

---

## Typical Usage Flow

1. Open the frontend.
2. Upload one or more AFM images.
3. Wait while the backend runs CNN classification and U-Net segmentation.
4. Review the predicted class and mask for each image.
5. Optionally edit the mask in the browser.
6. Run batch analysis.
7. Inspect Voronoi or color-wheel outputs depending on the morphology.
8. Export a PDF report.

---

## Model Files

The repository includes pretrained weights:

- `AFM_Web-main/cnn_rgb_classifier.pth`
- `AFM_Web-main/best_quality_unet.pt`

These weights are loaded directly by `app.py`.

---

## Notes on the Current Workflow

- `app.py` is the main entry point for the backend.
- The repository is organized around **batch analysis**, not just single-image inference.
- `irregular` classifications are mapped to `mixed` in the UI layer.
- The frontend includes a canvas-based editor for mask correction before analysis.
- The repo contains generated outputs and cache folders from previous runs; these are useful as examples but are not required for a fresh run.

---

## Suggested Use Cases

This platform is designed for:

- polymer morphology characterization
- AFM image interpretation
- automated nanoscale structure analysis
- batch processing of AFM micrographs
- human-in-the-loop refinement of segmentation masks
- research workflows requiring downloadable analysis summaries

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

If you use this work in academic research, presentations, or publications, please consider citing this repository and acknowledging the authors.

---

## Authors

**Mostakim Khan Rayan**  
Electrical & Computer Engineering  
Vanderbilt University

GitHub: `(https://github.com/NIne-WIngEd/PSE)`

---

## Acknowledgments

This project combines deep learning and domain-specific image analysis to automate AFM morphology characterization in a research setting.
