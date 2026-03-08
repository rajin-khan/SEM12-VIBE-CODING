"""OCR Transcript Scanner Service.

Uses Tesseract OCR to extract transcript data from images or PDFs,
then parses the text with regex to generate an NSU-format CSV string
suitable for the GradGate engine.
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image, ImageEnhance
except ImportError:
    pytesseract = None
    convert_from_path = None
    Image = None
    ImageEnhance = None


# Regex to match NSU transcript lines: e.g. "CSE115  3  A-  Spring 2023"
# Or variations with strange spacing/typos due to OCR
COURSE_PATTERN = re.compile(
    r'([A-Z]{2,4}\d{3}[A-Z]?)'  # Course Code (e.g. CSE115, ENG102, MAT120A)
    r'\s+'
    r'(\d+(?:\.\d+)?)'          # Credits (e.g. 3, 3.0, 1.5)
    r'\s+'
    r'([A-DF]\s*[+-]?|W|I|T|P)'                          # Grade
    r'\s+'
    r'(Spring|Summer|Fall)'     # Semester Season
    r'\s+'
    r'(\d{4})'                  # Semester Year
)

CSV_HEADER = "Course_Code,Credits,Grade,Semester"


class OCRError(Exception):
    """Raised when OCR or parsing fails."""
    pass


def _preprocess_image(img: Image.Image) -> Image.Image:
    """Apply basic preprocessing to improve OCR accuracy."""
    # Convert to grayscale
    img = img.convert("L")
    # Increase contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    return img


def _extract_from_image(img: Image.Image) -> str:
    """Run Tesseract on a single PIL Image and return raw text."""
    if pytesseract is None:
        raise RuntimeError("pytesseract is not installed")

    img = _preprocess_image(img)
    # PSM 6: Assume a single uniform block of text
    text = pytesseract.image_to_string(img, config="--psm 6")
    return text


def extract_transcript_csv(file_path: str | Path) -> str:
    """Process an image or PDF transcript and return a structured CSV string.

    Raises:
        OCRError: If no valid courses were found or processing failed.
    """
    if Image is None or pytesseract is None:
        raise RuntimeError("OCR dependencies (pytesseract, Pillow, pdf2image) are not installed")

    path = Path(file_path)
    if not path.exists():
        raise OCRError(f"File not found: {path}")

    ext = path.suffix.lower()
    raw_text = ""

    try:
        if ext == ".pdf":
            # Convert PDF pages to images
            if convert_from_path is None:
                raise RuntimeError("pdf2image is not installed")
            pages = convert_from_path(str(path))
            for page in pages:
                raw_text += _extract_from_image(page) + "\n"
        elif ext in (".png", ".jpg", ".jpeg"):
            # Process single image
            with Image.open(path) as img:
                raw_text = _extract_from_image(img)
        else:
            raise OCRError(f"Unsupported file type: {ext}. Use PDF, PNG, or JPEG.")
    except Exception as e:
        raise OCRError(f"Failed to process image/PDF: {e}") from e

    # Parse raw text with regex
    records = []
    for line in raw_text.splitlines():
        # Clean up common OCR artifacts in the line first
        line = line.strip()
        if not line:
            continue

        match = COURSE_PATTERN.search(line)
        if match:
            code = match.group(1).upper()
            credits = match.group(2)
            # Fix common OCR typos in grades (e.g., A - -> A-)
            grade = match.group(3).upper().replace(" ", "")
            semester = f"{match.group(4).capitalize()} {match.group(5)}"

            # Additional cleanup for missing decimals in credits if it was OCR'd purely as an integer (like 3 instead of 3.0, which is fine)
            records.append((code, credits, grade, semester))

    if not records:
        raise OCRError("No valid course records found in the document. Ensure it's a clear NSU transcript.")

    # Generate CSV string
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(CSV_HEADER.split(","))
    for rec in records:
        writer.writerow(rec)

    return output.getvalue().strip()
