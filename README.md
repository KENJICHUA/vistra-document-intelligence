# VISTRA Document Intelligence (OCR)

Standalone Python package for OCR and information extraction from medical
documents. It is designed to be integrated into the VISTRA backend through
an authenticated FastAPI service.

## Supported document families

- Laboratory results
- Medical certificates
- Vital-signs sheets
- Prescriptions
- Imaging/diagnostic reports
- Dental records/odontograms
- Generic fallback for unknown documents

## Setup

Recommended Python version for the standalone OCR environment: **3.11**.

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Notes:
- PaddleOCR models are downloaded on first run and cached locally.
- The package is framework-independent and does not import FastAPI, Supabase,
  or VISTRA application modules.

## Run the CLI

```bash
python main.py
```

Enter a path to an image (PNG/JPG) or PDF when prompted. Results are written
to `output/ocr_result.json`.

## Run tests

```bash
pytest
```

Tests include loader, pipeline, classification, extraction, validation, and
review workflows.

## Evaluate extraction quality

Synthetic, de-identified fixtures are stored in `tests/fixtures/`. Run:

```bash
python scripts/evaluate.py
```

This reports classification accuracy and field exact-match accuracy.

## Project layout

```text
src/document_intelligence/
  loader.py                  # format detection + page loading
  preprocessor.py            # conservative image preprocessing
  engines/
    base.py                  # OCR engine interface
    paddle_engine.py         # PaddleOCR 3.x adapter
  classification/
    classifier.py            # deterministic document classifier
  extractors/
    laboratory.py
    medical_certificate.py
    vital_signs.py
    prescription.py
    imaging.py
    dental.py
    generic.py
  validation/
    medical.py                # field and document validation
  review.py                  # staff review helpers
  formatter.py               # consistent JSON output
  pipeline.py                # orchestrates the pipeline
  models/
    common.py                # shared enums
tests/
  fixtures/                  # de-identified evaluation fixtures
scripts/
  evaluate.py                # field-level metrics
```

## Output contract

Every result includes:

- `document_id`
- `filename`
- `document_type` and `document_type_confidence`
- `status` (`processed` or `needs_review`)
- `pages` with text, lines, confidence, and bounding boxes
- `raw_text`
- `patient`, `document_date`, `extracted_data`
- `warnings`
- `review` state

OCR results are drafts. A staff member must review and explicitly approve
them before any clinical data is written.

## VISTRA backend integration

The package is consumed by the VISTRA FastAPI backend as an installed
dependency. See `VISTRA_OCR_Development_Blueprint.md` for the full
architecture and phased roadmap. Backend integration endpoints:

- `POST /api/v1/ocr/extract`
- `GET /api/v1/ocr/{document_id}`
- `POST /api/v1/ocr/{document_id}/review`

## Privacy and safety

- No diagnosis or treatment recommendations are produced.
- Missing or low-confidence values are flagged, not guessed.
- No automatic writes to clinical tables.
- Temporary OCR files are cleaned up after processing.