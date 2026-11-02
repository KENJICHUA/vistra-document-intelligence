"""PaddleOCR engine wrapper.

The engine is a long-lived object: model initialization is expensive, so it is
created once and reused for every page and document.
"""

from __future__ import annotations

import os

os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "False"
os.environ["OMP_NUM_THREADS"] = "1"

from typing import Any, Dict, List

import numpy as np
from paddleocr import PaddleOCR


class OCREngine:
    def __init__(self, lang: str = "en") -> None:
        self.lang = lang
        self._ocr = PaddleOCR(lang=lang, use_textline_orientation=True)

    def recognize(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Run OCR on a single image and return a list of line dicts."""
        result = self._ocr.predict(image)
        if not result:
            return []

        page = result[0] if isinstance(result, (list, tuple)) else result
        if not isinstance(page, dict):
            return []

        texts = page.get("rec_texts") or []
        scores = page.get("rec_scores") or []
        boxes = page.get("rec_boxes")
        polys = page.get("rec_polys") or []

        lines: List[Dict[str, Any]] = []
        for index, text in enumerate(texts):
            score = float(scores[index]) if index < len(scores) else 0.0

            if boxes is not None and index < len(boxes):
                box = boxes[index]
                bbox = [int(box[0]), int(box[1]), int(box[2]), int(box[3])]
            elif index < len(polys) and polys[index] is not None:
                poly = polys[index]
                xs = [int(point[0]) for point in poly]
                ys = [int(point[1]) for point in poly]
                bbox = [min(xs), min(ys), max(xs), max(ys)]
            else:
                bbox = [0, 0, 0, 0]

            lines.append(
                {
                    "text": str(text),
                    "confidence": round(score, 4),
                    "bounding_box": bbox,
                }
            )

        return lines