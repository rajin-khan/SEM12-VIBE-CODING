"""Unit tests for the OCR and PDF transcript extraction service."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from api.services import ocr
from api.services.ocr import COURSE_PATTERN, OCRDependencyError, OCRError, extract_transcript_csv, get_ocr_status


def test_course_pattern_regex_clean():
    raw = "CSE115  3  A-  Spring 2023"
    match = COURSE_PATTERN.search(raw)
    assert match is not None
    assert match.group(1) == "CSE115"
    assert match.group(2) == "3"
    assert match.group(3) == "A-"
    assert match.group(4) == "Spring"
    assert match.group(5) == "2023"


def test_course_pattern_regex_noisy_spacing():
    raw = "ENG102    3.0    B +    Summer   2021"
    match = COURSE_PATTERN.search(raw)
    assert match is not None
    assert match.group(1) == "ENG102"
    assert match.group(2) == "3.0"
    assert match.group(3) == "B +"
    assert match.group(4) == "Summer"
    assert match.group(5) == "2021"


def test_extract_transcript_csv_mocked_image(tmp_path):
    dummy_img = tmp_path / "dummy.png"
    dummy_img.write_bytes(b"fake_image_data")

    mock_tesseract_output = """
North South University
Academic Transcript
ENG102  3   A-    Spring 2019
MAT120  3.0 C +   Summer 2019
CSE115  3   F     Fall 2019
"""

    with patch("api.services.ocr.Image.open") as mock_open:
        mock_open.return_value.__enter__.return_value = MagicMock()
        with patch("api.services.ocr._extract_from_image", return_value=mock_tesseract_output):
            result_csv = extract_transcript_csv(dummy_img)

    lines = result_csv.splitlines()
    assert lines == [
        "Course_Code,Credits,Grade,Semester",
        "ENG102,3,A-,Spring 2019",
        "MAT120,3.0,C+,Summer 2019",
        "CSE115,3,F,Fall 2019",
    ]


def test_extract_transcript_csv_text_pdf_first(tmp_path, monkeypatch):
    dummy_pdf = tmp_path / "transcript.pdf"
    dummy_pdf.write_bytes(b"%PDF-1.4 fake")

    class FakePage:
        def extract_text(self):
            return "ENG102 3 A- Spring 2019\nCSE115 3 A Fall 2019"

    class FakeReader:
        def __init__(self, _path: str):
            self.pages = [FakePage()]

    monkeypatch.setattr(ocr, "PdfReader", FakeReader)

    result_csv = extract_transcript_csv(dummy_pdf)

    assert result_csv.splitlines() == [
        "Course_Code,Credits,Grade,Semester",
        "ENG102,3,A-,Spring 2019",
        "CSE115,3,A,Fall 2019",
    ]


def test_extract_transcript_csv_scanned_pdf_falls_back_to_ocr(tmp_path, monkeypatch):
    dummy_pdf = tmp_path / "scanned.pdf"
    dummy_pdf.write_bytes(b"%PDF-1.4 fake")

    class EmptyPage:
        def extract_text(self):
            return ""

    class EmptyReader:
        def __init__(self, _path: str):
            self.pages = [EmptyPage()]

    monkeypatch.setattr(ocr, "PdfReader", EmptyReader)
    with patch("api.services.ocr._extract_text_via_pdf_ocr", return_value="EEE154 1 A Fall 2020"):
        result_csv = extract_transcript_csv(dummy_pdf)

    assert result_csv.splitlines() == [
        "Course_Code,Credits,Grade,Semester",
        "EEE154,1,A,Fall 2020",
    ]


def test_extract_transcript_csv_no_courses(tmp_path):
    dummy_img = tmp_path / "dummy.png"
    dummy_img.write_bytes(b"fake_image_data")

    with patch("api.services.ocr.Image.open") as mock_open:
        mock_open.return_value.__enter__.return_value = MagicMock()
        with patch("api.services.ocr._extract_from_image", return_value="random text only"):
            with pytest.raises(OCRError, match="No valid course records found"):
                extract_transcript_csv(dummy_img)


def test_extract_transcript_csv_missing_image_ocr_dependency(tmp_path, monkeypatch):
    dummy_img = tmp_path / "dummy.png"
    dummy_img.write_bytes(b"fake_image_data")

    monkeypatch.setattr(ocr, "pytesseract", None)
    monkeypatch.setattr(ocr, "_which", lambda binary: None if binary == "tesseract" else "/usr/bin/pdftoppm")

    with patch("api.services.ocr.Image.open") as mock_open:
        mock_open.return_value.__enter__.return_value = MagicMock()
        with pytest.raises(OCRDependencyError, match="Image OCR is not available"):
            extract_transcript_csv(dummy_img)


def test_ocr_status_reports_dependency_state(monkeypatch):
    monkeypatch.setattr(ocr, "pytesseract", SimpleNamespace(image_to_string=lambda *_args, **_kwargs: ""))
    monkeypatch.setattr(ocr, "convert_from_path", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ocr, "PdfReader", object)
    monkeypatch.setattr(
        ocr,
        "_which",
        lambda binary: "/usr/bin/fake" if binary in {"tesseract", "pdftoppm"} else None,
    )

    status = get_ocr_status()

    assert status["image_ocr_ready"] is True
    assert status["scanned_pdf_ready"] is True
    assert status["text_pdf_ready"] is True
    assert status["messages"] == []


def test_extract_transcript_csv_file_not_found():
    with pytest.raises(OCRError, match="File not found"):
        extract_transcript_csv("nonexistent_file.pdf")
