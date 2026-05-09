"""Canonical document ingestion for scanned transcripts."""

from __future__ import annotations

import csv
import io
import re
import shutil
from dataclasses import dataclass
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


class _MissingImageFilterModule:
    MedianFilter = object


try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
except ImportError:
    pytesseract = None
    convert_from_path = None
    Image = _MissingImageModule()
    ImageEnhance = _MissingImageEnhanceModule()
    ImageFilter = _MissingImageFilterModule()
    ImageOps = None

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import pillow_heif
except ImportError:
    pillow_heif = None

if pillow_heif is not None:
    pillow_heif.register_heif_opener()


CSV_HEADER = "Course_Code,Credits,Grade,Semester"
MIN_TRANSCRIPT_ROWS = 3
STRONG_MATCH_ROW_TARGET = 10
STRONG_MATCH_CONFIDENCE_TARGET = 8.2
BASE_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".bmp",
    ".webp",
    ".gif",
}
HEIF_EXTENSIONS = {".heic", ".heif"}
PDF_EXTENSIONS = {".pdf"}
ALL_SUPPORTED_EXTENSIONS = BASE_IMAGE_EXTENSIONS | HEIF_EXTENSIONS | PDF_EXTENSIONS
VALID_GRADES = {"A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F", "W", "I", "T", "P"}
SEMESTER_PATTERN = re.compile(r"\b(Spring|Summer|Fall|Autumn)\b", re.IGNORECASE)
YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")
COURSE_CODE_PATTERN = re.compile(r"\b([A-Z]{2,4})\s*-?\s*(\d{3})([A-Z]?)\b", re.IGNORECASE)
FULL_ROW_PATTERN = re.compile(
    r"(?P<course>[A-Z]{2,4}\s*-?\s*\d{3}\s*[A-Z]?)"
    r"(?:\s+|[|:])"
    r"(?P<credits>\d(?:\.\d)?)"
    r"(?:\s+|[|:])"
    r"(?P<grade>A\+?|A-|B\+|B-|B|C\+|C-|C|D\+|D|F|W|I|T|P|8\+|8-|8)"
    r"(?:\s+|[|:])+"
    r"(?P<semester>Spring|Summer|Fall|Autumn)"
    r"(?:\s+|[|:])+(?P<year>(?:19|20)\d{2})",
    re.IGNORECASE,
)


class OCRError(Exception):
    """Raised when transcript extraction or OCR parsing fails."""


class OCRDependencyError(OCRError):
    """Raised when local OCR dependencies are missing."""


@dataclass
class ParsedRow:
    course_code: str
    credits: str
    grade: str
    semester: str
    confidence: float
    raw_line: str


@dataclass
class ExtractionResult:
    input_type: str
    extraction_mode: str
    warnings: list[str]
    pages_processed: int
    rows: list[ParsedRow]
    extracted_csv: str
    review_required: bool

    @property
    def rows_detected(self) -> int:
        return len(self.rows)

    def preview_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "course_code": row.course_code,
                "credits": row.credits,
                "grade": row.grade,
                "semester": row.semester,
                "confidence": round(row.confidence, 3),
                "raw_line": row.raw_line,
            }
            for row in self.rows[:20]
        ]

    def review_payload(self) -> dict[str, Any]:
        return {
            "input_type": self.input_type,
            "extraction_mode": self.extraction_mode,
            "review_required": self.review_required,
            "warnings": self.warnings,
            "pages_processed": self.pages_processed,
            "rows_detected": self.rows_detected,
            "extracted_preview_rows": self.preview_rows(),
            "extracted_csv": self.extracted_csv,
        }

    def metadata(self) -> dict[str, Any]:
        return {
            "input_type": self.input_type,
            "extraction_mode": self.extraction_mode,
            "warnings": self.warnings,
            "pages_processed": self.pages_processed,
            "rows_detected": self.rows_detected,
            "review_required": self.review_required,
        }


def _which(binary: str) -> str | None:
    return shutil.which(binary)


def get_supported_extensions() -> list[str]:
    extensions = set(BASE_IMAGE_EXTENSIONS | PDF_EXTENSIONS)
    if pillow_heif is not None:
        extensions |= HEIF_EXTENSIONS
    return sorted(extensions)


def get_ocr_status() -> dict[str, Any]:
    pytesseract_ready = pytesseract is not None
    pillow_ready = hasattr(Image, "open")
    pdf_renderer_ready = convert_from_path is not None
    pdf_text_ready = PdfReader is not None
    tesseract_ready = _which("tesseract") is not None
    poppler_ready = _which("pdftoppm") is not None
    heif_ready = pillow_heif is not None

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
    if not heif_ready:
        messages.append("Install `pillow-heif` to enable HEIC/HEIF transcript uploads.")

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
            "pillow_heif": heif_ready,
        },
        "supported_extensions": get_supported_extensions(),
        "extraction_modes": ["pdf_text", "pdf_ocr", "image_ocr"],
        "messages": messages,
    }


def _raise_missing_for_image(ext: str) -> None:
    status = get_ocr_status()
    if ext in HEIF_EXTENSIONS and not status["dependencies"]["pillow_heif"]:
        raise OCRDependencyError(
            "HEIC/HEIF image support is not available on this machine. "
            + " ".join(status["messages"])
        )
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


def _normalise_course_code(token: str) -> str:
    match = COURSE_CODE_PATTERN.search(token.upper().replace(" ", ""))
    if not match:
        raise OCRError(f"Could not normalise course code from '{token}'")
    return f"{match.group(1)}{match.group(2)}{match.group(3)}".upper()


def _normalise_grade(token: str) -> str | None:
    cleaned = token.upper().replace(" ", "")
    cleaned = cleaned.replace("8+", "B+").replace("8-", "B-").replace("8", "B")
    cleaned = cleaned.replace("A+", "A")
    return cleaned if cleaned in VALID_GRADES else None


def _normalise_semester(semester: str, year: str) -> str:
    season = semester.capitalize()
    if season == "Autumn":
        season = "Fall"
    return f"{season} {year}"


def _normalise_line(line: str) -> str:
    cleaned = line.strip()
    cleaned = cleaned.replace("|", " ")
    cleaned = cleaned.replace("•", " ")
    cleaned = cleaned.replace("\t", " ")
    cleaned = cleaned.replace("B +", "B+").replace("A -", "A-").replace("C +", "C+").replace("C -", "C-")
    cleaned = cleaned.replace("D +", "D+").replace("B -", "B-")
    cleaned = cleaned.replace("Sprlng", "Spring").replace("Fa11", "Fall").replace("Fali", "Fall")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def _extract_semester_header(line: str) -> str | None:
    semester = SEMESTER_PATTERN.search(line)
    year = YEAR_PATTERN.search(line)
    if semester and year:
        return _normalise_semester(semester.group(1), year.group(0))
    return None


def _extract_semester_headers(line: str) -> list[str]:
    semesters = list(SEMESTER_PATTERN.finditer(line))
    years = list(YEAR_PATTERN.finditer(line))
    pairs: list[str] = []
    for index, semester in enumerate(semesters):
        if index < len(years):
            pairs.append(_normalise_semester(semester.group(1), years[index].group(0)))
    return pairs


def _extract_credit_token(remainder: str) -> str | None:
    match = re.search(r"\b(\d(?:\.\d)?)\b", remainder)
    if not match:
        return None
    credits = match.group(1)
    if float(credits) > 6:
        return None
    return credits


def _parse_line(line: str, current_semester: str | None) -> ParsedRow | None:
    exact = FULL_ROW_PATTERN.search(line)
    if exact:
        return ParsedRow(
            course_code=_normalise_course_code(exact.group("course")),
            credits=exact.group("credits"),
            grade=_normalise_grade(exact.group("grade")) or exact.group("grade").upper(),
            semester=_normalise_semester(exact.group("semester"), exact.group("year")),
            confidence=0.99,
            raw_line=line,
        )

    course_match = COURSE_CODE_PATTERN.search(line)
    if not course_match:
        return None

    course_code = _normalise_course_code(course_match.group(0))
    remainder = line[course_match.end():]
    credits = _extract_credit_token(remainder)
    grade_match = re.search(r"\b(A\+?|A-|B\+|B-|B|C\+|C-|C|D\+|D|F|W|I|T|P|8\+|8-|8)\b", remainder, re.IGNORECASE)
    grade = _normalise_grade(grade_match.group(1)) if grade_match else None

    line_semester = _extract_semester_header(line)
    semester = line_semester or current_semester
    if not credits or not grade or not semester:
        return None

    confidence = 0.72
    if line_semester:
        confidence += 0.14
    if "." in credits:
        confidence += 0.04
    if current_semester and not line_semester:
        confidence -= 0.05

    return ParsedRow(
        course_code=course_code,
        credits=credits,
        grade=grade,
        semester=semester,
        confidence=min(confidence, 0.92),
        raw_line=line,
    )


def _split_course_segments(line: str) -> list[str]:
    matches = list(COURSE_CODE_PATTERN.finditer(line))
    if not matches:
        return []
    if len(matches) == 1:
        return [line]

    segments: list[str] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(line)
        segment = line[start:end].strip()
        if segment:
            segments.append(segment)
    return segments


def _rows_to_csv(rows: list[ParsedRow]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(CSV_HEADER.split(","))
    for row in rows:
        writer.writerow([row.course_code, row.credits, row.grade, row.semester])
    return output.getvalue().strip()


def _score_rows(rows: list[ParsedRow], candidate_lines: int, extraction_mode: str) -> tuple[bool, list[str]]:
    warnings: list[str] = []
    if not rows:
        return False, ["No valid transcript rows were extracted."]

    average_confidence = sum(row.confidence for row in rows) / len(rows)
    match_ratio = len(rows) / max(candidate_lines, len(rows))

    if candidate_lines and match_ratio < 0.75:
        warnings.append("Some transcript-like rows could not be parsed cleanly.")
    if average_confidence < 0.9:
        warnings.append("OCR confidence is lower than ideal; please review extracted rows.")
    if extraction_mode != "pdf_text" and len(rows) < 8:
        warnings.append("Only a small number of rows were extracted from this scanned document.")

    review_required = bool(warnings)
    return review_required, warnings


def _parse_rows(raw_text: str, extraction_mode: str) -> tuple[list[ParsedRow], list[str]]:
    rows: list[ParsedRow] = []
    seen: set[tuple[str, str, str, str]] = set()
    current_semester: str | None = None
    column_semesters: list[str | None] = [None, None]
    candidate_lines = 0

    for source_line in raw_text.splitlines():
        line = _normalise_line(source_line)
        if not line:
            continue
        headers = _extract_semester_headers(line)
        if len(headers) >= 2:
            column_semesters = [headers[0], headers[1]]
        elif len(headers) == 1:
            current_semester = headers[0]

        segments = _split_course_segments(line)
        if not segments:
            continue

        candidate_lines += len(segments)
        for index, segment in enumerate(segments):
            semester_hint = current_semester
            if len(segments) >= 2 and index < len(column_semesters) and column_semesters[index]:
                semester_hint = column_semesters[index]

            parsed = _parse_line(segment, semester_hint)
            if not parsed:
                continue

            if parsed.semester:
                current_semester = parsed.semester

            key = (parsed.course_code, parsed.credits, parsed.grade, parsed.semester)
            if key in seen:
                continue
            seen.add(key)
            rows.append(parsed)

    review_required, warnings = _score_rows(rows, candidate_lines, extraction_mode)
    return rows, warnings if review_required else []


def _prepare_image_variants(img: Image.Image) -> list[Image.Image]:
    base = ImageOps.exif_transpose(img) if ImageOps else img
    if max(base.size) < 1600:
        scale = 1600 / max(base.size)
        base = base.resize((int(base.width * scale), int(base.height * scale)))

    grayscale = base.convert("L")
    threshold = grayscale.point(lambda pixel: 255 if pixel > 180 else 0)
    enhanced = ImageEnhance.Contrast(grayscale).enhance(2.4)
    sharpened = enhanced.filter(ImageFilter.MedianFilter(size=3))
    return [grayscale, threshold, sharpened, enhanced]


def _prepare_quick_image(img: Image.Image) -> Image.Image:
    base = ImageOps.exif_transpose(img) if ImageOps else img
    target_max = 1800
    scale = target_max / max(base.size)
    if abs(scale - 1.0) > 0.08:
        base = base.resize((max(1, int(base.width * scale)), max(1, int(base.height * scale))))
    return base.convert("L")


def _image_layouts(img: Image.Image) -> list[list[Image.Image]]:
    layouts: list[list[Image.Image]] = []
    if img.width > img.height * 1.08:
        gutter = max(10, img.width // 80)
        middle = img.width // 2
        left = img.crop((0, 0, middle + gutter, img.height))
        right = img.crop((middle - gutter, 0, img.width, img.height))
        layouts.append([left, right])
    layouts.append([img])
    return layouts


def _best_ocr_text(img: Image.Image) -> str:
    best_text = ""
    best_metric = (-1, -1.0)
    base = ImageOps.exif_transpose(img) if ImageOps else img
    orientations = [base, base.rotate(270, expand=True), base.rotate(90, expand=True), base.rotate(180, expand=True)]

    for oriented in orientations:
        for layout in _image_layouts(oriented):
            for psm in ("6", "4", "11"):
                parts: list[str] = []
                for piece in layout:
                    prepared_variants = _prepare_image_variants(piece)
                    piece_best_text = ""
                    piece_best_metric = (-1, -1.0)
                    for variant in prepared_variants:
                        text = pytesseract.image_to_string(variant, config=f"--oem 3 --psm {psm}")
                        rows, _warnings = _parse_rows(text, "image_ocr")
                        confidence_sum = sum(row.confidence for row in rows)
                        metric = (len(rows), confidence_sum)
                        if metric > piece_best_metric:
                            piece_best_metric = metric
                            piece_best_text = text
                        if metric[0] >= STRONG_MATCH_ROW_TARGET and metric[1] >= STRONG_MATCH_CONFIDENCE_TARGET:
                            break
                    if piece_best_text:
                        parts.append(piece_best_text)

                text = "\n".join(part for part in parts if part).strip()
                rows, _warnings = _parse_rows(text, "image_ocr")
                confidence_sum = sum(row.confidence for row in rows)
                metric = (len(rows), confidence_sum)
                if metric > best_metric:
                    best_metric = metric
                    best_text = text
                if metric[0] >= STRONG_MATCH_ROW_TARGET and metric[1] >= STRONG_MATCH_CONFIDENCE_TARGET:
                    return best_text
    return best_text


def _quick_page_ocr_text(img: Image.Image) -> str:
    best_text = ""
    best_rows = -1
    base = _prepare_quick_image(img)
    orientations = [base.rotate(270, expand=True), base] if base.width > base.height else [base]
    for oriented in orientations:
        text = pytesseract.image_to_string(oriented, config="--oem 3 --psm 6")
        rows, _warnings = _parse_rows(text, "image_ocr")
        if len(rows) > best_rows:
            best_rows = len(rows)
            best_text = text
        if len(rows) >= MIN_TRANSCRIPT_ROWS:
            return text
    return best_text


def _looks_like_transcript_page(text: str) -> bool:
    upper = text.upper()
    course_hits = len(COURSE_CODE_PATTERN.findall(upper))
    semester_hits = len(SEMESTER_PATTERN.findall(upper))
    return course_hits >= 2 or (course_hits >= 1 and semester_hits >= 1)


def _extract_from_image(path: Path) -> tuple[str, int]:
    _raise_missing_for_image(path.suffix.lower())
    with Image.open(path) as img:
        text = _best_ocr_text(img)
    return text, 1


def _extract_text_from_pdf(path: Path) -> tuple[str, int]:
    _raise_missing_for_text_pdf()
    reader = PdfReader(str(path))
    chunks: list[str] = []
    for page in reader.pages:
        chunks.append(page.extract_text() or "")
    return "\n".join(chunks).strip(), len(reader.pages)


def _extract_text_via_pdf_ocr(path: Path) -> tuple[str, int]:
    _raise_missing_for_scanned_pdf()
    pages = convert_from_path(str(path))
    parts: list[str] = []
    for page in pages:
        quick_text = _quick_page_ocr_text(page)
        quick_rows, _quick_warnings = _parse_rows(quick_text, "image_ocr")
        if len(quick_rows) >= MIN_TRANSCRIPT_ROWS:
            parts.append(quick_text)
            continue
        if _looks_like_transcript_page(quick_text):
            parts.append(_best_ocr_text(page))
    return "\n".join(parts).strip(), len(pages)


def extract_transcript_document(file_path: str | Path) -> ExtractionResult:
    path = Path(file_path)
    if not path.exists():
        raise OCRError(f"File not found: {path}")

    ext = path.suffix.lower()
    if ext not in ALL_SUPPORTED_EXTENSIONS:
        raise OCRError(
            f"Unsupported file type: {ext}. Supported types: {', '.join(get_supported_extensions())}."
        )

    input_type = "pdf" if ext in PDF_EXTENSIONS else "image"
    raw_text = ""
    pages_processed = 1
    extraction_mode = "image_ocr"
    warnings: list[str] = []

    try:
        if ext in PDF_EXTENSIONS:
            extraction_mode = "pdf_text"
            try:
                raw_text, pages_processed = _extract_text_from_pdf(path)
            except OCRDependencyError:
                raw_text = ""

            rows, parse_warnings = _parse_rows(raw_text, extraction_mode)
            if rows and not parse_warnings:
                return ExtractionResult(
                    input_type=input_type,
                    extraction_mode=extraction_mode,
                    warnings=[],
                    pages_processed=pages_processed,
                    rows=rows,
                    extracted_csv=_rows_to_csv(rows),
                    review_required=False,
                )

            extraction_mode = "pdf_ocr"
            raw_text, pages_processed = _extract_text_via_pdf_ocr(path)
        else:
            raw_text, pages_processed = _extract_from_image(path)
    except OCRDependencyError:
        raise
    except OCRError:
        raise
    except Exception as exc:
        raise OCRError(f"Failed to process document: {exc}") from exc

    rows, warnings = _parse_rows(raw_text, extraction_mode)
    if not rows or len(rows) < MIN_TRANSCRIPT_ROWS:
        raise OCRError(
            "No valid transcript course records were found in the document. Please upload an official NSU transcript image or PDF."
        )

    return ExtractionResult(
        input_type=input_type,
        extraction_mode=extraction_mode,
        warnings=warnings,
        pages_processed=pages_processed,
        rows=rows,
        extracted_csv=_rows_to_csv(rows),
        review_required=bool(warnings),
    )
