"""Medical certificate extractor."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .base import BaseExtractor
from .common import DATE_PATTERNS, find_document_date, find_patient_name, iter_lines, make_field


class MedicalCertificateExtractor(BaseExtractor):
    document_type = "medical_certificate"

    def extract(self, document: Any) -> Dict[str, Any]:
        warnings: List[str] = []

        patient_name = find_patient_name(document)
        issue_date = self._find_labeled_date(
            document, ["issue", "issued", "certificate date", "date issued", "date of issue"]
        )
        if issue_date is None:
            issue_date = find_document_date(document)

        examination_date = self._find_labeled_date(
            document, ["examination", "examined", "date of examination", "date examined"]
        )

        issuing_clinic = self._find_labeled_text(
            document, ["clinic", "hospital", "medical center", "health center", "issued by"]
        )
        diagnosis_reason = self._find_labeled_text(
            document, ["diagnosis", "reason", "complaint", "illness", "condition", "findings"]
        )
        rest_leave = self._find_labeled_text(
            document, ["rest", "leave", "absence", "days off", "off duty"]
        )
        fitness_statement = self._find_statement(
            document, ["fit to work", "fit for work", "medically fit", "unfit", "cleared", "fit for duty"]
        )
        provider_name = self._find_labeled_text(
            document, ["doctor", "physician", "provider", "examined by", "signed by", "dr."]
        )
        license_details = self._find_labeled_text(
            document, ["license", "prc", "registration", "license no"]
        )

        extracted_data: Dict[str, Any] = {
            "issuing_clinic": issuing_clinic,
            "examination_date": examination_date,
            "issue_date": issue_date,
            "diagnosis_reason": diagnosis_reason,
            "rest_leave": rest_leave,
            "fitness_statement": fitness_statement,
            "provider_name": provider_name,
            "license_details": license_details,
        }

        if patient_name is None:
            warnings.append("Patient name not detected.")
        if examination_date is None and issue_date is None:
            warnings.append("No examination or issue date detected.")
        if diagnosis_reason is None:
            warnings.append("No stated diagnosis or reason detected.")
        if fitness_statement is None:
            warnings.append("No fitness statement detected.")

        return {
            "patient": {"name": patient_name, "patient_id": None},
            "document_date": issue_date,
            "extracted_data": extracted_data,
            "warnings": warnings,
        }

    @staticmethod
    def _find_labeled_date(document: Any, labels: List[str]) -> Optional[Dict[str, Any]]:
        for page_number, line in iter_lines(document):
            text = str(line.get("text", "")).strip()
            lowered = text.lower()
            if not any(label in lowered for label in labels):
                continue
            for pattern in DATE_PATTERNS:
                match = re.search(pattern, text, flags=re.IGNORECASE)
                if match:
                    return make_field(match.group(0), line.get("confidence", 0.0), page_number, text)
        return None

    @staticmethod
    def _find_labeled_text(document: Any, labels: List[str]) -> Optional[Dict[str, Any]]:
        for page_number, line in iter_lines(document):
            text = str(line.get("text", "")).strip()
            lowered = text.lower()
            if not any(label in lowered for label in labels):
                continue
            # Prefer text after a separator when present.
            value = text
            for sep in (":", "-"):
                if sep in text:
                    idx = text.find(sep)
                    if idx != -1 and idx + 1 < len(text):
                        candidate = text[idx + 1 :].strip()
                        if candidate:
                            value = candidate
                            break
            if value and len(value) < 200:
                return make_field(value, line.get("confidence", 0.0), page_number, text)
        return None

    @staticmethod
    def _find_statement(document: Any, phrases: List[str]) -> Optional[Dict[str, Any]]:
        for page_number, line in iter_lines(document):
            text = str(line.get("text", "")).strip()
            lowered = text.lower()
            if any(phrase in lowered for phrase in phrases):
                return make_field(text, line.get("confidence", 0.0), page_number, text)
        return None