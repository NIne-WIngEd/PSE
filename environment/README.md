# Environment

The repository was smoke-tested with Python 3.13.5 and the exact CPU package versions in `requirements-lock.txt`.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The lock file uses CPU PyTorch wheels. CUDA users should install the compatible `torch` and `torchvision` wheels from the official PyTorch index first, then install the remaining pinned packages.

The frontend is independently locked by `frontend/package-lock.json` and was tested with Node.js 22.16.0 and npm 10.9.2.
