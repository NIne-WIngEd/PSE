# inference script for Bradley's CNN model
import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
from pathlib import Path
import os

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# From Bradley's cnn_loader.iypnb
class DeeperCNN(nn.Module):
    def __init__(self, num_classes=4, in_channels=3,
                 num_filters1=32, num_filters2=64, num_filters3=128,
                 kernel_size=5, dropout_rate=0.5):
        super(DeeperCNN, self).__init__()

        # Block 1
        self.block1 = nn.Sequential(
            nn.Conv2d(in_channels, num_filters1, kernel_size=kernel_size, padding=2),  # in_channels=3 for RGB, 1 for grayscale
            nn.BatchNorm2d(num_filters1),
            nn.ReLU(),
            nn.Conv2d(num_filters1, num_filters1, kernel_size=kernel_size, padding=2),
            nn.BatchNorm2d(num_filters1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        # Block 2
        self.block2 = nn.Sequential(
            nn.Conv2d(num_filters1, num_filters2, kernel_size=kernel_size, padding=2),
            nn.BatchNorm2d(num_filters2),
            nn.ReLU(),
            nn.Conv2d(num_filters2, num_filters2, kernel_size=kernel_size, padding=2),
            nn.BatchNorm2d(num_filters2),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        # Block 3
        self.block3 = nn.Sequential(
            nn.Conv2d(num_filters2, num_filters3, kernel_size=kernel_size, padding=2),
            nn.BatchNorm2d(num_filters3),
            nn.ReLU(),
            nn.Conv2d(num_filters3, num_filters3, kernel_size=kernel_size, padding=2),
            nn.BatchNorm2d(num_filters3),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        # Fully connected layers
        self.flatten = nn.Flatten()
        self.fc_layers = nn.Sequential(
            nn.Linear(128 * 27 * 27, 512),  # Corrected size # change here to fix the new color model 
            nn.ReLU(),
            nn.Dropout(p=dropout_rate),
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Dropout(p=dropout_rate),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.flatten(x)
        x = self.fc_layers(x)
        return x


def load_model(model_path, in_channels=3, device=None):

    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    model = DeeperCNN(in_channels=in_channels)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    return model


def _get_transform(image_size=217, in_channels=3):
    ops = [transforms.Resize((image_size, image_size))]
    if in_channels == 1:
        ops.append(transforms.Grayscale())
    ops.append(transforms.ToTensor())
    return transforms.Compose(ops)


def predict_image(model, image_path, class_labels=None, image_size=217, in_channels=3, device=None):
    
    if class_labels is None:
        class_labels = ['dots', 'irregular', 'lines', 'mixed']
    
    if device is None:
        device = next(model.parameters()).device
    
    # Load and preprocess image
    pil_mode = 'RGB' if in_channels == 3 else 'L'
    transform = _get_transform(image_size, in_channels)
    image = Image.open(image_path).convert(pil_mode)
    image_tensor = transform(image).unsqueeze(0).to(device)
    
    # Run inference
    model.eval()
    with torch.no_grad():
        output = model(image_tensor)
        probabilities = torch.softmax(output, dim=1).squeeze()
        predicted_idx = torch.argmax(probabilities).item()
        confidence = probabilities[predicted_idx].item()
    
    # Format results
    result = {
        'predicted_class': class_labels[predicted_idx],
        'confidence': confidence,
        'probabilities': {class_labels[i]: probabilities[i].item() for i in range(len(class_labels))}
    }
    
    return result


def predict_folder(model, folder_path, class_labels=None, image_size=217, in_channels=3,
                   recursive=False, extensions=('.png', '.jpg', '.jpeg', '.tif', '.tiff'), 
                   device=None, verbose=True):
    
    if class_labels is None:
        class_labels = ['dots', 'irregular', 'lines', 'mixed']
    
    folder_path = Path(folder_path)
    
    # Find all images
    if recursive:
        image_files = [f for f in folder_path.rglob('*') if f.suffix.lower() in extensions]
    else:
        image_files = [f for f in folder_path.glob('*') if f.suffix.lower() in extensions]
    
    if not image_files:
        print(f"No images found in {folder_path}")
        return []
    
    if verbose:
        print(f"Found {len(image_files)} images in {folder_path}")
    
    # Run predictions
    results = []
    for i, img_path in enumerate(image_files):
        if verbose and (i + 1) % 10 == 0:
            print(f"  Processing {i + 1}/{len(image_files)}...")
        
        try:
            prediction = predict_image(model, img_path, class_labels, image_size, in_channels, device)
            prediction['filename'] = img_path.name
            prediction['path'] = str(img_path)
            results.append(prediction)
        except Exception as e:
            if verbose:
                print(f"  Error processing {img_path.name}: {e}")
    
    if verbose:
        print(f"✓ Completed {len(results)}/{len(image_files)} predictions")
        
        # Print summary
        class_counts = {}
        for r in results:
            cls = r['predicted_class']
            class_counts[cls] = class_counts.get(cls, 0) + 1
        
        print("\nPrediction summary:")
        for cls, count in sorted(class_counts.items()):
            print(f"  {cls}: {count} images ({count/len(results)*100:.1f}%)")
    
    return results


if __name__ == "__main__":
    import sys
    
    MODEL_PATH = "cnn_rgb_classifier.pth"  # RGB model
    IN_CHANNELS = 3                         # 3 for RGB, 1 for grayscale
    CLASS_LABELS = ['dots', 'irregular', 'lines', 'mixed']
    image_path = '/home/newuser/Documents/Mukesh_AFM/data/for_unet/Images/324.png'

    model = load_model(MODEL_PATH, in_channels=IN_CHANNELS)
    print(f"Model loaded on {device}\n")
    
    # predict single image 
    result = predict_image(model, image_path=image_path, in_channels=IN_CHANNELS, device=device)
    print(result)