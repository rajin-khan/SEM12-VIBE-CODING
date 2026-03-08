"""CSV transcript parsing, retake resolution, and course validation."""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

GRADE_POINTS: Dict[str, float] = {
    "A": 4.0, "A-": 3.7,
    "B+": 3.3, "B": 3.0, "B-": 2.7,
    "C+": 2.3, "C": 2.0, "C-": 1.7,
    "D+": 1.3, "D": 1.0,
    "F": 0.0,
}

GRADE_ORDER: Dict[str, int] = {
    "T": 13, "A": 12, "A-": 11, "B+": 10, "B": 9, "B-": 8,
    "C+": 7, "C": 6, "C-": 5, "D+": 4, "D": 3,
    "F": 1, "I": 0, "W": -1, "P": -2,
}

PASSING_GRADES = {"A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "T", "P"}
NON_GPA_GRADES = {"W", "T", "P"}
SEMESTER_SEASON_ORDER = {"Spring": 0, "Summer": 1, "Fall": 2}

VALID_GRADES = set(GRADE_ORDER.keys())
RETAKE_ELIGIBLE_GRADES = {"B", "B-", "C+", "C", "C-", "D+", "D", "F"}


@dataclass
class CourseRecord:
    course_code: str
    credits: float
    grade: str
    semester: str
    status: str = ""
    grade_points: float = 0.0

    @property
    def is_passing(self) -> bool:
        return self.grade.upper() in PASSING_GRADES

    @property
    def is_gpa_bearing(self) -> bool:
        return self.grade.upper() not in NON_GPA_GRADES and self.credits > 0

    @property
    def semester_sort_key(self) -> Tuple[int, int]:
        parts = self.semester.strip().split()
        if len(parts) == 2:
            try:
                return (int(parts[1]), SEMESTER_SEASON_ORDER.get(parts[0], 99))
            except ValueError:
                pass
        return (9999, 99)


REQUIRED_COLUMNS = {"Course_Code", "Credits", "Grade", "Semester"}


def load_transcript(csv_path: str) -> List[CourseRecord]:
    """Load and parse a transcript CSV file."""
    path = Path(csv_path)
    if not path.exists():
        print(f"Error: Transcript file '{csv_path}' not found.")
        sys.exit(1)

    records: List[CourseRecord] = []
    try:
        with open(path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                reader.fieldnames = [n.strip() for n in reader.fieldnames]

            if reader.fieldnames:
                missing_cols = REQUIRED_COLUMNS - set(reader.fieldnames)
                if missing_cols:
                    print(f"Error: Transcript CSV is missing required column(s): "
                          f"{', '.join(sorted(missing_cols))}")
                    print(f"  Found columns: {', '.join(reader.fieldnames)}")
                    print(f"  Required: {', '.join(sorted(REQUIRED_COLUMNS))}")
                    sys.exit(1)

            for row in reader:
                code = row.get("Course_Code", "").strip()
                if not code:
                    continue
                grade = row.get("Grade", "").strip().upper()
                semester = row.get("Semester", "Unknown").strip()
                try:
                    credits = max(0.0, float(row.get("Credits", "0").strip()))
                except ValueError:
                    credits = 0.0

                gp = GRADE_POINTS.get(grade, 0.0)
                records.append(CourseRecord(
                    course_code=code,
                    credits=credits,
                    grade=grade,
                    semester=semester,
                    grade_points=gp,
                ))
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error reading transcript: {e}")
        sys.exit(1)

    return records


def validate_grades(records: List[CourseRecord]) -> List[str]:
    """Return list of error messages for invalid grades."""
    errors = []
    for r in records:
        if r.grade.upper() not in VALID_GRADES:
            errors.append(f"Invalid grade '{r.grade}' for course {r.course_code} in {r.semester}")
    return errors


def validate_courses(records: List[CourseRecord], nsu_courses: Set[str]) -> List[str]:
    """Return list of course codes not found in NSU course list."""
    non_nsu = []
    for r in records:
        if r.course_code and r.course_code not in nsu_courses:
            if r.course_code not in non_nsu:
                non_nsu.append(r.course_code)
    return non_nsu


def resolve_retakes(records: List[CourseRecord],
                    equivalences: Optional[Dict[str, Set[str]]] = None
                    ) -> List[CourseRecord]:
    """Resolve retakes: best grade wins, subject to retake eligibility.

    NSU Policy: Only courses with grade B or lower may be retaken.
    Retakes of B+ or above are flagged as "Retake (Ineligible)".

    Status values: Counted, Retake (Ignored), Retake (Ineligible),
                   Failed, Withdrawn, Incomplete, Waived, Transfer
    """
    groups: Dict[str, List[CourseRecord]] = {}
    for r in records:
        canonical = r.course_code
        if equivalences and r.course_code in equivalences:
            group_codes = sorted(equivalences[r.course_code])
            canonical = group_codes[0]
            for gc in group_codes:
                if gc in groups:
                    canonical = gc
                    break

        if canonical not in groups:
            groups[canonical] = []
        groups[canonical].append(r)

    for canonical, group in groups.items():
        gpa_records = [r for r in group if r.grade.upper() not in {"W", "I"}]
        non_gpa = [r for r in group if r.grade.upper() in {"W", "I"}]

        for r in non_gpa:
            if r.grade.upper() == "W":
                r.status = "Withdrawn"
            elif r.grade.upper() == "I":
                r.status = "Incomplete"

        if not gpa_records:
            continue

        if len(gpa_records) == 1:
            r = gpa_records[0]
            if r.grade.upper() == "T":
                r.status = "Waived"
            elif r.grade.upper() == "P":
                r.status = "Counted"
            elif r.grade.upper() == "F":
                r.status = "Failed"
            elif r.is_passing:
                r.status = "Counted"
            else:
                r.status = "Failed"
        else:
            sorted_by_time = sorted(gpa_records, key=lambda x: x.semester_sort_key)
            first = sorted_by_time[0]
            first_grade_ineligible = (
                first.grade.upper() not in RETAKE_ELIGIBLE_GRADES
                and first.grade.upper() not in NON_GPA_GRADES
            )

            if first_grade_ineligible:
                first_status = "Waived" if first.grade.upper() == "T" else "Counted"
                first.status = first_status
                for r in gpa_records:
                    if r is not first:
                        r.status = "Retake (Ineligible)"
            else:
                best = max(gpa_records, key=lambda x: (
                    GRADE_ORDER.get(x.grade.upper(), -99),
                    x.semester_sort_key
                ))
                for r in gpa_records:
                    if r is best:
                        if r.grade.upper() == "T":
                            r.status = "Waived"
                        elif r.grade.upper() == "F":
                            r.status = "Failed"
                        elif r.is_passing:
                            r.status = "Counted"
                        else:
                            r.status = "Failed"
                    else:
                        r.status = "Retake (Ignored)"

    return records


def get_best_records(records: List[CourseRecord]) -> Dict[str, CourseRecord]:
    """Get the best record per course code (Counted, Waived, or Failed if standalone)."""
    best: Dict[str, CourseRecord] = {}
    for r in records:
        if r.status in ("Counted", "Waived", "Failed", "Transfer"):
            existing = best.get(r.course_code)
            if existing is None or GRADE_ORDER.get(r.grade.upper(), -99) > GRADE_ORDER.get(existing.grade.upper(), -99):
                best[r.course_code] = r
    return best


def get_passed_courses(records: List[CourseRecord]) -> Set[str]:
    """Get set of course codes that the student has passed (best attempt)."""
    passed: Set[str] = set()
    best = get_best_records(records)
    for code, r in best.items():
        if r.is_passing:
            passed.add(code)
    return passed


def get_semesters_ordered(records: List[CourseRecord]) -> List[str]:
    """Get unique semesters in chronological order."""
    sems: Dict[str, Tuple[int, int]] = {}
    for r in records:
        if r.semester not in sems:
            sems[r.semester] = r.semester_sort_key
    return sorted(sems.keys(), key=lambda s: sems[s])


def get_records_by_semester(records: List[CourseRecord]) -> Dict[str, List[CourseRecord]]:
    """Group records by semester."""
    by_sem: Dict[str, List[CourseRecord]] = {}
    for r in records:
        by_sem.setdefault(r.semester, []).append(r)
    return by_sem
