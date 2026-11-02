"""Entry point for the VISTRA document intelligence OCR tool."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from document_intelligence import OCRPipeline  # noqa: E402


def main() -> None:
    document_path = input("Enter document path: ").strip()
    if not document_path:
        print("No path provided.")
        return

    pipeline = OCRPipeline()
    result = pipeline.process(document_path)

    output_dir = ROOT / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "ocr_result.json"
    output_path.write_text(
        result.model_dump_json(indent=2), encoding="utf-8"
    )

    print("\nOCR completed successfully!\n")
    print(f"Pages processed: {result.page_count}")
    print(f"Output saved to: {output_path}\n")
    print("Extracted text:\n")
    print(result.raw_text)


if __name__ == "__main__":
    main()