from pathlib import Path
import argparse
import csv
import numpy as np

METRICS = [
    "dice",
    "iou",
    "pixel_precision",
    "pixel_recall",
    "specificity",
    "pixel_accuracy",
]

def percentile_ci(values, confidence=0.95):
    alpha = 1.0 - confidence
    lower = np.quantile(values, alpha / 2)
    upper = np.quantile(values, 1 - alpha / 2)
    return float(lower), float(upper)

def class_from_relative_path(relative_path):
    return Path(relative_path).parts[0].lower()

def main():
    parser = argparse.ArgumentParser(
        description="Image-level stratified bootstrap confidence intervals for segmentation metrics."
    )
    parser.add_argument(
        "--input",
        default="segmentation_per_image_metrics_final.csv",
        help="Per-image segmentation metrics CSV.",
    )
    parser.add_argument(
        "--output-dir",
        default="evaluation_outputs/experiment_2_segmentation/bootstrap",
        help="Directory for bootstrap outputs.",
    )
    parser.add_argument("--iterations", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260622)
    parser.add_argument("--confidence", type=float, default=0.95)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise ValueError("The input CSV is empty.")

    for row in rows:
        row["class_label"] = class_from_relative_path(row["relative_path"])
        for metric in METRICS:
            row[metric] = float(row[metric])

    classes = sorted({row["class_label"] for row in rows})
    grouped = {
        class_name: [row for row in rows if row["class_label"] == class_name]
        for class_name in classes
    }

    rng = np.random.default_rng(args.seed)

    # Overall bootstrap: preserve the original number of images in each class.
    overall_replicates = {metric: np.empty(args.iterations) for metric in METRICS}

    for iteration in range(args.iterations):
        sampled_rows = []
        for class_name, class_rows in grouped.items():
            indices = rng.integers(0, len(class_rows), size=len(class_rows))
            sampled_rows.extend(class_rows[index] for index in indices)

        for metric in METRICS:
            overall_replicates[metric][iteration] = np.mean(
                [row[metric] for row in sampled_rows]
            )

    overall_output = []
    for metric in METRICS:
        observed = float(np.mean([row[metric] for row in rows]))
        standard_deviation = float(
            np.std([row[metric] for row in rows], ddof=1)
        )
        median = float(np.median([row[metric] for row in rows]))
        lower, upper = percentile_ci(
            overall_replicates[metric], args.confidence
        )
        overall_output.append({
            "metric": metric,
            "n_images": len(rows),
            "observed_mean": observed,
            "standard_deviation": standard_deviation,
            "median": median,
            "confidence_level": args.confidence,
            "bootstrap_iterations": args.iterations,
            "bootstrap_seed": args.seed,
            "bootstrap_method": "image_level_stratified_percentile",
            "ci_lower": lower,
            "ci_upper": upper,
        })

    overall_path = output_dir / "bootstrap_confidence_intervals.csv"
    with overall_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=overall_output[0].keys())
        writer.writeheader()
        writer.writerows(overall_output)

    # Class-specific bootstrap confidence intervals.
    class_output = []
    for class_name, class_rows in grouped.items():
        for metric in METRICS:
            observed_values = np.array(
                [row[metric] for row in class_rows], dtype=float
            )
            bootstrap_means = np.empty(args.iterations)
            for iteration in range(args.iterations):
                indices = rng.integers(
                    0, len(class_rows), size=len(class_rows)
                )
                bootstrap_means[iteration] = observed_values[indices].mean()

            lower, upper = percentile_ci(
                bootstrap_means, args.confidence
            )
            class_output.append({
                "class_label": class_name,
                "metric": metric,
                "n_images": len(class_rows),
                "observed_mean": float(observed_values.mean()),
                "standard_deviation": float(
                    observed_values.std(ddof=1)
                    if len(observed_values) > 1 else 0.0
                ),
                "median": float(np.median(observed_values)),
                "confidence_level": args.confidence,
                "bootstrap_iterations": args.iterations,
                "bootstrap_seed": args.seed,
                "bootstrap_method": "image_level_within_class_percentile",
                "ci_lower": lower,
                "ci_upper": upper,
            })

    class_path = output_dir / "bootstrap_class_confidence_intervals.csv"
    with class_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=class_output[0].keys())
        writer.writeheader()
        writer.writerows(class_output)

    # Optional raw replicate means for reproducibility / plotting.
    replicate_path = output_dir / "bootstrap_replicate_means.csv"
    with replicate_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["replicate"] + METRICS
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for iteration in range(args.iterations):
            row = {"replicate": iteration + 1}
            for metric in METRICS:
                row[metric] = overall_replicates[metric][iteration]
            writer.writerow(row)

    print(f"Saved: {overall_path}")
    print(f"Saved: {class_path}")
    print(f"Saved: {replicate_path}")

if __name__ == "__main__":
    main()
