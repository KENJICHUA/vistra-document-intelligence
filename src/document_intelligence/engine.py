"""Backward-compatible alias for the PaddleOCR engine."""

from .engines.paddle_engine import PaddleOCREngine as OCREngine

__all__ = ["OCREngine"]