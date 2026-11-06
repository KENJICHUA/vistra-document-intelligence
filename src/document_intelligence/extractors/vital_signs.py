"""Vital-signs sheet extractor."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .base import BaseExtractor
from .common import DATE_PATTERNS, find_document_date, find_patient_name, iter_lines, make_field


class VitalSignsExtractor(BaseExtractor):
    document_type = "vital_signs"

    def extract(self, document: Any) -> Dict[str, Any]:
        warnings: List[str] = []
        lines = list(iter_lines(document))

        measurement_date = self._find_labeled_date(
            document, ["date", "time", "measurement", "recorded", "taken"]
        )
        if measurement_date is None:
            measurement_date = find_document_date(document)

        blood_pressure = self._extract_blood_pressure(lines)
        heart_rate = self._extract_labeled_number(lines, ["heart rate", "pulse", "hr", "pulse rate"])
        respiratory_rate = self._extract_labeled_number(
            lines, ["respiratory rate", "respiration rate", "rr", "resp rate", "respiratory"]
        )
        temperature = self._extract_temperature(lines)
        spo2 = self._extract_labeled_number(lines, ["spo2", "oxygen saturation", "o2 sat", "saturation"])
        height = self._extract_measurement(lines, ["height", "ht"], r"(cm|m|in|ft|inch|inches)")
        weight = self._extract_measurement(lines, ["weight", "wt"], r"(kg|lb|lbs|g|grams)")

        if blood_pressure is None:
            warnings.append("Blood pressure not detected.")
        if heart_rate is None:
            warnings.append("Heart rate/pulse not detected.")
        if temperature is None:
            warnings.append("Temperature not detected.")

        return {
            "patient": {"name": find_patient_name(document), "patient_id": None},
            "document_date": measurement_date,
            "extracted_data": {
                "measurement_date": measurement_date,
                "blood_pressure": blood_pressure,
                "heart_rate": heart_rate,
                "respiratory_rate": respiratory_rate,
                "temperature": temperature,
                "spo2": spo2,
                "height": height,
                "weight": weight,
            },
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
    def _extract_blood_pressure(lines: List) -> Optional[Dict[str, Any]]:
        for page_number, line in lines:
            text = str(line.get("text", ""))
            lowered = text.lower()
            if "bp" not in lowered and "blood pressure" not in lowered:
                continue
            match = re.search(r"(\d{2,3})\s*/\s*(\d{2,3})", text)
            if match:
                systolic = int(match.group(1))
                diastolic = int(match.group(2))
                return {
                    "systolic": systolic,
                    "diastolic": diastolic,
                    "value": f"{systolic}/{diastolic}",
                    "confidence": round(float(line.get("confidence", 0.0) or 0.0), 4),
                    "source": {"page": page_number, "text": text},
                }
        return None

    @staticmethod
    def _extract_labeled_number(lines: List, labels: List[str]) -> Optional[Dict[str, Any]]:
        for page_number, line in lines:
            text = str(line.get("text", ""))
            lowered = text.lower()
            if not any(label in lowered for label in labels):
                continue
            match = re.search(r":\s*(\d+(?:\.\d+)?)", text)
            if not match:
                match = re.search(r"(\d+(?:\.\d+)?)", text.split(":")[-1] if ":" in text else text)
            if match:
                return make_field(float(match.group(1)), line.get("confidence", 0.0), page_number, text)
        return None

    @staticmethod
    def _extract_temperature(lines: List) -> Optional[Dict[str, Any]]:
        for page_number, line in lines:
            text = str(line.get("text", ""))
            lowered = text.lower()
            if "temp" not in lowered and "temperature" not in lowered:
                continue
            segment = text.split(":")[-1] if ":" in text else text
            match = re.search(r"(\d+(?:\.\d+)?)\s*(°?\s?[CF])?", segment, flags=re.IGNORECASE)
            if match:
                value = match.group(1)
                unit = (match.group(2) or "").strip() or None
                field = make_field(value, line.get("confidence", 0.0), page_number, text)
                field["unit"] = unit
                return field
        return None

    @staticmethod
    def _extract_measurement(lines: List, labels: List[str], unit_pattern: str) -> Optional[Dict[str, Any]]:
        for page_number, line in lines:
            text = str(line.get("text", ""))
            lowered = text.lower()
            if not any(label in lowered for label in labels):
                continue
            segment = text.split(":")[-1] if ":" in text else text
            match = re.search(r"(\d+(?:\.\d+)?)\s*(" + unit_pattern + r")?", segment, flags=re.IGNORECASE)
            if match:
                value = match.group(1)
                unit = (match.group(2) or "").strip() or None
                field = make_field(value, line.get("confidence", 0.0), page_number, text)
                field["unit"] = unit
                return field
        return None