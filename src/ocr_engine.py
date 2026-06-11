from __future__ import annotations

import logging
import os
import contextlib
from pathlib import Path

import numpy as np
from PIL import Image

from .models import OcrRecord


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def find_images(input_dir: Path, recursive: bool = False) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    return sorted(
        path
        for path in input_dir.glob(pattern)
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


class RapidOcrEngine:
    def __init__(self) -> None:
        project_root = Path(__file__).absolute().parents[1]
        os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
        os.environ.setdefault("RAPIDOCR_HOME", str(project_root / "models" / "rapidocr"))
        logging.disable(logging.CRITICAL)
        logging.getLogger("RapidOCR").setLevel(logging.ERROR)

        try:
            from rapidocr import RapidOCR
        except ImportError as exc:
            raise RuntimeError("缺少 RapidOCR 依赖，当前工具包可能不完整。") from exc

        with open(os.devnull, "w", encoding="utf-8") as devnull:
            with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
                self._ocr = RapidOCR()

    def extract(self, image_path: Path) -> OcrRecord:
        try:
            image = np.array(Image.open(image_path).convert("RGB"))
            with open(os.devnull, "w", encoding="utf-8") as devnull:
                with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
                    result = self._ocr(image)
            lines, confidences = _parse_rapidocr_result(result)
            avg_confidence = sum(confidences) / len(confidences) if confidences else None
            return OcrRecord.success(image_path, "\n".join(lines), avg_confidence)
        except Exception as exc:  # noqa: BLE001
            return OcrRecord.failure(image_path, exc)


# Alias kept so the rest of the app can stay simple.
PaddleOcrEngine = RapidOcrEngine


def _parse_rapidocr_result(result: object) -> tuple[list[str], list[float]]:
    texts = getattr(result, "txts", None)
    scores = getattr(result, "scores", None)
    if texts is not None:
        clean_texts = [str(text).strip() for text in texts if str(text).strip()]
        clean_scores = [_to_float(score) for score in (scores or [])]
        return clean_texts, [score for score in clean_scores if score is not None]

    if isinstance(result, tuple) and len(result) >= 2:
        rows = result[0] or []
        lines: list[str] = []
        confidences: list[float] = []
        for row in rows:
            if not row or len(row) < 2:
                continue
            text = str(row[1]).strip()
            confidence = _to_float(row[2] if len(row) > 2 else None)
            if text:
                lines.append(text)
            if confidence is not None:
                confidences.append(confidence)
        return lines, confidences

    return [], []


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
