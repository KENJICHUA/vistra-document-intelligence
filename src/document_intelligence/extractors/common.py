"""Shared extraction helpers."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


DATE_PATTERNS = [
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b",
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}\b",
]


def make_field(value: Any, confidence: float, page: int, text: str) -> Dict[str, Any]:
    return {
        "value": value,
        "confidence": round(float(confidence), 4),
        "source": {"page": page, "text": text},
    }


def iter_lines(document: Any) -> List[Tuple[int, Dict[str, Any]]]:
    result: List[Tuple[int, Dict[str, Any]]] = []
    for page in getattr(document, "pages", []) or []:
        page_number = getattr(page, "page_number", None)
        if page_number is None and isinstance(page, dict):
            page_number = page.get("page_number")
        lines = getattr(page, "lines", None)
        if lines is None and isinstance(page, dict):
            lines = page.get("lines", [])
        for line in lines or []:
            if isinstance(line, dict):
                item = line
            else:
                item = line.model_dump() if hasattr(line, "model_dump") else dict(line)
            result.append((int(page_number or 0), item))
    return result


def find_patient_name(document: Any) -> Optional[Dict[str, Any]]:
    patterns = [
        r"patient\s*(?:name)?\s*[:\-]\s*(.+)",
        r"name\s*[:\-]\s*(.+)",
    ]
    for page_number, line in iter_lines(document):
        text = str(line.get("text", "")).strip()
        lowered = text.lower()
        for pattern in patterns:
            match = re.search(pattern, lowered)
            if match:
                # Use original text slice after separator to preserve casing.
                sep_index = None
                for sep in (":", "-"):
                    idx = text.find(sep)
                    if idx != -1:
                        sep_index = idx
                        break
                if sep_index is not None and sep_index + 1 < len(text):
                    value = text[sep_index + 1 :].strip()
                else:
                    value = text[match.start(1) :].strip() if match.group(1) else None
                if value and len(value) < 80:
                    return make_field(value, line.get("confidence", 0.0), page_number, text)
    return None


def find_document_date(document: Any) -> Optional[Dict[str, Any]]:
    for page_number, line in iter_lines(document):
        text = str(line.get("text", "")).strip()
        for pattern in DATE_PATTERNS:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return make_field(match.group(0), line.get("confidence", 0.0), page_number, text)
    return None