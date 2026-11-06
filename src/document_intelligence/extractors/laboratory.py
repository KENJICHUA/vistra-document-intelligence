"""Laboratory result extractor."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .base import BaseExtractor
from .common import find_document_date, find_patient_name, iter_lines, make_field


class LaboratoryExtractor(BaseExtractor):
    document_type = "laboratory_result"

    _ROW_RE = re.compile(
        r"^(?P<name>[A-Za-z][A-Za-z0-9 ,()/%-]*?)\s*:?\s+"
        r"(?P<result>[<>]?\d+(?:[.,]\d+)?)\s*"
        r"(?P<unit>[A-Za-z%][A-Za-z0-9/%.\-]*)?\s*"
        r"(?P<rest>.*)$"
    )

    _FLAG_TOKENS = {"h", "l", "high", "low", "*", "abnormal"}

    def extract(self, document: Any) -> Dict[str, Any]:
        warnings: List[str] = []
        tests: List[Dict[str, Any]] = []

        for page_number, line in iter_lines(document):
            text = str(line.get("text", "")).strip()
            confidence = float(line.get("confidence", 0.0) or 0.0)
            if not text:
                continue

            match = self._ROW_RE.match(text)
            if not match:
                continue

            name = match.group("name").strip(" ,:-")
            result_value = match.group("result").strip()
            unit = (match.group("unit") or "").strip() or None
            rest = (match.group("rest") or "").strip()

            if not name or not any(ch.isalpha() for ch in name):
                continue

            flag = self._extract_flag(rest)
            reference_range = self._extract_reference_range(rest, flag)

            test = {
                "name": name,
                "result": result_value,
                "unit": unit,
                "reference_range": reference_range,
                "flag": flag,
                "confidence": round(confidence, 4),
                "source": {"page": page_number, "text": text},
            }
            tests.append(test)

            if confidence < 0.7:
                warnings.append(
                    f"Low OCR confidence ({confidence:.2f}) for laboratory row: {text}"
                )

        if not tests:
            warnings.append("No laboratory test rows could be extracted.")

        patient_name = find_patient_name(document)
        document_date = find_document_date(document)

        return {
            "patient": {"name": patient_name, "patient_id": None},
            "document_date": document_date,
            "extracted_data": {"tests": tests},
            "warnings": warnings,
        }

    @staticmethod
    def _extract_flag(text: str) -> Optional[str]:
        tokens = text.split()
        for token in reversed(tokens):
            cleaned = token.strip(".,:;()").lower()
            if cleaned in LaboratoryExtractor._FLAG_TOKENS:
                return token.strip(".,:;()")
        return None

    @staticmethod
    def _extract_reference_range(text: str, flag: Optional[str]) -> Optional[str]:
        value = text
        if flag:
            value = value.replace(flag, "").strip()
        value = value.strip(" ,:-")
        return value or None