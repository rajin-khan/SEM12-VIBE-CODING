"""
Smoke tests for the GradGate engine.
These verify that core modules import correctly and produce valid output
on well-known test fixtures.
"""

from pathlib import Path

import pytest

# Resolve paths relative to repo root
REPO = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO / "tests"
KNOWLEDGE = REPO / "data" / "curriculum" / "catalog.json"
TC01 = TESTS_DIR / "happy_cse_default.csv"
TC02 = TESTS_DIR / "happy_bba_finance.csv"


# ── Import smoke ────────────────────────────────────────────────────────────


def test_engine_imports():
    """All engine modules can be imported without error."""
    from engine.audit import run_audit
    from engine.cgpa import compute_grade_distribution, compute_semester_progression
    from engine.credits import tally_credits
    from engine.prerequisites import check_prerequisites
    from engine.program_loader import load_equivalences, load_nsu_course_list, load_program
    from engine.transcript import load_transcript, resolve_retakes, validate_grades
    from engine.waivers import get_waivers


def test_display_imports():
    """Display module can be imported without error."""
    from display.formatter import (
        print_audit_report,
        print_credit_tally,
        print_grade_distribution,
        print_semester_progression,
    )


# ── Transcript loading ──────────────────────────────────────────────────────


@pytest.mark.skipif(not TC01.exists(), reason="tc01 test fixture not found")
def test_load_transcript_cse():
    from engine.transcript import load_transcript, validate_grades

    records = load_transcript(str(TC01))
    assert len(records) > 0, "Expected records in happy_cse_default.csv"
    errors = validate_grades(records)
    assert errors == [], f"Unexpected grade errors: {errors}"


@pytest.mark.skipif(not TC02.exists(), reason="tc02 test fixture not found")
def test_load_transcript_bba():
    from engine.transcript import load_transcript, validate_grades

    records = load_transcript(str(TC02))
    assert len(records) > 0, "Expected records in happy_bba_finance.csv"
    errors = validate_grades(records)
    assert errors == [], f"Unexpected grade errors: {errors}"


# ── Program loader ──────────────────────────────────────────────────────────


@pytest.mark.skipif(not KNOWLEDGE.exists(), reason="catalog.json not found")
def test_program_loader_cse():
    from engine.program_loader import load_program

    info = load_program(str(KNOWLEDGE), "CSE")
    assert info is not None, "CSE program must be found"
    assert info.total_credits > 0
    assert info.min_cgpa == 2.0
    assert len(info.major_core) > 0


@pytest.mark.skipif(not KNOWLEDGE.exists(), reason="catalog.json not found")
def test_program_loader_bba():
    from engine.program_loader import load_program

    info = load_program(str(KNOWLEDGE), "BBA")
    assert info is not None, "BBA program must be found"
    assert info.total_credits > 0


@pytest.mark.skipif(not KNOWLEDGE.exists(), reason="catalog.json not found")
def test_nsu_course_list_nonempty():
    from engine.program_loader import load_nsu_course_list

    courses = load_nsu_course_list(str(KNOWLEDGE))
    assert len(courses) > 50, "NSU course list should have many entries"


# ── Retake resolution ───────────────────────────────────────────────────────


def test_retake_best_grade_wins():
    from engine.transcript import CourseRecord, resolve_retakes

    records = [
        CourseRecord("CSE115", 3, "F", "Spring 2022"),
        CourseRecord("CSE115", 3, "B+", "Fall 2022"),
    ]
    resolve_retakes(records)
    statuses = {r.grade: r.status for r in records}
    assert statuses["B+"] == "Counted"
    assert statuses["F"] == "Retake (Ignored)"


def test_retake_ineligible_above_bplus():
    from engine.transcript import CourseRecord, resolve_retakes

    records = [
        CourseRecord("CSE115", 3, "A", "Spring 2022"),
        CourseRecord("CSE115", 3, "B", "Fall 2022"),
    ]
    resolve_retakes(records)
    statuses = {r.grade: r.status for r in records}
    assert statuses["A"] == "Counted"
    assert statuses["B"] == "Retake (Ineligible)"


# ── Credit tally ────────────────────────────────────────────────────────────


@pytest.mark.skipif(not (TC01.exists() and KNOWLEDGE.exists()), reason="fixtures missing")
def test_credit_tally_cse_all_pass():
    from engine.credits import tally_credits
    from engine.program_loader import load_equivalences, load_program
    from engine.transcript import load_transcript, resolve_retakes, validate_grades

    records = load_transcript(str(TC01))
    assert not validate_grades(records)
    equivalences = load_equivalences(str(KNOWLEDGE))
    resolve_retakes(records, equivalences)
    program = load_program(str(KNOWLEDGE), "CSE")
    assert program is not None
    summary = tally_credits(records, program, waived_courses=set(), equivalences=equivalences)
    assert summary.total_earned > 0


# ── CGPA ────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(not TC01.exists(), reason="tc01 fixture missing")
def test_cgpa_positive():
    from engine.cgpa import compute_semester_progression
    from engine.transcript import load_transcript, resolve_retakes

    records = load_transcript(str(TC01))
    resolve_retakes(records)
    snapshots = compute_semester_progression(records, waived=set())
    assert len(snapshots) > 0
    final = snapshots[-1]
    assert final.cumulative_cgpa > 0.0
