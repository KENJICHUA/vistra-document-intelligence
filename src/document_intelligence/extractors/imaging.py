"""Imaging and diagnostic report extractor."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .base import BaseExtractor
from .common import DATE_PATTERNS, find_document_date, find_patient_name, iter_lines, make_field


class ImagingReportExtractor(BaseExtractor):
    document_type = "imaging_report"

    _MODALITIES = [
        "ultrasound", "x-ray", "xray", "ct scan", "ct", "mri", "mammogram",
        "radiograph", "echocardiogram", "ecg", "eeg",
    ]

    _BODY_REGIONS = [
        "chest", "abdomen", "pelvis", "head", "brain", "spine", "neck",
        "knee", "shoulder", "wrist", "ankle", "breast", "thyroid",
    ]

    def extract(self, document: Any) -> Dict[str, Any]:
        warnings: List[str] = []
        lines = list(iter_lines(document))
        text = getattr(document, "raw_text", "") or ""

        modality = self._detect_one(text, self._MODALITIES)
        body_region = self._detect_one(text, self._BODY_REGIONS)

        examination_date = self._find_labeled_date(lines, ["examination", "exam date", "study date", "performed"])
        report_date = self._find_labeled_date(lines, ["report date", "reported", "date of report"])
        if report_date is None:
            report_date = find_document_date(document)

        findings = self._section_text(lines, ["findings"])
        impression = self._section_text(lines, ["impression", "conclusion", "interpretation"])
        provider = self._find_labeled_text(lines, ["radiologist", "reported by", "physician", "doctor", "dr."])

        if modality is None:
            warnings.append("Imaging modality not detected.")
        if findings is None:
            warnings.append("Findings section not detected.")
        if impression is None:
            warnings.append("Impression/conclusion not detected.")

        return {
            "patient": {"name": find_patient_name(document), "patient_id": None},
            "document_date": report_date,
            "extracted_data": {
                "modality": make_field(modality, 0.5, 1, modality) if modality else None,
                "body_region": make_field(body_region, 0.5, 1, body_region) if body_region else None,
                "examination_date": examination_date,
                "report_date": report_date,
                "findings": findings,
                "impression": impression,
                "provider": provider,
            },
            "warnings": warnings,
        }

    @staticmethod
    def _detect_one(text: str, candidates: List[str]) -> Optional[str]:
        lowered = (text or "").lower()
        for candidate in candidates:
            if candidate in lowered:
                return candidate
        return None

    @staticmethod
    def _find_labeled_date(lines: List, labels: List[str]) -> Optional[Dict[str, Any]]:
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
    def _section_text(lines: List, labels: List[str]) -> Optional[Dict[str, Any]]:
        collecting = False
        collected: List[str] = []
        source_page = None
        source_text = None
        for page_number, line in lines:
            text = str(line.get("text", "")).strip()
            lowered = text.lower()
            if any(label in lowered for label in labels):
                collecting = True
                source_page = page_number
                source_text = text
                # Include text after label if present.
                for label in labels:
                    if label in lowered:
                        idx = lowered.find(label) + len(label)
                        remainder = text[idx:].strip(" :.-")
                        if remainder:
                            collected.append(remainder)
                continue
            if collecting:
                if any(stop in lowered for stop in ["impression", "conclusion", "recommendation", "radiologist"]):
                    break
                if text:
                    collected.append(text)
        if not collected:
            return None
        return {
            "value": " ".join(collected),
            "confidence": 0.5,
            "source": {"page": source_page, "text": source_text},
        }