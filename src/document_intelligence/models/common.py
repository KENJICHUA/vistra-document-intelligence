"""Common enumerations and simple data types."""

from __future__ import annotations

from enum import Enum


class DocumentType(str, Enum):
    LABORATORY_RESULT = "laboratory_result"
    PRESCRIPTION = "prescription"
    MEDICAL_CERTIFICATE = "medical_certificate"
    VITAL_SIGNS = "vital_signs"
    MEDICAL_EXAMINATION = "medical_examination"
    DENTAL_RECORD = "dental_record"
    IMAGING_REPORT = "imaging_report"
    DISCHARGE_SUMMARY = "discharge_summary"
    GENERAL_PATIENT_RECORD = "general_patient_record"
    OTHER = "other"
    UNKNOWN = "unknown"