
from voronoi_mask_pipeline import run_voronoi_analysis as run_voronoi_analysis_from_mask
import os
from pathlib import Path
import numpy as np
from PIL import Image
import warnings
warnings.filterwarnings("ignore")

# Configure matplotlib to use non-interactive backend (prevents plt.show() from blocking)
import matplotlib
matplotlib.use('Agg')  # Must be before importing pyplot or voronoi_v7
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab

# Matplotlib params to match run_image_analysis_knn
params = {'legend.fontsize': 'x-large',
         'axes.labelsize': 'x-large',
         'axes.titlesize':'x-large',
         'xtick.labelsize':'x-large',
         'ytick.labelsize':'x-large'}
pylab.rcParams.update(params)

import skimage
from skimage import color
import skimage.util

import voronoi_v7


def load_image(image_path, max_size=1024):
    """
    Load and process image using the SAME method as run_image_analysis_knn.ipynb
    
    Args:
        image_path: Path to image
        max_size: Maximum dimension (pixels). Images larger than this will be downsampled.
    
    Returns:
        Processed numpy array ready for voronoi_v7.analyze_image()
    """
    image_path = Path(image_path)
    
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    try:
        # Load image exactly like run_image_analysis_knn.ipynb
        im = Image.open(image_path)
        im = im.convert("RGB")
        
        # Key step: 1 - color.rgb2gray to invert (white dots become dark)
        data = 1 - color.rgb2gray(skimage.img_as_float(im))
        im.close()
        
        print(f"Loaded image: {image_path.name}")
        
        # Downsample if too large (speeds up processing dramatically)
        original_shape = data.shape
        if max_size is not None and (data.shape[0] > max_size or data.shape[1] > max_size):
            h, w = data.shape
            scale = max_size / max(h, w)
            new_h, new_w = int(h * scale), int(w * scale)
            from skimage.transform import resize
            data = resize(data, (new_h, new_w), anti_aliasing=True, preserve_range=True)
            print(f"  ⚠ Downsampled from {original_shape} to {data.shape} for faster processing")
        
        # Validate
        print(f"  Shape: {data.shape}")
        print(f"  Data type: {data.dtype}")
        print(f"  Value range: [{data.min():.3f}, {data.max():.3f}]")
        
        if data.ndim != 2:
            raise ValueError(f"Expected 2D image, got shape {data.shape}")
        
        return data
        
    except Exception as e:
        raise ValueError(f"Failed to load image: {e}")


def run_voronoi_analysis(image_path, image_size=1.0, output_dir='voronoi_outputs', threshold_edge=0.025, max_size=1024):
    return run_voronoi_analysis_from_mask(
        mask_path=image_path,
        image_size=image_size,
        threshold_edge=threshold_edge,
        max_size=max_size
    )

if __name__ == "__main__":
    # Run analysis matching run_image_analysis_knn.ipynb
    results = run_voronoi_analysis(
        image_path='/home/newuser/Desktop/Mukesh_AFM/data/for_unet/Images/A_AC.png',
        image_size=1.0,  # Size in micrometers (1 = 1μm)
        output_dir='voronoi_outputs',
        threshold_edge=0.025,  # 2.5% tolerance (matches run_image_analysis_knn)
        max_size=1024  # Downsample for speed
    )

