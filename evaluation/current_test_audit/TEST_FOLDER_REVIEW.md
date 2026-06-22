# Review of the Current `test/` Folder

## Actual dataset size

The uploaded test folder contains **56 images**, not 38:

| Class | Images | Share |
|---|---:|---:|
| Dots | 14 | 25.0% |
| Lines | 27 | 48.2% |
| Mixed | 10 | 17.9% |
| Irregular | 5 | 8.9% |
| **Total** | **56** | **100%** |

This is substantially imbalanced. Accuracy alone will be misleading, so the formal analysis should include macro F1, balanced accuracy, per-class recall, support, and a confusion matrix.

## Three exact development-example duplicates

The audit found three files in `test/` that are byte-for-byte identical to the images in `Cnn_classifier_test/`:

- `test/dots/dot_12.png` = `Cnn_classifier_test/dots.png`
- `test/lines/lines_23.png` = `Cnn_classifier_test/lines.png`
- `test/mixed/Mixed_02.png` = `Cnn_classifier_test/mixed.png`

These are the same three standard examples shown during development. If they were repeatedly used to inspect model behavior, choose architecture, change preprocessing, or debug predictions, they should not be described as untouched external validation. The supplied manifest marks them `include_in_primary = no` by default.

After excluding them, the proposed primary set contains **53 images**:

- 13 dots
- 26 lines
- 9 mixed
- 5 irregular

## Image-size and aspect-ratio concerns

The CNN preprocessing forcibly resizes every input to `217 × 217` without preserving aspect ratio.

Most images are close enough to square, but four have a long-to-short aspect ratio of at least 1.25:

- `irregular/irregular_04.png` — 343 × 239
- `mixed/Mixed_03.png` — 378 × 292
- `mixed/Mixed_05.png` — 190 × 140
- `mixed/Mixed_06.png` — 240 × 96

`Mixed_06.png` is especially narrow and will be strongly stretched during preprocessing. It is still usable as a robustness example, but its limitation should be declared before inference.

Two files are smaller than the CNN input in at least one dimension and therefore require upscaling:

- `mixed/Mixed_05.png`
- `mixed/Mixed_06.png`

Do not delete them based on prediction performance. Decide before the formal run whether they belong in the primary set or a predefined `quality_limited` subset.

## Color/rendering-domain shift

The set contains several rendering styles:

- the orange/brown style resembling the development examples
- purple/yellow renderings
- red/yellow renderings
- green/yellow renderings
- high-contrast and low-contrast images

The five irregular images share a particularly distinctive purple/yellow appearance. This creates a possible confound: the CNN may learn palette/source cues in addition to morphology.

Before inference, assign each image to a declared rendering subgroup such as:

- `same_rendering_domain`
- `cross_colormap`
- `quality_limited`

Report subgroup results separately. The included color-robustness script provides an additional controlled stress test.

## Label-definition concern: lines versus mixed

The visual boundary between `lines` and `mixed` is not consistently obvious from the folder names alone. Several line images are labyrinthine or locally disordered, while several mixed images are also dominated by short or curved line segments.

This does not mean the labels are wrong. It means the paper needs an operational labeling rule. Before freezing the set:

1. Write a one- or two-sentence definition for each class.
2. Have at least one AFM/polymer-domain expert review every image without seeing the model output.
3. Record disagreements and how they were resolved.
4. Mark the completed review in `label_review_status`.

Do not use CNN confidence to decide the ground-truth label.

## Publication-panel and provenance concerns

`dots/dot_01.png` contains the panel label `(a)` in the upper-right corner, suggesting at least some images may have been cropped from published figures.

For every image, record:

- source paper or dataset
- DOI or stable URL
- figure/panel number
- whether redistribution is permitted
- source/sample grouping

You may be able to evaluate copyrighted images for research, but that does not automatically grant permission to publish the image files in the GitHub repository or release them as a dataset.

If several images are crops from the same AFM scan, sample, or publication figure, they should share a `source_group_id`; otherwise the set may overstate the number of independent observations.

## What is safe to do next

1. Complete the supplied `test_manifest.csv` before running the formal script.
2. Exclude the three development duplicates from the primary result unless you can document that they played no role in model development.
3. Keep all other decisions independent of model output.
4. Run the full 56-image result and the frozen 53-image primary result; report both transparently.
5. Treat cross-colormap performance as a separate robustness result rather than silently mixing it with same-domain accuracy.
