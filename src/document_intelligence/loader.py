"""Document loading: convert supported file formats into a list of images."""

from __future__ import annotations

from pathlib import Path
from typing import List

import cv2
import pymupdf  # PyMuPDF
import numpy as np


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


class DocumentLoader:
    """Load a document (image or PDF) and return a list of BGR images (one per page)."""

    def __init__(self, pdf_dpi: int = 200) -> None:
        self.pdf_dpi = pdf_dpi

    def load(self, file_path: str | Path) -> List[np.ndarray]:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Document not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return self._load_pdf(path)
        if suffix in IMAGE_EXTENSIONS:
            return [self._load_image(path)]
        raise ValueError(f"Unsupported file format: {suffix}")

    @staticmethod
    def _load_image(path: Path) -> np.ndarray:
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Could not read image: {path}")
        return image

    def _load_pdf(self, path: Path) -> List[np.ndarray]:
        images: List[np.ndarray] = []
        zoom = self.pdf_dpi / 72.0
        matrix = pymupdf.Matrix(zoom, zoom)
        with pymupdf.open(str(path)) as document:
            for page in document:
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                samples = pixmap.samples
                image = np.frombuffer(samples, dtype=np.uint8).reshape(
                    pixmap.height, pixmap.width, pixmap.n
                )
                if pixmap.n == 4:
                    image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
                elif pixmap.n == 3:
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                elif pixmap.n == 1:
                    image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
                images.append(image)
        if not images:
            raise ValueError(f"PDF contains no pages: {path}")
        return images