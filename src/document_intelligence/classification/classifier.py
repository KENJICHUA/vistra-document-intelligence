"""Deterministic, keyword-based document classifier."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from ..models.common import DocumentType


@dataclass
class ClassificationResult:
    document_type: DocumentType
    confidence: float
    matched_indicators: List[str] = field(default_factory=list)


class DocumentClassifier:
    """Classify a document from its OCR text using keyword scoring."""

    _KEYWORDS: Dict[DocumentType, List[Tuple[str, int]]] = {
        DocumentType.LABORATORY_RESULT: [
            ("laboratory", 2),
            ("lab result", 2),
            ("test result", 2),
            ("reference range", 2),
            ("specimen", 2),
            ("hemoglobin", 1),
            ("wbc", 1),
            ("platelet", 1),
            ("glucose", 1),
            ("cholesterol", 1),
        ],
        DocumentType.PRESCRIPTION: [
            ("rx", 2),
            ("prescription", 2),
            ("prescriber", 2),
            ("medication", 2),
            ("dosage", 1),
            ("take", 1),
            ("tablets", 1),
            ("capsules", 1),
            ("refill", 1),
            ("sig:", 1),
        ],
        DocumentType.MEDICAL_CERTIFICATE: [
            ("medical certificate", 3),
            ("certify", 2),
            ("fit to work", 2),
            ("medical clearance", 2),
            ("rest for", 1),
            ("sick leave", 1),
            ("diagnosis", 1),
        ],
        DocumentType.VITAL_SIGNS: [
            ("vital signs", 3),
            ("blood pressure", 2),
            ("temperature", 1),
            ("pulse", 1),
            ("respiratory rate", 2),
            ("spo2", 2),
            ("heart rate", 1),
            ("oxygen saturation", 2),
        ],
        DocumentType.MEDICAL_EXAMINATION: [
            ("medical examination", 3),
            ("physical examination", 2),
            ("examination form", 2),
            ("findings", 1),
            ("assessment", 1),
        ],
        DocumentType.DENTAL_RECORD: [
            ("odontogram", 3),
            ("dental", 2),
            ("tooth", 1),
            ("caries", 2),
            ("restoration", 1),
            ("fdi", 1),
        ],
        DocumentType.IMAGING_REPORT: [
            ("radiology", 2),
            ("impression", 2),
            ("findings", 1),
            ("ultrasound", 2),
            ("x-ray", 2),
            ("ct scan", 2),
            ("mri", 2),
            ("radiologist", 2),
        ],
        DocumentType.DISCHARGE_SUMMARY: [
            ("discharge summary", 3),
            ("admission", 2),
            ("discharge", 2),
            ("hospital course", 2),
            ("discharge diagnosis", 2),
        ],
        DocumentType.GENERAL_PATIENT_RECORD: [
            ("patient record", 2),
            ("medical history", 2),
            ("patient information", 1),
        ],
    }

    def classify(self, text: str) -> ClassificationResult:
        lowered = (text or "").lower()
        if not lowered.strip():
            return ClassificationResult(DocumentType.UNKNOWN, 0.0, [])

        scores: Dict[DocumentType, Tuple[int, List[str]]] = {}
        for doc_type, keywords in self._KEYWORDS.items():
            matched: List[str] = []
            score = 0
            for term, weight in keywords:
                if term in lowered:
                    matched.append(term)
                    score += weight
            scores[doc_type] = (score, matched)

        best_type = max(scores, key=lambda t: scores[t][0])
        best_score, best_matched = scores[best_type]

        if best_score >= 2:
            confidence = min(1.0, best_score / 6.0)
            return ClassificationResult(best_type, round(confidence, 4), best_matched)

        if best_score == 1:
            return ClassificationResult(DocumentType.OTHER, 0.3, best_matched)

        return ClassificationResult(DocumentType.UNKNOWN, 0.0, [])