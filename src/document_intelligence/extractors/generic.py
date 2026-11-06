"""Generic fallback extractor."""

from __future__ import annotations

from typing import Any, Dict

from .base import BaseExtractor
from .common import find_document_date, find_patient_name


class GenericExtractor(BaseExtractor):
    document_type = "generic"

    def extract(self, document: Any) -> Dict[str, Any]:
        warnings = ["Document type is unknown or unsupported; returning raw OCR text only."]
        patient_name = find_patient_name(document)
        document_date = find_document_date(document)
        return {
            "patient": {"name": patient_name, "patient_id": None},
            "document_date": document_date,
            "extracted_data": {},
            "warnings": warnings,
        }