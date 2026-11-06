import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from document_intelligence.extractors.dental import DentalExtractor  # noqa: E402
from document_intelligence.extractors.imaging import ImagingReportExtractor  # noqa: E402
from document_intelligence.extractors.prescription import PrescriptionExtractor  # noqa: E402
from document_intelligence.extractors.vital_signs import VitalSignsExtractor  # noqa: E402
from document_intelligence.formatter import Line, OCRResult, PageResult  # noqa: E402


def _doc(text: str) -> OCRResult:
    lines = [Line(text=line, confidence=0.95, bounding_box=[0, 0, 10, 10]) for line in text.splitlines() if line.strip()]
    return OCRResult(
        filename="doc.png",
        processed_at="2026-11-02T00:00:00+00:00",
        page_count=1,
        pages=[PageResult(page_number=1, text=text, lines=lines)],
        raw_text=text,
    )


def test_vital_signs_extraction() -> None:
    text = """Vital Signs
Patient Name: John Doe
Date: 10/31/2026
Blood Pressure: 120/80
Heart Rate: 72
Respiratory Rate: 16
Temperature: 36.5 C
SpO2: 98%
Height: 170 cm
Weight: 65 kg"""
    extraction = VitalSignsExtractor().extract(_doc(text))
    data = extraction["extracted_data"]
    assert extraction["patient"]["name"]["value"] == "John Doe"
    assert data["blood_pressure"]["systolic"] == 120
    assert data["blood_pressure"]["diastolic"] == 80
    assert data["heart_rate"]["value"] == 72.0
    assert data["respiratory_rate"]["value"] == 16.0
    assert data["temperature"]["value"] == "36.5"
    assert data["spo2"]["value"] == 98.0
    assert data["height"]["value"] == "170"
    assert data["weight"]["value"] == "65"


def test_prescription_extraction() -> None:
    text = """Prescription
Patient Name: John Doe
Date: 10/31/2026
Rx: Amoxicillin 500 mg take one tablet twice daily
Dr. Smith
Clinic: VISTRA Clinic"""
    extraction = PrescriptionExtractor().extract(_doc(text))
    data = extraction["extracted_data"]
    assert extraction["patient"]["name"]["value"] == "John Doe"
    assert data["prescriber"]["value"] == "Dr. Smith"
    assert data["clinic"]["value"] == "VISTRA Clinic"
    assert len(data["medications"]) == 1
    assert "Amoxicillin" in data["medications"][0]["raw_text"]


def test_imaging_extraction() -> None:
    text = """Imaging Report
Patient Name: John Doe
Ultrasound of abdomen
Examination Date: 10/30/2026
Report Date: 10/31/2026
Findings: Normal liver
Impression: No abnormalities
Radiologist: Dr. Lee"""
    extraction = ImagingReportExtractor().extract(_doc(text))
    data = extraction["extracted_data"]
    assert extraction["patient"]["name"]["value"] == "John Doe"
    assert data["modality"]["value"] == "ultrasound"
    assert data["body_region"]["value"] == "abdomen"
    assert data["examination_date"]["value"] == "10/30/2026"
    assert data["report_date"]["value"] == "10/31/2026"
    assert "Normal liver" in data["findings"]["value"]
    assert "No abnormalities" in data["impression"]["value"]
    assert "Lee" in data["provider"]["value"]


def test_dental_extraction() -> None:
    text = """Dental Record
Patient Name: John Doe
Tooth 12 caries
Tooth 14 filling"""
    extraction = DentalExtractor().extract(_doc(text))
    data = extraction["extracted_data"]
    assert extraction["patient"]["name"]["value"] == "John Doe"
    assert len(data["teeth"]) == 2
    assert data["teeth"][0]["tooth"] == "12"
    assert data["teeth"][0]["condition"] == "caries"