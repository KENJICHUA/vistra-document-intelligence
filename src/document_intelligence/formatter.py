"""Consistent JSON output formatting for OCR results."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class Line(BaseModel):
    text: str
    confidence: float
    bounding_box: List[int]


class PageResult(BaseModel):
    page_number: int
    text: str
    lines: List[Line] = Field(default_factory=list)


class OCRResult(BaseModel):
    filename: str
    processed_at: str
    page_count: int
    pages: List[PageResult] = Field(default_factory=list)
    raw_text: str = ""


class ResultFormatter:
    """Build an :class:`OCRResult` from per-page OCR output."""

    def format(self, filename: str, pages: List[Dict[str, Any]]) -> OCRResult:
        page_results: List[PageResult] = []
        raw_parts: List[str] = []

        for page in pages:
            lines = [Line(**line) for line in page.get("lines", [])]
            text = page.get("text", "")
            page_results.append(
                PageResult(
                    page_number=page["page_number"],
                    text=text,
                    lines=lines,
                )
            )
            raw_parts.append(text)

        return OCRResult(
            filename=filename,
            processed_at=datetime.now(timezone.utc).isoformat(),
            page_count=len(page_results),
            pages=page_results,
            raw_text="\n\n".join(part for part in raw_parts if part),
        )