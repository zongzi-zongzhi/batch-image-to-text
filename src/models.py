from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class OcrRecord:
    image_path: str
    file_name: str
    status: str
    text: str
    confidence: float | None = None
    line_count: int = 0
    char_count: int = 0
    needs_review: bool = False
    error: str = ""

    @classmethod
    def success(cls, image_path: Path, text: str, confidence: float | None) -> "OcrRecord":
        normalized_text = text.strip()
        line_count = len([line for line in normalized_text.splitlines() if line.strip()])
        char_count = len(normalized_text)
        low_confidence = confidence is not None and confidence < 0.75
        empty = char_count == 0
        return cls(
            image_path=str(image_path),
            file_name=image_path.name,
            status="empty" if empty else "ok",
            text=normalized_text,
            confidence=confidence,
            line_count=line_count,
            char_count=char_count,
            needs_review=empty or low_confidence,
        )

    @classmethod
    def failure(cls, image_path: Path, error: Exception | str) -> "OcrRecord":
        return cls(
            image_path=str(image_path),
            file_name=image_path.name,
            status="failed",
            text="",
            confidence=None,
            needs_review=True,
            error=str(error),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
