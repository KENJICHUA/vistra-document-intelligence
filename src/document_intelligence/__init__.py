"""VISTRA Document Intelligence OCR package."""

from .pipeline import OCRPipeline
from .formatter import OCRResult

__all__ = ["OCRPipeline", "OCRResult"]
__version__ = "0.1.0"