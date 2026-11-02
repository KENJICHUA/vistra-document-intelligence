import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from document_intelligence.loader import DocumentLoader  # noqa: E402


def test_load_image() -> None:
    image_path = ROOT / "samples" / "images" / "laboratory_result.png"
    pages = DocumentLoader().load(image_path)
    assert len(pages) == 1
    assert pages[0].ndim == 3


def test_load_pdf() -> None:
    pdf_path = ROOT / "samples" / "pdfs" / "laboratory_result.pdf"
    pages = DocumentLoader().load(pdf_path)
    assert len(pages) >= 1
    assert pages[0].ndim == 3