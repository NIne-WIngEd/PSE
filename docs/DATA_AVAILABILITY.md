# Data availability

Raw AFM dataset images are not redistributed in this repository. The repository instead provides:

- trained CNN and U-Net weights;
- externally verified manual segmentation masks;
- final model-predicted masks;
- per-image classification and segmentation results;
- bootstrap confidence-interval outputs;
- raw timing and ColorWheel validation results;
- generated publication figures and tables;
- scripts for model inference, evaluation, and application execution.

The evaluation scripts accept an authorized local image directory. Reviewers who receive the source images separately can reproduce the reported predictions and metrics using the included manifests and SHA-256 records.


## Training-source availability

Data availability

A legally redistributable 50-image AFM benchmark/evaluation dataset is archived on Zenodo at https://doi.org/10.5281/zenodo.21422891. The archive contains validation AFM images, classification labels, manual segmentation masks, predicted segmentation masks, externally verified record manifests, segmentation-metric tables, SHA-256 file hashes, and verification scripts needed to inspect and re-evaluate the reported classification and segmentation results.

The finalized benchmark contains 13 dot, 7 irregular, 20 line, and 10 mixed AFM images. The segmentation masks use a binary convention in which foreground pixels have value 0 and background pixels have value 255. The supplied metric script follows this convention and reproduces the reported Experiment 2 means: Dice = 0.845, IoU = 0.737, precision = 0.858, recall = 0.839, specificity = 0.959, and pixel accuracy = 0.934.

The original historical training dataset used during model development was not preserved. Therefore, retraining-based reproduction of the submitted checkpoints and historical train/test leakage assessment are not claimed. The repository provides the submitted checkpoints, inference code, evaluation scripts, raw machine-readable outputs, reconstructed compatible training scripts, and checkpoint-verification logs to support checkpoint-level reproducibility and benchmark-level validation.
