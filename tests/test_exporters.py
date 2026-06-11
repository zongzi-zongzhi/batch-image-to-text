from pathlib import Path

from src.exporters import export_all
from src.models import OcrRecord


def test_export_all_creates_expected_files(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.jpg"
    record = OcrRecord.success(image_path, "第一行\n第二行", 0.98)

    export_all([record], tmp_path)

    assert (tmp_path / "ocr_raw.md").exists()
    assert (tmp_path / "ocr_raw.jsonl").exists()
    assert (tmp_path / "images_index.csv").exists()
    assert (tmp_path / "ocr_review.md").exists()
    assert "第一行" in (tmp_path / "ocr_raw.md").read_text(encoding="utf-8")
