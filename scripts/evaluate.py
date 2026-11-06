"""Evaluate OCR extraction against de-identified fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from document_intelligence import OCRPipeline  # noqa: E402


def get_path(obj: object, path: str):
    current = obj
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            return None
        if current is None:
            return None
    return current


def values_equal(actual, expected) -> bool:
    if isinstance(actual, list) and not isinstance(expected, list):
        return len(actual) == expected
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        try:
            return float(actual) == float(expected)
        except (TypeError, ValueError):
            return False
    return str(actual).strip() == str(expected).strip()


def main() -> None:
    fixtures_dir = ROOT / "tests" / "fixtures"
    fixture_files = sorted(fixtures_dir.glob("*.json"))
    if not fixture_files:
        print("No fixtures found.")
        return

    pipeline = OCRPipeline()
    total_fields = 0
    correct_fields = 0
    classification_correct = 0

    for fixture_path in fixture_files:
        ground_truth = json.loads(fixture_path.read_text(encoding="utf-8"))
        image_path = ROOT / ground_truth["image"]
        result = pipeline.process(image_path)

        print(f"\n=== {fixture_path.name} ===")
        print(f"Predicted type: {result.document_type} (expected: {ground_truth['document_type']})")
        if result.document_type == ground_truth["document_type"]:
            classification_correct += 1

        result_dict = result.model_dump()
        for field_path, expected in ground_truth.get("fields", {}).items():
            actual = get_path(result_dict, field_path)
            ok = values_equal(actual, expected)
            total_fields += 1
            if ok:
                correct_fields += 1
            print(f"  {field_path}: expected={expected!r} actual={actual!r} {'OK' if ok else 'MISMATCH'}")

    print("\n=== Summary ===")
    print(f"Classification accuracy: {classification_correct}/{len(fixture_files)}")
    if total_fields:
        print(f"Field exact-match accuracy: {correct_fields}/{total_fields} ({correct_fields / total_fields:.2%})")


if __name__ == "__main__":
    main()