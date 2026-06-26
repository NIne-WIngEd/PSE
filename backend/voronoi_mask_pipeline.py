import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image
import warnings
warnings.filterwarnings("ignore")

# Configure matplotlib to use a non-interactive backend.
import matplotlib
matplotlib.use('Agg')  # Must be before importing pyplot or voronoi_v7
import matplotlib.pylab as pylab

# Matplotlib params to match run_image_analysis_knn
params = {
    'legend.fontsize': 'x-large',
    'axes.labelsize': 'x-large',
    'axes.titlesize': 'x-large',
    'xtick.labelsize': 'x-large',
    'ytick.labelsize': 'x-large'
}
pylab.rcParams.update(params)

import skimage
from skimage import color

import voronoi_v7


def _score_dot_extraction(
    mask_path: str,
    *,
    invert_mask: bool,
    min_circularity: float,
    max_aspect_ratio: float,
    min_area: int,
    max_area: int,
) -> Tuple[int, int]:
    """Return (kept_features, total_features) for a given mask polarity."""
    import cv2
    from skimage.measure import label, regionprops

    img = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return (0, 0)

    if invert_mask:
        img = 255 - img

    _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    labels_img = label(opened == 255)
    props = regionprops(labels_img)

    kept = 0
    for prop in props:
        area = prop.area
        perimeter = prop.perimeter
        circularity = 4 * np.pi * area / (perimeter**2) if perimeter > 0 else 0.0
        aspect = (
            prop.major_axis_length / prop.minor_axis_length
            if prop.minor_axis_length > 0
            else float("inf")
        )

        if (
            min_area <= area <= max_area
            and circularity >= min_circularity
            and aspect <= max_aspect_ratio
        ):
            kept += 1

    return (kept, len(props))


def _guess_invert_mask(mask_path: str, dot_params: Dict[str, Any]) -> bool:
    """Try both polarities and pick the one that keeps more dots."""
    kept_false, total_false = _score_dot_extraction(
        mask_path, invert_mask=False, **dot_params
    )
    kept_true, total_true = _score_dot_extraction(
        mask_path, invert_mask=True, **dot_params
    )

    if kept_true > kept_false:
        return True
    if kept_false > kept_true:
        return False

    if total_true > total_false:
        return True
    return False


def extract_dots_from_mask(
    mask_path: str,
    output_path: str,
    *,
    min_circularity: float = 0.6,
    max_aspect_ratio: float = 1.8,
    min_area: int = 15,
    max_area: int = 400,
    invert_mask: bool = False,
) -> Dict[str, Any]:
    """Extract dot-like features from a binary mask and write a dots-only image.

    Output is a black image with standardized 5x5 white dots.
    """
    import cv2
    from skimage.measure import label, regionprops

    img = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not read mask image: {mask_path}")

    if invert_mask:
        img = 255 - img

    _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    labels_img = label(opened == 255)
    props = regionprops(labels_img)

    output = np.zeros_like(binary)
    kept = 0

    for prop in props:
        area = prop.area
        perimeter = prop.perimeter
        circularity = 4 * np.pi * area / (perimeter**2) if perimeter > 0 else 0.0
        aspect = (
            prop.major_axis_length / prop.minor_axis_length
            if prop.minor_axis_length > 0
            else float("inf")
        )

        if (
            min_area <= area <= max_area
            and circularity >= min_circularity
            and aspect <= max_aspect_ratio
        ):
            cy, cx = map(int, prop.centroid)
            y1, y2 = max(cy - 2, 0), min(cy + 3, output.shape[0])
            x1, x2 = max(cx - 2, 0), min(cx + 3, output.shape[1])
            output[y1:y2, x1:x2] = 255
            kept += 1

    os.makedirs(str(Path(output_path).parent), exist_ok=True)
    ok = cv2.imwrite(output_path, output)
    if not ok:
        raise IOError(f"Failed to write dots image: {output_path}")

    total = len(props)
    return {
        "output_path": output_path,
        "total_features": total,
        "kept_features": kept,
        "rejected_features": total - kept,
    }


def pick_best_voronoi_images(voronoi_root: Path, image_stem: str) -> Tuple[str, str, str, str]:
    """Pick a small set of key output images if present."""
    folder = voronoi_root / image_stem
    if not folder.exists():
        return "", "", "", ""

    pngs = sorted(folder.glob("*.png"))
    if not pngs:
        return "", "", "", ""

    def _first_contains(substr: str) -> Optional[Path]:
        substr = substr.lower()
        return next((p for p in pngs if substr in p.name.lower()), None)

    voronoi_overlay = _first_contains("voronoi_overlay")
    morphology_map = _first_contains("morphology_map")
    snapshot = _first_contains("snapshot")
    original = _first_contains("original")

    return (
        str(voronoi_overlay) if voronoi_overlay else "",
        str(morphology_map) if morphology_map else "",
        str(snapshot) if snapshot else "",
        str(original) if original else "",
    )


def get_voronoi_stats(voronoi_root: Path, image_stem: str) -> Dict[str, Any]:
    """Read all txt outputs into a dict (keyed by stem)."""
    folder = voronoi_root / image_stem
    if not folder.exists():
        return {}

    stats: Dict[str, Any] = {}
    for txt_file in sorted(folder.glob("*.txt")):
        try:
            stats[txt_file.stem] = txt_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass
    return stats


def collect_all_outputs(voronoi_root: Path, image_stem: str) -> Dict[str, List[str]]:
    """Collect all paths under the voronoi output folder for an image."""
    folder = voronoi_root / image_stem
    if not folder.exists():
        return {"png": [], "txt": [], "all": []}

    pngs = [str(p) for p in sorted(folder.glob("*.png"))]
    txts = [str(p) for p in sorted(folder.glob("*.txt"))]
    others = [
        str(p)
        for p in sorted(folder.glob("*"))
        if p.suffix.lower() not in {".png", ".txt"}
    ]
    return {"png": pngs, "txt": txts, "all": pngs + txts + others}


def load_image(image_path, max_size=1024, *, invert: bool = True):
    """Load image as grayscale float array, optionally inverted."""
    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    try:
        im = Image.open(image_path)
        im = im.convert("RGB")

        gray = color.rgb2gray(skimage.img_as_float(im))
        data = (1 - gray) if invert else gray
        im.close()

        print(f"Loaded image: {image_path.name}")

        original_shape = data.shape
        if max_size is not None and (data.shape[0] > max_size or data.shape[1] > max_size):
            h, w = data.shape
            scale = max_size / max(h, w)
            new_h, new_w = int(h * scale), int(w * scale)
            from skimage.transform import resize
            data = resize(data, (new_h, new_w), anti_aliasing=True, preserve_range=True)
            print(f"  ⚠ Downsampled from {original_shape} to {data.shape} for faster processing")

        print(f"  Shape: {data.shape}")
        print(f"  Data type: {data.dtype}")
        print(f"  Value range: [{data.min():.3f}, {data.max():.3f}]")
        print(f"  Inverted grayscale: {invert}")

        if data.ndim != 2:
            raise ValueError(f"Expected 2D image, got shape {data.shape}")

        return data

    except Exception as e:
        raise ValueError(f"Failed to load image: {e}")


def _run_voronoi_analysis_direct(
    image_path,
    image_size=1.0,
    output_dir='voronoi_outputs',
    threshold_edge=0.025,
    max_size=1024,
    *,
    invert: bool = True,
):
    """Run Voronoi analysis directly on an input image."""
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print("Loading Image")
    print(f"{'='*60}")

    try:
        image_data = load_image(image_path, max_size=max_size, invert=invert)
    except (FileNotFoundError, ValueError) as e:
        print(f"\n✗ Error: {e}")
        return None

    image_name = Path(image_path).stem

    print(f"\n{'='*60}")
    print("Running Voronoi Analysis")
    print(f"{'='*60}")
    print(f"Image: {image_name}")
    print(f"Image size (real-world): {image_size} μm")
    print(f"Threshold edge: {threshold_edge}")
    print(f"Invert grayscale: {invert}")
    print(f"Output directory: {output_dir}")
    print(f"{'='*60}\n")

    try:
        results_dict = voronoi_v7.analyze_image(
            image_data=image_data,
            image_name=image_name,
            image_size=image_size,
            save_image=True,
            show_image=False,
            save_location=output_dir,
            threshold_edge=threshold_edge,
        )

        print(f"\n{'='*60}")
        print("Analysis Results")
        print(f"{'='*60}")
        for key, value in results_dict.items():
            if isinstance(value, float):
                print(f"{key:25s}: {value:.4f}")
            else:
                print(f"{key:25s}: {value}")
        print(f"{'='*60}\n")

        output_path = Path(output_dir) / image_name
        print("✓ Analysis complete!")
        print(f"Results saved to: {output_path}/")
        print("\nGenerated files:")
        if output_path.exists():
            for file in sorted(output_path.glob('*')):
                print(f"  - {file.name}")

        return results_dict

    except Exception as e:
        print(f"\n✗ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_voronoi_analysis_on_image(
    image_path: str,
    image_size: float = 1.0,
    output_dir: str = "voronoi_outputs",
    threshold_edge: float = 0.025,
    max_size: int = 1024,
    *,
    invert: bool = True,
):
    """Direct Voronoi analysis on an input image (no dot extraction)."""
    return _run_voronoi_analysis_direct(
        image_path=image_path,
        image_size=image_size,
        output_dir=output_dir,
        threshold_edge=threshold_edge,
        max_size=max_size,
        invert=invert,
    )


def run_voronoi_analysis(
    mask_path: str,
    image_size: float = 1.0,
    threshold_edge: float = 0.025,
    max_size: int = 1024,
    *,
    output_dir: Optional[str] = None,
    invert_mask: Optional[bool] = None,
    invert_grayscale: bool = True,
    dot_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run dot-extraction + Voronoi starting from a mask image."""
    mask_p = Path(mask_path)
    if not mask_p.exists():
        raise FileNotFoundError(f"Mask not found: {mask_path}")

    job_dir = mask_p.parent

    params = {
        "min_circularity": 0.35,
        "max_aspect_ratio": 3.5,
        "min_area": 8,
        "max_area": 600,
    }
    if dot_params:
        params.update(dot_params)

    if invert_mask is None:
        invert_mask = _guess_invert_mask(
            str(mask_p),
            {
                "min_circularity": float(params["min_circularity"]),
                "max_aspect_ratio": float(params["max_aspect_ratio"]),
                "min_area": int(params["min_area"]),
                "max_area": int(params["max_area"]),
            },
        )

    params["invert_mask"] = bool(invert_mask)

    dots_mask_path = str(job_dir / f"{mask_p.stem}_DOTS_ONLY.png")
    dot_stats = extract_dots_from_mask(str(mask_p), dots_mask_path, **params)

    if int(dot_stats.get("kept_features", 0)) < 4:
        return {
            "mask_path": str(mask_p),
            "invert_mask_used": bool(invert_mask),
            "invert_grayscale_used": bool(invert_grayscale),
            "dots_mask_path": dots_mask_path,
            "dot_extraction_stats": dot_stats,
            "ran_voronoi": False,
            "reason": "Insufficient dots for Voronoi analysis (need 4+)",
            "selected_images": {
                "voronoi_overlay": "",
                "morphology_map": "",
                "snapshot": "",
                "original": "",
            },
            "all_outputs": {"png": [], "txt": [], "all": []},
            "voronoi_stats_txt": {},
        }

    vor_dir = Path(output_dir).expanduser().resolve() if output_dir else job_dir / "voronoi_outputs"
    vor_dir.mkdir(parents=True, exist_ok=True)

    results = _run_voronoi_analysis_direct(
        image_path=dots_mask_path,
        image_size=image_size,
        output_dir=str(vor_dir),
        threshold_edge=threshold_edge,
        max_size=max_size,
        invert=invert_grayscale,
    )

    stem = Path(dots_mask_path).stem
    voronoi_overlay, morphology_map, snapshot, original = pick_best_voronoi_images(vor_dir, stem)

    # Trust actual generated files for UI display
    ran_voronoi = bool(voronoi_overlay or morphology_map or snapshot or original)

    return {
        "mask_path": str(mask_p),
        "invert_mask_used": bool(invert_mask),
        "invert_grayscale_used": bool(invert_grayscale),
        "dots_mask_path": dots_mask_path,
        "dot_extraction_stats": dot_stats,
        "ran_voronoi": ran_voronoi,
        "reason": "" if ran_voronoi else "Voronoi image files were not found",
        "voronoi_dir": str(vor_dir),
        "voronoi_results": results or {},
        "selected_images": {
            "voronoi_overlay": voronoi_overlay,
            "morphology_map": morphology_map,
            "snapshot": snapshot,
            "original": original,
        },
        "all_outputs": collect_all_outputs(vor_dir, stem),
        "voronoi_stats_txt": get_voronoi_stats(vor_dir, stem),
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Extract dot-like components from a mask and run Voronoi analysis."
    )
    parser.add_argument("mask_path", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("voronoi_outputs"))
    parser.add_argument("--image-size", type=float, default=1.0)
    parser.add_argument("--threshold-edge", type=float, default=0.025)
    parser.add_argument("--max-size", type=int, default=1024)
    args = parser.parse_args()

    output = run_voronoi_analysis(
        str(args.mask_path),
        image_size=args.image_size,
        output_dir=str(args.output_dir),
        threshold_edge=args.threshold_edge,
        max_size=args.max_size,
    )
    print(json.dumps(output, indent=2, default=str))
