"""Main OCR processing pipeline."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Union

from .classification import DocumentClassifier
from .engine import OCREngine
from .extractors import (
    DentalExtractor,
    GenericExtractor,
    ImagingReportExtractor,
    LaboratoryExtractor,
    MedicalCertificateExtractor,
    PrescriptionExtractor,
    VitalSignsExtractor,
)
from .formatter import OCRResult, ResultFormatter
from .loader import DocumentLoader
from .preprocessor import ImagePreprocessor
from .validation import validate_result


class OCRPipeline:
    def __init__(
        self,
        lang: str = "en",
        max_side: int = 2000,
        deskew: bool = False,
    ) -> None:
        self.loader = DocumentLoader()
        self.preprocessor = ImagePreprocessor(max_side=max_side, deskew=deskew)
        self.engine = OCREngine(lang=lang)
        self.classifier = DocumentClassifier()
        self.formatter = ResultFormatter()

    def process(self, file_path: Union[str, Path]) -> OCRResult:
        path = Path(file_path)
        images = self.loader.load(path)

        pages = []
        for page_number, image in enumerate(images, start=1):
            processed = self.preprocessor.process(image)
            lines = self.engine.recognize(processed)
            text = "\n".join(line["text"] for line in lines)
            pages.append(
                {
                    "page_number": page_number,
                    "text": text,
                    "lines": lines,
                }
            )

        raw_text = "\n\n".join(page["text"] for page in pages if page["text"])
        classification = self.classifier.classify(raw_text)

        result = self.formatter.format(
            filename=path.name,
            pages=pages,
            document_id=str(uuid.uuid4()),
            classification=classification,
        )

        extractor = self._get_extractor(classification.document_type.value if hasattr(classification.document_type, "value") else str(classification.document_type))
        extraction = extractor.extract(result)
        result.patient = extraction.get("patient", {})
        result.document_date = extraction.get("document_date")
        result.extracted_data = extraction.get("extracted_data", {})
        result.warnings = extraction.get("warnings", [])

        validation_warnings = validate_result(result)
        result.warnings = validation_warnings
        result.status = "needs_review" if result.warnings else "processed"

        return result

    @staticmethod
    def _get_extractor(document_type: str):
        if document_type == "laboratory_result":
            return LaboratoryExtractor()
        if document_type == "medical_certificate":
            return MedicalCertificateExtractor()
        if document_type == "vital_signs":
            return VitalSignsExtractor()
        if document_type == "prescription":
            return PrescriptionExtractor()
        if document_type == "imaging_report":
            return ImagingReportExtractor()
        if document_type == "dental_record":
            return DentalExtractor()
        return GenericExtractor()