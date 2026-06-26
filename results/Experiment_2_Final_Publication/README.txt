EXPERIMENT 2 FINAL PUBLICATION PACKAGE
======================================

Contents
--------
Experiment_2_Publication_Tables.xlsx
    Formatted key-results sheet and six publication/supporting tables.

tables/
    Standalone CSV versions of the finalized tables.

figures/
    Five publication figures in PNG and PDF formats. Vector SVG files are
    included for Figures 1–3, and TIFF files are included for Figures 4–5.

supporting_data/
    Final per-image metrics, overall and class-specific bootstrap confidence
    intervals, externally verified manifest, audit report, and case index.

Experiment_2_Methodology_Bullets.txt
    Bullet-point dataset, annotation, metric, bootstrap, and limitation details.

Experiment_2_Figure_Captions.txt
    Suggested captions for all five figures.

Primary results
---------------
Mean Dice = 0.8452 (95% CI 0.8245–0.8593)
Mean IoU = 0.7369 (95% CI 0.7139–0.7539)
Strongest case = lines_08, Dice 0.912
Weakest case = Mixed_01, Dice 0.377

Mixed_01 is retained and should be discussed as a severe under-segmentation
failure rather than removed as an outlier.
