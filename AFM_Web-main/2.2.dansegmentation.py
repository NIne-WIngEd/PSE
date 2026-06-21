import os
from pathlib import Path
import numpy as np
import cv2
import pandas as pd
import matplotlib.pyplot as plt
from scipy.ndimage import distance_transform_edt, label as scipy_label
from skimage.morphology import skeletonize
from skimage.filters import threshold_niblack
from PIL import Image


def binarize_image(
    image_path,
    method="adaptive",
    output_path=None,
    output_dir="binarized",
    # Adaptive threshold parameters
    adaptive_method="gaussian",
    block_size=11,
    C=2,
    # Niblack parameters
    niblack_window=25,
    k=0.1,
    # Preprocessing
    blur="none",
    blur_ksize=5,
    equalize=False,
    clahe=False,
    # Combination
    combine_mode="OR",
    alpha=0.5,
):

    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    print(f"\n{'='*60}")
    print("Dan's Binarization")
    print(f"{'='*60}")
    print(f"Image: {image_path.name}")
    print(f"Method: {method}")

    # Load image
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Failed to load image: {image_path}")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    processed = gray.copy()

    # Preprocessing
    if equalize:
        processed = cv2.equalizeHist(processed)
        print("  Preprocessing: Histogram equalization")

    if clahe:
        clahe_obj = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        processed = clahe_obj.apply(processed)
        print("  Preprocessing: CLAHE")

    if blur == "gaussian":
        processed = cv2.GaussianBlur(processed, (blur_ksize, blur_ksize), 0)
        print(f"  Preprocessing: Gaussian blur (kernel={blur_ksize})")
    elif blur == "median":
        processed = cv2.medianBlur(processed, blur_ksize)
        print(f"  Preprocessing: Median blur (kernel={blur_ksize})")
    elif blur == "bilateral":
        processed = cv2.bilateralFilter(processed, 9, 75, 75)
        print(f"  Preprocessing: Bilateral filter")

    # Thresholding
    thresh_adaptive = None
    thresh_niblack = None

    if method in ["adaptive", "both"]:
        method_flag = (
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C
            if adaptive_method == "gaussian"
            else cv2.ADAPTIVE_THRESH_MEAN_C
        )
        thresh_adaptive = cv2.adaptiveThreshold(
            processed, 255, method_flag, cv2.THRESH_BINARY_INV, block_size, C
        )
        print(
            f"  Adaptive threshold: method={adaptive_method}, block_size={block_size}, C={C}"
        )

    if method in ["niblack", "both"]:
        t_niblack = threshold_niblack(processed, window_size=niblack_window, k=k)
        thresh_niblack = (processed < t_niblack).astype(np.uint8) * 255
        print(f"  Niblack threshold: window={niblack_window}, k={k}")

    # Combine or select
    if method == "adaptive":
        final = thresh_adaptive
    elif method == "niblack":
        final = thresh_niblack
    elif method == "both":
        if combine_mode == "AND":
            final = cv2.bitwise_and(thresh_adaptive, thresh_niblack)
        elif combine_mode == "OR":
            final = cv2.bitwise_or(thresh_adaptive, thresh_niblack)
        elif combine_mode == "adaptive":
            final = thresh_adaptive
        elif combine_mode == "niblack":
            final = thresh_niblack
        elif combine_mode == "weighted":
            blend = alpha * thresh_adaptive.astype(np.float32) + (
                1 - alpha
            ) * thresh_niblack.astype(np.float32)
            final = (blend > 127).astype(np.uint8) * 255
        print(f"  Combination: {combine_mode}")

    # Calculate statistics
    blk_px_percent = np.sum(final == 255) / final.size * 100
    print(f"  Black pixels: {blk_px_percent:.1f}%")

    # Save
    if output_path is None:
        os.makedirs(output_dir, exist_ok=True)
        output_path = Path(output_dir) / f"{image_path.stem}_binary.png"

    cv2.imwrite(str(output_path), final)

    print(f"\n✓ Binary mask saved to: {output_path}")
    print(f"{'='*60}\n")

    return str(output_path)


def calculate_pixel_size(image_shape, image_size_um):
    return (image_size_um / image_shape[0]) * 1000


def ensure_minority_phase_black(binary_img, invert=False):

    count_black = np.sum(binary_img == 0)
    count_white = np.size(binary_img) - count_black

    # Invert if white is minority (automatic detection)
    if count_white < count_black:
        binary_img = 255 - binary_img

    # Apply manual inversion if requested
    if invert:
        binary_img = 255 - binary_img

    return binary_img


def label_black_regions(binary_img):
    black_mask = binary_img == 0
    region_labels, _ = scipy_label(black_mask)
    return black_mask, region_labels


def compute_voronoi_distances(black_mask, region_labels):
    dist_transform, (inds_y, inds_x) = distance_transform_edt(
        ~black_mask, return_indices=True
    )
    nearest_labels = region_labels[inds_y, inds_x]
    return dist_transform, nearest_labels


def extract_voronoi_boundaries(nearest_labels, black_mask):
    """Extract Voronoi boundaries between features."""
    padded = np.pad(nearest_labels, 1, mode="edge")

    # Find pixels with different nearest neighbors
    boundary_mask = (
        (padded[1:-1, 1:-1] != padded[:-2, 1:-1])  # up
        | (padded[1:-1, 1:-1] != padded[2:, 1:-1])  # down
        | (padded[1:-1, 1:-1] != padded[1:-1, :-2])  # left
        | (padded[1:-1, 1:-1] != padded[1:-1, 2:])  # right
    )

    # Keep boundaries in white regions only
    skeleton_mask = boundary_mask & (~black_mask)

    # Thin to 1-pixel skeleton
    skeleton_mask = skeletonize(skeleton_mask)

    return skeleton_mask


def calculate_spacing_values(skeleton_mask, dist_transform, pixel_size_nm):
    diameter_px = 2.0 * dist_transform[skeleton_mask]
    diameter_nm = diameter_px * pixel_size_nm

    # Filter valid values
    valid_diameters = diameter_nm[np.isfinite(diameter_nm) & (diameter_nm > 0)]

    return valid_diameters


def save_visualizations(
    binary_img, skeleton_mask, dist_transform, spacing_values, filename, output_dir
):

    os.makedirs(output_dir, exist_ok=True)

    # === Histogram ===
    if len(spacing_values) > 0:
        fig, ax = plt.subplots(figsize=(6, 4), dpi=150)

        mean_val = float(np.mean(spacing_values))
        median_val = float(np.median(spacing_values))

        ax.hist(
            spacing_values,
            bins=30,
            density=True,
            color=(1.0, 213 / 255.0, 73 / 255.0),
            edgecolor="black",
            alpha=0.7,
        )
        ax.axvline(
            mean_val, color="red", linestyle="--", label=f"Mean: {mean_val:.1f} nm"
        )
        ax.axvline(
            median_val,
            color="blue",
            linestyle="--",
            label=f"Median: {median_val:.1f} nm",
        )

        ax.set_xlabel("Inter-feature spacing (nm)", fontsize=12)
        ax.set_ylabel("Probability Density", fontsize=12)
        ax.set_title(f"{filename} — Voronoi Spacing", fontsize=14)
        ax.legend()
        ax.grid(alpha=0.3)

        fig.tight_layout()
        hist_path = os.path.join(output_dir, f"{filename}_spacing_histogram.png")
        fig.savefig(hist_path)
        plt.close(fig)

    # === Skeleton Overlay ===
    h, w = binary_img.shape[:2]
    fig, ax = plt.subplots(figsize=(6, 6), dpi=150)

    ax.imshow(binary_img, cmap="gray", vmin=0, vmax=255, origin="lower")

    # Overlay skeleton
    overlay = np.zeros((h, w, 4), dtype=float)
    overlay[..., :3] = (1.0, 213 / 255.0, 73 / 255.0)  # RGB
    overlay[..., 3] = 0.0
    overlay[skeleton_mask, 3] = 1.0

    ax.imshow(overlay, origin="lower")
    ax.set_title(f"{filename} — Voronoi Skeleton", fontsize=14)
    ax.axis("off")

    fig.tight_layout()
    overlay_path = os.path.join(output_dir, f"{filename}_voronoi_overlay.png")
    fig.savefig(overlay_path)
    plt.close(fig)


def analyze_spacing(
    image_path,
    image_size_um=2.0,
    output_dir="spacing_output",
    invert=False,
    save_viz=True,
):

    # Load image
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    print(f"\n{'='*60}")
    print("Voronoi Spacing Analysis")
    print(f"{'='*60}")
    print(f"Image: {image_path.name}")

    # Read as grayscale
    binary_img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if binary_img is None:
        raise ValueError(f"Failed to load image: {image_path}")

    print(f"Size: {binary_img.shape[0]}x{binary_img.shape[1]}")

    # Calculate pixel size
    pixel_size_nm = calculate_pixel_size(binary_img.shape, image_size_um)
    print(f"Pixel size: {pixel_size_nm:.3f} nm/pixel")

    # Ensure features are black
    binary_img = ensure_minority_phase_black(binary_img, invert=invert)

    # Voronoi analysis pipeline
    print("Computing Voronoi boundaries...")
    black_mask, region_labels = label_black_regions(binary_img)
    dist_transform, nearest_labels = compute_voronoi_distances(
        black_mask, region_labels
    )
    skeleton_mask = extract_voronoi_boundaries(nearest_labels, black_mask)
    spacing_values = calculate_spacing_values(
        skeleton_mask, dist_transform, pixel_size_nm
    )

    if len(spacing_values) == 0:
        print("⚠ Warning: No spacing values computed (no features detected)")
        return None

    # Calculate statistics
    results = {
        "filename": image_path.name,
        "mean_spacing_nm": float(np.mean(spacing_values)),
        "median_spacing_nm": float(np.median(spacing_values)),
        "std_spacing_nm": float(np.std(spacing_values)),
        "min_spacing_nm": float(np.min(spacing_values)),
        "max_spacing_nm": float(np.max(spacing_values)),
        "num_measurements": len(spacing_values),
    }

    # Print results
    print(f"\n{'='*60}")
    print("Results")
    print(f"{'='*60}")
    print(f"Mean spacing:      {results['mean_spacing_nm']:.2f} nm")
    print(f"Median spacing:    {results['median_spacing_nm']:.2f} nm")
    print(f"Std deviation:     {results['std_spacing_nm']:.2f} nm")
    print(f"Min spacing:       {results['min_spacing_nm']:.2f} nm")
    print(f"Max spacing:       {results['max_spacing_nm']:.2f} nm")
    print(f"Measurements:      {results['num_measurements']}")
    print(f"{'='*60}\n")

    # Save visualizations
    if save_viz:
        filename_stem = image_path.stem
        save_visualizations(
            binary_img,
            skeleton_mask,
            dist_transform,
            spacing_values,
            filename_stem,
            output_dir,
        )
        print(f"Visualizations saved to: {output_dir}/")

    return results


def analyze_spacing_batch(
    folder_path,
    image_size_um=2.0,
    output_dir="spacing_output",
    extensions=(".png", ".jpg", ".tif"),
    csv_output="spacing_results.csv",
):

    folder_path = Path(folder_path)

    # Find all images
    image_files = []
    for ext in extensions:
        image_files.extend(folder_path.glob(f"*{ext}"))
        image_files.extend(folder_path.glob(f"*{ext.upper()}"))

    image_files = sorted(image_files)

    if len(image_files) == 0:
        print(f"No images found in {folder_path}")
        return None

    print(f"\nFound {len(image_files)} images")
    print(f"{'='*60}\n")

    # Process each image
    all_results = []
    for img_path in image_files:
        try:
            result = analyze_spacing(
                img_path,
                image_size_um=image_size_um,
                output_dir=output_dir,
                save_viz=True,
            )
            if result is not None:
                all_results.append(result)
        except Exception as e:
            print(f"✗ Error processing {img_path.name}: {e}\n")

    # Save to CSV
    if len(all_results) > 0:
        df = pd.DataFrame(all_results)
        csv_path = Path(output_dir) / csv_output
        df.to_csv(csv_path, index=False)
        print(f"\n{'='*60}")
        print(f"✓ Batch processing complete!")
        print(f"{'='*60}")
        print(f"Processed: {len(all_results)}/{len(image_files)} images")
        print(f"Results saved to: {csv_path}")
        return df
    else:
        print("No successful results to save.")
        return None


if __name__ == "__main__":
    from pathlib import Path
    
    # Use relative paths
    script_dir = Path(__file__).parent
    test_image = script_dir / "Cnn_classifier_test" / "dots.png"
    
    binarize_image(
        image_path=str(test_image),
        method="adaptive",
        adaptive_method="gaussian",
        block_size=11,
        C=2,
        output_dir="binarized",
    )
