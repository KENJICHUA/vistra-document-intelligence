import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from document_intelligence import OCRPipeline, apply_review  # noqa: E402


def test_apply_review_approval() -> None:
    image_path = ROOT / "samples" / "images" / "laboratory_result.png"
    result = OCRPipeline().process(image_path)
    record = apply_review(result, reviewer_id="staff-1", approved=True)
    assert record.status.value == "approved"
    assert result.status == "approved"
    assert result.review["reviewed_by"] == "staff-1"


def test_apply_review_correction() -> None:
    image_path = ROOT / "samples" / "images" / "laboratory_result.png"
    result = OCRPipeline().process(image_path)
    record = apply_review(
        result,
        reviewer_id="staff-2",
        approved=True,
        corrections={"extracted_data.tests.0.result": "14.3"},
    )
    assert record.status.value == "corrected"
    assert result.extracted_data["tests"][0]["result"] == "14.3"
    assert record.changes[0]["old_value"] == "14.2"