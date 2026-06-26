# Experiment 2 — U-Net segmentation

This experiment evaluates the final U-Net at a fixed threshold of 0.5 against externally verified manual masks.

- evaluation script: `scripts/experiment_2_segmentation.py`
- bootstrap script: `scripts/bootstrap_segmentation_metrics.py`
- raw per-image metrics and bootstrap outputs: `raw_results/`
- complete manual and predicted masks: `../../masks/`
- publication package: `../../results/Experiment_2_Final_Publication/`

The raw AFM images are intentionally excluded. The manifest retains image identifiers, dimensions, and SHA-256 values so an authorized local image collection can be audited against the reported evaluation.
