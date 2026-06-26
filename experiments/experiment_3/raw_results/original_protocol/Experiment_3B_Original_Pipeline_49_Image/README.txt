EXPERIMENT 3B — ORIGINAL PIPELINE, 49-IMAGE TIMING
==================================================

This package leaves app.py and 3.colorwheel.py unchanged.

The image actually associated with the interrupted run was:
    irregular/irregular_06.jpeg

It was excluded only from Experiment 3B downstream timing. The supplied
manifest contains 49 included rows because include_in_primary=False was set
only for that row.

Files
-----
- cnn_predictions_primary_reviewed_exp3_49.csv
- experiment_3_downstream_original_timeout.py
- colorwheel_original_worker.py
- EXPERIMENT_3B_EXCLUSION_RECORD.txt
- RUN_COMMANDS.txt

Installation
------------
Copy these three files to the repository root, beside AFM_Web-main and test:

- cnn_predictions_primary_reviewed_exp3_49.csv
- experiment_3_downstream_original_timeout.py
- colorwheel_original_worker.py

Do not replace app.py.
Do not replace 3.colorwheel.py.

The timing script imports and measures your existing original 3.colorwheel.py.

Before the full run
-------------------
Delete the incomplete prior output:

Remove-Item "evaluation_outputs\experiment_3_downstream" -Recurse -Force -ErrorAction SilentlyContinue

Quick test
----------
python experiment_3_downstream_original_timeout.py `
  --project-dir "." `
  --test-dir "test" `
  --manifest "cnn_predictions_primary_reviewed_exp3_49.csv" `
  --output-dir "evaluation_outputs/experiment_3_downstream_original_49_test" `
  --device auto `
  --repeats 1 `
  --max-images 4 `
  --colorwheel-timeout-seconds 120

The first four images are dots, so this confirms setup and Voronoi only.

Full run
--------
python experiment_3_downstream_original_timeout.py `
  --project-dir "." `
  --test-dir "test" `
  --manifest "cnn_predictions_primary_reviewed_exp3_49.csv" `
  --output-dir "evaluation_outputs/experiment_3_downstream_original_49" `
  --device auto `
  --repeats 3 `
  --max-images 0 `
  --colorwheel-timeout-seconds 120 `
  --num-clusters 8

Caution
-------
The original ColorWheel may time out on additional large images. The script
will continue and record them in downstream_failures.csv. Do not delete those
failures from the reported results.
