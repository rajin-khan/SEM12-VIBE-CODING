#!/usr/bin/env python3
"""Generate canonical handbook-era transcript fixtures from the structured catalog."""

from __future__ import annotations

import csv
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
CLI_DIR = REPO / "cli"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(CLI_DIR) not in sys.path:
    sys.path.insert(0, str(CLI_DIR))

from engine.audit import AuditResult, run_audit
from engine.program_loader import ProgramInfo, load_all_programs, load_equivalences, load_nsu_course_list
from engine.transcript import GRADE_POINTS, CourseRecord, load_transcript, resolve_retakes, validate_courses
from engine.waivers import get_waivers

CATALOG = REPO / "data" / "curriculum" / "catalog.json"
BLUEPRINTS_PATH = REPO / "data" / "curriculum" / "fixture_blueprints.json"
TESTS_DIR = REPO / "tests"
MANIFEST_PATH = TESTS_DIR / "canonical_fixture_expectations.json"
LEGACY_MAP_PATH = TESTS_DIR / "legacy_fixture_map.json"

SEMESTERS = [
    f"{season} {year}"
    for year in range(2019, 2027)
    for season in ("Spring", "Summer", "Fall")
]

GRADE_PROFILES = {
    "strong": ["A", "A-", "B+", "A", "B+", "A-"],
    "good": ["B+", "B", "A-", "B", "B+", "A-"],
    "borderline": ["B", "B-", "C+", "B", "C+", "B-"],
    "poor": ["C", "C-", "D+", "C", "D", "C-"],
}

SCENARIOS: list[dict[str, Any]] = [
    {"filename": "happy_cse_default.csv", "program": "CSE", "profile": "strong"},
    {
        "filename": "happy_cse_extended.csv",
        "program": "CSE",
        "profile": "strong",
        "extra_filler_courses": 1,
    },
    {
        "filename": "short_cse_credit_gap.csv",
        "program": "CSE",
        "profile": "good",
        "drop_filler_courses": 1,
    },
    {"filename": "happy_eee_default.csv", "program": "EEE", "profile": "strong"},
    {
        "filename": "short_eee_credit_gap.csv",
        "program": "EEE",
        "profile": "good",
        "drop_filler_courses": 1,
    },
    {"filename": "happy_ete_default.csv", "program": "ETE", "profile": "strong"},
    {
        "filename": "short_ete_credit_gap.csv",
        "program": "ETE",
        "profile": "good",
        "drop_filler_courses": 1,
    },
    {"filename": "happy_cee_default.csv", "program": "CEE", "profile": "strong"},
    {
        "filename": "short_cee_credit_gap.csv",
        "program": "CEE",
        "profile": "good",
        "drop_filler_courses": 1,
    },
    {"filename": "happy_env_default.csv", "program": "ENV", "profile": "strong"},
    {
        "filename": "short_env_credit_gap.csv",
        "program": "ENV",
        "profile": "good",
        "drop_filler_courses": 1,
    },
    {"filename": "happy_eng_default.csv", "program": "ENG", "profile": "strong"},
    {
        "filename": "short_eng_credit_gap.csv",
        "program": "ENG",
        "profile": "good",
        "drop_filler_courses": 1,
    },
    {
        "filename": "happy_bba_finance.csv",
        "program": "BBA",
        "profile": "strong",
        "concentration": "FIN",
    },
    {
        "filename": "short_bba_credit_gap.csv",
        "program": "BBA",
        "profile": "good",
        "concentration": "FIN",
        "drop_filler_courses": 1,
    },
    {"filename": "happy_eco_default.csv", "program": "ECO", "profile": "strong"},
    {
        "filename": "short_eco_credit_gap.csv",
        "program": "ECO",
        "profile": "good",
        "drop_filler_courses": 1,
    },
    {
        "filename": "concentration_bba_finance.csv",
        "program": "BBA",
        "profile": "strong",
        "concentration": "FIN",
    },
    {
        "filename": "concentration_bba_undeclared.csv",
        "program": "BBA",
        "profile": "good",
        "concentration": "FIN",
        "drop_concentration_courses": 3,
    },
    {
        "filename": "concentration_bba_finance_low_gpa.csv",
        "program": "BBA",
        "profile": "good",
        "concentration": "FIN",
        "set_grades": {
            "FIN410": "C",
            "FIN433": "C",
            "FIN435": "C-",
            "FIN440": "C",
            "FIN444": "C-",
            "FIN455": "C",
        },
    },
    {
        "filename": "minor_cse_math_complete.csv",
        "program": "CSE",
        "profile": "strong",
        "minor": "MATH",
    },
    {
        "filename": "minor_cse_physics_complete.csv",
        "program": "CSE",
        "profile": "strong",
        "minor": "PHYSICS",
    },
    {
        "filename": "minor_cse_math_partial.csv",
        "program": "CSE",
        "profile": "good",
        "minor": "MATH",
        "drop_minor_courses": 2,
    },
    {
        "filename": "minor_cse_math_missing_prereqs.csv",
        "program": "CSE",
        "profile": "good",
        "minor": "MATH",
        "drop_courses": ["MAT250"],
        "replacement_courses": ["PSY101", "SOC201"],
    },
    {
        "filename": "waiver_cse_eng102.csv",
        "program": "CSE",
        "profile": "strong",
        "waivers": ["ENG102"],
        "drop_filler_courses": 1,
    },
    {
        "filename": "waiver_cse_mat112.csv",
        "program": "CSE",
        "profile": "strong",
        "waivers": ["MAT112"],
        "drop_filler_courses": 1,
    },
    {
        "filename": "waiver_cse_both.csv",
        "program": "CSE",
        "profile": "strong",
        "waivers": ["ENG102", "MAT112"],
        "drop_filler_courses": 2,
    },
    {
        "filename": "prereq_cse_database_early.csv",
        "program": "CSE",
        "profile": "strong",
        "force_terms": {"CSE311": 2, "CSE225": 6, "CSE225L": 6},
    },
    {
        "filename": "prereq_eee_circuits_early.csv",
        "program": "EEE",
        "profile": "strong",
        "force_terms": {"EEE241": 2, "EEE141": 6, "EEE141L": 6},
    },
    {
        "filename": "prereq_bba_finance_early.csv",
        "program": "BBA",
        "profile": "strong",
        "concentration": "FIN",
        "force_terms": {"FIN254": 2, "ACT201": 5},
    },
    {
        "filename": "prereq_bba_internship_early.csv",
        "program": "BBA",
        "profile": "strong",
        "concentration": "FIN",
        "force_terms": {"BUS498": 3},
    },
    {
        "filename": "retake_cse_recovered.csv",
        "program": "CSE",
        "profile": "strong",
        "prepend_attempts": [{"code": "CSE225", "grade": "F", "term_index": 4}],
    },
    {
        "filename": "retake_cse_unresolved.csv",
        "program": "CSE",
        "profile": "good",
        "prepend_attempts": [{"code": "CSE225", "grade": "F", "term_index": 4}],
        "set_grades": {"CSE225": "F"},
    },
    {
        "filename": "retake_cse_multiple.csv",
        "program": "CSE",
        "profile": "strong",
        "prepend_attempts": [
            {"code": "CSE225", "grade": "F", "term_index": 3},
            {"code": "CSE225", "grade": "D", "term_index": 5}
        ],
    },
    {
        "filename": "retake_cse_worse_second_attempt.csv",
        "program": "CSE",
        "profile": "strong",
        "prepend_attempts": [{"code": "CSE225", "grade": "B", "term_index": 4}],
        "set_grades": {"CSE225": "C"},
    },
    {
        "filename": "retake_cse_ineligible.csv",
        "program": "CSE",
        "profile": "strong",
        "prepend_attempts": [{"code": "CSE225", "grade": "A", "term_index": 4}],
        "set_grades": {"CSE225": "B"},
    },
    {
        "filename": "failed_cse_core.csv",
        "program": "CSE",
        "profile": "good",
        "set_grades": {"CSE225": "F"},
    },
    {
        "filename": "failed_bba_core.csv",
        "program": "BBA",
        "profile": "good",
        "concentration": "FIN",
        "set_grades": {"ACT201": "F"},
    },
    {
        "filename": "incomplete_cse_hold.csv",
        "program": "CSE",
        "profile": "good",
        "set_grades": {"CSE323": "I"},
    },
    {
        "filename": "incomplete_cse_resolved.csv",
        "program": "CSE",
        "profile": "strong",
        "prepend_attempts": [{"code": "CSE323", "grade": "I", "term_index": 8}],
    },
    {
        "filename": "incomplete_bba_hold.csv",
        "program": "BBA",
        "profile": "good",
        "concentration": "FIN",
        "set_grades": {"MGT489": "I"},
    },
    {
        "filename": "withdrawn_cse_hold.csv",
        "program": "CSE",
        "profile": "good",
        "set_grades": {"CSE327": "W"},
    },
    {
        "filename": "withdrawn_bba_hold.csv",
        "program": "BBA",
        "profile": "good",
        "concentration": "FIN",
        "set_grades": {"BUS401": "W"},
    },
    {
        "filename": "mixed_cse_statuses.csv",
        "program": "CSE",
        "profile": "good",
        "set_grades": {"CSE225": "F", "CSE323": "I", "CSE327": "W"},
    },
    {
        "filename": "mixed_bba_statuses.csv",
        "program": "BBA",
        "profile": "good",
        "concentration": "FIN",
        "set_grades": {"ACT201": "F", "MGT489": "I", "BUS401": "W"},
    },
    {
        "filename": "transfer_cse_external_credit.csv",
        "program": "CSE",
        "profile": "strong",
        "add_rows": [
            {"Course_Code": "EXT101", "Credits": 3.0, "Grade": "A", "Semester": SEMESTERS[2]}
        ],
    },
    {
        "filename": "probation_bba_borderline.csv",
        "program": "BBA",
        "profile": "borderline",
        "concentration": "FIN",
    },
    {
        "filename": "probation_bba_recovery.csv",
        "program": "BBA",
        "profile": "borderline",
        "concentration": "FIN",
        "set_grades": {
            "BUS498": "A",
            "FIN455": "A",
            "FIN444": "A-",
            "FIN440": "A-"
        },
    },
    {
        "filename": "probation_bba_dismissal_risk.csv",
        "program": "BBA",
        "profile": "poor",
        "concentration": "FIN",
    },
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_course_credits(catalog_blob: dict[str, Any], blueprints: dict[str, Any]) -> dict[str, float]:
    credits: dict[str, float] = {}
    for payload in catalog_blob["programs"].values():
        for courses in payload.get("buckets", {}).values():
            for course in courses:
                credits[course["code"]] = float(course["credits"])
        for trail in payload.get("trails", []):
            for code in trail.get("courses", []):
                credits.setdefault(code, 1.0 if code.endswith("L") else 3.0)
        for concentration in payload.get("concentrations", []):
            for code in concentration.get("courses", []):
                credits.setdefault(code, 1.0 if code.endswith("L") else 3.0)
        for minor in payload.get("minors", []):
            for code in minor.get("required_courses", []) + minor.get("elective_courses", []):
                credits.setdefault(code, 1.0 if code.endswith("L") else 3.0)
    for codes in blueprints["program_electives"].values():
        for code in codes:
            credits.setdefault(code, 1.0 if code.endswith("L") else 3.0)
    for code in blueprints["generic_open_electives"]:
        credits.setdefault(code, 1.0 if code.endswith("L") else 3.0)
    return credits


def _ordered_unique(values: list[str]) -> list[str]:
    return list(OrderedDict.fromkeys(values))


def _required_courses(program: ProgramInfo) -> list[str]:
    required: list[str] = []
    for bucket in (
        program.mandatory_ged,
        program.core_math,
        program.core_science,
        program.core_business,
        program.major_core,
        program.capstone,
        program.internship,
    ):
        required.extend(course.code for course in bucket)
    return _ordered_unique(required)


def _pick_trail_courses(program: ProgramInfo) -> list[str]:
    needed = program.trail_credits_required // 3
    if needed <= 0:
        return []
    picked: list[str] = []
    for trail in program.trails:
        for code in trail.courses:
            if code not in picked:
                picked.append(code)
            if len(picked) >= needed:
                return picked
    return picked


def _pick_concentration_courses(program: ProgramInfo, alias: str | None) -> list[str]:
    if not alias or program.concentration_credits_required <= 0:
        return []
    needed = program.concentration_credits_required // 3
    for concentration in program.concentrations:
        if concentration.alias.upper() == alias.upper() or concentration.name.upper() == alias.upper():
            return concentration.courses[:needed]
    return []


def _pick_minor_courses(program: ProgramInfo, minor_name: str | None) -> list[str]:
    if not minor_name:
        return []
    for minor in program.minors:
        if minor.name.upper() == minor_name.upper():
            courses = list(minor.required_courses)
            if minor.elective_pick_count > 0:
                courses.extend(minor.elective_courses[: minor.elective_pick_count])
            return courses
    return []


def _candidate_fillers(
    alias: str,
    program: ProgramInfo,
    selected: list[str],
    blueprints: dict[str, Any],
    credits_map: dict[str, float],
    equivalences: dict[str, set[str]],
    excluded_codes: set[str] | None = None,
) -> list[str]:
    used = set(selected)
    excluded = excluded_codes or set()
    ordered_candidates = (
        blueprints["program_electives"].get(alias, [])
        + blueprints["generic_open_electives"]
        + [
            code
            for other_alias, courses in blueprints["program_electives"].items()
            if other_alias != alias
            for code in courses
        ]
    )
    candidates: list[str] = []
    for code in ordered_candidates:
        if code in used:
            continue
        if code in excluded:
            continue
        if equivalences.get(code, {code}) & used:
            continue
        prereqs = set(program.prerequisites.get(code, []))
        if prereqs and not prereqs.issubset(used):
            continue
        if credits_map.get(code, 3.0) <= 0:
            continue
        candidates.append(code)
        used.add(code)
    return candidates


def _selection_credits(codes: list[str], credits_map: dict[str, float]) -> float:
    return round(sum(credits_map.get(code, 3.0) for code in codes), 3)


def _depths(program: ProgramInfo, codes: list[str]) -> dict[str, int]:
    selected = set(codes)
    memo: dict[str, int] = {}

    def depth(code: str) -> int:
        if code in memo:
            return memo[code]
        result = 0
        for prereq in program.prerequisites.get(code, []):
            if prereq in selected:
                result = max(result, depth(prereq) + 1)
        if code in program.credit_prerequisites:
            result = max(result, 8)
        if code.endswith("L") and code[:-1] in selected:
            result = max(result, depth(code[:-1]))
        memo[code] = result
        return result

    for code in codes:
        depth(code)
    return memo


def _rows_from_codes(
    program: ProgramInfo,
    codes: list[str],
    credits_map: dict[str, float],
    profile: str,
) -> list[dict[str, Any]]:
    depths = _depths(program, codes)
    ordered = sorted(codes, key=lambda code: (depths.get(code, 0), code.endswith("L"), code))
    grade_cycle = GRADE_PROFILES[profile]
    rows: list[dict[str, Any]] = []
    for idx, code in enumerate(ordered):
        term = SEMESTERS[min(idx // 5, len(SEMESTERS) - 1)]
        rows.append(
            {
                "Course_Code": code,
                "Credits": credits_map.get(code, 3.0),
                "Grade": grade_cycle[idx % len(grade_cycle)],
                "Semester": term,
            }
        )
    return rows


def _records_from_rows(rows: list[dict[str, Any]]) -> list[CourseRecord]:
    return [
        CourseRecord(
            course_code=str(row["Course_Code"]),
            credits=float(row["Credits"]),
            grade=str(row["Grade"]),
            semester=str(row["Semester"]),
            grade_points=GRADE_POINTS.get(str(row["Grade"]), 0.0),
        )
        for row in rows
    ]


def _index_by_code(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["Course_Code"]), []).append(row)
    return grouped


def _drop_codes(rows: list[dict[str, Any]], codes: list[str]) -> list[dict[str, Any]]:
    targets = set(codes)
    remaining: list[dict[str, Any]] = []
    removed: set[str] = set()
    for row in rows:
        code = str(row["Course_Code"])
        if code in targets and code not in removed:
            removed.add(code)
            continue
        remaining.append(row)
    return remaining


def _set_grades(rows: list[dict[str, Any]], updates: dict[str, str]) -> None:
    grouped = _index_by_code(rows)
    for code, grade in updates.items():
        if grouped.get(code):
            grouped[code][-1]["Grade"] = grade


def _force_terms(rows: list[dict[str, Any]], updates: dict[str, int]) -> None:
    grouped = _index_by_code(rows)
    for code, term_index in updates.items():
        if grouped.get(code):
            grouped[code][-1]["Semester"] = SEMESTERS[min(term_index, len(SEMESTERS) - 1)]


def _prepend_attempts(
    rows: list[dict[str, Any]],
    attempts: list[dict[str, Any]],
    credits_map: dict[str, float],
) -> list[dict[str, Any]]:
    prepended: list[dict[str, Any]] = []
    for attempt in attempts:
        prepended.append(
            {
                "Course_Code": attempt["code"],
                "Credits": credits_map.get(attempt["code"], 3.0),
                "Grade": attempt["grade"],
                "Semester": SEMESTERS[min(int(attempt["term_index"]), len(SEMESTERS) - 1)],
            }
        )
    return prepended + rows


def _write_fixture(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Course_Code", "Credits", "Grade", "Semester"])
        writer.writeheader()
        writer.writerows(rows)


def _compute_expectation(
    path: Path,
    program: str,
    waivers: list[str],
    concentration: str | None,
    minor: str | None,
) -> dict[str, Any]:
    programs = load_all_programs(str(CATALOG))
    program_info = programs[program]
    records = load_transcript(str(path))
    equivalences = load_equivalences(str(CATALOG))
    nsu_courses = load_nsu_course_list(str(CATALOG))
    for code in validate_courses(records, nsu_courses):
        for record in records:
            if record.course_code == code:
                record.grade = "T"
                record.status = "Transfer"
    resolve_retakes(records, equivalences)
    active_waivers = get_waivers(
        program_info,
        cli_waivers=",".join(waivers),
        interactive=False,
    )
    audit = run_audit(
        records,
        program_info,
        active_waivers,
        equivalences,
        concentration=concentration,
        minor=minor,
    )
    return {
        "program": program,
        "scenario": path.stem,
        "eligible": audit.eligible,
        "credits_completed": audit.credits_completed,
        "credits_required": audit.credits_required,
        "reasons": audit.reasons,
        "waivers": waivers,
        "concentration": concentration,
        "minor": minor,
    }


def _audit_rows(
    rows: list[dict[str, Any]],
    program_info: ProgramInfo,
    equivalences: dict[str, set[str]],
    nsu_courses: set[str],
    waivers: list[str],
    concentration: str | None,
    minor: str | None,
) -> AuditResult:
    records = _records_from_rows(rows)
    for code in validate_courses(records, nsu_courses):
        for record in records:
            if record.course_code == code:
                record.grade = "T"
                record.status = "Transfer"
    resolve_retakes(records, equivalences)
    active_waivers = get_waivers(
        program_info,
        cli_waivers=",".join(waivers),
        interactive=False,
    )
    return run_audit(
        records,
        program_info,
        active_waivers,
        equivalences,
        concentration=concentration,
        minor=minor,
    )


def _top_up_rows(
    rows: list[dict[str, Any]],
    program_info: ProgramInfo,
    spec: dict[str, Any],
    blueprints: dict[str, Any],
    credits_map: dict[str, float],
    equivalences: dict[str, set[str]],
    nsu_courses: set[str],
) -> list[dict[str, Any]]:
    concentration = spec.get("concentration") or blueprints["default_concentrations"].get(
        spec["program"]
    )
    minor = spec.get("minor")
    waivers = list(spec.get("waivers", []))
    trail_codes = {code for trail in program_info.trails for code in trail.courses}
    concentration_codes = {code for conc in program_info.concentrations for code in conc.courses}

    while True:
        audit = _audit_rows(
            rows,
            program_info,
            equivalences,
            nsu_courses,
            waivers,
            concentration,
            minor,
        )
        if (
            audit.credits_completed >= audit.credits_required
            and audit.deficiencies.missing_open_elective == 0
        ):
            return rows

        existing_codes = [str(row["Course_Code"]) for row in rows]
        candidates = _candidate_fillers(
            program_info.alias,
            program_info,
            existing_codes,
            blueprints,
            credits_map,
            equivalences,
            excluded_codes=trail_codes | concentration_codes,
        )
        if not candidates:
            return rows
        new_code = candidates[0]
        rows.append(
            {
                "Course_Code": new_code,
                "Credits": credits_map.get(new_code, 3.0),
                "Grade": GRADE_PROFILES[spec["profile"]][len(rows) % len(GRADE_PROFILES[spec["profile"]])],
                "Semester": SEMESTERS[min(len(rows) // 5 + 8, len(SEMESTERS) - 1)],
            }
        )


def _build_rows(
    spec: dict[str, Any],
    programs: dict[str, ProgramInfo],
    blueprints: dict[str, Any],
    credits_map: dict[str, float],
    equivalences: dict[str, set[str]],
    nsu_courses: set[str],
) -> list[dict[str, Any]]:
    program = programs[spec["program"]]
    concentration = spec.get("concentration") or blueprints["default_concentrations"].get(
        spec["program"]
    )
    minor = spec.get("minor")

    required = _required_courses(program)
    trail = _pick_trail_courses(program)
    concentration_courses = _pick_concentration_courses(program, concentration)
    minor_courses = _pick_minor_courses(program, minor)
    selected = _ordered_unique(required + trail + concentration_courses + minor_courses)

    trail_codes = {code for trail in program.trails for code in trail.courses}
    concentration_code_set = {code for conc in program.concentrations for code in conc.courses}
    open_fillers = _candidate_fillers(
        spec["program"],
        program,
        selected,
        blueprints,
        credits_map,
        equivalences,
        excluded_codes=trail_codes | concentration_code_set,
    )
    open_needed = program.open_elective_credits // 3
    open_filler = open_fillers[:open_needed]
    selected.extend(open_filler)
    remaining_fillers = _candidate_fillers(
        spec["program"],
        program,
        selected,
        blueprints,
        credits_map,
        equivalences,
    )
    selected_fillers = list(open_filler)

    extra_filler_courses = int(spec.get("extra_filler_courses", 0))
    if extra_filler_courses > 0:
        chosen = remaining_fillers[:extra_filler_courses]
        selected.extend(chosen)
        selected_fillers.extend(chosen)
        remaining_fillers = remaining_fillers[extra_filler_courses:]

    while _selection_credits(selected, credits_map) < program.total_credits and remaining_fillers:
        chosen = remaining_fillers.pop(0)
        selected.append(chosen)
        selected_fillers.append(chosen)

    rows = _rows_from_codes(program, _ordered_unique(selected), credits_map, spec["profile"])
    rows = _top_up_rows(rows, program, spec, blueprints, credits_map, equivalences, nsu_courses)

    if spec.get("drop_filler_courses"):
        removable = list(reversed(selected_fillers))
        rows = _drop_codes(rows, removable[: spec["drop_filler_courses"]])

    if spec.get("drop_concentration_courses"):
        rows = _drop_codes(rows, concentration_courses[-spec["drop_concentration_courses"] :])

    if spec.get("drop_minor_courses"):
        rows = _drop_codes(rows, minor_courses[-spec["drop_minor_courses"] :])

    if spec.get("drop_courses"):
        rows = _drop_codes(rows, list(spec["drop_courses"]))

    if spec.get("replacement_courses"):
        rows.extend(
            {
                "Course_Code": code,
                "Credits": credits_map.get(code, 3.0),
                "Grade": GRADE_PROFILES[spec["profile"]][idx % len(GRADE_PROFILES[spec["profile"]])],
                "Semester": SEMESTERS[min(10 + idx, len(SEMESTERS) - 1)],
            }
            for idx, code in enumerate(spec["replacement_courses"])
        )

    if spec.get("set_grades"):
        _set_grades(rows, dict(spec["set_grades"]))

    if spec.get("force_terms"):
        _force_terms(rows, dict(spec["force_terms"]))

    if spec.get("prepend_attempts"):
        rows = _prepend_attempts(rows, list(spec["prepend_attempts"]), credits_map)

    if spec.get("add_rows"):
        rows.extend(spec["add_rows"])

    rows.sort(key=lambda row: (SEMESTERS.index(row["Semester"]), row["Course_Code"], str(row["Grade"])))
    return rows


def main() -> None:
    catalog_blob = _read_json(CATALOG)
    blueprints = _read_json(BLUEPRINTS_PATH)
    programs = load_all_programs(str(CATALOG))
    equivalences = load_equivalences(str(CATALOG))
    nsu_courses = load_nsu_course_list(str(CATALOG))
    credits_map = _load_course_credits(catalog_blob, blueprints)

    manifest: dict[str, Any] = {}
    for spec in SCENARIOS:
        rows = _build_rows(spec, programs, blueprints, credits_map, equivalences, nsu_courses)
        fixture_path = TESTS_DIR / spec["filename"]
        _write_fixture(fixture_path, rows)
        manifest[spec["filename"]] = _compute_expectation(
            fixture_path,
            spec["program"],
            list(spec.get("waivers", [])),
            spec.get("concentration"),
            spec.get("minor"),
        )

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    LEGACY_MAP_PATH.write_text(
        json.dumps(blueprints["legacy_aliases"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"[fixtures] generated {len(SCENARIOS)} canonical fixtures, "
        f"manifest -> {MANIFEST_PATH.name}, legacy map -> {LEGACY_MAP_PATH.name}"
    )


if __name__ == "__main__":
    main()
