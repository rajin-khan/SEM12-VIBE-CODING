"""Transcript extraction service for scanned images and PDFs."""

from __future__ import annotations

import csv
import io
import re
import shutil
from pathlib import Path
from typing import Any


class _MissingImageModule:
    @staticmethod
    def open(*_args, **_kwargs):
        raise RuntimeError("Pillow is not installed")


class _MissingImageEnhanceModule:
    @staticmethod
    def Contrast(*_args, **_kwargs):
        raise RuntimeError("Pillow is not installed")


try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image, ImageEnhance
except ImportError:
    pytesseract = None
    convert_from_path = None
    Image = _MissingImageModule()
    ImageEnhance = _MissingImageEnhanceModule()

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


CSV_HEADER = "Course_Code,Credits,Grade,Semester"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
PDF_EXTENSIONS = {".pdf"}

# Match NSU-style transcript rows with some OCR noise tolerance.
COURSE_PATTERN = re.compile(
    r"([A-Z]{2,4}\d{3}[A-Z]?)"
    r"\s+"
    r"(\d+(?:\.\d+)?)"
    r"\s+"
    r"([A-DF]\s*[+-]?|W|I|T|P)"
    r"\s+"
    r"(Spring|Summer|Fall)"
    r"\s+"
    r"(\d{4})",
    re.IGNORECASE,
)


class OCRError(Exception):
    """Raised when transcript extraction or OCR parsing fails."""


class OCRDependencyError(OCRError):
    """Raised when local OCR dependencies are missing."""


def _which(binary: str) -> str | None:
    return shutil.which(binary)


def get_ocr_status() -> dict[str, Any]:
    """Return OCR capability metadata for local development and diagnostics."""
    pytesseract_ready = pytesseract is not None
    pillow_ready = hasattr(Image, "open")
    pdf_renderer_ready = convert_from_path is not None
    pdf_text_ready = PdfReader is not None
    tesseract_ready = _which("tesseract") is not None
    poppler_ready = _which("pdftoppm") is not None

    image_ocr_ready = pytesseract_ready and pillow_ready and tesseract_ready
    scanned_pdf_ready = image_ocr_ready and pdf_renderer_ready and poppler_ready
    text_pdf_ready = pdf_text_ready

    messages: list[str] = []
    if not pytesseract_ready:
        messages.append("Install Python OCR extras: `pip install '.[ocr]'`.")
    if not tesseract_ready:
        messages.append("Install the `tesseract` binary and ensure it is on PATH.")
    if not poppler_ready:
        messages.append("Install Poppler so `pdftoppm` is available on PATH for scanned PDFs.")
    if not pdf_text_ready:
        messages.append("Install `pypdf` to enable text-based PDF extraction.")

    return {
        "ready": image_ocr_ready or text_pdf_ready,
        "image_ocr_ready": image_ocr_ready,
        "scanned_pdf_ready": scanned_pdf_ready,
        "text_pdf_ready": text_pdf_ready,
        "dependencies": {
            "pytesseract": pytesseract_ready,
            "pillow": pillow_ready,
            "pdf2image": pdf_renderer_ready,
            "pypdf": pdf_text_ready,
            "tesseract": tesseract_ready,
            "pdftoppm": poppler_ready,
        },
        "messages": messages,
    }


def _raise_missing_for_image() -> None:
    status = get_ocr_status()
    if status["image_ocr_ready"]:
        return
    raise OCRDependencyError(
        "Image OCR is not available on this machine. " + " ".join(status["messages"])
    )


def _raise_missing_for_scanned_pdf() -> None:
    status = get_ocr_status()
    if status["scanned_pdf_ready"]:
        return
    raise OCRDependencyError(
        "Scanned PDF OCR is not available on this machine. " + " ".join(status["messages"])
    )


def _raise_missing_for_text_pdf() -> None:
    status = get_ocr_status()
    if status["text_pdf_ready"]:
        return
    raise OCRDependencyError(
        "Text-based PDF extraction is not available on this machine. " + " ".join(status["messages"])
    )


def _preprocess_image(img: Image.Image) -> Image.Image:
    """Apply light preprocessing to improve OCR accuracy."""
    img = img.convert("L")
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(2.0)


def _extract_from_image(img: Image.Image) -> str:
    """Run Tesseract on a single PIL image."""
    _raise_missing_for_image()
    processed = _preprocess_image(img)
    return pytesseract.image_to_string(processed, config="--psm 6")


def _extract_text_from_pdf(path: Path) -> str:
    """Extract embedded text from a digital PDF."""
    _raise_missing_for_text_pdf()
    reader = PdfReader(str(path))
    chunks: list[str] = []
    for page in reader.pages:
        chunks.append(page.extract_text() or "")
    return "\n".join(chunks).strip()


def _extract_text_via_pdf_ocr(path: Path) -> str:
    """Render PDF pages and OCR them."""
    _raise_missing_for_scanned_pdf()
    pages = convert_from_path(str(path))
    parts: list[str] = []
    for page in pages:
        parts.append(_extract_from_image(page))
    return "\n".join(parts).strip()


def _normalise_line(line: str) -> str:
    cleaned = line.strip()
    cleaned = cleaned.replace("|", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.replace("B +", "B+").replace("A -", "A-").replace("C +", "C+").replace("C -", "C-")
    cleaned = cleaned.replace("D +", "D+")
    return cleaned


def _parse_course_rows(raw_text: str) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    seen: set[tuple[str, str, str, str]] = set()

    for source_line in raw_text.splitlines():
        line = _normalise_line(source_line)
        if not line:
            continue
        match = COURSE_PATTERN.search(line)
        if not match:
            continue

        row = (
            match.group(1).upper(),
            match.group(2),
            match.group(3).upper().replace(" ", ""),
            f"{match.group(4).capitalize()} {match.group(5)}",
        )
        if row not in seen:
            seen.add(row)
            rows.append(row)

    return rows


def _rows_to_csv(rows: list[tuple[str, str, str, str]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(CSV_HEADER.split(","))
    writer.writerows(rows)
    return output.getvalue().strip()


def extract_transcript_csv(file_path: str | Path) -> str:
    """Extract transcript rows from a PDF or image and return canonical CSV."""
    path = Path(file_path)
    if not path.exists():
        raise OCRError(f"File not found: {path}")

    ext = path.suffix.lower()
    raw_text = ""

    try:
        if ext in PDF_EXTENSIONS:
            try:
                raw_text = _extract_text_from_pdf(path)
            except OCRDependencyError:
                raw_text = ""

            rows = _parse_course_rows(raw_text)
            if rows:
                return _rows_to_csv(rows)

            raw_text = _extract_text_via_pdf_ocr(path)
        elif ext in IMAGE_EXTENSIONS:
            with Image.open(path) as img:
                raw_text = _extract_from_image(img)
        else:
            raise OCRError(f"Unsupported file type: {ext}. Use PDF, PNG, JPG, or JPEG.")
    except OCRDependencyError:
        raise
    except OCRError:
        raise
    except Exception as exc:
        raise OCRError(f"Failed to process document: {exc}") from exc

    rows = _parse_course_rows(raw_text)
    if not rows:
        raise OCRError(
            "No valid course records found in the document. Ensure the transcript is clear and readable."
        )

    return _rows_to_csv(rows)
