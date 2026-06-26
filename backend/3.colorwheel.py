"""Optimized orientation-based ColorWheel analysis for AFM segmentation masks.

The public ``analyze_image`` interface is backward compatible with the original
module while adding full-resolution output processing, bounded pixel-sampled clustering,
and vectorized connected-component analysis.
"""
from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from skimage.morphology import skeletonize


def check_cupy_available() -> bool:
    try:
        import cupy  # noqa: F401
        return True
    except ImportError:
        return False


def _resize_to_max_dimension(image: np.ndarray, max_dimension: int) -> tuple[np.ndarray, float]:
    """Resize only when max_dimension is positive; 0 preserves full resolution."""
    if max_dimension <= 0:
        return image, 1.0
    height, width = image.shape[:2]
    longest = max(height, width)
    if longest <= max_dimension:
        return image, 1.0
    scale = max_dimension / float(longest)
    new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return cv2.resize(image, new_size, interpolation=cv2.INTER_NEAREST), scale


def _foreground_from_mask(gray: np.ndarray) -> np.ndarray:
    """Return morphology foreground; project masks use black foreground."""
    return gray < 128


def compute_average_angle(image_path: str | os.PathLike[str], max_dimension: int = 1024) -> float:
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")
    image, _ = _resize_to_max_dimension(image, max_dimension)
    foreground = _foreground_from_mask(image)
    skeleton = skeletonize(foreground, method="lee").astype(np.uint8) * 255
    contours, _ = cv2.findContours(skeleton, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    angles: list[float] = []
    for contour in contours:
        for index in range(0, max(0, len(contour) - 10), 10):
            subcontour = contour[index:index + 10]
            if len(subcontour) >= 2:
                dx = float(subcontour[-1, 0, 0] - subcontour[0, 0, 0])
                dy = float(subcontour[-1, 0, 1] - subcontour[0, 0, 1])
                if dx != 0.0 or dy != 0.0:
                    angles.append(math.atan2(dy, dx))

    if not angles:
        return 0.0
    # Axial circular mean: line orientation repeats every 180 degrees.
    doubled = np.asarray(angles, dtype=np.float64) * 2.0
    mean_angle = 0.5 * math.atan2(float(np.sin(doubled).mean()), float(np.cos(doubled).mean()))
    return math.degrees(mean_angle)


class ColorWheelProcessor:
    def __init__(self, binarized_image: np.ndarray, gpu_accelerated: bool, color_wheel_origin: float = 0):
        self.binarized_image = binarized_image
        self.sym = 2
        self.color = 5
        self.brightness = 1
        self.contrast = 5
        self.gpu_accelerated = gpu_accelerated
        self.color_wheel_origin = math.radians(color_wheel_origin)
        self.cp = __import__("cupy") if gpu_accelerated else np

    def process_image(self) -> Image.Image:
        data = np.asarray(self.binarized_image, dtype=np.uint8)
        wheel = self._build_color_wheel(data.shape[0], data.shape[1], self.sym)
        processed = self._apply_fft_color_wheel(wheel, data)
        processed -= np.min(processed)
        max_value = float(np.max(processed)) if processed.size else 0.0
        if max_value > 0:
            processed = processed / max_value * 255.0
        else:
            processed = np.zeros_like(processed)
        image = Image.fromarray(np.uint8(np.clip(processed, 0, 255)))
        image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
        image = ImageEnhance.Color(image).enhance(self.color)
        image = ImageEnhance.Brightness(image).enhance(self.brightness)
        image = ImageEnhance.Contrast(image).enhance(self.contrast)
        return image

    def _build_color_wheel(self, nx: int, ny: int, sym: int):
        cp = self.cp
        cda = cp.ones((nx, ny, 2))
        cx = cp.linspace(-nx, nx, nx)
        cy = cp.linspace(-ny, ny, ny)
        cxx, cyy = cp.meshgrid(cy, cx)
        czz = (((cp.arctan2(cxx, cyy) - self.color_wheel_origin) / math.pi + 1.0) / 2.0) * sym
        carr = cp.dstack((czz, cda))
        chi = cp.floor(carr[..., 0] * 6)
        fraction = carr[..., 0] * 6 - chi
        p = carr[..., 2] * (1 - carr[..., 1])
        q = carr[..., 2] * (1 - fraction * carr[..., 1])
        t = carr[..., 2] * (1 - (1 - fraction) * carr[..., 1])
        v = carr[..., 2]
        chi = cp.stack([chi, chi, chi], axis=-1).astype(cp.uint8) % 6
        out = cp.choose(
            chi,
            cp.stack([
                cp.stack((v, t, p), axis=-1), cp.stack((q, v, p), axis=-1),
                cp.stack((p, v, t), axis=-1), cp.stack((p, q, v), axis=-1),
                cp.stack((t, p, v), axis=-1), cp.stack((v, p, q), axis=-1),
            ]),
        )
        return cp.asnumpy(out) if self.gpu_accelerated else out

    def _apply_fft_color_wheel(self, wheel, image):
        cp = self.cp
        image_cp = cp.asarray(image)
        fft_image = cp.fft.fft2(image_cp)
        wheel = cp.fft.fftshift(wheel)
        magnitude = cp.repeat(cp.abs(fft_image)[:, :, cp.newaxis], 3, axis=2)
        phase = cp.repeat(cp.angle(fft_image)[:, :, cp.newaxis], 3, axis=2)
        combined = wheel * magnitude * cp.exp(1j * phase)
        processed = cp.zeros((*image.shape, 3), dtype=cp.float64)
        for channel in range(3):
            channel_data = cp.real(cp.fft.ifft2(combined[:, :, channel]))
            channel_data -= cp.min(channel_data)
            denominator = cp.max(channel_data)
            if float(denominator) > 0:
                channel_data /= denominator
            processed[:, :, channel] = channel_data
        return cp.asnumpy(processed) if self.gpu_accelerated else processed


class PhaseSubtraction:
    def __init__(self, input_image: Image.Image, foreground_mask: np.ndarray):
        self.input_image = input_image
        self.foreground_mask = foreground_mask.astype(bool)

    def subtract_black_from_input(self) -> Image.Image:
        input_array = np.asarray(self.input_image)
        result = np.full_like(input_array, 255)
        result[self.foreground_mask] = input_array[self.foreground_mask]
        return Image.fromarray(result.astype(np.uint8))


class ColorMaskProcessor:
    def __init__(
        self,
        input_image: Image.Image,
        foreground_mask: np.ndarray,
        output_path: str | os.PathLike[str],
        num_clusters: int,
        random_state: int = 42,
        max_fit_samples: int = 50_000,
        min_component_size: int = 15,
    ):
        self.input_image = input_image.convert("RGB")
        self.foreground_mask = foreground_mask.astype(bool)
        self.output_path = Path(output_path)
        self.num_clusters = int(num_clusters)
        self.random_state = int(random_state)
        self.max_fit_samples = int(max_fit_samples)
        self.min_component_size = int(min_component_size)
        if self.num_clusters < 1:
            raise ValueError("num_clusters must be at least 1")

    def create_color_masks(self) -> tuple[list[np.ndarray], int]:
        image = np.asarray(self.input_image)
        foreground_pixels = image[self.foreground_mask]
        if foreground_pixels.size == 0:
            return [np.zeros(self.foreground_mask.shape, dtype=bool) for _ in range(self.num_clusters)], 0

        unique_count = len(np.unique(foreground_pixels, axis=0))
        clusters_used = max(1, min(self.num_clusters, unique_count, len(foreground_pixels)))
        rng = np.random.default_rng(self.random_state)
        if len(foreground_pixels) > self.max_fit_samples:
            indices = rng.choice(len(foreground_pixels), self.max_fit_samples, replace=False)
            fit_pixels = foreground_pixels[indices]
        else:
            fit_pixels = foreground_pixels

        # Bounded clustering: fit centers on at most ``max_fit_samples`` pixels,
        # then assign all foreground pixels to the nearest fitted center. OpenCV's
        # implementation is substantially faster than fitting sklearn KMeans on
        # the full image and keeps runtime predictable.
        fit_pixels_f32 = np.asarray(fit_pixels, dtype=np.float32)
        foreground_pixels_f32 = np.asarray(foreground_pixels, dtype=np.float32)
        cv2.setRNGSeed(self.random_state)
        criteria = (
            cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
            30,
            0.5,
        )
        _, _, centers = cv2.kmeans(
            fit_pixels_f32,
            clusters_used,
            None,
            criteria,
            1,
            cv2.KMEANS_PP_CENTERS,
        )
        # Assign every foreground pixel to its nearest center in bounded chunks.
        # This preserves full-resolution output without allocating an enormous
        # N_pixels x N_clusters x 3 temporary array.
        foreground_labels = np.empty(len(foreground_pixels_f32), dtype=np.int16)
        assignment_chunk_size = 100_000
        for start in range(0, len(foreground_pixels_f32), assignment_chunk_size):
            stop = min(start + assignment_chunk_size, len(foreground_pixels_f32))
            chunk = foreground_pixels_f32[start:stop]
            distances = ((chunk[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
            foreground_labels[start:stop] = distances.argmin(axis=1).astype(np.int16)
        label_image = np.full(self.foreground_mask.shape, -1, dtype=np.int16)
        label_image[self.foreground_mask] = foreground_labels
        masks = [(label_image == cluster_id) for cluster_id in range(clusters_used)]
        masks.extend(
            np.zeros(self.foreground_mask.shape, dtype=bool)
            for _ in range(self.num_clusters - clusters_used)
        )
        return masks, clusters_used

    @staticmethod
    def _component_outputs(mask: np.ndarray, cluster_id: int, min_size: int):
        count, labels, stats, _ = cv2.connectedComponentsWithStats(
            mask.astype(np.uint8), connectivity=8
        )
        if count <= 1:
            empty = np.zeros((*mask.shape, 3), dtype=np.uint8)
            return mask & False, empty, {}
        sizes = stats[1:, cv2.CC_STAT_AREA].astype(np.int64)
        valid_component_ids = np.flatnonzero(sizes >= min_size) + 1
        if valid_component_ids.size == 0:
            empty = np.zeros((*mask.shape, 3), dtype=np.uint8)
            return mask & False, empty, {}

        valid_sizes = stats[valid_component_ids, cv2.CC_STAT_AREA].astype(np.int64)
        average_size = float(valid_sizes.mean())
        retained_ids = valid_component_ids[valid_sizes >= average_size]
        if retained_ids.size == 0:
            retained_ids = valid_component_ids

        retained = np.isin(labels, retained_ids)
        rng = np.random.default_rng(10_000 + cluster_id)
        color_lut = np.zeros((count, 3), dtype=np.uint8)
        color_lut[retained_ids] = rng.integers(40, 256, size=(len(retained_ids), 3), dtype=np.uint8)
        colorized = color_lut[labels]
        group_sizes = {
            int(component_id): int(stats[component_id, cv2.CC_STAT_AREA])
            for component_id in retained_ids
        }
        return retained, colorized, group_sizes

    def process_image(self) -> dict[str, Any]:
        self.output_path.mkdir(parents=True, exist_ok=True)
        image = np.asarray(self.input_image)
        masks, clusters_used = self.create_color_masks()
        grain_outputs: list[str] = []
        grain_counts: dict[str, int] = {}

        for cluster_id, cluster_mask in enumerate(masks):
            raw = np.zeros_like(image)
            raw[cluster_mask] = image[cluster_mask]
            Image.fromarray(raw).save(self.output_path / f"mask_{cluster_id}.tiff")

            retained, colorized, group_sizes = self._component_outputs(
                cluster_mask, cluster_id, self.min_component_size
            )
            filtered = np.zeros_like(image)
            filtered[retained] = image[retained]
            Image.fromarray(filtered).save(self.output_path / f"filtered_mask_{cluster_id}.tiff")

            if group_sizes:
                grain_path = self.output_path / f"Mask_{cluster_id}.tiff"
                Image.fromarray(colorized).save(grain_path)
                stats_path = self.output_path / f"grains_{cluster_id}.txt"
                with stats_path.open("w", encoding="utf-8") as handle:
                    for group_id, size in sorted(group_sizes.items()):
                        handle.write(f"Group {group_id}: {size} pixels\n")
                grain_outputs.append(str(grain_path))
                grain_counts[str(cluster_id)] = len(group_sizes)

        return {
            "clusters_used": clusters_used,
            "grain_outputs": grain_outputs,
            "grain_counts": grain_counts,
        }


def analyze_image(
    image_path,
    output_dir="colorwheel_output",
    num_clusters=8,
    max_dimension=0,
    orientation_max_dimension=1024,
    random_state=42,
    max_fit_samples=10_000,
    min_component_size=15,
):
    """Run the optimized ColorWheel analysis.

    By default, output maps remain at the original mask resolution. Only the
    global orientation-angle estimation is bounded to 1024 pixels. Existing
    callers that provide only ``image_path``, ``output_dir`` and
    ``num_clusters`` remain compatible.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    gray_original = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if gray_original is None:
        raise ValueError(f"Could not read image: {image_path}")
    original_height, original_width = gray_original.shape
    # max_dimension=0 preserves the full input dimensions. A positive value can
    # be used only as an explicit safety cap, but the default scientific output
    # remains full resolution.
    gray, scale = _resize_to_max_dimension(gray_original.astype(np.uint8), int(max_dimension))
    foreground = _foreground_from_mask(gray)
    binary = np.where(foreground, 0, 255).astype(np.uint8)

    gpu_accelerated = check_cupy_available()
    # Orientation estimation may use a smaller working copy because it returns
    # a single global angle; all generated maps and components stay full size.
    orientation_angle = compute_average_angle(
        str(image_path), max_dimension=int(orientation_max_dimension)
    )
    processor = ColorWheelProcessor(binary, gpu_accelerated, color_wheel_origin=orientation_angle)
    color_wheel_image = processor.process_image()

    color_wheel_path = output_path / "color_wheel_output.png"
    color_wheel_image.save(color_wheel_path)

    one_phase = PhaseSubtraction(color_wheel_image, foreground).subtract_black_from_input()
    one_phase_path = output_path / "one_phase_output.png"
    one_phase.save(one_phase_path)

    mask_processor = ColorMaskProcessor(
        one_phase,
        foreground,
        output_path,
        num_clusters=int(num_clusters),
        random_state=int(random_state),
        max_fit_samples=int(max_fit_samples),
        min_component_size=int(min_component_size),
    )
    mask_results = mask_processor.process_image()

    return {
        "orientation_angle": float(orientation_angle),
        "color_wheel_image": str(color_wheel_path),
        "one_phase_image": str(one_phase_path),
        "grain_masks": mask_results["grain_outputs"],
        "output_directory": str(output_path),
        "gpu_accelerated": bool(gpu_accelerated),
        "num_clusters_requested": int(num_clusters),
        "num_clusters_used": int(mask_results["clusters_used"]),
        "grain_counts": mask_results["grain_counts"],
        "original_width": int(original_width),
        "original_height": int(original_height),
        "processed_width": int(gray.shape[1]),
        "processed_height": int(gray.shape[0]),
        "scale_factor": float(scale),
        "foreground_fraction": float(foreground.mean()),
        "max_dimension": int(max_dimension),
        "orientation_max_dimension": int(orientation_max_dimension),
        "full_resolution_output": bool(int(max_dimension) <= 0),
        "max_fit_samples": int(max_fit_samples),
        "min_component_size": int(min_component_size),
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Run the fixed full-resolution ColorWheel analysis.")
    parser.add_argument("image_path", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("colorwheel_output"))
    parser.add_argument("--num-clusters", type=int, default=8)
    parser.add_argument("--max-dimension", type=int, default=0)
    parser.add_argument("--orientation-max-dimension", type=int, default=1024)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--max-fit-samples", type=int, default=10000)
    parser.add_argument("--min-component-size", type=int, default=15)
    args = parser.parse_args()

    result = analyze_image(
        image_path=str(args.image_path),
        output_dir=str(args.output_dir),
        num_clusters=args.num_clusters,
        max_dimension=args.max_dimension,
        orientation_max_dimension=args.orientation_max_dimension,
        random_state=args.random_state,
        max_fit_samples=args.max_fit_samples,
        min_component_size=args.min_component_size,
    )
    print(json.dumps(result, indent=2, default=str))
