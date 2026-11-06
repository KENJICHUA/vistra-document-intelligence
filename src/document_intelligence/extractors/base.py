"""Shared extractor interface (Phase 3+)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseExtractor(ABC):
    document_type: str

    @abstractmethod
    def extract(self, document: Any) -> Any:
        """Extract type-specific fields from a processed document."""