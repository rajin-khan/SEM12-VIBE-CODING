"""Unit tests for canonical document ingestion."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from api.services import document_ingestion as ingestion
from api.services.ocr import COURSE_PATTERN, OCRDependencyError, OCRError, extract_transcript_csv, get_ocr_status


def test_course_pattern_regex_clean():
    raw = "CSE115  3  A-  Spring 2023"
    match = COURSE_PATTERN.search(raw)
    assert match is not None


def test_extract_transcript_csv_mocked_image(tmp_path):
    dummy_img = tmp_path / "dummy.png"
    dummy_img.write_bytes(b"fake_image_data")

    with patch(
        "api.services.document_ingestion._extract_from_image",
        return_value=(
            "ENG102 3 A- Spring 2019\nCSE115 3 A Spring 2019\nMAT120 3 B+ Spring 2019",
            1,
        ),
    ):
        result_csv = extract_transcript_csv(dummy_img)

    assert result_csv.splitlines() == [
        "Course_Code,Credits,Grade,Semester",
        "ENG102,3,A-,Spring 2019",
        "CSE115,3,A,Spring 2019",
        "MAT120,3,B+,Spring 2019",
    ]


def test_extract_transcript_document_text_pdf_first(tmp_path, monkeypatch):
    dummy_pdf = tmp_path / "transcript.pdf"
    dummy_pdf.write_bytes(b"%PDF-1.4 fake")

    class FakePage:
        def extract_text(self):
            return "ENG102 3 A- Spring 2019\nCSE115 3 A Fall 2019\nMAT120 3 B+ Fall 2019"

    class FakeReader:
        def __init__(self, _path: str):
            self.pages = [FakePage()]

    monkeypatch.setattr(ingestion, "PdfReader", FakeReader)

    result = ingestion.extract_transcript_document(dummy_pdf)

    assert result.extraction_mode == "pdf_text"
    assert result.review_required is False
    assert result.extracted_csv.splitlines() == [
        "Course_Code,Credits,Grade,Semester",
        "ENG102,3,A-,Spring 2019",
        "CSE115,3,A,Fall 2019",
        "MAT120,3,B+,Fall 2019",
    ]


def test_extract_transcript_document_scanned_pdf_falls_back_to_ocr(tmp_path, monkeypatch):
    dummy_pdf = tmp_path / "scanned.pdf"
    dummy_pdf.write_bytes(b"%PDF-1.4 fake")

    class EmptyPage:
        def extract_text(self):
            return ""

    class EmptyReader:
        def __init__(self, _path: str):
            self.pages = [EmptyPage()]

    monkeypatch.setattr(ingestion, "PdfReader", EmptyReader)
    with patch(
        "api.services.document_ingestion._extract_text_via_pdf_ocr",
        return_value=("EEE154 1 A Fall 2020\nEEE111 3 B Fall 2020\nCSE115 3 A Fall 2020", 1),
    ):
        result = ingestion.extract_transcript_document(dummy_pdf)

    assert result.extraction_mode == "pdf_ocr"
    assert result.rows_detected == 3


def test_extract_transcript_document_low_confidence_requires_review(tmp_path):
    dummy_img = tmp_path / "dummy.png"
    dummy_img.write_bytes(b"fake_image_data")

    with patch(
        "api.services.document_ingestion._extract_from_image",
        return_value=(
            "Spring 2019\nENG102 Intro Composition 3 A-\nCSE115 Intro Programming 3 A\nMAT120 Calculus 3 B+\nPHY107 Physics 3 B",
            1,
        ),
    ):
        result = ingestion.extract_transcript_document(dummy_img)

    assert result.review_required is True
    assert result.review_payload()["warnings"]


def test_extract_transcript_csv_missing_image_ocr_dependency(tmp_path, monkeypatch):
    dummy_img = tmp_path / "dummy.png"
    dummy_img.write_bytes(b"fake_image_data")

    monkeypatch.setattr(ingestion, "pytesseract", None)
    monkeypatch.setattr(
        ingestion,
        "_which",
        lambda binary: None if binary == "tesseract" else "/usr/bin/pdftoppm",
    )

    with pytest.raises(OCRDependencyError, match="Image OCR is not available"):
        ingestion.extract_transcript_document(dummy_img)


def test_ocr_status_reports_dependency_state(monkeypatch):
    monkeypatch.setattr(ingestion, "pytesseract", SimpleNamespace(image_to_string=lambda *_args, **_kwargs: ""))
    monkeypatch.setattr(ingestion, "convert_from_path", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ingestion, "PdfReader", object)
    monkeypatch.setattr(ingestion, "pillow_heif", SimpleNamespace(register_heif_opener=lambda: None))
    monkeypatch.setattr(
        ingestion,
        "_which",
        lambda binary: "/usr/bin/fake" if binary in {"tesseract", "pdftoppm"} else None,
    )

    status = get_ocr_status()

    assert status["image_ocr_ready"] is True
    assert status["scanned_pdf_ready"] is True
    assert status["text_pdf_ready"] is True
    assert ".pdf" in status["supported_extensions"]
    assert "pdf_text" in status["extraction_modes"]


def test_extract_transcript_document_file_not_found():
    with pytest.raises(OCRError, match="File not found"):
        ingestion.extract_transcript_document("nonexistent_file.pdf")


def test_extract_transcript_document_unsupported_type(tmp_path):
    bad = tmp_path / "transcript.txt"
    bad.write_text("hello")
    with pytest.raises(OCRError, match="Unsupported file type"):
        ingestion.extract_transcript_document(bad)


def test_extract_transcript_document_rejects_non_transcript_like_file(tmp_path):
    dummy_img = tmp_path / "dummy.png"
    dummy_img.write_bytes(b"fake_image_data")

    with patch(
        "api.services.document_ingestion._extract_from_image",
        return_value=("ENG102 3 A- Spring 2019", 1),
    ):
        with pytest.raises(OCRError, match="No valid transcript course records were found"):
            ingestion.extract_transcript_document(dummy_img)
