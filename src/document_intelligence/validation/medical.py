"""Medical-document validation helpers."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..validation import make_warning


def _parse_date(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, dict):
        value = value.get("value")
    if value is None:
        return True
    text = str(value).strip()
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%m-%d-%Y",
        "%d-%m-%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    ]
    for fmt in formats:
        try:
            datetime.strptime(text, fmt)
            return True
        except ValueError:
            continue
    return False


def validate_result(result: Any) -> List[Dict[str, Any]]:
    warnings: List[Dict[str, Any]] = []

    document_type = getattr(result, "document_type", None)
    confidence = getattr(result, "document_type_confidence", 0.0) or 0.0
    if document_type in ("unknown", "other") or confidence < 0.5:
        warnings.append(
            make_warning(
                "LOW_CLASSIFICATION_CONFIDENCE",
                "document_type",
                "Document type is unknown, other, or low confidence.",
            )
        )

    for page in getattr(result, "pages", []) or []:
        page_number = getattr(page, "page_number", 0)
        for line in getattr(page, "lines", []) or []:
            line_conf = getattr(line, "confidence", None)
            if line_conf is None and isinstance(line, dict):
                line_conf = line.get("confidence", 1.0)
            if (line_conf or 0.0) < 0.7:
                text = getattr(line, "text", None)
                if text is None and isinstance(line, dict):
                    text = line.get("text", "")
                warnings.append(
                    make_warning(
                        "LOW_OCR_CONFIDENCE",
                        f"pages[{page_number}]",
                        f"Low OCR confidence ({float(line_conf or 0.0):.2f}): {str(text)[:80]}",
                    )
                )

    extracted = getattr(result, "extracted_data", {}) or {}
    doc_type = document_type

    if doc_type == "laboratory_result":
        tests = extracted.get("tests", []) if isinstance(extracted, dict) else []
        if not tests:
            warnings.append(make_warning("NO_LAB_TESTS", "extracted_data.tests", "No laboratory test rows could be extracted."))
        for index, test in enumerate(tests or []):
            if not test.get("result"):
                warnings.append(make_warning("MISSING_LAB_RESULT", f"extracted_data.tests[{index}].result", "Laboratory row is missing a result value."))
            if not test.get("name"):
                warnings.append(make_warning("MISSING_LAB_NAME", f"extracted_data.tests[{index}].name", "Laboratory row is missing a test name."))
            if float(test.get("confidence", 1.0) or 0.0) < 0.7:
                warnings.append(make_warning("LOW_FIELD_CONFIDENCE", f"extracted_data.tests[{index}]", "Low confidence laboratory row."))

    elif doc_type == "medical_certificate":
        if not extracted.get("diagnosis_reason"):
            warnings.append(make_warning("MISSING_DIAGNOSIS", "extracted_data.diagnosis_reason", "No stated diagnosis or reason detected."))
        if not extracted.get("fitness_statement"):
            warnings.append(make_warning("MISSING_FITNESS_STATEMENT", "extracted_data.fitness_statement", "No fitness statement detected."))
        for field_name in ("examination_date", "issue_date"):
            if not _parse_date(extracted.get(field_name)):
                warnings.append(make_warning("INVALID_DATE_FORMAT", f"extracted_data.{field_name}", "Date could not be parsed."))

    elif doc_type == "vital_signs":
        bp = extracted.get("blood_pressure")
        if bp is None:
            warnings.append(make_warning("MISSING_BLOOD_PRESSURE", "extracted_data.blood_pressure", "Blood pressure not detected."))
        else:
            sys_val = bp.get("systolic") if isinstance(bp, dict) else None
            dia_val = bp.get("diastolic") if isinstance(bp, dict) else None
            if sys_val is None or dia_val is None:
                warnings.append(make_warning("INVALID_BLOOD_PRESSURE", "extracted_data.blood_pressure", "Blood pressure is missing systolic/diastolic values."))
        spo2 = extracted.get("spo2")
        if isinstance(spo2, dict):
            try:
                spo2_value = float(spo2.get("value"))
                if not (0 <= spo2_value <= 100):
                    warnings.append(make_warning("OUT_OF_RANGE_SPO2", "extracted_data.spo2", "SpO2 is outside the technical range 0-100."))
            except (TypeError, ValueError):
                pass
        for field_name in ("heart_rate", "temperature", "height", "weight"):
            field = extracted.get(field_name)
            if isinstance(field, dict) and float(field.get("confidence", 1.0) or 0.0) < 0.7:
                warnings.append(make_warning("LOW_FIELD_CONFIDENCE", f"extracted_data.{field_name}", f"Low confidence {field_name}."))

    elif doc_type == "prescription":
        medications = extracted.get("medications", []) if isinstance(extracted, dict) else []
        if not medications:
            warnings.append(make_warning("NO_MEDICATIONS", "extracted_data.medications", "No medication rows could be extracted."))
        for field_name in ("prescriber", "clinic"):
            if not extracted.get(field_name):
                warnings.append(make_warning(f"MISSING_{field_name.upper()}", f"extracted_data.{field_name}", f"{field_name.title()} not detected."))

    elif doc_type == "imaging_report":
        if not extracted.get("findings"):
            warnings.append(make_warning("MISSING_FINDINGS", "extracted_data.findings", "Findings section not detected."))
        if not extracted.get("impression"):
            warnings.append(make_warning("MISSING_IMPRESSION", "extracted_data.impression", "Impression/conclusion not detected."))

    elif doc_type == "dental_record":
        teeth = extracted.get("teeth", []) if isinstance(extracted, dict) else []
        if not teeth:
            warnings.append(make_warning("NO_DENTAL_FINDINGS", "extracted_data.teeth", "No tooth/condition pairs could be extracted."))

    # Merge any extractor-provided warnings if they are strings.
    for w in getattr(result, "warnings", []) or []:
        if isinstance(w, str):
            warnings.append(make_warning("EXTRACTOR_WARNING", "result", w))
        elif isinstance(w, dict):
            warnings.append(w)

    # Deduplicate exact duplicates.
    seen = set()
    unique = []
    for w in warnings:
        key = (w.get("code"), w.get("field"), w.get("message"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(w)
    return unique