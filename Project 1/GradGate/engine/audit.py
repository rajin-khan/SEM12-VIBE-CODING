"""Level 3: Graduation audit, deficiency checking, and roadmap generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from engine.transcript import (
    CourseRecord, get_passed_courses, get_best_records, GRADE_POINTS, GRADE_ORDER,
)
from engine.program_loader import ProgramInfo, AlternativeGroup, MinorInfo
from engine.cgpa import compute_cgpa_simple, compute_major_cgpa
from engine.waivers import compute_adjusted_credits, waiver_credit_bonus
from engine.prerequisites import check_prerequisites, PrereqViolation


@dataclass
class DeficiencyReport:
    missing_ged: List[str] = field(default_factory=list)
    missing_math: List[str] = field(default_factory=list)
    missing_science: List[str] = field(default_factory=list)
    missing_business: List[str] = field(default_factory=list)
    missing_major: List[str] = field(default_factory=list)
    missing_capstone: List[str] = field(default_factory=list)
    missing_internship: List[str] = field(default_factory=list)
    missing_trail: int = 0
    missing_concentration: int = 0
    missing_open_elective: int = 0

    @property
    def total_missing(self) -> int:
        return (len(self.missing_ged) + len(self.missing_math) +
                len(self.missing_science) + len(self.missing_business) +
                len(self.missing_major) + len(self.missing_capstone) +
                len(self.missing_internship) + self.missing_trail +
                self.missing_concentration + self.missing_open_elective)

    @property
    def has_missing(self) -> bool:
        return self.total_missing > 0


@dataclass
class AuditResult:
    program: ProgramInfo
    credits_earned: float
    credits_required: int
    waiver_bonus: float
    credits_completed: float  # earned + waiver bonus
    cgpa: float
    gpa_credits: float
    grade_points: float
    major_cgpa: float
    concentration_cgpa: float
    concentration_name: str
    deficiencies: DeficiencyReport
    prereq_violations: List[PrereqViolation]
    eligible: bool
    reasons: List[str]
    roadmap: List[str]
    failed_courses: List[str]
    minor_name: str = ""
    minor_completed: bool = False
    minor_courses_taken: List[str] = field(default_factory=list)
    minor_courses_missing: List[str] = field(default_factory=list)
    minor_prereqs_met: bool = True
    minor_prereqs_missing: List[str] = field(default_factory=list)


def _expand_passed(passed: Set[str], equivalences: Dict[str, Set[str]]) -> Set[str]:
    """Expand passed courses with equivalences."""
    expanded = set(passed)
    for code in list(passed):
        if code in equivalences:
            expanded |= equivalences[code]
    return expanded


def _check_category(required_courses: list, passed: Set[str],
                    alternative_groups: List[AlternativeGroup]) -> List[str]:
    """Check which required courses are missing, respecting alternative groups."""
    missing = []
    alt_map: Dict[str, AlternativeGroup] = {}
    for ag in alternative_groups:
        for opt in ag.options:
            alt_map[opt] = ag

    checked_groups: Set[int] = set()

    for cr in required_courses:
        code = cr.code

        if code in alt_map:
            ag = alt_map[code]
            group_id = id(ag)
            if group_id in checked_groups:
                continue
            checked_groups.add(group_id)

            if any(opt in passed for opt in ag.options):
                continue
            missing.append(f"{'/'.join(ag.options)}")
        else:
            if code not in passed:
                missing.append(code)

    return missing


def _detect_minor(program_info: ProgramInfo,
                  passed: Set[str],
                  explicit: Optional[str] = None
                  ) -> Optional[MinorInfo]:
    """Detect which minor the student is pursuing.

    If *explicit* is given, match by name; otherwise pick the minor with the
    most matching courses in the transcript.
    """
    if not program_info.minors:
        return None

    if explicit:
        for m in program_info.minors:
            if m.name.upper() == explicit.upper():
                return m
        return None

    best: Optional[MinorInfo] = None
    best_count = 0
    for m in program_info.minors:
        all_minor = set(m.required_courses) | set(m.elective_courses)
        count = len(all_minor & passed)
        if count > best_count:
            best = m
            best_count = count
    return best if best_count > 0 else None


def _evaluate_minor(minor: MinorInfo, passed: Set[str]
                    ) -> Tuple[List[str], List[str], bool, List[str]]:
    """Return (courses_taken, courses_missing, prereqs_met, prereqs_missing)."""
    taken: List[str] = []
    missing: List[str] = []

    for c in minor.required_courses:
        if c in passed:
            taken.append(c)
        else:
            missing.append(c)

    elec_taken = [c for c in minor.elective_courses if c in passed]
    taken.extend(elec_taken)
    elec_still_needed = max(0, minor.elective_pick_count - len(elec_taken))

    if elec_still_needed > 0:
        remaining = [c for c in minor.elective_courses if c not in passed]
        for c in remaining[:elec_still_needed]:
            missing.append(c)

    if minor.elective_pick_count > 0 and not minor.elective_courses:
        prefix = minor.name[:3].upper()
        any_extra = [c for c in passed
                     if c.startswith(prefix) and c not in minor.required_courses]
        if not any_extra:
            missing.append(f"1 additional {minor.name} course")

    prereqs_missing = sorted(minor.prerequisites - passed)
    prereqs_met = len(prereqs_missing) == 0

    return taken, missing, prereqs_met, prereqs_missing


def _detect_concentration(records: List[CourseRecord],
                          program_info: ProgramInfo,
                          passed: Set[str],
                          explicit: Optional[str] = None
                          ) -> Tuple[str, str, float]:
    """Detect BBA concentration and compute concentration CGPA.

    Returns (concentration_name, concentration_alias, concentration_cgpa).
    """
    if not program_info.concentrations:
        return "", "", 0.0

    if explicit:
        for conc in program_info.concentrations:
            if conc.alias.upper() == explicit.upper() or conc.name.upper() == explicit.upper():
                conc_courses = set(conc.courses) & passed
                cgpa = compute_major_cgpa(records, conc_courses)
                return conc.name, conc.alias, cgpa

    best_name, best_alias, best_count = "", "", 0
    for conc in program_info.concentrations:
        count = len(set(conc.courses) & passed)
        if count > best_count:
            best_name = conc.name
            best_alias = conc.alias
            best_count = count

    if best_name:
        for conc in program_info.concentrations:
            if conc.name == best_name:
                conc_courses = set(conc.courses) & passed
                cgpa = compute_major_cgpa(records, conc_courses)
                return best_name, best_alias, cgpa

    return "", "", 0.0


def run_audit(records: List[CourseRecord],
              program_info: ProgramInfo,
              waivers: Set[str],
              equivalences: Dict[str, Set[str]],
              concentration: Optional[str] = None,
              minor: Optional[str] = None) -> AuditResult:
    """Run a full graduation audit."""
    passed_raw = get_passed_courses(records)
    passed = _expand_passed(passed_raw, equivalences)

    cgpa, gpa_credits, grade_points = compute_cgpa_simple(records, waivers)

    major_codes = {cr.code for cr in program_info.major_core}
    major_cgpa = compute_major_cgpa(records, major_codes, waivers)

    conc_name, conc_alias, conc_cgpa = _detect_concentration(
        records, program_info, passed, concentration
    )

    best = get_best_records(records)
    credits_earned = sum(r.credits for r in best.values() if r.is_passing and r.credits > 0)
    transcript_codes = {r.course_code for r in records if r.is_passing}
    w_bonus = waiver_credit_bonus(waivers, program_info, transcript_codes)
    credits_completed = credits_earned + w_bonus
    credits_required = compute_adjusted_credits(program_info, waivers)

    deficiencies = DeficiencyReport()
    deficiencies.missing_ged = _check_category(
        program_info.mandatory_ged, passed, program_info.alternative_groups)
    deficiencies.missing_math = _check_category(
        program_info.core_math, passed, [])
    deficiencies.missing_science = _check_category(
        program_info.core_science, passed, [])
    deficiencies.missing_business = _check_category(
        program_info.core_business, passed, [])
    deficiencies.missing_major = _check_category(
        program_info.major_core, passed, [])
    deficiencies.missing_capstone = _check_category(
        program_info.capstone, passed, [])
    deficiencies.missing_internship = _check_category(
        program_info.internship, passed, [])

    if program_info.trail_credits_required > 0:
        trail_courses_taken = 0
        for trail in program_info.trails:
            for tc in trail.courses:
                if tc in passed:
                    trail_courses_taken += 1
        needed = program_info.trail_credits_required // 3
        deficiencies.missing_trail = max(0, needed - trail_courses_taken)

    if program_info.concentration_credits_required > 0 and conc_name:
        for conc in program_info.concentrations:
            if conc.name == conc_name:
                taken = len(set(conc.courses) & passed)
                needed = program_info.concentration_credits_required // 3
                deficiencies.missing_concentration = max(0, needed - taken)

    if program_info.open_elective_credits > 0:
        all_required = program_info.all_required_codes()
        trail_codes: Set[str] = set()
        for t in program_info.trails:
            trail_codes.update(t.courses)
        conc_codes: Set[str] = set()
        for c in program_info.concentrations:
            conc_codes.update(c.courses)

        open_count = 0
        for code in passed_raw:
            if code not in all_required and code not in trail_codes and code not in conc_codes:
                br = best.get(code)
                if br and br.credits > 0:
                    open_count += 1

        needed = program_info.open_elective_credits // 3
        deficiencies.missing_open_elective = max(0, needed - open_count)

    prereq_violations = check_prerequisites(records, program_info, equivalences)

    failed_courses = []
    for code, r in best.items():
        if r.grade.upper() == "F":
            failed_courses.append(code)

    reasons: List[str] = []
    eligible = True

    if credits_completed < credits_required:
        eligible = False
        gap = credits_required - credits_completed
        reasons.append(f"Need {gap:.1f} more credits ({credits_completed:.1f}/{credits_required})")

    if cgpa < program_info.min_cgpa:
        eligible = False
        reasons.append(f"CGPA {cgpa:.2f} below minimum {program_info.min_cgpa:.2f}")

    if deficiencies.has_missing:
        eligible = False
        reasons.append(f"{deficiencies.total_missing} missing course(s)")

    if program_info.concentration_min_cgpa > 0 and conc_name:
        if conc_cgpa < program_info.concentration_min_cgpa:
            eligible = False
            reasons.append(
                f"Concentration CGPA {conc_cgpa:.2f} below minimum "
                f"{program_info.concentration_min_cgpa:.2f}"
            )

    minor_name = ""
    minor_completed = False
    minor_taken: List[str] = []
    minor_missing: List[str] = []
    minor_prereqs_met = True
    minor_prereqs_missing: List[str] = []

    detected_minor = _detect_minor(program_info, passed, minor)
    if detected_minor:
        minor_name = detected_minor.name
        minor_taken, minor_missing, minor_prereqs_met, minor_prereqs_missing = (
            _evaluate_minor(detected_minor, passed)
        )
        minor_completed = len(minor_missing) == 0 and minor_prereqs_met

    roadmap = _build_roadmap(
        credits_completed, credits_required, cgpa, program_info.min_cgpa,
        major_cgpa, conc_cgpa, conc_name, program_info.concentration_min_cgpa,
        deficiencies, failed_courses
    )

    if detected_minor and not minor_completed:
        if minor_missing:
            roadmap.append(
                f"Complete minor ({minor_name}): {', '.join(minor_missing)}"
            )
        if minor_prereqs_missing:
            roadmap.append(
                f"Complete minor prerequisites: {', '.join(minor_prereqs_missing)}"
            )

    return AuditResult(
        program=program_info,
        credits_earned=credits_earned,
        credits_required=credits_required,
        waiver_bonus=w_bonus,
        credits_completed=credits_completed,
        cgpa=cgpa,
        gpa_credits=gpa_credits,
        grade_points=grade_points,
        major_cgpa=major_cgpa,
        concentration_cgpa=conc_cgpa,
        concentration_name=conc_name,
        deficiencies=deficiencies,
        prereq_violations=prereq_violations,
        eligible=eligible,
        reasons=reasons,
        roadmap=roadmap,
        failed_courses=failed_courses,
        minor_name=minor_name,
        minor_completed=minor_completed,
        minor_courses_taken=minor_taken,
        minor_courses_missing=minor_missing,
        minor_prereqs_met=minor_prereqs_met,
        minor_prereqs_missing=minor_prereqs_missing,
    )


def _build_roadmap(credits_completed: float, credits_required: int,
                   cgpa: float, min_cgpa: float,
                   major_cgpa: float, conc_cgpa: float,
                   conc_name: str, conc_min_cgpa: float,
                   deficiencies: DeficiencyReport,
                   failed_courses: List[str]) -> List[str]:
    """Build a prioritized graduation roadmap."""
    steps: List[str] = []

    if credits_completed < credits_required:
        gap = credits_required - credits_completed
        steps.append(f"Earn {gap:.0f} more credits to reach the {credits_required}-credit requirement")

    if cgpa < min_cgpa:
        steps.append(f"Raise CGPA from {cgpa:.2f} to at least {min_cgpa:.2f}")

    if conc_name and conc_min_cgpa > 0 and conc_cgpa < conc_min_cgpa:
        steps.append(
            f"Raise {conc_name} concentration CGPA from {conc_cgpa:.2f} to at least {conc_min_cgpa:.2f}"
        )

    category_map = [
        ("GED", deficiencies.missing_ged),
        ("Core Math/School Core", deficiencies.missing_math),
        ("Core Science", deficiencies.missing_science),
        ("Core Business", deficiencies.missing_business),
        ("Major Core", deficiencies.missing_major),
        ("Capstone", deficiencies.missing_capstone),
        ("Internship", deficiencies.missing_internship),
    ]
    for cat_name, missing_list in category_map:
        if missing_list:
            courses = ", ".join(missing_list)
            steps.append(f"Complete missing {cat_name}: {courses}")

    if deficiencies.missing_trail > 0:
        steps.append(f"Complete {deficiencies.missing_trail} more trail/elective course(s)")

    if deficiencies.missing_concentration > 0:
        steps.append(f"Complete {deficiencies.missing_concentration} more concentration course(s)")

    if deficiencies.missing_open_elective > 0:
        steps.append(f"Complete {deficiencies.missing_open_elective} more open elective course(s)")

    if failed_courses:
        steps.append(f"Retake failed courses: {', '.join(sorted(failed_courses))}")

    return steps
