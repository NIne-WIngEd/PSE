#!/usr/bin/env python3
"""Run the repository's original 3.colorwheel.py in an isolated process."""

from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path


def import_module_from_file(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--result-json", required=True)
    parser.add_argument("--num-clusters", type=int, default=8)
    args = parser.parse_args()

    result_path = Path(args.result_json)
    result_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        module = import_module_from_file(
            "original_colorwheel_worker_module",
            Path(args.module).resolve(),
        )
        start = time.perf_counter()
        result = module.analyze_image(
            image_path=str(Path(args.image).resolve()),
            output_dir=str(Path(args.output_dir).resolve()),
            num_clusters=args.num_clusters,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        payload = {
            "status": "completed",
            "elapsed_ms": elapsed_ms,
            "result_type": type(result).__name__,
        }
    except Exception as exc:
        payload = {
            "status": "failed",
            "elapsed_ms": "",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        }

    result_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 0 if payload["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
