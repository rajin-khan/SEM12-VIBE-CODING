"""Prerequisite violation detection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from engine.transcript import CourseRecord, get_semesters_ordered, get_records_by_semester
from engine.program_loader import ProgramInfo


@dataclass
class PrereqViolation:
    course: str
    semester: str
    missing_prereqs: List[str]
    violation_type: str  # "course" or "credits"


def _is_corequisite(course: str, prereq: str) -> bool:
    """Check if a prerequisite is really a co-requisite (lab+lecture pair).

    A lab course (ending in 'L') and its base lecture are co-requisites
    and may be taken in the same semester.
    """
    if course.endswith("L") and course[:-1] == prereq:
        return True
    if prereq.endswith("L") and prereq[:-1] == course:
        return True
    return False


def check_prerequisites(records: List[CourseRecord],
                        program_info: ProgramInfo,
                        equivalences: Optional[Dict[str, Set[str]]] = None
                        ) -> List[PrereqViolation]:
    """Check for prerequisite violations in chronological order.

    For each course taken, verify that all prerequisites were passed
    in an earlier semester. Co-requisites (lab+lecture pairs in the
    same semester) are not flagged.
    """
    violations: List[PrereqViolation] = []
    equivalences = equivalences or {}

    semesters = get_semesters_ordered(records)
    by_sem = get_records_by_semester(records)

    passed_before: Set[str] = set()
    credits_before: float = 0.0

    for sem in semesters:
        sem_records = by_sem.get(sem, [])
        sem_codes = {r.course_code for r in sem_records}

        for r in sem_records:
            code = r.course_code

            if code in program_info.credit_prerequisites:
                needed = program_info.credit_prerequisites[code]
                if credits_before < needed:
                    violations.append(PrereqViolation(
                        course=code,
                        semester=sem,
                        missing_prereqs=[f"{needed} credits (had {credits_before:.0f})"],
                        violation_type="credits",
                    ))

            if code in program_info.prerequisites:
                missing = []
                for prereq in program_info.prerequisites[code]:
                    satisfied = prereq in passed_before
                    if not satisfied and equivalences:
                        equiv_codes = equivalences.get(prereq, set())
                        satisfied = bool(equiv_codes & passed_before)
                    if not satisfied and (prereq in sem_codes or _is_corequisite(code, prereq)):
                        satisfied = True
                    if not satisfied:
                        missing.append(prereq)

                if missing:
                    violations.append(PrereqViolation(
                        course=code,
                        semester=sem,
                        missing_prereqs=missing,
                        violation_type="course",
                    ))

        for r in sem_records:
            if r.is_passing and r.status not in ("Retake (Ignored)", "Retake (Ineligible)", "Withdrawn"):
                passed_before.add(r.course_code)
                if equivalences and r.course_code in equivalences:
                    passed_before |= equivalences[r.course_code]
                if r.credits > 0 and r.status not in ("Retake (Ignored)", "Retake (Ineligible)"):
                    credits_before += r.credits

    return violations
