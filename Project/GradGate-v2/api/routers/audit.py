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
from api.models import AuditResponse
from api.services.ocr import OCRError, extract_transcript_csv
from api.services.supabase_client import get_supabase
from engine.audit import run_audit
from engine.cgpa import compute_grade_distribution, compute_semester_progression
from engine.credits import tally_credits
from engine.program_loader import (
    PROGRAM_ALIASES,
    load_equivalences,
    load_nsu_course_list,
    load_program,
)
from engine.transcript import load_transcript, resolve_retakes, validate_courses, validate_grades
from engine.waivers import get_waivers

router = APIRouter(prefix="/audit", tags=["audit"])

KNOWLEDGE_PATH = str(Path(__file__).resolve().parents[2] / "data" / "program_knowledge.md")


def _run_engine(csv_path: str, program: str, waivers_list: list[str]) -> dict[str, Any]:
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

    waived: set[str] = set(waivers_list) if waivers_list else set()
    if not waived:
        # Use non-interactive mode — no waivers if not specified
        waived = get_waivers(program_info, cli_waivers="", interactive=False)

    # Run all three levels
    credit_summary = tally_credits(records, program_info, waived_courses=waived, equivalences=equivalences)
    snapshots = compute_semester_progression(records, waived=waived)
    grade_dist = compute_grade_distribution(records)
    audit_result = run_audit(records, program_info, waived, equivalences)

    # Serialise everything into a plain dict (JSON-safe)
    return {
        "program": program_info.full_name,
        "program_alias": program_upper,
        "non_nsu_courses_flagged": non_nsu,
        "waivers_applied": sorted(waived),
        "credits": {
            "total_earned": credit_summary.total_earned,
            "total_attempted": credit_summary.total_attempted,
            "program_required": credit_summary.program_credits,
            "elective": credit_summary.elective_credits,
            "excluded": credit_summary.excluded_credits,
            "waived": credit_summary.waived_credits,
        },
        "cgpa": {
            "final": round(snapshots[-1].cumulative_cgpa, 3) if snapshots else 0.0,
            "semesters": [
                {
                    "semester": s.semester,
                    "tgpa": round(s.tgpa, 3),
                    "cumulative_cgpa": round(s.cumulative_cgpa, 3),
                    "probation_status": s.probation_status,
                }
                for s in snapshots
            ],
        },
        "grade_distribution": grade_dist,
        "audit": {
            "eligible": audit_result.eligible,
            "reasons": audit_result.reasons,
            "roadmap": audit_result.roadmap,
            "cgpa": round(audit_result.cgpa, 3),
            "major_cgpa": round(audit_result.major_cgpa, 3),
            "credits_completed": audit_result.credits_completed,
            "credits_required": audit_result.credits_required,
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
                "open_elective_credits_missing": audit_result.deficiencies.missing_open_elective,
            },
            "prerequisite_violations": [
                {
                    "course": v.course,
                    "missing_prereqs": v.missing_prereqs,
                    "semester": v.semester,
                }
                for v in audit_result.prereq_violations
            ],
            "minor": {
                "name": audit_result.minor_name,
                "completed": audit_result.minor_completed,
                "courses_taken": audit_result.minor_courses_taken,
                "courses_missing": audit_result.minor_courses_missing,
                "prereqs_met": audit_result.minor_prereqs_met,
                "prereqs_missing": audit_result.minor_prereqs_missing,
            } if audit_result.minor_name else None,
        },

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


@router.post("/csv", response_model=AuditResponse, summary="Run audit from CSV transcript")
async def audit_csv(
    user_id: CurrentUser,
    file: Annotated[UploadFile, File(description="Transcript CSV file")],
    program: Annotated[str, Form(description="Program alias e.g. CSE, BBA")],
    waivers: Annotated[str, Form(description="Comma-separated waiver codes, or empty")] = "",
) -> AuditResponse:
    """Upload a transcript CSV and run the full GradGate audit.

    Returns the complete audit result and stores it in scan history.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a .csv",
        )

    waivers_list = [w.strip().upper() for w in waivers.split(",") if w.strip()] if waivers else []

    # Write upload to a temp file so the engine can read it via path
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = _run_engine(tmp_path, program, waivers_list)
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

    waivers_list = [w.strip().upper() for w in waivers.split(",") if w.strip()] if waivers else []

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
            result = _run_engine(tmp_csv_path, program, waivers_list)
        finally:
            Path(tmp_csv_path).unlink(missing_ok=True)

    finally:
        Path(tmp_img_path).unlink(missing_ok=True)

    # Skip DB save in TEST_MODE (no real user in auth.users)
    if TEST_MODE:
        import uuid
        scan_id = str(uuid.uuid4())
    else:
        scan_id = _save_scan(
            user_id=user_id,
            program=program.upper(),
            input_type="image",
            file_name=file.filename,
            result=result,
        )

    return AuditResponse(scan_id=scan_id, program=program.upper(), input_type="image", result=result)
