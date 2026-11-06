"""Consistent JSON output formatting for OCR results."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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
    document_id: str = ""
    filename: str
    document_type: str = "unknown"
    document_type_confidence: float = 0.0
    matched_indicators: List[str] = Field(default_factory=list)
    status: str = "processed"
    processed_at: str
    page_count: int
    pages: List[PageResult] = Field(default_factory=list)
    raw_text: str = ""
    patient: Dict[str, Any] = Field(default_factory=dict)
    document_date: Optional[Dict[str, Any]] = None
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class ResultFormatter:
    """Build an :class:`OCRResult` from per-page OCR output."""

    def format(
        self,
        filename: str,
        pages: List[Dict[str, Any]],
        document_id: str = "",
        classification: Optional[Any] = None,
        warnings: Optional[List[str]] = None,
    ) -> OCRResult:
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

        document_type = "unknown"
        document_type_confidence = 0.0
        matched_indicators: List[str] = []
        if classification is not None:
            document_type = getattr(classification, "document_type", document_type)
            if hasattr(document_type, "value"):
                document_type = document_type.value
            document_type_confidence = getattr(classification, "confidence", 0.0)
            matched_indicators = list(getattr(classification, "matched_indicators", []))

        return OCRResult(
            document_id=document_id,
            filename=filename,
            document_type=document_type,
            document_type_confidence=document_type_confidence,
            matched_indicators=matched_indicators,
            status="processed",
            processed_at=datetime.now(timezone.utc).isoformat(),
            page_count=len(page_results),
            pages=page_results,
            raw_text="\n\n".join(part for part in raw_parts if part),
            warnings=list(warnings or []),
        )