# Contributing

Thank you for contributing to the AFM Morphology Analysis Platform.

## Contribution license

By submitting a contribution, you certify that you have the legal right to provide it and agree that your contribution will be licensed under the **GNU Affero General Public License, version 3 or later** (`AGPL-3.0-or-later`), consistent with the rest of the project.

Do not submit code, data, figures, model files, documentation, or other material copied from a source that you are not authorized to redistribute. Clearly identify adapted third-party work and preserve all required copyright and license notices.

## Development requirements

1. Create a feature branch.
2. Do not commit raw AFM datasets, credentials, private information, runtime outputs, `.next`, `node_modules`, or Python cache files.
3. Keep model binaries under Git LFS.
4. Document scientific and algorithmic changes, especially changes to preprocessing, routing, thresholds, model architecture, or downstream analysis.
5. Update tests, documentation, and reproducibility metadata when behavior changes.
6. Preserve the source-code link or source offer required for modified network deployments under AGPL section 13.
7. Do not remove copyright, attribution, citation, license, or provenance information.

## Required checks

From the repository root:

```bash
python scripts/verify_repository.py
python scripts/smoke_test_backend.py
```

From `frontend/`:

```bash
npm ci
npm run lint
npm run build
```

## Research integrity

Contributions must not fabricate, falsify, selectively hide, or misrepresent results. Any changed masks, exclusions, thresholds, evaluation sets, or reported metrics must be disclosed clearly.

Review [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) before participating.
