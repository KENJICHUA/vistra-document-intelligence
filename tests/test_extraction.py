import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from document_intelligence import OCRPipeline  # noqa: E402


def test_laboratory_extraction() -> None:
    image_path = ROOT / "samples" / "images" / "laboratory_result.png"
    result = OCRPipeline().process(image_path)
    assert result.document_type == "laboratory_result"
    tests = result.extracted_data.get("tests", [])
    assert len(tests) >= 2
    hemoglobin = next((t for t in tests if "Hemoglobin" in t["name"]), None)
    assert hemoglobin is not None
    assert hemoglobin["result"] == "14.2"
    assert hemoglobin["unit"] == "g/dL"
    assert hemoglobin["source"]["page"] == 1


def test_unknown_extraction_generic() -> None:
    # Reuse a non-lab image if present; fallback to generic by text.
    image_path = ROOT / "samples" / "images" / "images.png"
    result = OCRPipeline().process(image_path)
    # Either classified or generic; ensure no crash and warnings list exists.
    assert isinstance(result.warnings, list)