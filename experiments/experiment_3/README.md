# Experiment 3 — Runtime and ColorWheel validation

## Scripts

- `scripts/experiment_3_cold_warm_timing.py`: cold model startup and warm CNN/U-Net timing
- `scripts/experiment_3_downstream_timing.py`: fixed downstream Voronoi/ColorWheel timing
- `scripts/experiment_3_downstream_original_timeout.py`: timeout-safe archived pre-fix ColorWheel timing
- `scripts/experiment_3_full_pipeline_batch.py`: complete direct pipeline and batch timing
- `scripts/colorwheel_original_worker.py`: subprocess worker used by the archived implementation

## Raw results

- `raw_results/cold_warm/`
- `raw_results/downstream_original/`
- `raw_results/downstream_fixed/`
- `raw_results/full_pipeline/`
- `raw_results/colorwheel_preservation/`
- `raw_results/audits/`
- `raw_results/original_protocol/`

The final summary package is at `../../results/Experiment_3_Final_Publication/`.

`backend/3.colorwheel.py` is the fixed production implementation. `backend/3.colorwheel_before_fix.py` is preserved only for the historical comparison. The original baseline is censored because most routed cases exceeded the 120-second timeout.
