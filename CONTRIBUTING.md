# Contributing

1. Create a feature branch.
2. Do not commit raw AFM datasets, credentials, runtime outputs, `.next`, or `node_modules`.
3. Keep model binaries under Git LFS.
4. Run `python scripts/verify_repository.py`.
5. Run `python scripts/smoke_test_backend.py` when model weights are available.
6. In `frontend/`, run `npm ci`, `npm run lint`, and `npm run build`.
7. Describe scientific or algorithmic changes explicitly, especially changes to preprocessing, routing, thresholds, or downstream analysis.
