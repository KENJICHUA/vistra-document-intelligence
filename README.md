# VISTRA Document Intelligence

OCR pipeline for medical documents using PaddleOCR.

## Setup

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

Enter a path to an image (PNG/JPG) or PDF when prompted. Results are written to `output/ocr_result.json`.

## Project layout

```
src/document_intelligence/
  loader.py        # format detection + page loading
  preprocessor.py  # conservative image preprocessing
  engine.py        # PaddleOCR wrapper (long-lived)
  formatter.py     # consistent JSON output
  pipeline.py      # orchestrates the pipeline
```