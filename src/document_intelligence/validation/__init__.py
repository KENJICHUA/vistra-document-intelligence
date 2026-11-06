from .confidence import is_low_confidence


def make_warning(code: str, field: str, message: str, severity: str = "warning") -> dict:
    return {
        "code": code,
        "field": field,
        "message": message,
        "severity": severity,
    }


from .medical import validate_result

__all__ = ["is_low_confidence", "make_warning", "validate_result"]