# app.py
"""
Flask backend for AFM pipeline with batch upload support.

Flow:
1) Upload one or more images in a single batch
2) Create ONE job_id for that batch
3) For each image:
   - save image
   - run CNN classifier
   - run U-Net segmentation
   - return per-image preview + metadata
4) Frontend selects any image in the batch
5) Frontend optionally edits that mask
6) Run Voronoi / ColorWheel on one selected image OR the full batch
7) Store all results under the same batch job folder
8) Export one analyzed result or the whole batch as real PDF
"""

import base64
import io
import os
import uuid
from datetime import datetime
from pathlib import Path
import importlib.util

from PIL import Image
from flask import Flask, request, jsonify, send_file, abort, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename

from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdf_canvas


# ----------------------------
# 1) PROJECT PATHS
# ----------------------------
BASE_DIR = Path(__file__).parent

CNN_SCRIPT = BASE_DIR / "1.cnn_inference 1.py"
UNET_SCRIPT = BASE_DIR / "2.segmentation.py"
VORONOI_SCRIPT = BASE_DIR / "2.voronoi.py"
COLORWHEEL_SCRIPT = BASE_DIR / "3.colorwheel.py"

CNN_WEIGHTS = BASE_DIR / "cnn_rgb_classifier.pth"
UNET_WEIGHTS = BASE_DIR / "best_quality_unet.pt"

CNN_IN_CHANNELS = 3
CNN_IMAGE_SIZE = 217

UPLOAD_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"

UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


# ----------------------------
# 2) DYNAMIC IMPORT
# ----------------------------
def import_module_from_file(module_name: str, file_path: Path):
    if not file_path.exists():
        raise FileNotFoundError(f"Missing file: {file_path}")
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


cnn_mod = import_module_from_file("cnn_backend", CNN_SCRIPT)
unet_mod = import_module_from_file("unet_backend", UNET_SCRIPT)
vor_mod = import_module_from_file("voronoi_backend", VORONOI_SCRIPT)
cw_mod = import_module_from_file("colorwheel_backend", COLORWHEEL_SCRIPT)


# ----------------------------
# 3) LOAD MODELS ONCE
# ----------------------------
if not CNN_WEIGHTS.exists():
    raise FileNotFoundError(f"Missing CNN weights: {CNN_WEIGHTS}")

CNN_MODEL = cnn_mod.load_model(str(CNN_WEIGHTS), in_channels=CNN_IN_CHANNELS)
UNET_MODEL, UNET_IMG_SIZE, UNET_DEVICE = unet_mod.load_model(
    str(UNET_WEIGHTS), device="cuda"
)


def run_unet_cached(image_path: str, job_dir: Path) -> str:
    img_tensor, original_size = unet_mod.preprocess_image(
        image_path,
        img_size=UNET_IMG_SIZE,
        denoise=0,
        sharpen=0,
        invert=False,
    )
    mask = unet_mod.predict_mask(UNET_MODEL, img_tensor, UNET_DEVICE, threshold=0.5)

    out_path = job_dir / f"{Path(image_path).stem}_mask.png"
    unet_mod.save_mask(mask, str(out_path), original_size)
    return str(out_path)


# ----------------------------
# 4) HELPERS
# ----------------------------
def validate_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".jpeg":
        ext = ".jpg"
    if ext not in ALLOWED_EXTS:
        raise ValueError(f"Unsupported file type {ext}. Allowed: {sorted(ALLOWED_EXTS)}")
    return ext


def save_uploaded_image_from_bytes(raw: bytes, filename: str, item_dir: Path, index: int) -> str:
    ext = validate_extension(filename)
    safe_name = secure_filename(Path(filename).stem) or f"image_{index:03d}"

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:8]

    global_copy = UPLOAD_DIR / f"upload_{stamp}_{uid}_{safe_name}{ext}"
    global_copy.write_bytes(raw)

    item_copy = item_dir / f"input_{index:03d}_{safe_name}{ext}"
    item_copy.write_bytes(raw)
    return str(item_copy)


def image_path_to_data_url(image_path: str) -> str:
    if not image_path or not os.path.exists(image_path):
        return ""
    with Image.open(image_path) as im:
        im = im.convert("RGBA")
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def format_probs(probabilities: dict) -> str:
    return " | ".join(f"{k}: {v:.2f}" for k, v in probabilities.items())


def pick_best_voronoi_images(voronoi_root: Path, image_stem: str):
    folder = voronoi_root / image_stem
    if not folder.exists():
        return "", ""

    pngs = sorted(folder.glob("*.png"))
    if not pngs:
        return "", ""

    overlay = next((p for p in pngs if "overlay" in p.name.lower()), None) or pngs[0]
    hist = next((p for p in pngs if "hist" in p.name.lower()), None)
    if hist is None:
        hist = pngs[1] if len(pngs) > 1 else ""

    return str(overlay) if overlay else "", str(hist) if hist else ""


def decode_base64_image(data_url: str) -> Image.Image:
    if not data_url or "," not in data_url:
        raise ValueError("Invalid base64 image format.")
    _, b64data = data_url.split(",", 1)
    raw = base64.b64decode(b64data)
    return Image.open(io.BytesIO(raw))


def save_edited_mask_from_base64(data_url: str, original_mask_path: str, out_path: Path) -> str:
    edited_img = decode_base64_image(data_url).convert("L")

    with Image.open(original_mask_path) as orig:
        edited_img = edited_img.resize(orig.size, Image.NEAREST)

    out_path.parent.mkdir(exist_ok=True)
    edited_img.save(str(out_path))
    return str(out_path)


def parse_numeric_metrics(result_dict: dict) -> list[dict]:
    metrics = []

    if not isinstance(result_dict, dict):
        return metrics

    for key, value in result_dict.items():
        if isinstance(value, (int, float)):
            label = key.replace("_", " ").strip()
            display = f"{value:.4f}" if isinstance(value, float) else str(value)
            metrics.append({
                "key": key,
                "label": label,
                "value": display
            })

    return metrics


def extract_class_probabilities(probabilities: dict) -> dict:
    ordered_keys = ["dots", "mixed", "lines", "irregular"]
    cleaned = {}
    for key in ordered_keys:
        cleaned[key] = float(probabilities.get(key, 0.0))
    for key, value in probabilities.items():
        if key not in cleaned:
            cleaned[key] = float(value)
    return cleaned


def decode_data_url_to_pil(data_url: str):
    if not data_url or "," not in data_url:
        return None
    try:
        _, b64data = data_url.split(",", 1)
        raw = base64.b64decode(b64data)
        return Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        return None


def fit_image_size(img_w, img_h, max_w, max_h):
    if img_w <= 0 or img_h <= 0:
        return max_w, max_h
    scale = min(max_w / img_w, max_h / img_h)
    return img_w * scale, img_h * scale


def wrap_text(text: str, max_chars: int = 110):
    if not text:
        return []
    lines = []
    for paragraph in str(text).split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue

        current = words[0]
        for word in words[1:]:
            candidate = current + " " + word
            if len(candidate) <= max_chars:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def draw_result_block(pdf, x, y, width, title, data_url, caption="", max_height=210):
    pil_img = decode_data_url_to_pil(data_url)
    if pil_img is None:
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(x, y, title)
        pdf.setFont("Helvetica", 9)
        pdf.drawString(x, y - 14, "No image available")
        return y - 40

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(x, y, title)
    y -= 14

    img_w, img_h = pil_img.size
    draw_w, draw_h = fit_image_size(img_w, img_h, width, max_height)

    reader = ImageReader(pil_img)
    pdf.drawImage(
        reader,
        x,
        y - draw_h,
        width=draw_w,
        height=draw_h,
        preserveAspectRatio=True,
        mask="auto"
    )

    y = y - draw_h - 8
    if caption:
        pdf.setFont("Helvetica", 8)
        pdf.drawString(x, y, str(caption)[:100])
        y -= 12

    return y - 8


def build_single_result_pdf_bytes(batch_data: dict, current_item: dict, current_analysis: dict) -> bytes:
    buffer = io.BytesIO()
    pdf = pdf_canvas.Canvas(buffer, pagesize=letter)
    page_w, page_h = letter

    margin = 36
    usable_w = page_w - 2 * margin
    y = page_h - margin

    def new_page():
        nonlocal y
        pdf.showPage()
        y = page_h - margin

    def ensure_space(required_height):
        nonlocal y
        if y - required_height < margin:
            new_page()

    pdf.setTitle("AFM Analysis Export")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(margin, y, "AFM Analysis Export")
    y -= 24

    pdf.setFont("Helvetica", 10)
    meta_lines = [
        f"Job ID: {batch_data.get('job_id', '-')}",
        f"Job Directory: {batch_data.get('job_dir', '-')}",
        f"Item ID: {current_item.get('item_id', '-')}",
        f"Filename: {current_analysis.get('original_filename', current_item.get('original_filename', '-'))}",
        f"Predicted Class: {current_analysis.get('predicted_class', current_item.get('predicted_class', '-'))}",
        f"Confidence: {float(current_analysis.get('confidence', current_item.get('confidence', 0.0))) * 100:.1f}%",
        f"CNN Model: {current_analysis.get('cnn_model_name', current_item.get('cnn_model_name', '-'))}",
        f"U-Net Model: {current_analysis.get('unet_model_name', current_item.get('unet_model_name', '-'))}",
    ]
    for line in meta_lines:
        pdf.drawString(margin, y, line[:130])
        y -= 13

    y -= 8

    image_blocks = [
        ("Original", current_analysis.get("original_image_url", current_item.get("original_image_url", "")), current_analysis.get("original_filename", "")),
        ("Final Mask", current_analysis.get("final_mask_url", ""), current_analysis.get("final_mask_filename", "")),
        (current_analysis.get("extra1_note", "Extra Output 1"), current_analysis.get("extra1_url", ""), current_analysis.get("extra1_note", "")),
        (current_analysis.get("extra2_note", "Extra Output 2"), current_analysis.get("extra2_url", ""), current_analysis.get("extra2_note", "")),
        (current_analysis.get("extra3_note", "Extra Output 3"), current_analysis.get("extra3_url", ""), current_analysis.get("extra3_note", "")),
        (current_analysis.get("extra4_note", "Extra Output 4"), current_analysis.get("extra4_url", ""), current_analysis.get("extra4_note", "")),
    ]

    for title, src, caption in image_blocks:
        if not src:
            continue
        ensure_space(260)
        y = draw_result_block(pdf, margin, y, usable_w, title, src, caption, max_height=230)

    metrics = current_analysis.get("metrics", [])
    if metrics:
        ensure_space(60 + 16 * len(metrics))
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(margin, y, "Metrics")
        y -= 18
        for metric in metrics:
            ensure_space(16)
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(margin, y, str(metric.get("label", ""))[:55])
            pdf.setFont("Helvetica", 10)
            pdf.drawString(margin + 230, y, str(metric.get("value", ""))[:45])
            y -= 14

    details = current_analysis.get("details", "")
    if details:
        detail_lines = wrap_text(details, 115)
        ensure_space(40)
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(margin, y, "Details")
        y -= 18
        pdf.setFont("Helvetica", 9)
        for line in detail_lines:
            ensure_space(12)
            pdf.drawString(margin, y, line[:130])
            y -= 11

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


def build_batch_pdf_bytes(batch_data: dict, items: list, analysis_results: list) -> bytes:
    buffer = io.BytesIO()
    pdf = pdf_canvas.Canvas(buffer, pagesize=letter)
    page_w, page_h = letter

    margin = 36
    usable_w = page_w - 2 * margin

    pdf.setTitle("AFM Batch Analysis Export")

    analysis_map = {}
    for result in analysis_results:
        item_id = result.get("item_id")
        if item_id:
            analysis_map[item_id] = result

    for idx, item in enumerate(items):
        if idx > 0:
            pdf.showPage()

        y = page_h - margin
        result = analysis_map.get(item.get("item_id"))

        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(margin, y, "AFM Batch Analysis Export")
        y -= 24

        pdf.setFont("Helvetica", 10)
        meta_lines = [
            f"Job ID: {batch_data.get('job_id', '-')}",
            f"Item {item.get('item_index', '-')}: {item.get('original_filename', '-')}",
            f"Item ID: {item.get('item_id', '-')}",
            f"Predicted Class: {(result or item).get('predicted_class', '-')}",
            f"Confidence: {float((result or item).get('confidence', 0.0)) * 100:.1f}%",
        ]
        for line in meta_lines:
            pdf.drawString(margin, y, line[:130])
            y -= 13

        y -= 10

        if result:
            image_blocks = [
                ("Original", result.get("original_image_url", item.get("original_image_url", "")), result.get("original_filename", "")),
                ("Final Mask", result.get("final_mask_url", ""), result.get("final_mask_filename", "")),
                (result.get("extra1_note", "Extra Output 1"), result.get("extra1_url", ""), result.get("extra1_note", "")),
                (result.get("extra2_note", "Extra Output 2"), result.get("extra2_url", ""), result.get("extra2_note", "")),
            ]

            for title, src, caption in image_blocks:
                if not src:
                    continue
                if y < 280:
                    pdf.showPage()
                    y = page_h - margin
                y = draw_result_block(pdf, margin, y, usable_w, title, src, caption, max_height=180)

            metrics = result.get("metrics", [])
            if metrics:
                if y < 140:
                    pdf.showPage()
                    y = page_h - margin
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(margin, y, "Metrics")
                y -= 16
                for metric in metrics[:12]:
                    if y < margin + 20:
                        pdf.showPage()
                        y = page_h - margin
                    pdf.setFont("Helvetica-Bold", 9)
                    pdf.drawString(margin, y, str(metric.get("label", ""))[:55])
                    pdf.setFont("Helvetica", 9)
                    pdf.drawString(margin + 220, y, str(metric.get("value", ""))[:45])
                    y -= 12
        else:
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(margin, y, "Status")
            y -= 18
            pdf.setFont("Helvetica", 10)
            pdf.drawString(margin, y, "No analysis result available for this item.")
            y -= 14

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


def sanitize_filename(name: str, fallback: str = "export") -> str:
    safe = secure_filename(name or "")
    return safe or fallback


def pdf_response(pdf_bytes: bytes, filename: str):
    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["Content-Length"] = str(len(pdf_bytes))
    return response


def process_single_file(file_storage, job_dir: Path, index: int) -> dict:
    if not file_storage or not file_storage.filename:
        raise ValueError("Encountered an empty file in the batch.")

    original_filename = Path(file_storage.filename).name
    item_id = uuid.uuid4().hex[:10]
    item_dir = job_dir / f"item_{index:03d}_{item_id}"
    item_dir.mkdir(parents=True, exist_ok=True)

    raw = file_storage.read()
    saved_path = save_uploaded_image_from_bytes(raw, original_filename, item_dir, index)

    cls = cnn_mod.predict_image(
        CNN_MODEL,
        saved_path,
        image_size=CNN_IMAGE_SIZE,
        in_channels=CNN_IN_CHANNELS,
    )

    predicted = cls.get("predicted_class", "unknown")
    confidence = float(cls.get("confidence", 0.0))
    probabilities = extract_class_probabilities(cls.get("probabilities", {}))
    predicted_for_ui = "mixed" if predicted == "irregular" else predicted

    mask_path = run_unet_cached(saved_path, job_dir=item_dir)

    return {
        "item_id": item_id,
        "item_index": index,
        "item_dir": str(item_dir),
        "saved_path": saved_path,
        "saved_filename": Path(saved_path).name,
        "original_filename": original_filename,
        "mask_path": mask_path,
        "mask_filename": Path(mask_path).name,
        "predicted_class": predicted_for_ui,
        "confidence": confidence,
        "probabilities": probabilities,
        "cnn_model_name": CNN_WEIGHTS.name,
        "unet_model_name": UNET_WEIGHTS.name,
        "original_image_url": image_path_to_data_url(saved_path),
        "mask_image_url": image_path_to_data_url(mask_path),
    }


def analyze_one_item(item_payload: dict, edited_mask_data_url: str = "") -> dict:
    job_id = item_payload.get("job_id")
    job_dir = Path(item_payload.get("job_dir"))
    item_id = item_payload.get("item_id")

    saved_path = item_payload.get("saved_path")
    mask_path = item_payload.get("mask_path")
    predicted_for_ui = item_payload.get("predicted_class")
    confidence = float(item_payload.get("confidence", 0.0))
    probabilities = extract_class_probabilities(item_payload.get("probabilities", {}))
    cnn_model_name = item_payload.get("cnn_model_name", CNN_WEIGHTS.name)
    unet_model_name = item_payload.get("unet_model_name", UNET_WEIGHTS.name)
    original_filename = item_payload.get(
        "original_filename",
        Path(saved_path).name if saved_path else ""
    )

    item_dir = Path(mask_path).parent if mask_path else job_dir

    final_mask_path = mask_path
    if edited_mask_data_url:
        edited_final_out = item_dir / "edited_mask.png"
        final_mask_path = save_edited_mask_from_base64(
            edited_mask_data_url,
            mask_path,
            edited_final_out
        )

    extra1_path = extra2_path = extra3_path = extra4_path = ""
    extra1_note = extra2_note = extra3_note = extra4_note = ""
    extra_details_lines = []

    all_metrics = []
    summary = ""

    if predicted_for_ui in ("dots", "mixed"):
        vor_dir = item_dir / "voronoi_outputs"
        vor_results = vor_mod.run_voronoi_analysis(
            image_path=final_mask_path,
            image_size=1.0,
            output_dir=str(vor_dir),
            threshold_edge=0.025,
            max_size=1024,
        )

        stem = Path(final_mask_path).stem
        v1, v2 = pick_best_voronoi_images(vor_dir, stem)

        extra1_path, extra2_path = v1, v2
        extra1_note = "Voronoi Overlay"
        extra2_note = "Nearest-Neighbour Histogram"

        if vor_results is None:
            extra_details_lines.append("Voronoi: no results (analysis returned None).")
        else:
            extra_details_lines.append("Voronoi results:")
            for k, v in vor_results.items():
                extra_details_lines.append(f"  {k}: {v}")
            all_metrics.extend(parse_numeric_metrics(vor_results))
            summary = f"{predicted_for_ui.upper()} class · Voronoi analysis applied"

    if predicted_for_ui in ("lines", "mixed"):
        cw_dir = item_dir / "colorwheel_output"
        cw_results = cw_mod.analyze_image(
            image_path=final_mask_path,
            output_dir=str(cw_dir),
            num_clusters=8,
        )

        if cw_results is None:
            extra_details_lines.append("Color wheel: no results (analysis returned None).")
        else:
            extra3_path = cw_results.get("color_wheel_image", "")
            extra4_path = cw_results.get("one_phase_image", "")
            extra3_note = "Color Wheel"
            extra4_note = "One-Phase Map"

            extra_details_lines.append("Color wheel results:")
            for k, v in cw_results.items():
                extra_details_lines.append(f"  {k}: {v}")
            all_metrics.extend(parse_numeric_metrics(cw_results))

            if summary:
                summary += " + ColorWheel analysis applied"
            else:
                summary = f"{predicted_for_ui.upper()} class · ColorWheel analysis applied"

    if predicted_for_ui not in ("dots", "lines", "mixed"):
        extra_details_lines.append(f"No rule for class: {predicted_for_ui}")
        summary = f"{predicted_for_ui.upper()} class · No analysis rule found"

    details = (
        f"CNN predicted class: {predicted_for_ui}\n"
        f"Confidence: {confidence:.3f}\n"
        f"Probabilities: {format_probs(probabilities)}\n\n"
        + "\n".join(extra_details_lines)
    )

    seen = set()
    unique_metrics = []
    for item in all_metrics:
        key = item["key"]
        if key not in seen:
            seen.add(key)
            unique_metrics.append(item)

    return {
        "message": "Analysis complete",
        "summary": summary or "Analysis complete",
        "job_id": job_id,
        "job_dir": str(job_dir),
        "item_id": item_id,
        "cnn_model_name": cnn_model_name,
        "unet_model_name": unet_model_name,
        "predicted_class": predicted_for_ui,
        "confidence": confidence,
        "probabilities": probabilities,
        "final_mask_path": final_mask_path,
        "final_mask_filename": Path(final_mask_path).name if final_mask_path else "",
        "original_filename": original_filename,
        "original_image_url": image_path_to_data_url(saved_path),
        "final_mask_url": image_path_to_data_url(final_mask_path),
        "extra1_url": image_path_to_data_url(extra1_path) if extra1_path else "",
        "extra2_url": image_path_to_data_url(extra2_path) if extra2_path else "",
        "extra3_url": image_path_to_data_url(extra3_path) if extra3_path else "",
        "extra4_url": image_path_to_data_url(extra4_path) if extra4_path else "",
        "extra1_note": extra1_note,
        "extra2_note": extra2_note,
        "extra3_note": extra3_note,
        "extra4_note": extra4_note,
        "metrics": unique_metrics,
        "details": details,
    }


# ----------------------------
# 5) FLASK APP
# ----------------------------
app = Flask(__name__)
CORS(app)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "message": "AFM backend running"})


@app.route("/job_file/<job_id>/<path:filename>", methods=["GET"])
def serve_job_file(job_id, filename):
    job_dir = RESULTS_DIR / f"job_{job_id}"
    file_path = (job_dir / filename).resolve()

    try:
        root = job_dir.resolve()
        if root not in file_path.parents and file_path != root:
            return abort(403)
    except Exception:
        return abort(403)

    if not file_path.exists():
        return abort(404)

    return send_file(str(file_path))


@app.route("/api/upload", methods=["POST"])
def upload_and_predict():
    try:
        files = request.files.getlist("files")
        if not files:
            single_file = request.files.get("file")
            if single_file:
                files = [single_file]

        if not files:
            return jsonify({"error": "No files uploaded."}), 400

        valid_files = [f for f in files if f and f.filename]
        if not valid_files:
            return jsonify({"error": "All uploaded files were empty."}), 400

        client_session_id = request.form.get("client_session_id", "").strip()
        if not client_session_id:
            client_session_id = uuid.uuid4().hex[:12]

        job_id = uuid.uuid4().hex[:10]
        job_dir = RESULTS_DIR / f"job_{job_id}"
        job_dir.mkdir(exist_ok=True)

        items = []
        for index, file_storage in enumerate(valid_files, start=1):
            item_data = process_single_file(file_storage, job_dir, index)
            item_data["job_id"] = job_id
            item_data["job_dir"] = str(job_dir)
            items.append(item_data)

        return jsonify({
            "message": "Batch upload + prediction successful",
            "client_session_id": client_session_id,
            "job_id": job_id,
            "job_dir": str(job_dir),
            "batch_count": len(items),
            "cnn_model_name": CNN_WEIGHTS.name,
            "unet_model_name": UNET_WEIGHTS.name,
            "items": items,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/run-analysis", methods=["POST"])
def run_analysis():
    try:
        data = request.get_json(force=True)
        edited_mask_data = data.get("edited_mask_data_url", "")
        result = analyze_one_item(data, edited_mask_data)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/run-analysis-batch", methods=["POST"])
def run_analysis_batch():
    try:
        data = request.get_json(force=True)

        job_id = data.get("job_id")
        job_dir = data.get("job_dir")
        items = data.get("items", [])

        if not job_id or not job_dir:
            return jsonify({"error": "Missing job_id or job_dir."}), 400

        if not isinstance(items, list) or not items:
            return jsonify({"error": "No batch items provided."}), 400

        edited_masks_by_item_id = data.get("edited_masks_by_item_id", {})
        if not isinstance(edited_masks_by_item_id, dict):
            edited_masks_by_item_id = {}

        results = []
        for item in items:
            item_payload = dict(item)
            item_payload["job_id"] = job_id
            item_payload["job_dir"] = job_dir

            item_id = item_payload.get("item_id", "")
            edited_mask_data = edited_masks_by_item_id.get(item_id, "")

            result = analyze_one_item(item_payload, edited_mask_data)
            results.append(result)

        return jsonify({
            "message": "Batch analysis complete",
            "job_id": job_id,
            "job_dir": job_dir,
            "result_count": len(results),
            "results": results,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/export-pdf", methods=["POST"])
def export_single_pdf():
    try:
        data = request.get_json(force=True)

        batch_data = data.get("batch_data")
        current_item = data.get("current_item")
        current_analysis = data.get("current_analysis")

        if not isinstance(batch_data, dict):
            return jsonify({"error": "Missing or invalid batch_data."}), 400
        if not isinstance(current_item, dict):
            return jsonify({"error": "Missing or invalid current_item."}), 400
        if not isinstance(current_analysis, dict):
            return jsonify({"error": "Missing or invalid current_analysis."}), 400

        pdf_bytes = build_single_result_pdf_bytes(
            batch_data=batch_data,
            current_item=current_item,
            current_analysis=current_analysis,
        )

        base_name = Path(
            current_analysis.get("original_filename")
            or current_item.get("original_filename")
            or "afm_result"
        ).stem
        filename = f"{sanitize_filename(base_name, 'afm_result')}_analysis.pdf"

        return pdf_response(pdf_bytes, filename)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/export-pdf-batch", methods=["POST"])
def export_batch_pdf():
    try:
        data = request.get_json(force=True)

        batch_data = data.get("batch_data")
        items = data.get("items")
        analysis_results = data.get("analysis_results")

        if not isinstance(batch_data, dict):
            return jsonify({"error": "Missing or invalid batch_data."}), 400
        if not isinstance(items, list) or not items:
            return jsonify({"error": "Missing or invalid items list."}), 400
        if not isinstance(analysis_results, list):
            return jsonify({"error": "Missing or invalid analysis_results list."}), 400

        pdf_bytes = build_batch_pdf_bytes(
            batch_data=batch_data,
            items=items,
            analysis_results=analysis_results,
        )

        job_id = sanitize_filename(batch_data.get("job_id", "batch"))
        filename = f"afm_batch_{job_id}.pdf"

        return pdf_response(pdf_bytes, filename)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8050, debug=True)