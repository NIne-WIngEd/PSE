# AFM Paper Evaluation Suite

This folder contains reproducible scripts for the four validation experiments planned for the AFM morphology software paper.

The scripts are written for the current repository structure and use the same:

- CNN architecture and class order
- RGB preprocessing (`217 × 217`, `ToTensor`, no normalization)
- U-Net implementation and checkpoint
- Voronoi analysis code
- Color-wheel analysis code
- routing behavior used by the Flask application

## Contents

```text
evaluation/
├── common.py
├── audit_test_dataset.py
├── experiment_1_classification.py
├── experiment_1b_color_robustness.py
├── experiment_2_segmentation.py
├── experiment_3_timing.py
├── experiment_4_case_studies.py
├── test_manifest.csv
├── case_studies_template.csv
├── manual_timing_template.csv
└── requirements-evaluation.txt

current_test_audit/
├── audit_summary.json
├── class_counts.csv
├── dataset_inventory_and_manifest.csv
├── duplicate_candidates.csv
└── test_contact_sheet.png
```

The `current_test_audit/` folder was generated from the test directory in the uploaded repository.

---

## 1. Installation

Copy the entire `evaluation/` folder into:

```text
AFM_Web-main/evaluation/
```

Your project should then look like:

```text
AFM_Web-main/
├── app.py
├── 1.cnn_inference 1.py
├── 2.segmentation.py
├── 2.voronoi.py
├── 3.colorwheel.py
├── cnn_rgb_classifier.pth
├── best_quality_unet.pt
├── test/
└── evaluation/
```

Install the project and evaluation dependencies:

```bash
pip install -r requirements.txt
pip install -r evaluation/requirements-evaluation.txt
```

### Important: retrieve the actual model weights

In the uploaded ZIP, both model files are Git LFS pointer files rather than the real weights:

- `cnn_rgb_classifier.pth` is about 134 bytes in the ZIP, but the pointer says the real file should be about 194.6 MB.
- `best_quality_unet.pt` is about 133 bytes in the ZIP, but the pointer says the real file should be about 57.5 MB.

From the cloned repository root, run:

```bash
git lfs install
git lfs pull
```

The scripts check for LFS pointers and stop with a clear error instead of attempting invalid inference.

---

## 2. Freeze the evaluation protocol before running the model

Do not change labels, remove difficult images, tune thresholds, retrain the CNN, or modify preprocessing after seeing the formal test results.

First audit and review the test set:

```bash
python evaluation/audit_test_dataset.py
```

This creates:

```text
evaluation_outputs/test_audit/
```

Review `dataset_inventory_and_manifest.csv`. At minimum, complete these columns:

- `include_in_primary`
- `evaluation_subset`
- `label_review_status`
- `color_domain_review`
- `source_reference`
- `source_group_id`
- `sample_id`
- `notes`

Then save the finalized file as:

```text
evaluation/test_manifest.csv
```

Recommended subset names:

- `same_rendering_domain`
- `cross_colormap`
- `quality_limited`
- `development_example`

Do not assign subsets based on whether the model predicts an image correctly.

---

# Experiment 1: CNN classification validation

## Purpose

Measure classification performance on independently labeled AFM images that were not used for model training.

## Run

```bash
python evaluation/experiment_1_classification.py \
  --manifest evaluation/test_manifest.csv
```

Use CPU explicitly if needed:

```bash
python evaluation/experiment_1_classification.py \
  --manifest evaluation/test_manifest.csv \
  --device cpu
```

## Main output

```text
evaluation_outputs/experiment_1_classification/
```

Key files:

- `cnn_predictions_all.csv`
- `cnn_predictions_primary.csv`
- `classification_errors_all.csv`
- `primary_summary_metrics.csv`
- `primary_per_class_metrics.csv`
- `primary_confusion_matrix_counts.csv`
- `primary_confusion_matrix_normalized.csv`
- confusion-matrix PNG figures
- per-class metric figure
- confidence histogram
- reliability diagram
- `run_metadata.json`

The prediction CSV contains:

- filename and relative path
- true class
- predicted class
- confidence of the predicted class
- all four class probabilities
- correct/incorrect status
- inference time
- image dimensions
- manifest subset and provenance fields
- image SHA-256 hash

## Metrics produced

- Accuracy with Wilson 95% confidence interval
- Balanced accuracy
- Macro precision, recall, and F1
- Weighted precision, recall, and F1
- Per-class precision, recall, F1, support, and mean confidence
- Matthews correlation coefficient
- Cohen's kappa
- Expected calibration error
- Confusion matrices

Because the current test set is imbalanced, the manuscript should emphasize macro F1, balanced accuracy, per-class recall, and the confusion matrix rather than accuracy alone.

---

# Experiment 1B: color/rendering robustness

## Purpose

Quantify whether CNN predictions change when the same spatial morphology is displayed with a different rendering.

This is a stress test. It does not replace the primary external validation.

## Run

```bash
python evaluation/experiment_1b_color_robustness.py \
  --manifest evaluation/test_manifest.csv
```

To retain all generated image variants:

```bash
python evaluation/experiment_1b_color_robustness.py \
  --manifest evaluation/test_manifest.csv \
  --save-variants
```

Variants:

- original RGB
- grayscale replicated to RGB
- inverted grayscale
- magma rendering
- viridis rendering
- inferno rendering

Outputs include per-image predictions, variant-level accuracy, macro F1, prediction consistency, and a summary figure.

The manuscript must state that the transformations operate on already-rendered images, not raw AFM height data.

---

# Experiment 2: U-Net segmentation validation

## Required data

This experiment cannot be calculated without manually reviewed ground-truth masks.

Create:

```text
AFM_Web-main/segmentation_test/
├── images/
│   ├── dots/
│   │   └── sample_01.png
│   └── ...
└── masks/
    ├── dots/
    │   └── sample_01.png
    └── ...
```

The image and mask must have the same relative path and filename stem.

Use binary ground-truth masks where white is foreground and black is background. If your masks use the opposite polarity, use `--invert-ground-truth`.

## Run

```bash
python evaluation/experiment_2_segmentation.py
```

Opposite mask polarity:

```bash
python evaluation/experiment_2_segmentation.py --invert-ground-truth
```

## Outputs

- per-image Dice, IoU, pixel precision, recall, specificity, and accuracy
- mean, standard deviation, median, range, and bootstrap 95% confidence intervals
- predicted masks
- comparison sheets showing original, ground truth, prediction, and disagreement
- publication-ready metric figure
- model/checkpoint metadata

The default threshold is fixed at `0.5`, matching the software. Do not optimize this threshold on the final test set.

---

# Experiment 3: timing and efficiency

## Purpose

Measure model-loading time, warm CNN inference time, U-Net inference time, and optionally the full downstream file-generating workflow.

## Basic run

```bash
python evaluation/experiment_3_timing.py \
  --manifest evaluation/test_manifest.csv \
  --max-images 20 \
  --repeats 3
```

## Include Voronoi and color-wheel processing

```bash
python evaluation/experiment_3_timing.py \
  --manifest evaluation/test_manifest.csv \
  --max-images 20 \
  --repeats 3 \
  --include-downstream
```

The script reports model-loading time separately because the Flask server loads the models once at startup.

## Manual comparison

The first timing run creates:

```text
evaluation_outputs/experiment_3_timing/manual_timing_template.csv
```

For each image, use a stopwatch to record the complete manual workflow under one predefined protocol. Do not change the manual task from image to image.

Then run:

```bash
python evaluation/experiment_3_timing.py \
  --manifest evaluation/test_manifest.csv \
  --include-downstream \
  --manual-timing-csv evaluation_outputs/experiment_3_timing/manual_timing_template.csv
```

The comparison outputs include:

- manual time per image
- automated time per image
- speedup factor
- seconds saved
- manual-versus-automated figure

For stronger evidence, use at least two analysts and report their experience levels.

---

# Experiment 4: end-to-end case studies

## Purpose

Create representative workflow figures showing:

1. original AFM image
2. generated or edited segmentation mask
3. morphology-specific outputs
4. CNN prediction and probabilities

Edit:

```text
evaluation/case_studies_template.csv
```

Suggested cases are already provided, one per class. These were chosen only as illustrative examples and must not replace test-set metrics.

An optional `edited_mask_path` can be provided for a human-corrected mask. Leave it blank to use the automatic U-Net mask.

## Run

```bash
python evaluation/experiment_4_case_studies.py
```

Outputs include:

- one folder per case
- original image
- mask used
- Voronoi and/or color-wheel outputs
- a combined case-study figure
- classification probabilities
- `case_study_summary.csv`

The script records both:

- the raw CNN prediction
- the routing class used by the current Flask application

This matters because the application currently maps `irregular` CNN predictions to the `mixed` analysis branch.

---

# Recommended order

1. Review `current_test_audit/TEST_FOLDER_REVIEW.md`.
2. Verify image provenance and permission to use each image.
3. Have a domain expert independently review all labels.
4. Finalize `evaluation/test_manifest.csv`.
5. Freeze the test set and preprocessing.
6. Pull the actual Git LFS model files.
7. Run Experiment 1 once as the formal benchmark.
8. Run Experiment 1B as a separate robustness study.
9. Produce ground-truth masks and run Experiment 2.
10. Run the timing protocol and collect manual timing data.
11. Generate case-study figures.

# Publication cautions

- Do not report the three development-example duplicates as untouched external validation if they were used while debugging or choosing the model.
- Do not relabel misclassified images based on what the CNN predicted.
- Do not remove low-confidence or incorrect images after inference.
- Do not combine same-domain and cross-colormap results into one accuracy value without also reporting subgroup performance.
- Record image sources and sample grouping. Multiple crops from the same AFM scan or publication are not fully independent observations.
- Do not upload images from published papers to GitHub unless you have permission to redistribute them.
