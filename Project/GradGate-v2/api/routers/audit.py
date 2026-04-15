"""Audit router — runs transcript analysis through the GradGate engine.

POST /audit/csv   — accepts a CSV file upload, runs all levels, saves to DB
POST /audit/image — accepts an image/PDF, runs OCR + engine, saves to DB
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

# Ensure repo root and cli/ are on path so engine imports work when run from any cwd
_root = str(Path(__file__).resolve().parents[2])
sys.path.insert(0, _root)
sys.path.insert(0, str(Path(_root) / "cli"))

from api.auth import CurrentUser
from api.auth import TEST_MODE
from api.models import AuditOptionsResponse, AuditResponse, OCRHealthResponse, SavedAuditRequest
from api.services.ocr import OCRDependencyError, OCRError, extract_transcript_csv, get_ocr_status
from api.services.supabase_client import get_supabase
from engine.audit import run_audit
from engine.cgpa import compute_grade_distribution, compute_semester_progression
from engine.credits import tally_credits
from engine.program_loader import (
    PROGRAM_ALIASES,
    load_equivalences,
    load_all_programs,
    load_nsu_course_list,
    load_program,
)
from engine.transcript import load_transcript, resolve_retakes, validate_courses, validate_grades
from engine.waivers import get_waivers

router = APIRouter(prefix="/audit", tags=["audit"])

KNOWLEDGE_PATH = str(Path(__file__).resolve().parents[2] / "data" / "curriculum" / "catalog.json")
LEVEL_LABELS = {
    "1": "Level 1 — Credit Tally",
    "2": "Level 2 — CGPA & Probation",
    "3": "Level 3 — Full Audit",
    "all": "All Levels",
    "dist": "Grade Distribution",
}
VALID_LEVELS = set(LEVEL_LABELS)
VALID_REPORT_MODES = {"normal", "full"}
VALID_MINORS = {"MATH", "PHYSICS"}


def _normalise_level(level: str | None) -> str:
    level_value = (level or "all").strip().lower()
    if level_value not in VALID_LEVELS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid level '{level}'. Valid: {', '.join(sorted(VALID_LEVELS))}",
        )
    return level_value


def _normalise_report_mode(report: str | None) -> str:
    report_value = (report or "normal").strip().lower()
    if report_value not in VALID_REPORT_MODES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid report mode '{report}'. Valid: {', '.join(sorted(VALID_REPORT_MODES))}",
        )
    return report_value


def _normalise_minor(minor: str | None) -> str | None:
    if not minor:
        return None
    minor_value = minor.strip().upper()
    if minor_value not in VALID_MINORS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid minor '{minor}'. Valid: {', '.join(sorted(VALID_MINORS))}",
        )
    return minor_value


def _parse_waivers(waivers: str | None) -> list[str]:
    if not waivers:
        return []
    return [w.strip().upper() for w in waivers.split(",") if w.strip()]


def _serialise_course(record, category: str | None = None) -> dict[str, Any]:
    payload = {
        "course_code": record.course_code,
        "credits": record.credits,
        "grade": record.grade,
        "semester": record.semester,
        "status": record.status,
        "grade_points": record.grade_points,
        "is_passing": record.is_passing,
        "is_gpa_bearing": record.is_gpa_bearing,
    }
    if category is not None:
        payload["bucket"] = category
    return payload


def _serialise_credit_summary(summary) -> dict[str, Any]:
    return {
        "total_earned": summary.total_earned,
        "total_attempted": summary.total_attempted,
        "program_required": summary.program_credits,
        "elective": summary.elective_credits,
        "excluded": summary.excluded_credits,
        "waived": summary.waived_credits,
        "course_statuses": [
            _serialise_course(record, category)
            for record, category in summary.course_statuses
        ],
    }


def _serialise_snapshots(snapshots) -> list[dict[str, Any]]:
    return [
        {
            "semester": snapshot.semester,
            "sem_credits": round(snapshot.sem_credits, 3),
            "sem_points": round(snapshot.sem_points, 3),
            "tgpa": round(snapshot.tgpa, 3),
            "cumulative_cgpa": round(snapshot.cumulative_cgpa, 3),
            "probation_status": snapshot.probation_status,
            "consecutive_prob_count": snapshot.consecutive_prob_count,
            "courses": [_serialise_course(record) for record in snapshot.courses],
        }
        for snapshot in snapshots
    ]


def _serialise_audit_result(audit_result, program_info, concentration_alias: str | None) -> dict[str, Any]:
    return {
        "eligible": audit_result.eligible,
        "reasons": audit_result.reasons,
        "roadmap": audit_result.roadmap,
        "cgpa": round(audit_result.cgpa, 3),
        "major_cgpa": round(audit_result.major_cgpa, 3),
        "credits_completed": audit_result.credits_completed,
        "credits_required": audit_result.credits_required,
        "credits_earned": audit_result.credits_earned,
        "waiver_bonus": audit_result.waiver_bonus,
        "gpa_credits": round(audit_result.gpa_credits, 3),
        "grade_points": round(audit_result.grade_points, 3),
        "failed_courses": audit_result.failed_courses,
        "missing_courses": {
            "ged": audit_result.deficiencies.missing_ged,
            "math": audit_result.deficiencies.missing_math,
            "science": audit_result.deficiencies.missing_science,
            "business": audit_result.deficiencies.missing_business,
            "major": audit_result.deficiencies.missing_major,
            "capstone": audit_result.deficiencies.missing_capstone,
            "internship": audit_result.deficiencies.missing_internship,
            "trail_credits_missing": audit_result.deficiencies.missing_trail,
            "concentration_credits_missing": audit_result.deficiencies.missing_concentration,
            "open_elective_credits_missing": audit_result.deficiencies.missing_open_elective,
        },
        "prerequisite_violations": [
            {
                "course": violation.course,
                "missing_prereqs": violation.missing_prereqs,
                "semester": violation.semester,
                "violation_type": violation.violation_type,
            }
            for violation in audit_result.prereq_violations
        ],
        "concentration": {
            "name": audit_result.concentration_name,
            "alias": concentration_alias,
            "cgpa": round(audit_result.concentration_cgpa, 3),
            "minimum_cgpa": program_info.concentration_min_cgpa,
        }
        if audit_result.concentration_name
        else None,
        "minor": {
            "name": audit_result.minor_name,
            "completed": audit_result.minor_completed,
            "courses_taken": audit_result.minor_courses_taken,
            "courses_missing": audit_result.minor_courses_missing,
            "prereqs_met": audit_result.minor_prereqs_met,
            "prereqs_missing": audit_result.minor_prereqs_missing,
        }
        if audit_result.minor_name
        else None,
        "bucket_gpas": audit_result.bucket_gpas,
    }


def _run_engine(
    csv_path: str,
    program: str,
    waivers_list: list[str],
    level: str = "all",
    report: str = "normal",
    concentration: str | None = None,
    minor: str | None = None,
) -> dict[str, Any]:
    """Run the full GradGate engine pipeline and return a JSON-serialisable result dict."""
    program_upper = program.strip().upper()
    if program_upper not in PROGRAM_ALIASES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown program '{program}'. Valid: {', '.join(PROGRAM_ALIASES)}",
        )

    records = load_transcript(csv_path)

    grade_errors = validate_grades(records)
    if grade_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"grade_errors": grade_errors},
        )

    equivalences = load_equivalences(KNOWLEDGE_PATH)
    nsu_courses = load_nsu_course_list(KNOWLEDGE_PATH)

    # Mark unrecognised courses as Transfer so they don't block the audit
    non_nsu = validate_courses(records, nsu_courses)
    for code in non_nsu:
        for r in records:
            if r.course_code == code:
                r.grade = "T"
                r.status = "Transfer"

    program_info = load_program(KNOWLEDGE_PATH, program_upper)
    if not program_info:
        raise HTTPException(status_code=500, detail="Program data could not be loaded")

    resolve_retakes(records, equivalences)

    waived = get_waivers(
        program_info,
        cli_waivers=",".join(waivers_list),
        interactive=False,
    )

    # Run all three levels
    credit_summary = tally_credits(records, program_info, waived_courses=waived, equivalences=equivalences)
    snapshots = compute_semester_progression(records, waived=waived)
    grade_dist = compute_grade_distribution(records)
    audit_result = run_audit(
        records,
        program_info,
        waived,
        equivalences,
        concentration=concentration,
        minor=minor,
    )

    # Serialise everything into a plain dict (JSON-safe)
    return {
        "program": program_info.full_name,
        "program_alias": program_upper,
        "metadata": {
            "requested_level": level,
            "requested_level_label": LEVEL_LABELS[level],
            "report_mode": report,
            "selected_concentration": concentration,
            "selected_minor": minor,
            "program_alias": program_upper,
        },
        "non_nsu_courses_flagged": non_nsu,
        "waivers_applied": sorted(waived),
        "credits": _serialise_credit_summary(credit_summary),
        "cgpa": {
            "final": round(snapshots[-1].cumulative_cgpa, 3) if snapshots else 0.0,
            "semesters": _serialise_snapshots(snapshots),
        },
        "grade_distribution": grade_dist,
        "audit": _serialise_audit_result(audit_result, program_info, concentration),
    }


def _save_scan(user_id: str, program: str, input_type: str, file_name: str, result: dict[str, Any]) -> str:
    """Insert a scan_sessions row and return the new UUID."""
    sb = get_supabase()
    response = (
        sb.table("scan_sessions")
        .insert(
            {
                "user_id": user_id,
                "program": program,
                "input_type": input_type,
                "file_name": file_name,
                "result_json": json.dumps(result),
            }
        )
        .execute()
    )
    return response.data[0]["id"]


@router.get("/options", response_model=AuditOptionsResponse, summary="Get web audit form options")
def get_audit_options() -> AuditOptionsResponse:
    programs = load_all_programs(KNOWLEDGE_PATH)
    bba = programs.get("BBA")

    return AuditOptionsResponse(
        programs=[
            {
                "value": alias,
                "label": f"{info.full_name} ({info.degree})",
                "waivable_courses": info.waivable,
                "supports_minor": alias in {"CSE", "EEE", "ETE", "CEE"},
            }
            for alias, info in programs.items()
        ],
        levels=[
            {"value": value, "label": label}
            for value, label in LEVEL_LABELS.items()
        ],
        report_modes=["normal", "full"],
        supported_minors=sorted(VALID_MINORS),
        bba_concentrations=[
            {"value": concentration.alias, "label": concentration.name}
            for concentration in (bba.concentrations if bba else [])
        ],
    )


@router.get("/ocr-status", response_model=OCRHealthResponse, summary="Get OCR/PDF readiness")
def get_ocr_status_route() -> OCRHealthResponse:
    return OCRHealthResponse(**get_ocr_status())


@router.post("/csv", response_model=AuditResponse, summary="Run audit from CSV transcript")
async def audit_csv(
    user_id: CurrentUser,
    file: Annotated[UploadFile, File(description="Transcript CSV file")],
    program: Annotated[str, Form(description="Program alias e.g. CSE, BBA")],
    waivers: Annotated[str, Form(description="Comma-separated waiver codes, or empty")] = "",
    level: Annotated[str, Form(description="Audit level: 1, 2, 3, all, or dist")] = "all",
    report: Annotated[str, Form(description="Report verbosity: normal or full")] = "normal",
    concentration: Annotated[str | None, Form(description="Optional BBA concentration alias")] = None,
    minor: Annotated[str | None, Form(description="Optional minor selection")] = None,
) -> AuditResponse:
    """Upload a transcript CSV and run the full GradGate audit.

    Returns the complete audit result and stores it in scan history.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a .csv",
        )

    waivers_list = _parse_waivers(waivers)
    level_value = _normalise_level(level)
    report_value = _normalise_report_mode(report)
    concentration_value = concentration.strip().upper() if concentration else None
    minor_value = _normalise_minor(minor)

    # Write upload to a temp file so the engine can read it via path
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = _run_engine(
            tmp_path,
            program,
            waivers_list,
            level=level_value,
            report=report_value,
            concentration=concentration_value,
            minor=minor_value,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    # Skip DB save in TEST_MODE (no real user in auth.users)
    if TEST_MODE:
        import uuid
        scan_id = str(uuid.uuid4())
    else:
        scan_id = _save_scan(
            user_id=user_id,
            program=program.upper(),
            input_type="csv",
            file_name=file.filename,
            result=result,
        )

    return AuditResponse(scan_id=scan_id, program=program.upper(), input_type="csv", result=result)


@router.post("/image", response_model=AuditResponse, summary="Run audit from scanned transcript image")
async def audit_image(
    user_id: CurrentUser,
    file: Annotated[UploadFile, File(description="Transcript image or PDF file")],
    program: Annotated[str, Form(description="Program alias e.g. CSE, BBA")],
    waivers: Annotated[str, Form(description="Comma-separated waiver codes, or empty")] = "",
    level: Annotated[str, Form(description="Audit level: 1, 2, 3, all, or dist")] = "all",
    report: Annotated[str, Form(description="Report verbosity: normal or full")] = "normal",
    concentration: Annotated[str | None, Form(description="Optional BBA concentration alias")] = None,
    minor: Annotated[str | None, Form(description="Optional minor selection")] = None,
) -> AuditResponse:
    """Upload a transcript image or PDF, run OCR to extract courses, and run the audit.

    Returns the complete audit result and stores it in scan history.
    """
    valid_extensions = (".png", ".jpg", ".jpeg", ".pdf")
    if not file.filename or not any(file.filename.lower().endswith(ext) for ext in valid_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File must be one of: {', '.join(valid_extensions)}",
        )

    waivers_list = _parse_waivers(waivers)
    level_value = _normalise_level(level)
    report_value = _normalise_report_mode(report)
    concentration_value = concentration.strip().upper() if concentration else None
    minor_value = _normalise_minor(minor)

    # Write upload to a temp file for OCR processing
    ext = Path(file.filename).suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_img_path = tmp.name

    try:
        # 1. OCR -> CSV string
        try:
            csv_str = extract_transcript_csv(tmp_img_path)
        except OCRDependencyError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "message": str(e),
                    "ocr_status": get_ocr_status(),
                },
            ) from e
        except OCRError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            ) from e

        # 2. Write CSV string to another temp file for the engine
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tmp_csv:
            tmp_csv.write(csv_str)
            tmp_csv_path = tmp_csv.name

        try:
            # 3. Run audit engine
            result = _run_engine(
                tmp_csv_path,
                program,
                waivers_list,
                level=level_value,
                report=report_value,
                concentration=concentration_value,
                minor=minor_value,
            )
        finally:
            Path(tmp_csv_path).unlink(missing_ok=True)

    finally:
        Path(tmp_img_path).unlink(missing_ok=True)

    input_type = "pdf" if ext == ".pdf" else "image"

    # Skip DB save in TEST_MODE (no real user in auth.users)
    if TEST_MODE:
        import uuid
        scan_id = str(uuid.uuid4())
    else:
        scan_id = _save_scan(
            user_id=user_id,
            program=program.upper(),
            input_type=input_type,
            file_name=file.filename,
            result=result,
        )

    return AuditResponse(scan_id=scan_id, program=program.upper(), input_type=input_type, result=result)


@router.post("/log", response_model=AuditResponse, summary="Save a locally computed audit result")
async def log_audit(
    user_id: CurrentUser,
    payload: SavedAuditRequest,
) -> AuditResponse:
    """Persist a CLI-computed audit result into scan history."""
    if TEST_MODE:
        import uuid

        scan_id = str(uuid.uuid4())
    else:
        scan_id = _save_scan(
            user_id=user_id,
            program=payload.program.upper(),
            input_type=payload.input_type,
            file_name=payload.file_name or "cli-local-run",
            result=payload.result,
        )

    return AuditResponse(
        scan_id=scan_id,
        program=payload.program.upper(),
        input_type=payload.input_type,
        result=payload.result,
    )
