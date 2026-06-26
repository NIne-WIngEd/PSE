#!/usr/bin/env python3
"""Isolated ColorWheel worker with JSON output for timeout-safe callers."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any


def import_module_from_file(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def json_safe(value: Any):
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--result-json", required=True)
    parser.add_argument("--num-clusters", type=int, default=8)
    parser.add_argument("--max-dimension", type=int, default=0)
    parser.add_argument("--max-fit-samples", type=int, default=10000)
    parser.add_argument("--min-component-size", type=int, default=15)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result_json = Path(args.result_json).resolve()
    result_json.parent.mkdir(parents=True, exist_ok=True)

    try:
        module_path = Path(args.module).resolve()
        image_path = Path(args.image).resolve()
        output_dir = Path(args.output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        module = import_module_from_file("colorwheel_isolated_worker", module_path)
        start = time.perf_counter()
        result = module.analyze_image(
            image_path=str(image_path),
            output_dir=str(output_dir),
            num_clusters=args.num_clusters,
            max_dimension=args.max_dimension,
            max_fit_samples=args.max_fit_samples,
            min_component_size=args.min_component_size,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        payload = {
            "status": "completed",
            "elapsed_ms": elapsed_ms,
            "result": json_safe(result),
        }
        exit_code = 0
    except Exception as exc:
        payload = {
            "status": "failed",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback": traceback.format_exc(),
        }
        exit_code = 1

    result_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
