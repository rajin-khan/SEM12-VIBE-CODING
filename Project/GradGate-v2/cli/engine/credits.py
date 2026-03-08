"""Level 1: Credit tally engine."""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.program_loader import ProgramInfo
from engine.transcript import CourseRecord


@dataclass
class CreditSummary:
    total_earned: float = 0.0
    total_attempted: float = 0.0
    program_credits: float = 0.0
    elective_credits: float = 0.0
    excluded_credits: float = 0.0
    waived_credits: float = 0.0
    course_statuses: list[tuple[CourseRecord, str]] = field(default_factory=list)


def tally_credits(
    records: list[CourseRecord],
    program_info: ProgramInfo | None = None,
    waived_courses: set[str] | None = None,
    equivalences: dict[str, set[str]] | None = None,
) -> CreditSummary:
    """Compute total valid earned credits from resolved transcript records."""
    summary = CreditSummary()
    waived = waived_courses or set()

    required_codes: set[str] = set()
    if program_info:
        required_codes = program_info.all_required_codes()
        if equivalences:
            expanded = set()
            for code in required_codes:
                expanded.add(code)
                if code in equivalences:
                    expanded |= equivalences[code]
            required_codes = expanded

    counted_courses: set[str] = set()

    for r in records:
        code = r.course_code
        category = "excluded"

        if code in waived:
            r.status = "Waived"
            summary.waived_credits += r.credits
            summary.course_statuses.append((r, "waived"))
            continue

        if r.status == "Withdrawn":
            summary.course_statuses.append((r, "excluded"))
            continue

        if r.status == "Incomplete":
            summary.total_attempted += r.credits
            summary.course_statuses.append((r, "excluded"))
            continue

        if r.status in ("Retake (Ignored)", "Retake (Ineligible)"):
            summary.course_statuses.append((r, "retake"))
            continue

        if r.grade.upper() == "F":
            summary.total_attempted += r.credits
            summary.course_statuses.append((r, "failed"))
            continue

        if r.status in ("Counted", "Waived", "Transfer"):
            if code in counted_courses:
                summary.course_statuses.append((r, "retake"))
                continue
            counted_courses.add(code)

            if r.credits > 0:
                summary.total_earned += r.credits
                summary.total_attempted += r.credits

            if program_info:
                is_required = code in required_codes
                if not is_required and equivalences and code in equivalences:
                    is_required = bool(equivalences[code] & required_codes)

                if is_required:
                    summary.program_credits += r.credits
                    category = "program"
                else:
                    summary.elective_credits += r.credits
                    category = "elective"
            else:
                category = "earned"

            summary.course_statuses.append((r, category))
            continue

        summary.course_statuses.append((r, "excluded"))

    return summary
