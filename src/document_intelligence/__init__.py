"""VISTRA Document Intelligence OCR package."""

from .pipeline import OCRPipeline
from .formatter import OCRResult
from .classification import DocumentClassifier, ClassificationResult
from .models.common import DocumentType

__all__ = [
    "OCRPipeline",
    "OCRResult",
    "DocumentClassifier",
    "ClassificationResult",
    "DocumentType",
]
__version__ = "0.2.0"