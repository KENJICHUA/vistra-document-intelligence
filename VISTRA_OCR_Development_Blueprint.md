# VISTRA Document Intelligence (OCR) --- Development Blueprint

> **Purpose:** Implementation specification for VISTRA's standalone
> medical-document OCR and information-extraction module. This file is
> intended to give an AI coding agent reliable project context.
>
> **Status:** Architecture and Phase 1 foundation planned. Treat
> implementation details as proposals until verified against the current
> repository and installed library versions.

------------------------------------------------------------------------

## 1. Project objective

Build a Python module that accepts a photo, scanned image, or PDF of a
medical document and returns structured, traceable information that a
VISTRA user can review.

Supported document families should include:

-   Laboratory results
-   Prescriptions and medication orders
-   Medical certificates
-   Vital-signs sheets
-   Medical examination forms
-   Dental records and odontograms
-   Imaging and diagnostic reports
-   Discharge summaries
-   General patient records and other documents

The system is an **OCR and document-understanding assistant**, not a
diagnostic system. It must not diagnose a patient, recommend treatment,
or silently write extracted values into a patient's medical record.

### Primary outcome

For every processed document, produce:

1.  Recognized text.
2.  Text regions and page references where available.
3.  Best-effort document classification.
4.  Structured fields appropriate to the document type.
5.  Confidence and validation information.
6.  Warnings and fields requiring human review.

A staff member must verify the result before it is committed to VISTRA's
clinical tables.

------------------------------------------------------------------------

## 2. Core design principles

1.  **Modular:** OCR, classification, extraction, validation, API
    integration, and persistence are separate layers.
2.  **Document-type aware:** Do not use one giant extraction function
    for every medical document.
3.  **Traceable:** Extracted fields retain source text and page/region
    references where possible.
4.  **Human in the loop:** OCR output is a draft. A human confirms or
    corrects it.
5.  **Privacy first:** Do not send medical documents to an external AI
    service unless VISTRA has explicitly approved the provider, data
    handling, and legal/security requirements.
6.  **No silent writes:** The OCR module must not directly modify
    `PATIENT`, `MEDICAL_VISIT`, `VITAL_SIGNS`, dental, laboratory, or
    other clinical tables.
7.  **Offline-capable:** The core OCR pipeline should run locally after
    model files and dependencies are installed.
8.  **Replaceable engines:** Keep PaddleOCR behind an interface so
    another OCR engine can be evaluated later.
9.  **Measured quality:** Evaluate using representative,
    consented/de-identified documents rather than relying on visual
    impressions.
10. **Fail safely:** Low-confidence or ambiguous extraction must be
    flagged, not guessed.

------------------------------------------------------------------------

## 3. High-level architecture

``` text
Image / PDF upload
       |
       v
Document intake and safety checks
       |
       v
File loader
  |-- Image loader
  |-- PDF page loader
  |-- (future) embedded PDF text extraction
       |
       v
Image preprocessing
  |-- orientation
  |-- resize
  |-- denoise
  |-- deskew (later)
       |
       v
OCR engine interface
  |-- PaddleOCR implementation
  |-- text, confidence, bounding boxes
       |
       v
Document classifier
       |
       +-----------------------------+
       |             |               |
       v             v               v
 Laboratory     Prescription      Certificate
 extractor       extractor        extractor
       |             |               |
       +-------------+---------------+
                     |
              Other extractors
                     |
                     v
          Normalization and validation
                     |
                     v
             Structured OCR result
                     |
                     v
              Staff review screen
                     |
              Explicit confirmation
                     |
                     v
           VISTRA business workflow
                     |
                     v
            Authorized database write
```

### Layer responsibilities

  -----------------------------------------------------------------------
  Layer                   Responsibility          Must not do
  ----------------------- ----------------------- -----------------------
  Intake                  Validate file type,     Interpret medical
                          size, page count, and   content
                          temporary storage       

  Loader                  Convert image/PDF pages Classify or extract
                          into a common image     fields
                          representation          

  Preprocessor            Improve image quality   Invent or alter
                          without destroying      document content
                          information             

  OCR engine              Recognize text and      Decide clinical meaning
                          return                  
                          regions/confidence      

  Classifier              Identify likely         Modify extracted values
                          document type           

  Extractors              Convert OCR output into Write to the database
                          type-specific fields    

  Validators              Check formats, ranges,  Treat plausible values
                          required fields, and    as medically correct
                          consistency             

  Review workflow         Let authorized staff    Auto-approve
                          confirm/correct results low-confidence fields

  VISTRA integration      Apply authorization and Bypass existing
                          persist approved data   services/RLS
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 4. Recommended technology

  -----------------------------------------------------------------------
  Concern                 Initial choice          Notes
  ----------------------- ----------------------- -----------------------
  Language                Python 3.11             Separate environment
                                                  until dependency
                                                  compatibility is proven

  OCR                     PaddleOCR 3.x           Keep behind an engine
                                                  adapter

  Image processing        OpenCV                  Resize, denoise,
                                                  orientation and later
                                                  deskew

  PDF handling            PyMuPDF                 Render scanned pages;
                                                  later extract embedded
                                                  text

  Data models             Pydantic                Typed extraction
                                                  results and validation

  API                     FastAPI (VISTRA backend Keep API concerns out
                          only)                   of the OCR package

  Testing                 pytest                  Unit, integration, and
                                                  regression tests

  Optional later          PP-StructureV3          Layout and table
                                                  extraction when needed

  Optional later          spaCy / rules /         Medical terminology and
                          dictionaries            entity normalization

  Optional later          Task queue              Move expensive OCR jobs
                                                  out of API request
                                                  workers
  -----------------------------------------------------------------------

Do not add an LLM to Phase 1. First establish reliable OCR output,
traceability, and a labeled evaluation set. If an LLM is considered
later, it must be optional, schema-constrained, privacy-reviewed, and
unable to invent missing values.

### Dependency management

-   Pin tested versions in dependency metadata or a lock file.
-   Install PaddlePaddle separately when required by the selected
    PaddleOCR build and platform.
-   Do not assume a dependency version works merely because it installs.
-   Record Python, PaddleOCR, PaddlePaddle, OpenCV, and PyMuPDF versions
    in test reports.
-   Verify the current PaddleOCR 3.x API against the installed version
    before relying on examples.

------------------------------------------------------------------------

## 5. Repository layout

### Recommended monorepo layout

Keep the OCR package independent inside the VISTRA backend repository:

``` text
VISTRA/
└── backend/
    ├── app/
    │   ├── routes/
    │   │   └── document_ocr.py
    │   ├── services/
    │   │   └── document_ocr_service.py
    │   ├── schemas/
    │   │   └── document_ocr.py
    │   └── main.py
    │
    ├── document-intelligence/
    │   ├── pyproject.toml
    │   ├── README.md
    │   ├── src/
    │   │   └── document_intelligence/
    │   │       ├── __init__.py
    │   │       ├── pipeline.py
    │   │       ├── loader.py
    │   │       ├── preprocessor.py
    │   │       ├── formatter.py
    │   │       ├── models/
    │   │       │   ├── __init__.py
    │   │       │   ├── common.py
    │   │       │   └── document.py
    │   │       ├── engines/
    │   │       │   ├── __init__.py
    │   │       │   ├── base.py
    │   │       │   └── paddle_engine.py
    │   │       ├── classification/
    │   │       │   ├── __init__.py
    │   │       │   └── classifier.py
    │   │       ├── extractors/
    │   │       │   ├── __init__.py
    │   │       │   ├── base.py
    │   │       │   ├── laboratory.py
    │   │       │   ├── prescription.py
    │   │       │   ├── medical_certificate.py
    │   │       │   ├── vital_signs.py
    │   │       │   ├── dental.py
    │   │       │   └── generic.py
    │   │       └── validation/
    │   │           ├── __init__.py
    │   │           ├── confidence.py
    │   │           └── medical.py
    │   ├── tests/
    │   │   ├── unit/
    │   │   ├── integration/
    │   │   └── fixtures/
    │   └── samples/
    │       ├── images/
    │       └── pdfs/
    │
    ├── requirements.txt
    └── ...
```

Do not commit real patient documents, model cache files, API keys, or
OCR output containing patient information. Use synthetic or properly
de-identified fixtures.

### Package boundary

`document-intelligence` should be framework-independent:

-   It may use Python, OpenCV, PyMuPDF, PaddleOCR, and Pydantic.
-   It must not import `app.*`, FastAPI routers, Supabase clients,
    VISTRA repositories, or authentication dependencies.
-   It returns Python dictionaries or Pydantic models.
-   The VISTRA backend owns upload authorization, patient access, audit
    logs, review state, and database persistence.

------------------------------------------------------------------------

## 6. Common data contract

All document types should return a common envelope. Type-specific fields
belong under `extracted_data`.

Illustrative example:

``` json
{
  "document_id": "generated-uuid",
  "filename": "laboratory-report.pdf",
  "document_type": "laboratory_result",
  "document_type_confidence": 0.94,
  "status": "pending_review",
  "patient": {
    "name": {
      "value": "Example Patient",
      "confidence": 0.91,
      "source": {
        "page": 1,
        "text": "Patient: Example Patient"
      }
    },
    "patient_id": null
  },
  "document_date": {
    "value": "2026-10-31",
    "confidence": 0.88,
    "source": {
      "page": 1,
      "text": "Date: 10/31/2026"
    }
  },
  "extracted_data": {
    "tests": [
      {
        "name": "Hemoglobin",
        "result": "14.2",
        "unit": "g/dL",
        "reference_range": "12.0-16.0",
        "flag": null,
        "confidence": 0.96,
        "source": {
          "page": 1,
          "text": "Hemoglobin 14.2 g/dL 12.0-16.0"
        }
      }
    ]
  },
  "pages": [],
  "warnings": [],
  "review": {
    "required": true,
    "reviewed_by": null,
    "reviewed_at": null
  }
}
```

### Contract rules

-   Use `null` when a value is absent or unreadable. Do not guess.
-   Preserve original recognized text.
-   Preserve raw and normalized values separately when normalization is
    applied.
-   Include page number and source text for extracted fields where
    possible.
-   Include bounding boxes if the OCR engine provides them reliably.
-   Keep OCR confidence separate from extraction confidence and
    validation status.
-   Confidence is not a probability that a medical interpretation is
    correct.
-   Use ISO 8601 dates for normalized dates, but retain original date
    text.
-   Do not force every document into the same `extracted_data` shape.

### Suggested status values

-   `processed`: OCR and extraction completed, awaiting review.
-   `needs_review`: processing completed but warnings or low confidence
    require attention.
-   `failed`: processing could not complete.
-   `approved`: authorized reviewer approved the result.
-   `rejected`: reviewer rejected the extraction.

The OCR package should generally return a processing result. VISTRA's
application service should own persistent review status and audit
history.

------------------------------------------------------------------------

## 7. OCR pipeline implementation

### 7.1 Document intake

Accept only supported formats initially:

-   `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tif`, `.tiff`
-   `.pdf`

Validate using both filename extension and file content/magic bytes.
Never trust the extension alone.

Initial configurable limits (confirm against VISTRA deployment
capacity):

-   Maximum upload size: 10 MB.
-   Maximum PDF pages: define a conservative limit, e.g. 20 pages for
    the first release.
-   Maximum rendered page dimension: bounded to prevent memory
    exhaustion.
-   Reject encrypted, malformed, or unsupported PDFs with a safe error.

Use generated temporary filenames rather than trusting user-supplied
paths or filenames. Always clean up temporary files.

### 7.2 Loading

The loader should produce a consistent list of pages:

``` python
list[np.ndarray]  # each page represented as an image array
```

Requirements:

-   Image inputs become one page.
-   PDF inputs become one image per rendered page for the initial OCR
    path.
-   Preserve page order.
-   Normalize color channel convention consistently (document whether
    arrays are RGB or BGR).
-   Raise typed exceptions for unsupported, missing, malformed, or
    oversized files.

**Future improvement:** For PDFs containing embedded text, extract that
text directly and OCR only scanned/image pages. Do not rasterize every
digital PDF unnecessarily.

### 7.3 Preprocessing

Start conservatively:

1.  Correct orientation when confidently detected.
2.  Resize oversized images while preserving aspect ratio.
3.  Apply mild denoising if needed.
4.  Add deskewing after tests show it improves target documents.
5.  Keep original image unchanged for audit/debug comparison.

Do not aggressively threshold, sharpen, or remove backgrounds by
default. Medical forms often contain faint text, colored marks, stamps,
and handwriting.

Preprocessing should be configurable and independently testable.

### 7.4 OCR engine adapter

Create an interface such as:

``` python
from abc import ABC, abstractmethod
from typing import Any

class OCREngine(ABC):
    @abstractmethod
    def recognize(self, image: Any) -> list[dict]:
        """Return normalized text regions for one page."""
```

The PaddleOCR implementation should:

-   Initialize the model once per worker/process, not once per page.
-   Use the currently supported PaddleOCR 3.x API.
-   Normalize engine-specific output into a stable internal format.
-   Return text, OCR confidence, and bounding box where available.
-   Handle empty pages and malformed engine output safely.
-   Avoid logging recognized patient text.

Normalized region example:

``` json
{
  "text": "Hemoglobin 14.2 g/dL",
  "confidence": 0.97,
  "bounding_box": [[100, 220], [500, 220], [500, 260], [100, 260]]
}
```

Do not let downstream extractors depend directly on PaddleOCR's raw
result object.

### 7.5 Page and document formatting

Keep both page-level and document-level output:

``` json
{
  "page_number": 1,
  "text": "All recognized text for this page...",
  "regions": []
}
```

Document-level `raw_text` may join page text using a clear page
separator. Never discard page-level data.

------------------------------------------------------------------------

## 8. Document classification

Classification should begin with deterministic rules and keyword
scoring, not a trained classifier.

  -----------------------------------------------------------------------
  Document type                       Possible indicators
  ----------------------------------- -----------------------------------
  Laboratory result                   `laboratory`, `test result`,
                                      `reference range`, `specimen`,
                                      common test names

  Prescription                        `Rx`, `prescription`, `take`,
                                      dosage units, frequency

  Medical certificate                 `medical certificate`, `certify`,
                                      `fit to work`, `diagnosis`

  Vital signs                         `blood pressure`, `temperature`,
                                      `pulse`, `respiratory rate`, `SpO2`

  Dental record                       `odontogram`, tooth numbers, dental
                                      surfaces, `caries`

  Imaging report                      `radiology`, `impression`,
                                      `findings`, `ultrasound`, `X-ray`

  Discharge summary                   `admission`, `discharge`,
                                      `hospital course`,
                                      `discharge diagnosis`
  -----------------------------------------------------------------------

Rules:

-   Return a type plus confidence/score and matched indicators.
-   Support `unknown` and `other`.
-   Do not force a classification when evidence is weak.
-   Allow a reviewer to correct the type.
-   Keep classification separate from extraction so new document types
    can be added without rewriting the OCR engine.

A later ML classifier may be evaluated once a sufficiently diverse,
labeled, privacy-approved dataset exists.

------------------------------------------------------------------------

## 9. Type-specific extraction

Every extractor should implement a shared interface and return a typed
result plus warnings.

``` python
class BaseExtractor:
    document_type: str

    def extract(self, document):
        raise NotImplementedError
```

### 9.1 Laboratory results

Suggested fields:

-   Laboratory/provider name
-   Patient name and patient identifier
-   Collection date/time
-   Report date
-   Specimen type
-   Test name
-   Result value
-   Unit
-   Reference range
-   Abnormal flag as printed on the report
-   Page/source reference

Important: - Preserve numeric values as printed before parsing. - Do not
infer units. - Do not infer abnormality from a generic range unless the
range and units are understood. - Capture a laboratory's printed flag
separately from later clinical interpretation. - Table layout extraction
may be needed for multi-column reports.

### 9.2 Prescriptions

Suggested fields:

-   Prescriber and clinic
-   Patient name
-   Prescription date
-   Medication name
-   Strength/concentration
-   Dose
-   Route
-   Frequency
-   Duration
-   Quantity
-   Refills
-   Instructions

Important: - Medication names and abbreviations can be ambiguous. - Do
not autocomplete an uncertain drug name. - Never convert an unclear
handwritten instruction into a confident dose. - Flag missing or
ambiguous dose, route, and frequency for review.

### 9.3 Medical certificates

Suggested fields:

-   Issuing clinic/provider
-   Patient name
-   Examination date
-   Certificate issue date
-   Stated diagnosis/reason, if present
-   Recommended rest/leave dates, if present
-   Fitness statement, if present
-   Provider name and license details, if printed

Do not infer a diagnosis or fitness status that is not explicitly
present.

### 9.4 Vital-signs sheets

Suggested fields:

-   Measurement date/time
-   Blood pressure (systolic/diastolic)
-   Heart rate/pulse
-   Respiratory rate
-   Temperature and unit
-   SpO2
-   Height and unit
-   Weight and unit
-   Source reference

Do not convert units unless the conversion is explicit, tested, and both
original and normalized values are retained. Flag implausible formats
for review; do not silently correct them.

### 9.5 Dental records and odontograms

Suggested fields depend on the source form:

-   Patient identifier
-   Examination date
-   Tooth identifier/system used (e.g. FDI, Universal)
-   Tooth condition/finding
-   Surface(s)
-   Existing restoration or missing tooth indicators
-   Treatment recommendation if explicitly recorded
-   Source region/page

Do not infer a tooth condition from an unclear mark. Dental chart
extraction may require layout-specific parsing and a human review
interface that overlays the source image.

### 9.6 Imaging and diagnostic reports

Suggested fields:

-   Modality
-   Body region
-   Examination date
-   Report date
-   Findings
-   Impression/conclusion
-   Radiologist/provider details

The module extracts report text; it does not interpret the underlying
radiology image or provide a diagnosis.

### 9.7 Generic fallback

For unknown documents, return raw text, pages and regions, possible
patient/date candidates only when clearly identified, classification
`unknown` or `other`, and a review warning. Do not force unknown
documents through a specialized extractor.

------------------------------------------------------------------------

## 10. Validation and confidence

Keep these concepts distinct:

1.  **OCR confidence:** How confident the OCR engine is about recognized
    text.
2.  **Extraction confidence:** How confidently a rule/model mapped text
    to a field.
3.  **Validation result:** Whether the extracted value passes format or
    consistency checks.
4.  **Clinical correctness:** Not established by OCR confidence or
    simple validation.

Validation examples:

-   Date parses to a supported format.
-   Blood pressure has a recognizable systolic/diastolic structure.
-   SpO2 is numeric and within a configurable technical range.
-   A lab row has a test name and a result.
-   A prescription has a medication candidate and required directions.
-   A dental tooth identifier belongs to the declared numbering system.

Validation should produce warnings rather than silently modifying source
values.

Example:

``` json
{
  "code": "LOW_FIELD_CONFIDENCE",
  "field": "medications[0].dose",
  "message": "The dose could not be read reliably.",
  "severity": "warning"
}
```

Never label a result medically safe merely because it passes a numeric
range check.

------------------------------------------------------------------------

## 11. VISTRA backend integration

Integrate the package into the existing FastAPI backend only after the
standalone pipeline is stable.

### 11.1 Install as a local package

From the VISTRA backend virtual environment:

``` powershell
cd path\to\VISTRA\backend
.venv\Scripts\activate
pip install -e .\document-intelligence
```

The import name uses underscores:

``` python
from document_intelligence import DocumentPipeline
```

The folder can remain named `document-intelligence`.

### 11.2 Keep application responsibilities outside the package

Recommended backend files:

-   `app/routes/document_ocr.py`: upload endpoint and HTTP response.
-   `app/services/document_ocr_service.py`: orchestrates package,
    storage, review workflow.
-   `app/schemas/document_ocr.py`: API request/response models.
-   Existing auth/access modules: enforce staff permissions and any
    patient-scoped access rules.
-   Existing repositories: persist approved records only.

The OCR package must not create its own Supabase client.

### 11.3 API workflow

Suggested initial endpoint:

``` text
POST /api/v1/ocr/extract
```

Workflow:

1.  Authenticate request.
2.  Authorize caller (initially staff-only unless a reviewed permission
    design says otherwise).
3.  Validate upload size, file signature, type, and page count.
4.  Store temporarily or in a private quarantine location.
5.  Run OCR in a worker/threadpool or background job; do not block the
    async event loop with CPU-heavy OCR.
6.  Return extraction result with `pending_review`.
7.  Record an audit event without logging PHI.
8.  Let staff inspect the original document and extracted fields.
9.  On explicit approval, call existing VISTRA services/repositories to
    save approved data.
10. Retain/delete the original according to VISTRA's retention policy.

### 11.4 Long-running jobs

For initial local development, a synchronous endpoint may be acceptable
for small documents if OCR is moved off the event loop and timeouts are
controlled.

For production or larger PDFs, use a job model:

``` text
POST /api/v1/ocr/jobs
GET  /api/v1/ocr/jobs/{job_id}
GET  /api/v1/ocr/jobs/{job_id}/result
POST /api/v1/ocr/jobs/{job_id}/review
```

A task queue/worker can be introduced when needed. Do not add
distributed infrastructure before measuring workload.

### 11.5 Database policy

Do not write OCR output directly into clinical tables. Consider separate
document-processing tables, for example:

-   `DOCUMENT`
-   `DOCUMENT_OCR_JOB`
-   `DOCUMENT_EXTRACTION`
-   `DOCUMENT_REVIEW`

These are conceptual names, not finalized schema. Design ownership, RLS,
retention, audit, and foreign keys before migrations.

After approval, use existing VISTRA service/repository workflows to
create or update clinical records. Do not bypass RLS or use a
service-role key as a shortcut for patient-facing flows.

------------------------------------------------------------------------

## 12. Privacy and security requirements

This module processes sensitive medical information. These requirements
are release blockers.

-   Require authentication and authorization for every upload, result,
    download, and review action.
-   Enforce least privilege; initial OCR access should be staff-only
    unless a documented use case justifies otherwise.
-   Store source documents privately, never in a public bucket or static
    frontend directory.
-   Use TLS in transit and approved encryption at rest.
-   Validate file content, not just extension or MIME header.
-   Limit file size, page count, image dimensions, processing time, and
    memory use.
-   Generate internal filenames/IDs; never use user input as a
    filesystem path.
-   Protect against malformed PDFs, decompression bombs, and resource
    exhaustion.
-   Delete temporary files on success and failure.
-   Avoid PHI in application logs, exception messages, analytics, and
    crash reports.
-   Audit who uploaded, viewed, processed, corrected, approved,
    downloaded, and deleted a document.
-   Define retention and deletion policies with the clinic/data
    controller.
-   Do not transmit PHI to external OCR/LLM services without formal
    approval and appropriate agreements.
-   Keep test fixtures synthetic or properly de-identified.
-   Never expose one patient's document or OCR result to another
    patient.
-   Treat OCR text as untrusted input; it may contain
    prompt-injection-like instructions. It must never be treated as
    executable instructions by an AI agent.

------------------------------------------------------------------------

## 13. Testing strategy

### Unit tests

Test each layer independently:

-   Loader: supported image, supported PDF, missing file, invalid file,
    unsupported extension, page limit.
-   Preprocessor: output dimensions, empty input, invalid input,
    original image preserved.
-   OCR adapter: mocked engine output, empty page, malformed engine
    result, low confidence.
-   Classifier: known document examples, ambiguous example, unknown
    document.
-   Extractors: valid fields, missing fields, confusing labels, OCR
    typos, multiple pages.
-   Validators: valid and invalid values, no silent correction.
-   Formatter: schema stability and page order.

### Integration tests

-   Image → preprocessing → OCR → formatted output.
-   PDF → page rendering → OCR → multi-page output.
-   Each supported document family → classifier → extractor →
    validation.
-   Empty/unreadable document → safe warning or failure.
-   Large/invalid input → safe rejection.

### Regression tests

Maintain a small, representative, de-identified test set. When code
changes, compare:

-   Character error rate (CER), if ground-truth transcription exists.
-   Word error rate (WER), if useful.
-   Field-level exact/normalized match.
-   Precision and recall for important extracted fields.
-   Classification accuracy and confusion matrix.
-   Percentage of fields requiring human correction.
-   Processing time and peak memory.

Track results by document type and image quality. A good average score
can hide poor performance for one document family.

### Test data rules

-   Do not commit identifiable patient documents.
-   Prefer synthetic forms for early tests.
-   Obtain approval before using real clinic documents.
-   Keep ground-truth annotations access-controlled.
-   Never use production patient records as casual debugging fixtures.

------------------------------------------------------------------------

## 14. Phased development roadmap

### Phase 0 --- Repository and environment

**Goal:** Establish a reproducible standalone Python package.

Tasks: - Create `document-intelligence/` package. - Use Python 3.11
environment initially. - Add `pyproject.toml`, dependency pins, README,
`.gitignore`. - Install compatible PaddlePaddle/PaddleOCR versions. -
Record tested OS/Python/library versions. - Confirm a simple OCR smoke
test works.

**Exit criteria:** A clean environment can install the package and run a
basic OCR test.

### Phase 1 --- OCR foundation

**Goal:** Convert images/PDFs into normalized OCR text with page
information.

Tasks: - Implement file loader. - Implement conservative
preprocessing. - Implement OCR engine interface and PaddleOCR adapter. -
Implement page/document formatter. - Implement a simple CLI. - Add unit
and integration tests. - Save JSON output for local test documents.

**Exit criteria:** - Supported images and PDFs process successfully. -
Multi-page PDFs preserve page order. - Output includes raw text, page
text, confidence, and regions where available. - Invalid files fail
safely. - No clinical data is written to Supabase.

### Phase 2 --- Classification

**Goal:** Identify the likely document family.

Tasks: - Add document type enum. - Implement keyword/rule classifier. -
Return confidence and matched indicators. - Add unknown/other
fallback. - Build labeled, de-identified test examples. - Measure
classification quality.

**Exit criteria:** Supported types are classified with measured
accuracy, and ambiguous documents remain unknown/other rather than being
forced into a category.

### Phase 3 --- Structured extraction

**Goal:** Extract type-specific fields.

Recommended implementation order: 1. Laboratory results. 2. Medical
certificates. 3. Vital-signs sheets. 4. Prescriptions. 5. Imaging
reports. 6. Dental records/odontograms. 7. Generic fallback
improvements.

Tasks: - Define Pydantic schemas per type. - Build one extractor per
type. - Retain source text/page references. - Add normalization and
warnings. - Test tables and multi-page documents.

**Exit criteria:** Each enabled extractor has documented fields, test
cases, and measured field-level performance.

### Phase 4 --- Review and validation

**Goal:** Make extraction safe for clinical workflow.

Tasks: - Add field-level confidence and validation status. - Add
warnings for missing/ambiguous fields. - Build staff review UI. - Show
original page next to extracted fields. - Allow correction and explicit
approval. - Record reviewer identity, timestamp, and changes.

**Exit criteria:** No OCR result can become a clinical record without
explicit authorized review.

### Phase 5 --- VISTRA backend integration

**Goal:** Connect the stable package to FastAPI.

Tasks: - Install local package with editable install. - Add
authenticated upload route. - Add OCR service and API schemas. - Add
private document storage and audit events. - Run processing outside the
async event loop. - Add job queue if measured workload requires it. -
Add database tables/migrations only after workflow design. - Persist
approved results through existing VISTRA services/repositories.

**Exit criteria:** End-to-end staff workflow works in a test environment
with RLS, audit, retention, and privacy checks.

### Phase 6 --- Optimization and advanced intelligence

Possible future work: - Embedded PDF text extraction and hybrid PDF
processing. - PP-StructureV3 for complex tables/layouts. - Handwriting
evaluation and specialized models. - Local terminology dictionaries and
abbreviation handling. - Language support based on real document
needs. - GPU acceleration or worker scaling. - Optional privacy-reviewed
LLM-assisted extraction with strict schemas and source grounding. -
Model evaluation and retraining only when a suitable labeled dataset
exists.

------------------------------------------------------------------------

## 15. Definition of done

The OCR module is not production-ready just because it recognizes text.

-   [ ] Clean installation from documented dependencies.
-   [ ] Supported image and PDF formats tested.
-   [ ] Multi-page documents supported.
-   [ ] OCR output normalized and traceable to source pages/regions.
-   [ ] Classification supports unknown/other.
-   [ ] Each enabled extractor has tests and measured field-level
    performance.
-   [ ] Low-confidence and missing fields are visibly flagged.
-   [ ] No values are silently invented or medically interpreted.
-   [ ] Staff review and explicit approval are required.
-   [ ] Authorization, RLS, audit, private storage, and retention are
    tested.
-   [ ] Temporary files and failed jobs are cleaned up.
-   [ ] PHI is not leaked into logs or external services.
-   [ ] Performance and resource limits are documented.
-   [ ] Known limitations are documented for each document type.

------------------------------------------------------------------------

## 16. Instructions for the AI coding agent

When assisting with this project, follow these rules:

1.  **Inspect before editing.** Read the current repository structure,
    `pyproject.toml`, requirements, Python version, and existing code
    before proposing file changes.
2.  **Do not assume files exist.** Confirm paths and current
    implementations first.
3.  **Implement one phase at a time.** Do not jump to LLM extraction,
    database writes, or microservices before Phase 1 is stable.
4.  **Preserve package boundaries.** The OCR package must not import
    VISTRA application modules, FastAPI, or Supabase.
5.  **Use typed interfaces.** Prefer Pydantic models, explicit return
    types, and typed exceptions.
6.  **Use the installed PaddleOCR API.** Check the actual installed
    version and official API shape. Do not copy outdated PaddleOCR 2.x
    examples into a 3.x project.
7.  **Normalize engine output.** Keep PaddleOCR-specific objects inside
    the adapter.
8.  **Do not guess medical values.** Missing or unclear data must be
    `null` with a warning.
9.  **Preserve evidence.** Every extracted field should retain source
    text and page/region information when possible.
10. **Do not write to clinical tables.** Database persistence is out of
    scope until the review workflow is implemented and explicitly
    approved.
11. **Protect PHI.** Never print or log full patient documents or
    recognized medical text during normal operation.
12. **Add tests with each feature.** Include normal, edge, malformed,
    and low-confidence cases.
13. **Explain commands for Windows PowerShell.** The primary development
    environment is Windows.
14. **Avoid unnecessary dependencies.** Add a library only when a
    concrete requirement justifies it.
15. **Report changes clearly.** For every implementation task, summarize
    files changed, commands to run, tests performed, results, and
    remaining risks.
16. **Do not claim a feature works without running its tests.** If tests
    cannot be run, state why.
17. **Ask before destructive changes.** Do not overwrite migrations,
    delete data, or change existing VISTRA auth/RLS behavior without
    explicit approval.

### Suggested first task for the agent

> Inspect the current VISTRA repository and create the standalone
> `backend/document-intelligence` Python package for Phase 1 only.
> Implement the loader, conservative preprocessor, PaddleOCR adapter
> compatible with the installed PaddleOCR 3.x version, normalized
> page/document output, CLI, and pytest tests. Do not implement medical
> extraction, LLM integration, FastAPI routes, or Supabase writes yet.
> First report the detected Python version, OS, repository layout, and
> dependency compatibility risks. Then implement incrementally and run
> the tests.

------------------------------------------------------------------------

## 17. Key architectural decision

**Build the OCR engine as a standalone, reusable Python package;
integrate it into VISTRA through a backend service and authenticated
API.**

This separates document recognition from clinical business logic. It
also allows the OCR engine to be tested independently, replaced later,
and eventually moved into a worker or microservice if processing demands
increase.

The first milestone is deliberately narrow: **reliably turn a supported
image or PDF into traceable OCR text.** Classification, medical
extraction, review, and database integration come afterward.
