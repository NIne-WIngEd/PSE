# Trained models

Both model files are tracked with Git LFS.

| File | Purpose | Size | SHA-256 |
|---|---|---:|---|
| `cnn_rgb_classifier.pth` | Four-class RGB AFM morphology classifier | 194,579,557 bytes | `dd309d7d0d6706f34b762b396b4142e2586f4859d27f5cb409b9093156bba256` |
| `best_quality_unet.pt` | Binary AFM segmentation checkpoint | 57,507,115 bytes | `18ecdf3b3c35408a467d0e7baab781dbdb88572a87c907c14f4ad01884b1be41` |

After cloning:

```bash
git lfs install
git lfs pull
```

A model file that is only about 130 bytes is an unresolved Git LFS pointer, not the trained checkpoint.


## Training provenance

The final weights are preserved exactly and verified by SHA-256. The historical training programs were lost. See `../training/CHECKPOINT_PROVENANCE.md` and `../training/checkpoint_provenance.json` for recovered metadata and explicit unknowns. The reconstructed trainers verify architecture compatibility and support future training, but are not claimed to be the original source.
