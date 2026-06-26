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

The exact historical CNN and U-Net training programs were not recoverable. Compatible reconstructed trainers and a machine-readable checkpoint-provenance record are included under `training/`. This limitation does not affect reproduction of the submitted predictions, validation metrics, timing results, or publication figures from the preserved final weights and raw evaluation outputs.
