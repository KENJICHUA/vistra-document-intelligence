"""Image preprocessing for OCR.

The preprocessor is intentionally conservative: it only resizes oversized images.
Aggressive grayscale/thresholding/sharpening is avoided because it can destroy
useful information in medical documents (coloured annotations, light text, tables).
"""

from __future__ import annotations

from typing import Optional

import cv2
import numpy as np


class ImagePreprocessor:
    def __init__(self, max_side: int = 2000, deskew: bool = False) -> None:
        self.max_side = max_side
        self.deskew = deskew

    def process(self, image: np.ndarray) -> np.ndarray:
        if image is None:
            raise ValueError("Input image is None")

        result = image.copy()

        # Resize oversized images to keep processing time reasonable.
        height, width = result.shape[:2]
        longest = max(height, width)
        if longest > self.max_side:
            scale = self.max_side / longest
            new_width = int(width * scale)
            new_height = int(height * scale)
            result = cv2.resize(
                result, (new_width, new_height), interpolation=cv2.INTER_AREA
            )

        if self.deskew:
            result = self._deskew(result)

        return result

    @staticmethod
    def _deskew(image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        coords = np.column_stack(np.where(gray < 255))
        if coords.size == 0:
            return image
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) < 0.5:
            return image
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(
            image, matrix, (width, height), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )