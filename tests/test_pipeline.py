import os
import sys
from pathlib import Path

os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "False")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from document_intelligence import OCRPipeline  # noqa: E402


def test_pipeline_image() -> None:
    image_path = ROOT / "samples" / "images" / "laboratory_result.png"
    result = OCRPipeline().process(image_path)
    assert result.page_count == 1
    assert "Patient Name" in result.raw_text
    assert result.pages[0].lines
    assert result.document_type == "laboratory_result"