"""Unit tests for the OCR transcript scanner service."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from api.services.ocr import COURSE_PATTERN, OCRError, extract_transcript_csv


def test_course_pattern_regex_clean():
    """Test the regex matching on clean, perfect OCR output."""
    raw = "CSE115  3  A-  Spring 2023"
    match = COURSE_PATTERN.search(raw)
    assert match is not None
    assert match.group(1) == "CSE115"
    assert match.group(2) == "3"
    assert match.group(3) == "A-"
    assert match.group(4) == "Spring"
    assert match.group(5) == "2023"

def test_course_pattern_regex_noisy_spacing():
    """Test the regex matching on OCR output with extra spaces/weird spacing."""
    # Sometimes OCR puts spaces inside the grade or around credits
    raw = "ENG102    3.0    B +    Summer   2021"
    match = COURSE_PATTERN.search(raw)
    assert match is not None
    assert match.group(1) == "ENG102"
    assert match.group(2) == "3.0"
    assert match.group(3) == "B +"  # Our code will strip the space later: replace(" ", "")
    assert match.group(4) == "Summer"
    assert match.group(5) == "2021"

def test_course_pattern_regex_complex_codes():
    """Test that it handles 4-letter course codes and appended letters."""
    raw = "ACT201A 3 A Fall 2020"
    match = COURSE_PATTERN.search(raw)
    assert match is not None
    assert match.group(1) == "ACT201A"

def test_extract_transcript_csv_mocked_image(tmp_path):
    """Test the full pipeline using a mock image and mock Tesseract return string."""
    # Create a dummy image file
    dummy_img = tmp_path / "dummy.png"
    dummy_img.write_bytes(b"fake_image_data")

    # The raw string Tesseract might return
    mock_tesseract_output = """
North South University
Academic Transcript
Name: Jane Doe
ID: 1234567

Course  Cr  Grade Semester
ENG102  3   A-    Spring 2019
MAT120  3.0 C +   Summer 2019
CSE115  3   F     Fall 2019
"""

    with patch('api.services.ocr.Image.open') as mock_open:
        # Mock the context manager behavior of Image.open()
        mock_img = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_img

        with patch('api.services.ocr._extract_from_image', return_value=mock_tesseract_output):
            result_csv = extract_transcript_csv(dummy_img)

            # Should have the header + 3 rows
            lines = result_csv.splitlines()
            assert len(lines) == 4
            assert lines[0] == "Course_Code,Credits,Grade,Semester"
            assert lines[1] == "ENG102,3,A-,Spring 2019"
            assert lines[2] == "MAT120,3.0,C+,Summer 2019"  # Ensure the C + became C+
            assert lines[3] == "CSE115,3,F,Fall 2019"

def test_extract_transcript_csv_no_courses(tmp_path):
    """Test that OCR raises an error if no valid courses are found."""
    dummy_img = tmp_path / "dummy.png"
    dummy_img.write_bytes(b"fake_image_data")

    mock_invalid_output = "Just some random text\nNothing matching a course."

    with patch('api.services.ocr.Image.open') as mock_open:
        mock_img = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_img

        with patch('api.services.ocr._extract_from_image', return_value=mock_invalid_output):
            with pytest.raises(OCRError, match="No valid course records found"):
                extract_transcript_csv(dummy_img)

def test_extract_transcript_csv_file_not_found():
    """Test file not found handling."""
    with pytest.raises(OCRError, match="File not found"):
        extract_transcript_csv("nonexistent_file.pdf")
