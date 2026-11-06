"""Main OCR processing pipeline."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Union

from .classification import DocumentClassifier
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
        self.classifier = DocumentClassifier()
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

        raw_text = "\n\n".join(page["text"] for page in pages if page["text"])
        classification = self.classifier.classify(raw_text)

        return self.formatter.format(
            filename=path.name,
            pages=pages,
            document_id=str(uuid.uuid4()),
            classification=classification,
        )