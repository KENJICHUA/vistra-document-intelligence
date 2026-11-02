"""Main OCR processing pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Union

from .engine import OCREngine
from .formatter import OCRResult, ResultFormatter
from .loader import DocumentLoader
from .preprocessor import ImagePreprocessor


class OCRPipeline:
    def __init__(
        self,
        lang: str = "en",
        max_side: int = 2000,
        deskew: bool = False,
    ) -> None:
        self.loader = DocumentLoader()
        self.preprocessor = ImagePreprocessor(max_side=max_side, deskew=deskew)
        self.engine = OCREngine(lang=lang)
        self.formatter = ResultFormatter()

    def process(self, file_path: Union[str, Path]) -> OCRResult:
        path = Path(file_path)
        images = self.loader.load(path)

        pages = []
        for page_number, image in enumerate(images, start=1):
            processed = self.preprocessor.process(image)
            lines = self.engine.recognize(processed)
            text = "\n".join(line["text"] for line in lines)
            pages.append(
                {
                    "page_number": page_number,
                    "text": text,
                    "lines": lines,
                }
            )

        return self.formatter.format(path.name, pages)