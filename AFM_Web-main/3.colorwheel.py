"""
Color Wheel Analysis Module
This module performs orientation-based color wheel analysis for line patterns in AFM images.
"""

import math
import os
import random
from collections import deque
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from sklearn.cluster import KMeans
from skimage import measure
from skimage.morphology import skeletonize


def check_cupy_available():
    """Check if CuPy is available for GPU acceleration."""
    try:
        import cupy
        return True
    except ImportError:
        return False


def compute_average_angle(image_path):
    """
    Compute the average orientation angle of line features in the image.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Average angle in degrees
    """
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    blurred_img = cv2.GaussianBlur(image, (3, 3), 0)
    skeleton = skeletonize(blurred_img // 255, method='lee').astype(np.uint8) * 255
    _, binary_skeleton = cv2.threshold(skeleton, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary_skeleton, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    
    angles = []
    for contour in contours:
        for i in range(0, len(contour) - 10, 10):
            subcontour = contour[i:i+10]
            if len(subcontour) >= 2:
                dx = subcontour[-1][0][0] - subcontour[0][0][0]
                dy = subcontour[-1][0][1] - subcontour[0][0][1]
                angles.append(math.degrees(math.atan2(dy, dx)))
    
    return sum(angles) / len(angles) if angles else 0


class ColorWheelProcessor:
    """Process images with orientation-dependent color wheel."""
    
    def __init__(self, binarized_image, gpu_accelerated, color_wheel_origin=0):
        """
        Initialize the color wheel processor.
        
        Args:
            binarized_image: Input grayscale image as numpy array
            gpu_accelerated: Whether to use GPU acceleration (CuPy)
            color_wheel_origin: Rotation angle for color wheel origin in degrees
        """
        self.binarized_image = binarized_image
        self.sym = 2
        self.color = 5
        self.brightness = 1
        self.contrast = 5
        self.gpu_accelerated = gpu_accelerated
        self.color_wheel_origin = math.radians(color_wheel_origin)
        
        # Import cupy or numpy based on GPU availability
        if gpu_accelerated:
            self.cp = __import__("cupy")
        else:
            self.cp = __import__("numpy")

    def process_image(self):
        """Apply color wheel transformation to the image."""
        data = np.array(self.binarized_image)
        clrwhl = self._bldclrwhl(data.shape[0], data.shape[1], self.sym)
        
        # Run the no-fft processing to combine wheel and image
        imnp = self._nofft(clrwhl, data, data.shape[0], data.shape[1])
        
        # Normalize result safely (avoid division by zero)
        imnp = imnp - np.min(imnp)
        maxv = np.max(imnp) if imnp.size > 0 else 0
        if maxv != 0:
            imnp = imnp / maxv * 255.0
        else:
            imnp = imnp * 0.0

        rgb2 = Image.fromarray(np.uint8(imnp))
        img2 = rgb2.filter(ImageFilter.GaussianBlur(radius=0.5))

        converter = ImageEnhance.Color(img2)
        img2 = converter.enhance(self.color)

        converter = ImageEnhance.Brightness(img2)
        img2 = converter.enhance(self.brightness)

        converter = ImageEnhance.Contrast(img2)
        img2 = converter.enhance(self.contrast)

        return img2

    def _bldclrwhl(self, nx, ny, sym):
        """Build the color wheel matrix."""
        cp = self.cp
        cda = cp.ones((nx, ny, 2))
        cx = cp.linspace(-nx, nx, nx)
        cy = cp.linspace(-ny, ny, ny)
        cxx, cyy = cp.meshgrid(cy, cx)
        
        # Apply the color wheel origin offset
        czz = (((cp.arctan2(cxx, cyy) - self.color_wheel_origin) / math.pi + 1.0) / 2.0) * sym
        cd2 = cp.dstack((czz, cda))
        carr = cd2
        chi = cp.floor(carr[..., 0] * 6)
        f = carr[..., 0] * 6 - chi
        p = carr[..., 2] * (1 - carr[..., 1])
        q = carr[..., 2] * (1 - f * carr[..., 1])
        t = carr[..., 2] * (1 - (1 - f) * carr[..., 1])
        v = carr[..., 2]
        chi = cp.stack([chi, chi, chi], axis=-1).astype(cp.uint8) % 6
        out = cp.choose(
            chi, cp.stack([cp.stack((v, t, p), axis=-1),
                           cp.stack((q, v, p), axis=-1),
                           cp.stack((p, v, t), axis=-1),
                           cp.stack((p, q, v), axis=-1),
                           cp.stack((t, p, v), axis=-1),
                           cp.stack((v, p, q), axis=-1)]))
        if self.gpu_accelerated:
            return cp.asnumpy(out)
        else:
            return out

    def _nofft(self, whl, img, nx, ny):
        """Apply FFT-based color wheel transformation."""
        cp = self.cp
        imnp = cp.array(img)
        fimg = cp.fft.fft2(imnp)
        whl = cp.fft.fftshift(whl)
        proimg = cp.zeros((nx, ny, 3))
        comb = cp.zeros((nx, ny, 3), dtype=complex)
        magnitude = cp.repeat(np.abs(fimg)[:, :, cp.newaxis], 3, axis=2)
        phase = cp.repeat(np.angle(fimg)[:, :, cp.newaxis], 3, axis=2)
        proimg = whl * magnitude
        comb = cp.multiply(proimg, cp.exp(1j * phase))
        for n in range(3):
            proimg[:, :, n] = cp.real(cp.fft.ifft2(comb[:, :, n]))
            proimg[:, :, n] = proimg[:, :, n] - cp.min(proimg[:, :, n])
            proimg[:, :, n] = proimg[:, :, n] / cp.max(proimg[:, :, n])

        if self.gpu_accelerated:
            return cp.asnumpy(proimg)
        else:
            return proimg


class PhaseSubtraction:
    """Subtract one phase from color wheel image to isolate single phase."""
    
    def __init__(self, input_image, binarized_image):
        """
        Initialize phase subtraction.
        
        Args:
            input_image: Color wheel processed image (PIL Image)
            binarized_image: Binary mask image (numpy array)
        """
        self.input_image = input_image
        self.binarized_image = binarized_image

    def subtract_black_from_input(self):
        """Subtract black regions from input to isolate colored phase."""
        input_array = np.array(self.input_image)
        binned_array = np.array(self.binarized_image)

        # Ensure the mask has the same number of channels as the input image
        if len(binned_array.shape) == 2:
            binned_array = np.expand_dims(binned_array, axis=-1)

        # Subtract black parts of the mask from the input image
        result_array = np.where(binned_array == 0, input_array, 255)

        result_image = Image.fromarray(result_array.astype(np.uint8))
        return result_image


class ColorMaskProcessor:
    """Create orientation-based masks using k-means clustering on colors."""
    
    def __init__(self, input_image, output_path):
        """
        Initialize mask processor.
        
        Args:
            input_image: Color wheel processed image (PIL Image)
            output_path: Directory to save output masks
        """
        self.input_image = input_image
        self.output_path = output_path

    def create_color_mask(self, num_clusters):
        """Create masks by clustering colors."""
        img_array = np.array(self.input_image)
        reshaped_array = img_array.reshape((-1, 3))

        # Use k-means clustering to group similar colors
        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
        kmeans.fit(reshaped_array)

        labels = kmeans.labels_
        segmented_image = labels.reshape(img_array.shape[:2])

        # Create a mask for each cluster
        masks = [(segmented_image == i) for i in range(num_clusters)]
        return masks

    def save_masks_as_images(self, image, masks):
        """Save each mask as separate image and apply filtering."""
        for i, mask in enumerate(masks):
            color_mask = np.zeros_like(image)
            color_mask[mask] = image[mask]
            mask_image = Image.fromarray(color_mask)
            mask_image.save(os.path.join(self.output_path, f"mask_{i}.tiff"))
            
            # Identify non-black pixels
            mask_array = np.array(mask_image)
            non_black_pixels = (mask_array[:, :, :3] > 0).any(axis=2)

            # Remove small clusters
            non_black_pixels = self.remove_small_clusters(non_black_pixels, min_size=15)

            # Create a new image with the modified non-black pixels
            result_img_array = np.zeros_like(mask_array)
            result_img_array[non_black_pixels] = mask_array[non_black_pixels]
            
            result_img = Image.fromarray(result_img_array, self.input_image.mode)
            result_img.save(os.path.join(self.output_path, f"filtered_mask_{i}.tiff"))

    def remove_small_clusters(self, image, min_size):
        """Remove clusters smaller than min_size pixels."""
        labeled_image, num_labels = measure.label(image, connectivity=2, return_num=True)
        for label in range(1, num_labels + 1):
            cluster_size = np.sum(labeled_image == label)
            if cluster_size < min_size:
                image[labeled_image == label] = 0
        return image

    def process_image(self):
        """Process image to create and save all masks."""
        masks = self.create_color_mask(num_clusters=4)
        image = self.input_image
        self.save_masks_as_images(np.array(image), masks)


class GrainFinder:
    """Find and colorize individual grains in orientation masks."""
    
    def __init__(self, mask_id, directory):
        """
        Initialize grain finder.
        
        Args:
            mask_id: ID of the mask to process
            directory: Directory containing the masks
        """
        self.mask = mask_id
        self.directory = directory
        mask_path = Path(directory) / f"filtered_mask_{mask_id}.tiff"
        
        if not mask_path.exists():
            self.image = None
            return
            
        self.image = Image.open(str(mask_path))
        self.pixels = self.image.load()
        self.output_path = str(Path(directory) / f"Mask_{mask_id}.tiff")
        self.grouped = set()
        self.group_id = 1
        self.group_sizes = {}

    def group_pixels(self, x, y):
        """Group adjacent pixels with the same color using BFS."""
        if self.image is None:
            return
            
        queue = deque([(x, y)])
        current_group_size = 0

        while queue:
            current_x, current_y = queue.popleft()

            if (
                current_x < 0
                or current_y < 0
                or current_x >= self.image.width
                or current_y >= self.image.height
            ):
                continue

            pixel = self.image.getpixel((current_x, current_y))
            if pixel == (0, 0, 0) or (current_x, current_y) in self.grouped:
                continue

            self.grouped.add((current_x, current_y))
            self.image.putpixel((current_x, current_y), self.group_id)
            current_group_size += 1

            # Add adjacent pixels to the queue
            for i in range(-8, 8):
                for j in range(-8, 8):
                    queue.append((current_x + i, current_y + j))

        self.group_sizes[self.group_id] = current_group_size
        self.group_id += 1

    def process_image(self):
        """Process the mask to identify and colorize grains."""
        if self.image is None:
            return None
            
        # Check if the image has only black pixels
        black_pixel_count = sum(
            1 for x in range(self.image.width) 
            for y in range(self.image.height) 
            if self.pixels[x, y] == (0, 0, 0)
        )
        
        if black_pixel_count == self.image.width * self.image.height:
            return None
    
        # Group pixels
        for x in range(self.image.width):
            for y in range(self.image.height):
                pixel = self.pixels[x, y]
                if pixel != (0, 0, 0) and (x, y) not in self.grouped:
                    self.group_pixels(x, y)
    
        if not self.group_sizes:
            return None
            
        # Calculate average group size
        average_size = sum(self.group_sizes.values()) / len(self.group_sizes)
    
        # Filter out groups deviating more than 150% from average and smaller than average
        filtered_group_ids = [
            group_id for group_id, size in self.group_sizes.items() 
            if size < average_size * 1.5 and size < average_size
        ]
    
        # Remove filtered groups
        self.group_sizes = {
            group_id: size for group_id, size in self.group_sizes.items() 
            if group_id not in filtered_group_ids
        }
    
        # Remove pixels in filtered groups
        for x in range(self.image.width):
            for y in range(self.image.height):
                pixel = self.image.getpixel((x, y))
                if isinstance(pixel, tuple) and pixel[0] in filtered_group_ids:
                    self.image.putpixel((x, y), (0, 0, 0))
    
        # Generate random colors for each group
        colors = [
            (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) 
            for _ in range(self.group_id)
        ]
    
        # Colorize the image based on group ids
        for x in range(self.image.width):
            for y in range(self.image.height):
                pixel = self.image.getpixel((x, y))
                if pixel != (0, 0, 0):
                    if isinstance(pixel, tuple):
                        group_id = pixel[0]
                    else:
                        group_id = pixel
                    self.image.putpixel((x, y), colors[group_id])
    
        # Save the colorized image
        self.image.save(self.output_path)
        
        # Save grain statistics
        stats_path = Path(self.directory) / f"grains_{self.mask}.txt"
        with open(str(stats_path), "w") as file:
            for group_id, size in self.group_sizes.items():
                file.write(f"Group {group_id}: {size} pixels\n")
        
        return self.output_path


def analyze_image(image_path, output_dir='colorwheel_output', num_clusters=8):
    """
    Main function to run complete color wheel analysis pipeline.
    
    Args:
        image_path: Path to input image (should be grayscale, not binary mask)
        output_dir: Directory to save outputs
        num_clusters: Number of orientation clusters for k-means (default 8)
        
    Returns:
        Dictionary containing results and output paths
    """
    # Check GPU availability
    gpu_accelerated = check_cupy_available()
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Read input image as grayscale (this should be the ORIGINAL image, not a mask)
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    # Ensure proper data type
    image = image.astype(np.uint8)
    
    # Compute orientation angle
    orientation_angle = compute_average_angle(str(image_path))
    
    # Process with color wheel
    processor = ColorWheelProcessor(image, gpu_accelerated, color_wheel_origin=orientation_angle)
    color_wheel_img = processor.process_image()
    
    # Save color wheel output
    color_wheel_path = Path(output_dir) / "color_wheel_output.png"
    color_wheel_img.save(str(color_wheel_path))
    
    # Phase subtraction
    phase_sub = PhaseSubtraction(color_wheel_img, image)
    one_phase = phase_sub.subtract_black_from_input()
    
    # Save phase subtraction output
    one_phase_path = Path(output_dir) / "one_phase_output.png"
    one_phase.save(str(one_phase_path))
    
    # Create orientation masks
    mask_maker = ColorMaskProcessor(one_phase, output_dir)
    mask_maker.process_image()
    
    # Find grains in each mask
    grain_outputs = []
    for i in range(num_clusters):
        grain_finder = GrainFinder(i, output_dir)
        result = grain_finder.process_image()
        if result is not None:
            grain_outputs.append(result)
    
    # Collect all mask paths
    mask_paths = [
        str(Path(output_dir) / f"Mask_{i}.tiff") 
        for i in range(num_clusters)
        if Path(output_dir) / f"Mask_{i}.tiff"
    ]
    
    results = {
        'orientation_angle': orientation_angle,
        'color_wheel_image': str(color_wheel_path),
        'one_phase_image': str(one_phase_path),
        'grain_masks': grain_outputs,
        'output_directory': output_dir,
        'gpu_accelerated': gpu_accelerated
    }
    
    return results
