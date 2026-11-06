"""Abstract OCR engine interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class OCREngine(ABC):
    @abstractmethod
    def recognize(self, image: Any) -> List[Dict[str, Any]]:
        """Return normalized text regions for one page."""