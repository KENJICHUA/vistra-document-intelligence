import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from document_intelligence.extractors.medical_certificate import MedicalCertificateExtractor  # noqa: E402
from document_intelligence.formatter import Line, OCRResult, PageResult  # noqa: E402


def test_medical_certificate_extraction() -> None:
    lines = [
        Line(text="VISTRA Clinic", confidence=0.99, bounding_box=[0, 0, 10, 10]),
        Line(text="Medical Certificate", confidence=0.99, bounding_box=[0, 0, 10, 10]),
        Line(text="Patient Name: John Doe", confidence=0.98, bounding_box=[0, 0, 10, 10]),
        Line(text="Examination Date: 10/31/2026", confidence=0.97, bounding_box=[0, 0, 10, 10]),
        Line(text="Issue Date: 11/01/2026", confidence=0.97, bounding_box=[0, 0, 10, 10]),
        Line(text="Diagnosis: Viral infection", confidence=0.96, bounding_box=[0, 0, 10, 10]),
        Line(text="Rest for 3 days", confidence=0.95, bounding_box=[0, 0, 10, 10]),
        Line(text="Fit to work", confidence=0.95, bounding_box=[0, 0, 10, 10]),
        Line(text="Dr. Smith", confidence=0.94, bounding_box=[0, 0, 10, 10]),
        Line(text="License No: 12345", confidence=0.94, bounding_box=[0, 0, 10, 10]),
    ]
    document = OCRResult(
        filename="certificate.png",
        processed_at="2026-11-02T00:00:00+00:00",
        page_count=1,
        pages=[PageResult(page_number=1, text="\n".join(l.text for l in lines), lines=lines)],
        raw_text="\n".join(l.text for l in lines),
    )

    extraction = MedicalCertificateExtractor().extract(document)
    data = extraction["extracted_data"]

    assert extraction["patient"]["name"]["value"] == "John Doe"
    assert data["examination_date"]["value"] == "10/31/2026"
    assert data["issue_date"]["value"] == "11/01/2026"
    assert "Viral infection" in data["diagnosis_reason"]["value"]
    assert "Rest for 3 days" in data["rest_leave"]["value"]
    assert "Fit to work" in data["fitness_statement"]["value"]
    assert "Smith" in data["provider_name"]["value"]
    assert data["license_details"]["value"] == "12345"