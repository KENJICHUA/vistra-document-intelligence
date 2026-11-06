import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from document_intelligence import DocumentClassifier, DocumentType  # noqa: E402


def test_laboratory_classification() -> None:
    text = "Laboratory Result\nHemoglobin 14.2 g/dL\nReference Range 12.0-16.0"
    result = DocumentClassifier().classify(text)
    assert result.document_type == DocumentType.LABORATORY_RESULT
    assert result.confidence > 0
    assert "laboratory" in result.matched_indicators or "reference range" in result.matched_indicators


def test_unknown_classification() -> None:
    result = DocumentClassifier().classify("hello world")
    assert result.document_type == DocumentType.UNKNOWN
    assert result.confidence == 0.0


def test_empty_classification() -> None:
    result = DocumentClassifier().classify("")
    assert result.document_type == DocumentType.UNKNOWN