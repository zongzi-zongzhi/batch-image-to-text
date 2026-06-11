from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import OcrRecord


def export_all(records: list[OcrRecord], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    export_markdown(records, output_dir / "ocr_raw.md")
    export_jsonl(records, output_dir / "ocr_raw.jsonl")
    export_index_csv(records, output_dir / "images_index.csv")
    export_review_markdown(records, output_dir / "ocr_review.md")


def export_markdown(records: list[OcrRecord], output_path: Path) -> None:
    lines = ["# OCR 原文提取结果", ""]
    for index, record in enumerate(records, start=1):
        lines.extend(
            [
                f"## {index}. {record.file_name}",
                "",
                f"- 图片路径：`{record.image_path}`",
                f"- 状态：{record.status}",
                f"- 平均置信度：{_format_confidence(record.confidence)}",
                f"- 是否需要复核：{'是' if record.needs_review else '否'}",
                "",
            ]
        )
        if record.error:
            lines.extend(["错误信息：", "", f"```text\n{record.error}\n```", ""])
        lines.extend(["原文：", "", "```text", record.text or "（未识别到文字）", "```", ""])
    output_path.write_text("\n".join(lines), encoding="utf-8")


def export_jsonl(records: list[OcrRecord], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")


def export_index_csv(records: list[OcrRecord], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "file_name",
                "image_path",
                "status",
                "confidence",
                "line_count",
                "char_count",
                "needs_review",
                "error",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "file_name": record.file_name,
                    "image_path": record.image_path,
                    "status": record.status,
                    "confidence": _format_confidence(record.confidence),
                    "line_count": record.line_count,
                    "char_count": record.char_count,
                    "needs_review": record.needs_review,
                    "error": record.error,
                }
            )


def export_review_markdown(records: list[OcrRecord], output_path: Path) -> None:
    review_records = [record for record in records if record.needs_review]
    lines = ["# OCR 复核清单", ""]
    if not review_records:
        lines.append("没有发现需要复核的图片。")
    for index, record in enumerate(review_records, start=1):
        reason = _review_reason(record)
        lines.extend(
            [
                f"## {index}. {record.file_name}",
                "",
                f"- 图片路径：`{record.image_path}`",
                f"- 原因：{reason}",
                f"- 状态：{record.status}",
                f"- 平均置信度：{_format_confidence(record.confidence)}",
                "",
            ]
        )
        if record.text:
            lines.extend(["当前识别原文：", "", "```text", record.text, "```", ""])
        if record.error:
            lines.extend(["错误信息：", "", "```text", record.error, "```", ""])
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _format_confidence(confidence: float | None) -> str:
    return "" if confidence is None else f"{confidence:.4f}"


def _review_reason(record: OcrRecord) -> str:
    if record.status == "failed":
        return "识别失败"
    if record.status == "empty":
        return "未识别到文字"
    if record.confidence is not None and record.confidence < 0.75:
        return "平均置信度低于 0.75"
    return "需要人工确认"
