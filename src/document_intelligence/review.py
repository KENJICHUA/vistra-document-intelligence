"""Staff review helpers for OCR results.

This module does not persist anything. The VISTRA backend owns audit storage.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReviewStatus(str, Enum):
    PENDING = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CORRECTED = "corrected"


class ReviewRecord(BaseModel):
    document_id: str
    reviewer_id: str
    status: ReviewStatus
    reviewed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    changes: List[Dict[str, Any]] = Field(default_factory=list)
    notes: Optional[str] = None


def _set_path(obj: Any, path: str, value: Any) -> None:
    current = obj
    parts = path.split(".")
    for part in parts[:-1]:
        if isinstance(current, dict):
            current = current.setdefault(part, {})
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return
        elif hasattr(current, part):
            next_value = getattr(current, part)
            if next_value is None:
                setattr(current, part, {})
                next_value = getattr(current, part)
            current = next_value
        else:
            return
    last = parts[-1]
    if isinstance(current, dict):
        current[last] = value
    elif isinstance(current, list):
        try:
            current[int(last)] = value
        except (ValueError, IndexError):
            return
    elif hasattr(current, last):
        setattr(current, last, value)


def apply_review(
    result: Any,
    reviewer_id: str,
    approved: bool,
    corrections: Optional[Dict[str, Any]] = None,
    notes: Optional[str] = None,
) -> ReviewRecord:
    changes: List[Dict[str, Any]] = []
    if corrections:
        for path, new_value in corrections.items():
            old_value = None
            try:
                old_value = _get_path(result, path)
            except Exception:
                old_value = None
            _set_path(result, path, new_value)
            changes.append({"field": path, "old_value": old_value, "new_value": new_value})

    status = ReviewStatus.APPROVED if approved and not changes else ReviewStatus.CORRECTED
    if not approved:
        status = ReviewStatus.REJECTED

    result.status = status.value
    result.review = {
        "required": True,
        "reviewed_by": reviewer_id,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }

    return ReviewRecord(
        document_id=getattr(result, "document_id", ""),
        reviewer_id=reviewer_id,
        status=status,
        changes=changes,
        notes=notes,
    )


def _get_path(obj: Any, path: str) -> Any:
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