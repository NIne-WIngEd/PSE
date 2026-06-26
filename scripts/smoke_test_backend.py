#!/usr/bin/env python3
"""Run a self-contained backend smoke test with a synthetic image."""

from __future__ import annotations

import importlib.util
import io
import os
import shutil
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    temp_root = Path(tempfile.mkdtemp(prefix="afm_backend_smoke_"))
    os.environ["AFM_RUNTIME_DIR"] = str(temp_root / "runtime")
    os.environ["AFM_DEVICE"] = "cpu"
    os.environ["FLASK_DEBUG"] = "0"

    try:
        app_path = ROOT / "backend" / "app.py"
        spec = importlib.util.spec_from_file_location("afm_backend_smoke", app_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not import {app_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        client = module.app.test_client()
        health = client.get("/api/health")
        if health.status_code != 200 or not health.get_json().get("ok"):
            raise RuntimeError(f"Health endpoint failed: {health.status_code} {health.data!r}")

        image = Image.new("RGB", (256, 256), "white")
        draw = ImageDraw.Draw(image)
        for x in range(24, 232, 32):
            draw.ellipse((x, 100, x + 12, 112), fill="black")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        response = client.post(
            "/api/upload",
            data={
                "files": (buffer, "synthetic_smoke.png"),
                "client_session_id": "repository_smoke_test",
            },
            content_type="multipart/form-data",
        )
        if response.status_code != 200:
            raise RuntimeError(f"Upload endpoint failed: {response.status_code} {response.data!r}")
        payload = response.get_json()
        items = payload.get("items") or []
        if len(items) != 1:
            raise RuntimeError(f"Expected one upload item, received {len(items)}")
        item = items[0]
        if item.get("predicted_class") not in {"dots", "irregular", "lines", "mixed"}:
            raise RuntimeError(f"Unexpected prediction payload: {item}")
        if not item.get("mask_filename"):
            raise RuntimeError("U-Net mask was not generated.")

        print("Backend smoke test passed.")
        print(f"- health endpoint: {health.status_code}")
        print(f"- upload endpoint: {response.status_code}")
        print(f"- predicted class: {item['predicted_class']}")
        print(f"- mask: {item['mask_filename']}")
        return 0
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
