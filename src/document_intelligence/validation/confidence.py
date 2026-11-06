"""Confidence helpers (Phase 4+)."""

from __future__ import annotations


def is_low_confidence(confidence: float, threshold: float = 0.7) -> bool:
    return confidence < threshold