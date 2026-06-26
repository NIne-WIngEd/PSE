# Backend

`app.py` is the production Flask backend. It dynamically imports the final CNN, U-Net, Voronoi, and ColorWheel modules from this directory and loads weights from the repository-level `models/` directory.

Run from the repository root:

```bash
python backend/app.py
```

Default endpoint: `http://127.0.0.1:8050`

Optional environment variables:

- `AFM_MODEL_DIR`: alternative model directory
- `AFM_RUNTIME_DIR`: alternative upload/result directory
- `AFM_DEVICE`: `auto`, `cpu`, or `cuda`
- `AFM_HOST`: default `127.0.0.1`
- `AFM_PORT`: default `8050`
- `FLASK_DEBUG`: set to `1` only for local development

`3.colorwheel.py` is the fixed production implementation. `3.colorwheel_before_fix.py` is retained only to reproduce the historical comparison in Experiment 3.
