# Experiment 2 mask data

This directory contains the complete mask evidence used for the finalized 50-image segmentation evaluation:

- `ground_truth/`: 50 externally verified manual masks prepared in Fiji
- `predicted/`: 50 final U-Net predicted masks
- `manifest.csv`: image-to-mask pairing, dimensions, binary-value audit, and SHA-256 checksums
- `manifest_audit.txt`: integrity audit from the finalized evaluation

Conventions:

- foreground: black (`0`)
- background: white (`255`)
- threshold used for model masks: `0.5`

Raw AFM source images are not included. The `image_path` fields in the manifest document the original evaluation layout but do not imply that those images are redistributed here.
