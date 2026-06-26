# Local data directory

Raw AFM dataset images are intentionally not redistributed in this repository.
They may be subject to source, laboratory, or publication restrictions.

To rerun classification or timing experiments, place authorized images locally using this layout:

```text
data/test/
├── dots/
├── irregular/
├── lines/
└── mixed/
```

Do not commit those images. The root `.gitignore` excludes everything under `data/` except this README.

The repository does include the externally verified manual masks, model-predicted masks, machine-readable metrics, trained weights, evaluation scripts, and generated publication outputs.
