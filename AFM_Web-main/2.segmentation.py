import os
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
import torchvision.transforms as transforms
import cv2


class BalancedUNet(nn.Module):
    def __init__(
        self,
        in_channels: int,
        num_classes: int,
        num_convs_per_block: int = 2,
        base_channels: int = 48,
        kernel_size: int = 3,
    ):
        super(BalancedUNet, self).__init__()

        if num_convs_per_block < 1:
            raise ValueError("num_convs_per_block must be at least 1")
        if kernel_size % 2 == 0:
            raise ValueError("kernel_size must be odd")

        padding = (kernel_size - 1) // 2

        def conv_block(in_c, out_c, num_convs, use_dropout=False, dropout_rate=0.3):
            layers = []
            layers += [
                nn.Conv2d(in_c, out_c, kernel_size=kernel_size, padding=padding),
                nn.BatchNorm2d(out_c),
                nn.ReLU(inplace=True),
            ]
            for _ in range(num_convs - 1):
                layers += [
                    nn.Conv2d(out_c, out_c, kernel_size=kernel_size, padding=padding),
                    nn.BatchNorm2d(out_c),
                    nn.ReLU(inplace=True),
                ]
            if use_dropout:
                layers.append(nn.Dropout2d(dropout_rate))
            return nn.Sequential(*layers)

        def downsample_conv(in_c, out_c):
            return nn.Sequential(
                nn.Conv2d(in_c, out_c, kernel_size=3, padding=1, stride=2),
                nn.BatchNorm2d(out_c),
                nn.ReLU(inplace=True),
            )

        # ENCODER
        self.enc1 = conv_block(in_channels, base_channels, num_convs_per_block)
        self.pool1 = downsample_conv(base_channels, base_channels)

        self.enc2 = conv_block(base_channels, base_channels * 2, num_convs_per_block)
        self.pool2 = downsample_conv(base_channels * 2, base_channels * 2)

        self.enc3 = conv_block(base_channels * 2, base_channels * 4, num_convs_per_block)
        self.pool3 = downsample_conv(base_channels * 4, base_channels * 4)

        # BOTTLENECK
        self.bottleneck = conv_block(
            base_channels * 4,
            base_channels * 8,
            num_convs_per_block,
            use_dropout=True,
            dropout_rate=0.2,
        )

        # DECODER
        self.upconv3 = nn.ConvTranspose2d(base_channels * 8, base_channels * 4, 2, 2)
        self.dec3 = conv_block(
            base_channels * 8,
            base_channels * 4,
            num_convs_per_block,
            use_dropout=True,
            dropout_rate=0.1,
        )

        self.upconv2 = nn.ConvTranspose2d(base_channels * 4, base_channels * 2, 2, 2)
        self.dec2 = conv_block(base_channels * 4, base_channels * 2, num_convs_per_block)

        self.upconv1 = nn.ConvTranspose2d(base_channels * 2, base_channels, 2, 2)
        self.dec1 = conv_block(base_channels * 2, base_channels, num_convs_per_block)

        # Final head
        self.final_conv = nn.Sequential(
            nn.Conv2d(
                base_channels,
                base_channels // 2,
                kernel_size=kernel_size,
                padding=padding,
            ),
            nn.BatchNorm2d(base_channels // 2),
            nn.ReLU(inplace=True),
            nn.Conv2d(base_channels // 2, num_classes, 1),
        )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        # Encoder
        e1 = self.enc1(x)
        p1 = self.pool1(e1)

        e2 = self.enc2(p1)
        p2 = self.pool2(e2)

        e3 = self.enc3(p2)
        p3 = self.pool3(e3)

        # Bottleneck
        bottleneck = self.bottleneck(p3)

        # Decoder
        d3 = self.upconv3(bottleneck)
        d3 = torch.cat((d3, e3), dim=1)
        d3 = self.dec3(d3)

        d2 = self.upconv2(d3)
        d2 = torch.cat((d2, e2), dim=1)
        d2 = self.dec2(d2)

        d1 = self.upconv1(d2)
        d1 = torch.cat((d1, e1), dim=1)
        d1 = self.dec1(d1)

        output = self.final_conv(d1)
        return output


def load_model(checkpoint_path, device="cuda"):
    """
    PyTorch 2.6+ default behavior changed (weights_only=True).
    Your checkpoint is a full dict (model_config + model_state_dict),
    so we explicitly load with weights_only=False.

    Only do this if you trust the checkpoint source (you trained it / got it internally).
    """
    device = torch.device(device if torch.cuda.is_available() else "cpu")

    checkpoint_path = str(checkpoint_path)
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Model not found: {checkpoint_path}")

    # IMPORTANT FIX:
    # Force full checkpoint loading for compatibility with older saved formats.
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)

    config = checkpoint["model_config"]
    model = BalancedUNet(
        in_channels=config["in_channels"],
        num_classes=config["num_classes"],
        base_channels=config.get("base_channels", 48),
        num_convs_per_block=config.get("num_convs_per_block", 2),
        kernel_size=config.get("kernel_size", 3),
    ).to(device)

    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    img_size = config.get("img_size", 256)

    return model, img_size, device


def preprocess_image(image_path, img_size=256, denoise=0, sharpen=0, invert=False):
    image = Image.open(image_path)
    original_size = image.size  # (width, height)

    # Convert to grayscale for model
    working_image = image.convert("L")
    working_array = np.array(working_image)

    # Apply preprocessing
    if denoise > 0:
        working_array = cv2.fastNlMeansDenoising(
            working_array,
            None,
            h=denoise,
            templateWindowSize=7,
            searchWindowSize=21,
        )

    if sharpen > 0:
        sigma = 1.0
        amount = sharpen / 10.0
        blurred = cv2.GaussianBlur(working_array, (0, 0), sigma)
        working_array = cv2.addWeighted(
            working_array, 1.0 + amount, blurred, -amount, 0
        )

    if invert:
        working_array = 255 - working_array

    working_image = Image.fromarray(working_array.astype(np.uint8))

    # Convert to tensor
    transform = transforms.Compose(
        [
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
        ]
    )

    img_tensor = transform(working_image).unsqueeze(0)

    return img_tensor, original_size


def predict_mask(model, image_tensor, device, threshold=0.5):
    model.eval()
    image_tensor = image_tensor.to(device)

    with torch.no_grad():
        output = model(image_tensor)
        probs = torch.sigmoid(output)
        pred_mask = (probs > threshold).long()
        pred_mask = pred_mask.squeeze().cpu().numpy()

    return pred_mask


def save_mask(mask, output_path, original_size):
    # Convert to PIL Image
    mask_img = Image.fromarray((mask * 255).astype(np.uint8), mode="L")

    # Resize to original size
    mask_img = mask_img.resize(original_size, Image.NEAREST)

    # Create output directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save
    mask_img.save(output_path)


def segment_image(
    image_path,
    model_path=None,
    output_dir="segmentation_output",
    threshold=0.5,
    denoise=0,
    sharpen=0,
    invert=False,
    device="cuda",
):
    # Default model path - use relative path from script location
    if model_path is None:
        script_dir = Path(__file__).parent
        model_path = script_dir / "best_quality_unet.pt"

    # Setup
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Load model
    print(f"\n{'='*60}")
    print("Loading Model")
    print(f"{'='*60}")
    print(f"Model: {Path(model_path).name}")

    model, img_size, device = load_model(model_path, device)
    print(f"Device: {device}")
    print(f"Input size: {img_size}x{img_size}")

    # Preprocessing info
    if denoise > 0 or sharpen > 0 or invert:
        print("\nPreprocessing:")
        if denoise > 0:
            print(f"  Denoising: {denoise}")
        if sharpen > 0:
            print(f"  Sharpening: {sharpen}")
        if invert:
            print("  Invert: True")

    # Load and preprocess
    print(f"\n{'='*60}")
    print("Processing Image")
    print(f"{'='*60}")
    print(f"Input: {image_path.name}")

    img_tensor, original_size = preprocess_image(
        str(image_path),
        img_size=img_size,
        denoise=denoise,
        sharpen=sharpen,
        invert=invert,
    )
    print(f"Original size: {original_size[0]}x{original_size[1]}")

    # Predict
    mask = predict_mask(model, img_tensor, device, threshold)

    # Save
    output_path = Path(output_dir) / f"{image_path.stem}_mask.png"
    save_mask(mask, str(output_path), original_size)

    print(f"\n{'='*60}")
    print("✓ Segmentation Complete!")
    print(f"{'='*60}")
    print(f"Mask saved to: {output_path}")

    return str(output_path)


if __name__ == "__main__":
    # Use relative paths
    script_dir = Path(__file__).parent
    test_image = script_dir / "Cnn_classifier_test" / "dots.png"

    segment_image(
        image_path=str(test_image),
        output_dir="segmentation_output",
        threshold=0.5,
        denoise=0,
        sharpen=0,
        invert=False,
    )

