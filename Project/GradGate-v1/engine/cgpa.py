"""Level 2: CGPA computation, semester progression, and probation detection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from engine.transcript import (
    CourseRecord, GRADE_POINTS, GRADE_ORDER, NON_GPA_GRADES,
    get_records_by_semester, get_semesters_ordered,
)


GPA_EXCLUDED = {"W", "T", "P"}


@dataclass
class SemesterSnapshot:
    semester: str
    courses: List[CourseRecord]
    sem_credits: float
    sem_points: float
    tgpa: float
    cumulative_cgpa: float
    probation_status: str  # NORMAL, P1, P2, DISMISSAL
    consecutive_prob_count: int


def compute_cgpa(records: List[CourseRecord],
                 waived: Optional[Set[str]] = None) -> float:
    """Compute cumulative CGPA using best attempt per course."""
    waived = waived or set()
    best: Dict[str, Tuple[float, float]] = {}

    for r in records:
        if r.course_code in waived:
            continue
        if r.grade.upper() in GPA_EXCLUDED:
            continue
        if r.status in ("Retake (Ignored)", "Retake (Ineligible)"):
            continue

        grade_upper = r.grade.upper()
        if grade_upper == "I":
            pts = 0.0
        elif grade_upper in GRADE_POINTS:
            pts = GRADE_POINTS[grade_upper]
        else:
            continue

        credits = r.credits
        if credits <= 0:
            continue

        existing = best.get(r.course_code)
        if existing is None or pts > existing[1] / existing[0] if existing[0] > 0 else True:
            rank = GRADE_ORDER.get(grade_upper, -99)
            ex_rank = GRADE_ORDER.get("", -100)
            if existing:
                ex_pts_per = existing[1] / existing[0] if existing[0] > 0 else 0
                if pts > ex_pts_per or (pts == ex_pts_per and rank > ex_rank):
                    best[r.course_code] = (credits, pts * credits)
            else:
                best[r.course_code] = (credits, pts * credits)

    total_credits = sum(c for c, _ in best.values())
    total_points = sum(p for _, p in best.values())

    return total_points / total_credits if total_credits > 0 else 0.0


def compute_cgpa_simple(records: List[CourseRecord],
                        waived: Optional[Set[str]] = None) -> Tuple[float, float, float]:
    """Compute CGPA returning (cgpa, total_gpa_credits, total_grade_points).

    Uses best attempt per course, excludes W/T/P and waived courses.
    I is treated as F (0.0).
    """
    waived = waived or set()
    best: Dict[str, Tuple[float, float, int]] = {}

    for r in records:
        if r.course_code in waived:
            continue
        if r.grade.upper() in GPA_EXCLUDED:
            continue
        if r.status in ("Retake (Ignored)", "Retake (Ineligible)"):
            continue
        if r.credits <= 0:
            continue

        grade_upper = r.grade.upper()
        if grade_upper == "I":
            pts = 0.0
            rank = GRADE_ORDER.get("I", 0)
        elif grade_upper in GRADE_POINTS:
            pts = GRADE_POINTS[grade_upper]
            rank = GRADE_ORDER.get(grade_upper, -99)
        else:
            continue

        existing = best.get(r.course_code)
        if existing is None or rank > existing[2]:
            best[r.course_code] = (r.credits, pts, rank)

    total_credits = sum(c for c, _, _ in best.values())
    total_points = sum(c * p for c, p, _ in best.values())
    cgpa = total_points / total_credits if total_credits > 0 else 0.0

    return cgpa, total_credits, total_points


def compute_semester_progression(records: List[CourseRecord],
                                 waived: Optional[Set[str]] = None
                                 ) -> List[SemesterSnapshot]:
    """Compute semester-by-semester TGPA and cumulative CGPA with probation tracking."""
    waived = waived or set()
    semesters = get_semesters_ordered(records)
    by_sem = get_records_by_semester(records)

    snapshots: List[SemesterSnapshot] = []
    cumulative_best: Dict[str, Tuple[float, float, int]] = {}
    consecutive_prob = 0

    for sem in semesters:
        sem_records = by_sem.get(sem, [])
        sem_pts = 0.0
        sem_cred = 0.0

        for r in sem_records:
            if r.course_code in waived:
                continue
            if r.grade.upper() in GPA_EXCLUDED:
                continue
            if r.credits <= 0:
                continue

            grade_upper = r.grade.upper()
            if grade_upper == "I":
                pts = 0.0
                rank = GRADE_ORDER.get("I", 0)
            elif grade_upper in GRADE_POINTS:
                pts = GRADE_POINTS[grade_upper]
                rank = GRADE_ORDER.get(grade_upper, -99)
            else:
                continue

            sem_pts += pts * r.credits
            sem_cred += r.credits

            existing = cumulative_best.get(r.course_code)
            if existing is None or rank > existing[2]:
                cumulative_best[r.course_code] = (r.credits, pts, rank)

        tgpa = sem_pts / sem_cred if sem_cred > 0 else 0.0

        cum_credits = sum(c for c, _, _ in cumulative_best.values())
        cum_points = sum(c * p for c, p, _ in cumulative_best.values())
        cumulative_cgpa = cum_points / cum_credits if cum_credits > 0 else 0.0

        if cum_credits > 0 and cumulative_cgpa < 2.0:
            consecutive_prob += 1
        else:
            consecutive_prob = 0

        if consecutive_prob == 0:
            prob_status = "NORMAL"
        elif consecutive_prob == 1:
            prob_status = "P1"
        elif consecutive_prob == 2:
            prob_status = "P2"
        else:
            prob_status = "DISMISSAL"

        snapshots.append(SemesterSnapshot(
            semester=sem,
            courses=sem_records,
            sem_credits=sem_cred,
            sem_points=sem_pts,
            tgpa=tgpa,
            cumulative_cgpa=cumulative_cgpa,
            probation_status=prob_status,
            consecutive_prob_count=consecutive_prob,
        ))

    return snapshots


def compute_major_cgpa(records: List[CourseRecord],
                       major_courses: Set[str],
                       waived: Optional[Set[str]] = None) -> float:
    """Compute CGPA for major courses only."""
    waived = waived or set()
    best: Dict[str, Tuple[float, float, int]] = {}

    for r in records:
        if r.course_code not in major_courses:
            continue
        if r.course_code in waived:
            continue
        if r.grade.upper() in GPA_EXCLUDED:
            continue
        if r.status in ("Retake (Ignored)", "Retake (Ineligible)"):
            continue
        if r.credits <= 0:
            continue

        grade_upper = r.grade.upper()
        if grade_upper == "I":
            pts = 0.0
            rank = 0
        elif grade_upper in GRADE_POINTS:
            pts = GRADE_POINTS[grade_upper]
            rank = GRADE_ORDER.get(grade_upper, -99)
        else:
            continue

        existing = best.get(r.course_code)
        if existing is None or rank > existing[2]:
            best[r.course_code] = (r.credits, pts, rank)

    total_credits = sum(c for c, _, _ in best.values())
    total_points = sum(c * p for c, p, _ in best.values())
    return total_points / total_credits if total_credits > 0 else 0.0


def compute_grade_distribution(records: List[CourseRecord]) -> Dict[str, int]:
    """Count occurrences of each grade (best attempt only)."""
    best: Dict[str, str] = {}
    for r in records:
        if r.status in ("Retake (Ignored)", "Retake (Ineligible)"):
            continue
        if r.status in ("Withdrawn",):
            continue
        existing = best.get(r.course_code)
        if existing is None:
            best[r.course_code] = r.grade
        else:
            if GRADE_ORDER.get(r.grade, -99) > GRADE_ORDER.get(existing, -99):
                best[r.course_code] = r.grade

    dist: Dict[str, int] = {}
    for grade in best.values():
        dist[grade] = dist.get(grade, 0) + 1
    return dict(sorted(dist.items(), key=lambda x: GRADE_ORDER.get(x[0], -99), reverse=True))
