"""Dental record and odontogram extractor."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .base import BaseExtractor
from .common import find_document_date, find_patient_name, iter_lines, make_field


class DentalExtractor(BaseExtractor):
    document_type = "dental_record"

    _TOOTH_RE = re.compile(r"\b(?:tooth\s*)?#?(\d{1,2})\b")
    _CONDITIONS = [
        "caries", "filling", "restoration", "missing", "extracted",
        "crown", "fracture", "healthy", "impacted", "root canal",
    ]

    def extract(self, document: Any) -> Dict[str, Any]:
        warnings: List[str] = []
        lines = list(iter_lines(document))

        teeth: List[Dict[str, Any]] = []
        for page_number, line in lines:
            text = str(line.get("text", "")).strip()
            lowered = text.lower()
            tooth_match = self._TOOTH_RE.search(text)
            condition = next((c for c in self._CONDITIONS if c in lowered), None)
            if tooth_match and condition:
                tooth = tooth_match.group(1)
                teeth.append(
                    {
                        "tooth": tooth,
                        "condition": condition,
                        "surface": None,
                        "confidence": round(float(line.get("confidence", 0.0) or 0.0), 4),
                        "source": {"page": page_number, "text": text},
                    }
                )

        if not teeth:
            warnings.append(
                "No tooth/condition pairs could be extracted; detailed odontogram parsing may require layout-specific review."
            )

        return {
            "patient": {"name": find_patient_name(document), "patient_id": None},
            "document_date": find_document_date(document),
            "extracted_data": {
                "tooth_numbering_system": None,
                "teeth": teeth,
            },
            "warnings": warnings,
        }