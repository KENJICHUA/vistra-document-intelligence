"""Prescription extractor."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from ..validation import make_warning
from .base import BaseExtractor
from .common import find_document_date, find_patient_name, iter_lines, make_field


class PrescriptionExtractor(BaseExtractor):
    document_type = "prescription"

    _MED_UNITS = re.compile(
        r"\b(mg|ml|g|mcg|iu|units?|tablet|tablets|capsule|capsules|tab|caps)\b",
        flags=re.IGNORECASE,
    )

    def extract(self, document: Any) -> Dict[str, Any]:
        warnings: List[str] = []
        lines = list(iter_lines(document))

        prescriber = self._find_labeled_text(lines, ["prescriber", "doctor", "physician", "dr.", "provider"])
        clinic = self._find_labeled_text(lines, ["clinic", "hospital", "medical center", "health center"])
        prescription_date = self._find_labeled_date(lines, ["date", "prescription date", "rx date"])
        if prescription_date is None:
            prescription_date = find_document_date(document)

        medications = self._extract_medications(lines)
        if not medications:
            warnings.append(make_warning("NO_MEDICATIONS", "extracted_data.medications", "No medication rows could be extracted."))

        patient_name = find_patient_name(document)

        return {
            "patient": {"name": patient_name, "patient_id": None},
            "document_date": prescription_date,
            "extracted_data": {
                "prescriber": prescriber,
                "clinic": clinic,
                "prescription_date": prescription_date,
                "medications": medications,
            },
            "warnings": warnings,
        }

    @staticmethod
    def _find_labeled_text(lines: List, labels: List[str]) -> Optional[Dict[str, Any]]:
        for page_number, line in lines:
            text = str(line.get("text", "")).strip()
            lowered = text.lower()
            if not any(label in lowered for label in labels):
                continue
            value = text
            for sep in (":", "-"):
                if sep in text:
                    idx = text.find(sep)
                    if idx != -1 and idx + 1 < len(text):
                        candidate = text[idx + 1 :].strip()
                        if candidate:
                            value = candidate
                            break
            if value and len(value) < 120:
                return make_field(value, line.get("confidence", 0.0), page_number, text)
        return None

    @staticmethod
    def _find_labeled_date(lines: List, labels: List[str]) -> Optional[Dict[str, Any]]:
        from .common import DATE_PATTERNS

        for page_number, line in lines:
            text = str(line.get("text", "")).strip()
            lowered = text.lower()
            if not any(label in lowered for label in labels):
                continue
            for pattern in DATE_PATTERNS:
                match = re.search(pattern, text, flags=re.IGNORECASE)
                if match:
                    return make_field(match.group(0), line.get("confidence", 0.0), page_number, text)
        return None

    @classmethod
    def _extract_medications(cls, lines: List) -> List[Dict[str, Any]]:
        medications: List[Dict[str, Any]] = []
        for page_number, line in lines:
            text = str(line.get("text", "")).strip()
            if not text:
                continue
            lowered = text.lower()
            if "rx" in lowered or cls._MED_UNITS.search(text):
                medications.append(
                    {
                        "medication": None,
                        "strength": None,
                        "dose": None,
                        "route": None,
                        "frequency": None,
                        "duration": None,
                        "quantity": None,
                        "refills": None,
                        "instructions": text,
                        "raw_text": text,
                        "confidence": round(float(line.get("confidence", 0.0) or 0.0), 4),
                        "source": {"page": page_number, "text": text},
                    }
                )
        return medications