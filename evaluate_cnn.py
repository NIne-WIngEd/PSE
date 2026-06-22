import os
import csv
import time
import torch
from PIL import Image
from torchvision import transforms

# Import your model/inference code
# Adjust this part depending on your file name
import importlib.util

spec = importlib.util.spec_from_file_location(
    "cnn_inference",
    "1.cnn_inference 1.py"
)
cnn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cnn)


TEST_DIR = "test"
MODEL_PATH = "cnn_rgb_classifier.pth"
OUTPUT_CSV = "cnn_predictions.csv"

CLASSES = ["dots", "irregular", "lines", "mixed"]


def main():
    model = cnn.load_model(MODEL_PATH)
    model.eval()

    rows = []

    for true_label in CLASSES:
        folder_path = os.path.join(TEST_DIR, true_label)

        if not os.path.exists(folder_path):
            print(f"Missing folder: {folder_path}")
            continue

        for filename in os.listdir(folder_path):
            if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
                continue

            image_path = os.path.join(folder_path, filename)

            start_time = time.time()

            pred_label, confidence, probabilities = cnn.predict_image(
                model,
                image_path
            )

            end_time = time.time()
            prediction_time_ms = (end_time - start_time) * 1000

            row = {
                "Filename": filename,
                "Image Path": image_path,
                "True Label": true_label,
                "Predicted Label": pred_label,
                "Confidence": confidence,
                "Dots": probabilities.get("dots", 0),
                "Irregular": probabilities.get("irregular", 0),
                "Lines": probabilities.get("lines", 0),
                "Mixed": probabilities.get("mixed", 0),
                "Correct": true_label == pred_label,
                "Prediction Time (ms)": prediction_time_ms
            }

            rows.append(row)

            print(f"{filename}: true={true_label}, predicted={pred_label}, confidence={confidence}")

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved results to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()