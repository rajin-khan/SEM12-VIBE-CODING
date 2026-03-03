"""Parse program_knowledge.md into structured program data."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class CourseReq:
    code: str
    name: str
    credits: float
    is_non_credit_lab: bool = False


@dataclass
class AlternativeGroup:
    """A group of courses where student must choose one."""
    options: List[str]
    credits: float


@dataclass
class ConcentrationInfo:
    name: str
    alias: str
    courses: List[str]


@dataclass
class TrailInfo:
    name: str
    courses: List[str]


@dataclass
class MinorInfo:
    name: str
    total_credits: int
    required_courses: List[str] = field(default_factory=list)
    elective_courses: List[str] = field(default_factory=list)
    elective_pick_count: int = 0
    prerequisites: Set[str] = field(default_factory=set)


@dataclass
class ProgramInfo:
    full_name: str
    alias: str
    degree: str
    total_credits: int
    min_cgpa: float
    waivable: List[str] = field(default_factory=list)
    credit_adjustment: Dict[str, int] = field(default_factory=dict)

    mandatory_ged: List[CourseReq] = field(default_factory=list)
    core_math: List[CourseReq] = field(default_factory=list)
    core_science: List[CourseReq] = field(default_factory=list)
    core_business: List[CourseReq] = field(default_factory=list)
    major_core: List[CourseReq] = field(default_factory=list)
    capstone: List[CourseReq] = field(default_factory=list)
    internship: List[CourseReq] = field(default_factory=list)

    alternative_groups: List[AlternativeGroup] = field(default_factory=list)
    trails: List[TrailInfo] = field(default_factory=list)
    trail_credits_required: int = 0
    concentrations: List[ConcentrationInfo] = field(default_factory=list)
    concentration_credits_required: int = 0
    concentration_min_cgpa: float = 0.0
    open_elective_credits: int = 0
    non_credit_labs: List[str] = field(default_factory=list)

    minors: List[MinorInfo] = field(default_factory=list)

    prerequisites: Dict[str, List[str]] = field(default_factory=dict)
    credit_prerequisites: Dict[str, int] = field(default_factory=dict)

    def all_required_codes(self) -> Set[str]:
        codes: Set[str] = set()
        for lst in [self.mandatory_ged, self.core_math, self.core_science,
                     self.core_business, self.major_core, self.capstone,
                     self.internship]:
            for cr in lst:
                codes.add(cr.code)
        return codes

    def all_required_with_credits(self) -> List[Tuple[str, float]]:
        result = []
        for lst in [self.mandatory_ged, self.core_math, self.core_science,
                     self.core_business, self.major_core, self.capstone,
                     self.internship]:
            for cr in lst:
                result.append((cr.code, cr.credits))
        return result


PROGRAM_ALIASES = {
    "CSE": "Computer Science & Engineering",
    "EEE": "Electrical & Electronic Engineering",
    "ETE": "Electronic & Telecom Engineering",
    "CEE": "Civil & Environmental Engineering",
    "ENV": "Environmental Science & Management",
    "ENG": "English",
    "BBA": "Business Administration",
    "ECO": "Economics",
}


def resolve_program_name(name: str) -> str:
    upper = name.strip().upper()
    if upper in PROGRAM_ALIASES:
        return PROGRAM_ALIASES[upper]
    for alias, full in PROGRAM_ALIASES.items():
        if full.lower() == name.strip().lower():
            return full
    return name.strip()


def _parse_course_line(line: str) -> Optional[CourseReq]:
    """Parse a line like '- CSE115: Programming Language I (3 credits)'."""
    m = re.match(
        r"^-\s+([A-Z]{2,4}\d{3}[A-Z]?)(?:/[A-Z]{2,4}\d{3}[A-Z]?)*"
        r":\s+(.+?)\s+\((\d+\.?\d*)\s+credits?\)",
        line.strip()
    )
    if m:
        code = m.group(1)
        name = m.group(2)
        credits = float(m.group(3))
        return CourseReq(code=code, name=name, credits=credits)

    m2 = re.match(
        r"^-\s+([A-Z]{2,4}\d{3}[A-Z]?):\s+(.+?)\s+\((\d+\.?\d*)\s+credits?\)",
        line.strip()
    )
    if m2:
        return CourseReq(code=m2.group(1), name=m2.group(2), credits=float(m2.group(3)))
    return None


def _parse_alternative_line(line: str) -> Optional[AlternativeGroup]:
    """Parse '- POL101/POL104: ... (3 credits) [Choose one]'."""
    m = re.match(
        r"^-\s+((?:[A-Z]{2,4}\d{3}[A-Z]?)(?:/[A-Z]{2,4}\d{3}[A-Z]?)+)"
        r":\s+.+?\s+\((\d+\.?\d*)\s+credits?\)\s+\[Choose one\]",
        line.strip()
    )
    if m:
        codes = m.group(1).split("/")
        credits = float(m.group(2))
        return AlternativeGroup(options=codes, credits=credits)
    return None


def _parse_prerequisite_line(line: str) -> Optional[Tuple[str, List[str]]]:
    """Parse '- CSE173 -> CSE115' or '- PHY108 -> MAT130, PHY107'
    or '- CSE299 -> 60 credits'."""
    m = re.match(
        r"^-\s+([A-Z]{2,4}\d{3}[A-Z]?)\s*->\s*(.+)$",
        line.strip()
    )
    if not m:
        return None
    course = m.group(1)
    rhs = m.group(2).strip()

    credit_m = re.match(r"^(\d+)\s+credits?$", rhs)
    if credit_m:
        return (course, [f"_CREDITS_{credit_m.group(1)}"])

    prereqs = [p.strip() for p in rhs.split(",")]
    return (course, prereqs)


def load_nsu_course_list(md_path: str) -> Set[str]:
    """Extract the master course list from program_knowledge.md."""
    text = Path(md_path).read_text(encoding="utf-8")
    courses: Set[str] = set()

    in_section = False
    for line in text.split("\n"):
        if "# NSU Course List" in line:
            in_section = True
            continue
        if in_section:
            if line.startswith("#") or line.startswith("---"):
                break
            for m in re.finditer(r'"([A-Z]{2,4}\d{3}[A-Z]?)"', line):
                courses.add(m.group(1))
            for m in re.finditer(r'"([A-Z]{2,4}\d{3}[A-Z]?)/([A-Z]{2,4}\d{3}[A-Z]?)"', line):
                courses.add(m.group(1))
                courses.add(m.group(2))

    return courses


def load_equivalences(md_path: str) -> Dict[str, Set[str]]:
    """Load course equivalence groups. Returns mapping: code -> set of equivalent codes."""
    text = Path(md_path).read_text(encoding="utf-8")
    equiv: Dict[str, Set[str]] = {}

    in_section = False
    for line in text.split("\n"):
        if "# Course Equivalences" in line:
            in_section = True
            continue
        if in_section:
            if line.startswith("#") or line.startswith("---"):
                break
            m = re.match(r"^-\s+((?:[A-Z]{2,4}\d{3}[A-Z]?)(?:\s*/\s*[A-Z]{2,4}\d{3}[A-Z]?)+)", line.strip())
            if m:
                codes = [c.strip() for c in m.group(1).split("/")]
                code_set = set(codes)
                for c in codes:
                    if c in equiv:
                        code_set |= equiv[c]
                for c in code_set:
                    equiv[c] = code_set

    return equiv


def load_program(md_path: str, program_name: str) -> Optional[ProgramInfo]:
    """Load a specific program's info from the knowledge file."""
    resolved = resolve_program_name(program_name)
    text = Path(md_path).read_text(encoding="utf-8")
    lines = text.split("\n")

    info: Optional[ProgramInfo] = None
    current_section: Optional[str] = None
    current_trail_name: Optional[str] = None
    in_target = False
    reading_prereqs = False
    reading_ncl = False
    reading_concentrations = False
    reading_minors = False
    current_concentration: Optional[str] = None
    current_concentration_alias: Optional[str] = None
    current_minor: Optional[MinorInfo] = None

    for line in lines:
        stripped = line.strip()

        program_m = re.match(r"^## \[Program:\s*(.+?)\]", stripped)
        if program_m:
            if in_target:
                break
            if program_m.group(1).strip() == resolved:
                in_target = True
                info = ProgramInfo(
                    full_name=resolved,
                    alias=program_name.strip().upper(),
                    degree="",
                    total_credits=0,
                    min_cgpa=2.0,
                )
            continue

        if not in_target or info is None:
            continue

        if stripped.startswith("- **Alias**:"):
            info.alias = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("- **Degree**:"):
            info.degree = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("- **Total Credits Required**:"):
            m = re.search(r"(\d+)", stripped)
            if m:
                info.total_credits = int(m.group(1))
        elif stripped.startswith("- **Minimum CGPA**:"):
            m = re.search(r"([\d.]+)", stripped.split(":", 2)[-1])
            if m:
                info.min_cgpa = float(m.group(1))
        elif stripped.startswith("- **Waivable Courses**:"):
            codes = re.findall(r"([A-Z]{2,4}\d{3}[A-Z]?)", stripped.split(":", 1)[1])
            info.waivable = codes
        elif stripped.startswith("- **Credit Adjustment**:"):
            pass

        if re.match(r"^###\s+", stripped):
            reading_prereqs = False
            reading_ncl = False
            reading_concentrations = False
            reading_minors = False
            current_trail_name = None
            current_concentration = None
            current_minor = None

            section_name = stripped.lstrip("#").strip().lower()

            if "mandatory ged" in section_name:
                current_section = "ged"
            elif "school core" in section_name:
                current_section = "math"
            elif "core math" in section_name:
                current_section = "math"
            elif "core science" in section_name:
                current_section = "science"
            elif "core business" in section_name:
                current_section = "business"
            elif "major core" in section_name:
                current_section = "major"
            elif "capstone" in section_name:
                current_section = "capstone"
            elif "internship" in section_name:
                current_section = "internship"
            elif "trail" in section_name:
                current_section = "trails"
                m = re.search(r"\((\d+)\s+credits", section_name)
                if m:
                    info.trail_credits_required = int(m.group(1))
                elif not info.trail_credits_required:
                    info.trail_credits_required = 9
            elif "open elective" in section_name:
                current_section = "open_elective"
                m = re.search(r"\((\d+)\s+credits", section_name)
                if m:
                    info.open_elective_credits = int(m.group(1))
                elif not info.open_elective_credits:
                    info.open_elective_credits = 3
            elif "prerequisite" in section_name:
                current_section = "prereqs"
                reading_prereqs = True
            elif "non-credit lab" in section_name or "non credit lab" in section_name:
                current_section = "ncl"
                reading_ncl = True
            elif "concentration" in section_name:
                current_section = "concentrations"
                reading_concentrations = True
                m = re.search(r"\((\d+)\s+credits", section_name)
                if m:
                    info.concentration_credits_required = int(m.group(1))
                elif not info.concentration_credits_required:
                    info.concentration_credits_required = 18
            elif "minor" in section_name:
                current_section = "minor"
                reading_minors = True
            else:
                current_section = None
            continue

        if current_section == "trails":
            trail_header = re.match(r"^\*\*(.+?):\*\*", stripped)
            if trail_header:
                current_trail_name = trail_header.group(1).strip()
                info.trails.append(TrailInfo(name=current_trail_name, courses=[]))
                continue
            cr = _parse_course_line(stripped)
            if cr and current_trail_name and info.trails:
                info.trails[-1].courses.append(cr.code)

        elif current_section == "concentrations" and reading_concentrations:
            conc_header = re.match(r"^\*\*(.+?)\s*\(([A-Z]{2,4})\):\*\*", stripped)
            if conc_header:
                current_concentration = conc_header.group(1).strip()
                current_concentration_alias = conc_header.group(2).strip()
                info.concentrations.append(ConcentrationInfo(
                    name=current_concentration,
                    alias=current_concentration_alias,
                    courses=[]
                ))
                continue
            if current_concentration and info.concentrations:
                for code in re.findall(r"([A-Z]{2,4}\d{3}[A-Z]?)", stripped):
                    if stripped.startswith("-") or stripped.startswith("*"):
                        info.concentrations[-1].courses.append(code)
            if "concentration cgpa" in stripped.lower() or "minimum" in stripped.lower():
                m = re.search(r"([\d.]+)", stripped.split(":")[-1])
                if m:
                    info.concentration_min_cgpa = float(m.group(1))

        elif reading_minors and current_section == "minor":
            minor_header = re.match(
                r"\*\*Minor in (\w+)\s*\((\d+)\s+Credits?\):\*\*", stripped
            )
            if minor_header:
                current_minor = MinorInfo(
                    name=minor_header.group(1).strip(),
                    total_credits=int(minor_header.group(2)),
                )
                info.minors.append(current_minor)
                continue
            if current_minor and stripped.startswith("-"):
                lower = stripped.lower()
                if "non-engineering" in lower:
                    pass
                elif "engineering students:" in lower:
                    pick_m = re.search(r"(\d+)\s+additional\s+courses?", lower)
                    if pick_m:
                        current_minor.elective_pick_count = int(pick_m.group(1))
                    codes = re.findall(r"([A-Z]{2,4}\d{3}[A-Z]?)", stripped)
                    current_minor.elective_courses = codes
                elif lower.lstrip("- ").startswith("required:"):
                    codes = re.findall(r"([A-Z]{2,4}\d{3}[A-Z]?)", stripped)
                    current_minor.required_courses = codes
                elif lower.lstrip("- ").startswith("elective:"):
                    pick_m = re.search(r"(\d+)\s+additional", lower)
                    if pick_m and current_minor.elective_pick_count == 0:
                        current_minor.elective_pick_count = int(pick_m.group(1))
                elif lower.lstrip("- ").startswith("prerequisites:"):
                    codes = re.findall(r"([A-Z]{2,4}\d{3}[A-Z]?)", stripped)
                    current_minor.prerequisites = set(codes)

        elif reading_prereqs:
            parsed = _parse_prerequisite_line(stripped)
            if parsed:
                course, prereqs = parsed
                credit_reqs = [p for p in prereqs if p.startswith("_CREDITS_")]
                course_reqs = [p for p in prereqs if not p.startswith("_CREDITS_")]
                if credit_reqs:
                    credits_needed = int(credit_reqs[0].replace("_CREDITS_", ""))
                    info.credit_prerequisites[course] = credits_needed
                if course_reqs:
                    info.prerequisites[course] = course_reqs

        elif reading_ncl:
            for code in re.findall(r"([A-Z]{2,4}\d{3}[A-Z]?)", stripped):
                if code not in info.non_credit_labs:
                    info.non_credit_labs.append(code)
        else:
            alt = _parse_alternative_line(stripped)
            if alt:
                info.alternative_groups.append(alt)
                first_code = alt.options[0]
                cr = CourseReq(code=first_code, name="", credits=alt.credits)
                if current_section == "ged":
                    info.mandatory_ged.append(cr)
                continue

            cr = _parse_course_line(stripped)
            if cr:
                ncl_tag = "[Non-Credit Lab]" in stripped or "[non-credit lab]" in stripped.lower()
                if ncl_tag:
                    cr.is_non_credit_lab = True
                    if cr.code not in info.non_credit_labs:
                        info.non_credit_labs.append(cr.code)

                if current_section == "ged":
                    info.mandatory_ged.append(cr)
                elif current_section == "math":
                    info.core_math.append(cr)
                elif current_section == "science":
                    info.core_science.append(cr)
                elif current_section == "business":
                    info.core_business.append(cr)
                elif current_section == "major":
                    info.major_core.append(cr)
                elif current_section == "capstone":
                    info.capstone.append(cr)
                elif current_section == "internship":
                    info.internship.append(cr)

        if "credit adjustment" in stripped.lower() or (
            re.match(r"^\s*-\s+(Both|One|None)\s+waived", stripped)
        ):
            ca_m = re.match(r"^\s*-\s+(Both|One|None)\s+waived:\s*(\d+)", stripped)
            if ca_m:
                info.credit_adjustment[ca_m.group(1).lower()] = int(ca_m.group(2))

        if "concentration cgpa minimum" in stripped.lower() or "concentration cgpa" in stripped.lower():
            m = re.search(r"([\d.]+)", stripped.split(":")[-1])
            if m:
                info.concentration_min_cgpa = float(m.group(1))

    return info


def load_all_programs(md_path: str) -> Dict[str, ProgramInfo]:
    """Load all programs from the knowledge file."""
    programs: Dict[str, ProgramInfo] = {}
    text = Path(md_path).read_text(encoding="utf-8")
    for m in re.finditer(r"## \[Program:\s*(.+?)\]", text):
        name = m.group(1).strip()
        info = load_program(md_path, name)
        if info:
            programs[info.alias] = info
    return programs
