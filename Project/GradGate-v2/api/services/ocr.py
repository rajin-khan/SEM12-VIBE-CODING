"""Backward-compatible OCR exports."""

from api.services.document_ingestion import (  # noqa: F401
    ALL_SUPPORTED_EXTENSIONS,
    BASE_IMAGE_EXTENSIONS,
    CSV_HEADER,
    PDF_EXTENSIONS,
    COURSE_CODE_PATTERN as COURSE_PATTERN,
    OCRDependencyError,
    OCRError,
    extract_transcript_document,
    get_ocr_status,
)


def extract_transcript_csv(file_path):
    return extract_transcript_document(file_path).extracted_csv

