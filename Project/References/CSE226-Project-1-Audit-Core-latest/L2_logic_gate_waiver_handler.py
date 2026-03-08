#!/usr/bin/env python3
"""
L2 Logic Gate & Waiver Handler
Step 2 of 3: Calculate CGPA with waiver support.
"""

import argparse
import csv
import math
import os
import re
import sys
from collections import defaultdict


# ---------------------------------------------------------------------------
# Program name resolution  (shared with L1)
# ---------------------------------------------------------------------------

PROGRAM_ALIASES = {
    "Computer Science": [
        "computer science", "computer science engineering",
        "computer science and engineering", "cse", "cs", "computer",
        "bsc cse", "b.sc cse", "bsc computer science", "b.sc. computer science",
    ],
    "Microbiology": [
        "microbiology", "mic", "micro", "bsc microbiology",
        "b.sc microbiology", "b.sc. microbiology", "microbio",
    ],
    "Architecture": ["architecture", "arc", "arch"],
    "Civil and Environmental Engineering": [
        "civil and environmental engineering", "civil & environmental engineering",
        "cee", "civil engineering", "environmental engineering", "civil",
    ],
    "Electrical and Electronic Engineering": [
        "electrical and electronic engineering", "electrical & electronic engineering",
        "eee", "electrical engineering", "electrical",
    ],
    "Electronic and Telecom Engineering": [
        "electronic and telecom engineering", "electronic & telecom engineering",
        "ete", "telecom engineering", "telecom",
    ],
    "Biochemistry and Biotechnology": [
        "biochemistry and biotechnology", "biochemistry & biotechnology",
        "bbt", "biochemistry", "biotechnology",
    ],
    "Environmental Science and Management": [
        "environmental science and management", "environmental science & management",
        "env", "environmental science", "esm",
    ],
    "Public Health": ["public health", "pbh", "ph"],
    "BPharm": ["bpharm", "pharmacy", "phr", "b.pharm"],
    "BBA Accounting": ["bba accounting", "accounting", "act", "bba acc"],
    "BBA Economics": ["bba economics", "economics", "eco", "bba eco"],
    "BBA Entrepreneurship": ["bba entrepreneurship", "entrepreneurship", "ent"],
    "BBA Finance": ["bba finance", "finance", "fin"],
    "BBA Human Resource and Management": [
        "bba human resource and management", "human resource", "hrm",
        "bba hrm", "human resource management",
    ],
    "BBA International Business": [
        "bba international business", "international business", "inb",
    ],
    "BBA Management": ["bba management", "management", "mgt", "bba mgt"],
    "BBA Management Information System": [
        "bba management information system", "management information system",
        "mis", "bba mis",
    ],
    "BBA Marketing": ["bba marketing", "marketing", "mkt"],
    "BBA Supply Chain Management": [
        "bba supply chain management", "supply chain management", "scm",
        "supply chain",
    ],
    "BBA General": ["bba general", "bba", "bba gen"],
    "Economics": ["economics (ba)", "ba economics"],
    "English": ["english", "eng", "ba english"],
    "Law": ["law", "llb", "llm"],
    "Media Communication and Journalism": [
        "media communication and journalism", "media communication & journalism",
        "mcj", "journalism", "media",
    ],
}

_ALIAS_TO_CANONICAL = {}
for _canon, _aliases in PROGRAM_ALIASES.items():
    for _alias in _aliases:
        _ALIAS_TO_CANONICAL[_alias] = _canon

# Programs that have a full course-structure section defined in the MD file.
STRUCTURED_PROGRAMS = {"Computer Science", "Microbiology"}


def resolve_program_name(program_name):
    """Resolve user-supplied name to canonical form, or None if unrecognised."""
    return _ALIAS_TO_CANONICAL.get(program_name.strip().lower())


def read_programs_offered(md_path):
    """Return set of canonical program names found in the Programs Offered section."""
    offered = set()
    if not os.path.exists(md_path):
        return offered
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        section_match = re.search(
            r'#\s+North South University\s*-\s*Programs Offered(.*?)(?=\n#[^#]|\Z)',
            content, re.IGNORECASE | re.DOTALL)
        if not section_match:
            return set(PROGRAM_ALIASES.keys())
        for line in section_match.group(1).splitlines():
            clean = re.sub(r'^[\s\-\*]+', '', line).strip()
            if clean:
                canonical = resolve_program_name(clean)
                if canonical:
                    offered.add(canonical)
                else:
                    base = re.sub(r'\s*\(.*?\)', '', clean).strip()
                    canonical = resolve_program_name(base)
                    if canonical:
                        offered.add(canonical)
    except Exception as e:
        print(f"Warning: Could not read Programs Offered section: {e}")
    return offered


def validate_program_name(program_name, md_path):
    """
    Validate program name is recognised and offered by NSU.
    Exits with an error if not. Returns canonical name on success.
    """
    canonical = resolve_program_name(program_name)
    if canonical is None:
        print(f"\n{'!'*60}")
        print(f"ERROR: NSU does not offer the program '{program_name}'.")
        print("Please check the program name and try again.")
        print("Examples of accepted names: cse, computer science, mic, microbiology,")
        print("  eee, architecture, bba, finance, law, mcj, public health, etc.")
        print(f"{'!'*60}\n")
        sys.exit(1)

    offered = read_programs_offered(md_path)
    if offered and canonical not in offered:
        print(f"\n{'!'*60}")
        print(f"ERROR: NSU does not offer the program '{program_name}'.")
        print(f"(Resolved as '{canonical}', which was not found in the Programs Offered list.)")
        print("Please check the program name and try again.")
        print(f"{'!'*60}\n")
        sys.exit(1)

    return canonical


# ---------------------------------------------------------------------------
# Legacy normalizer kept for internal use
# ---------------------------------------------------------------------------

def normalize_program_name(program_name):
    """
    Normalize to one of the two programs that have full course-structure data.
    Returns 'Computer Science', 'Microbiology', or None (GED-only fallback).
    """
    canonical = resolve_program_name(program_name)
    if canonical in ("Computer Science", "Microbiology"):
        return canonical
    return None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

def _collect_all_ged_codes(md_path, normalize_fn):
    ged_codes = set()
    if not os.path.exists(md_path):
        return ged_codes
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        for section_match in re.finditer(
                r'^#{1,3}\s+(?:GED|General Education|University Core)[^\n]*\n(.*?)(?=\n#{1,3}\s|\Z)',
                content, re.IGNORECASE | re.MULTILINE | re.DOTALL):
            for m in re.finditer(r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b',
                                  section_match.group(1)):
                ged_codes.add(normalize_fn(f"{m.group(1)}{m.group(2)}"))
    except Exception as e:
        print(f"Warning: Could not collect GED codes: {e}")
    return ged_codes


GRADE_POINTS = {
    'A': 4.0, 'A-': 3.7,
    'B+': 3.3, 'B': 3.0, 'B-': 2.7,
    'C+': 2.3, 'C': 2.0, 'C-': 1.7,
    'D+': 1.3, 'D': 1.0,
    'F': 0.0
}

NON_GRADE_ENTRIES = {'W', 'I', 'WA', 'IP', 'S', 'P', 'N', ''}

NON_CREDIT_LABS = {
    'CSE225L': 'CSE225',
    'CSE231L': 'CSE231',
    'CSE311L': 'CSE311',
    'CSE331L': 'CSE331',
    'CSE332L': 'CSE332',
}

CSE_TRAILS = {
    "Algorithms and Computation": ["CSE257", "CSE273", "CSE326", "CSE417", "CSE426", "CSE473"],
    "Software Engineering": ["CSE411"],
    "Networks": ["CSE338", "CSE422", "CSE438", "CSE482", "CSE485", "CSE486", "CSE562"],
    "Computer Architecture and VLSI": ["CSE413", "CSE414", "CSE435"],
    "Artificial Intelligence": ["CSE440", "CSE445", "CSE465", "CSE467", "CSE419", "CSE598"],
    "Bioinformatics": [],
}

MINOR_PREREQUISITES = {
    "Minor in Math": {"MAT116", "MAT120", "MAT125", "MAT130", "MAT250"},
    "Minor in Physics": {"PHY107", "PHY107L", "PHY108", "PHY108L"},
}


# ---------------------------------------------------------------------------
# Transcript & course helpers
# ---------------------------------------------------------------------------

def read_transcript(csv_path):
    courses = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                course = {
                    'code': row.get('Course_Code', '').strip(),
                    'credits': float(row.get('Credits', 0)),
                    'grade': row.get('Grade', '').strip().upper(),
                    'semester': row.get('Semester', '').strip()
                }
                course['grade_points'] = GRADE_POINTS.get(course['grade'], None)
                course['passed'] = course['grade'] in GRADE_POINTS and course['grade'] != 'F'
                courses.append(course)
    except FileNotFoundError:
        print(f"Error: Transcript file not found: {csv_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading transcript: {e}")
        sys.exit(1)
    return courses


def find_program_section(content, program_name):
    program_name_lower = program_name.lower()
    program_headers = list(re.finditer(r'^#\s+(.+?program.*)$', content, re.MULTILINE | re.IGNORECASE))
    for i, match in enumerate(program_headers):
        header = match.group(1).lower()
        is_match = False
        if program_name_lower == 'computer science':
            is_match = ('computer science' in header or 'cse' in header)
        elif program_name_lower == 'microbiology':
            is_match = 'microbiology' in header
        else:
            is_match = program_name_lower in header
        if is_match:
            start_pos = match.start()
            end_pos = program_headers[i + 1].start() if i + 1 < len(program_headers) else len(content)
            return content[start_pos:end_pos]
    return None


def normalize_course_code(code):
    return code.replace(' ', '').replace('-', '').upper()


def read_nsu_course_list(md_path):
    nsu_courses = set()
    if not os.path.exists(md_path):
        return nsu_courses
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        section_match = re.search(
            r'##\s+NSU Offered Course List(.*?)(?=\n#[^#]|\Z)',
            content, re.IGNORECASE | re.DOTALL)
        if not section_match:
            return nsu_courses
        section_text = section_match.group(1)
        quoted = re.findall(r'"([^"]+)"', section_text)
        for entry in quoted:
            for part in entry.split('/'):
                code = normalize_course_code(part.strip())
                if code:
                    nsu_courses.add(code)
        for m in re.finditer(r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b', section_text):
            nsu_courses.add(f"{m.group(1).upper()}{m.group(2).upper()}")
    except Exception as e:
        print(f"Warning: Could not read NSU course list: {e}")
    return nsu_courses


def check_non_nsu_courses(courses, nsu_course_list):
    """
    Check for unrecognised courses. Prompts about transfer student status.
    Returns (is_transfer: bool, non_nsu_codes: set).
    """
    if not nsu_course_list:
        return False, set()

    non_nsu = []
    for course in courses:
        code = normalize_course_code(course['code'])
        if code and code not in nsu_course_list:
            non_nsu.append(course['code'])

    if not non_nsu:
        return False, set()

    print(f"\n{'!'*60}")
    print("WARNING: This transcript contains course(s) not in the NSU offered course list.")
    print("The following course(s) were not recognised:")
    for c in non_nsu:
        print(f"  - {c}")
    print(f"{'!'*60}")

    try:
        answer = input("\nIs this student a transfer student from a different university? (y/n): ").strip().lower()
    except EOFError:
        answer = 'n'

    if answer in ('y', 'yes'):
        print("\nTransfer student confirmed.")
        print("Unrecognised courses will be placed in the 'Not Counted / Excluded' section.")
        non_nsu_codes = {normalize_course_code(c) for c in non_nsu}
        return True, non_nsu_codes
    else:
        print(f"\n{'!'*60}")
        print("ERROR: This transcript may not belong to an NSU student.")
        print("Processing stopped. Please verify the transcript and try again.")
        print(f"{'!'*60}\n")
        sys.exit(1)


def get_program_courses(md_path, program_name):
    program_courses = set()
    if not os.path.exists(md_path):
        return program_courses
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        program_section = find_program_section(content, program_name)
        if not program_section:
            return program_courses
        for match in re.finditer(r'\b([A-Z]{2,})\s*(\d{3,4}[A-Z]?)\b', program_section):
            dept = match.group(1).upper()
            num = match.group(2).upper()
            course_code = f"{dept}{num}"
            if len(dept) >= 2 and len(num) >= 3:
                program_courses.add(course_code)
    except Exception as e:
        print(f"Warning: Error reading program courses: {e}")
    return program_courses


def find_waivable_courses(md_path, program_name):
    waivable = []
    if not os.path.exists(md_path):
        return waivable
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        program_section = find_program_section(content, program_name)
        if not program_section:
            return waivable
        for line in program_section.split('\n'):
            line_clean = line.replace('_', '').replace('*', '')
            if 'waiv' in line_clean.lower() and '|' in line:
                matches = re.findall(r'\b([A-Z]{2,})\s*(\d{3,})\b', line_clean, re.IGNORECASE)
                for dept, num in matches:
                    if len(dept) >= 2:
                        course_code = f"{dept.upper()}{num}"
                        if course_code not in waivable:
                            waivable.append(course_code)
    except Exception as e:
        print(f"Warning: Error finding waivable courses: {e}")
    return waivable


def get_program_info(md_path, program_name):
    program_info = {
        'allowed_courses': set(),
        'capstone_courses': set(),   # internship/capstone — never open electives
        'major_elective_credits': 0,
        'major_elective_courses': set(),
        'open_elective_credits': 0,
        'elective_credits': 0,
        'elective_courses': set(),
        'waivable_courses': [],
        'alternative_courses': [],
        'not_mandatory_courses': set()
    }

    if not os.path.exists(md_path):
        return program_info

    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        program_section = find_program_section(content, program_name)
        if not program_section:
            return program_info

        for match in re.finditer(r'\b([A-Z]{2,})\s*(\d{3,4}[A-Z]?)\b', program_section):
            dept = match.group(1).upper()
            num = match.group(2).upper()
            course_code = f"{dept}{num}"
            if len(dept) >= 2 and len(num) >= 3:
                program_info['allowed_courses'].add(course_code)

        # Parse capstone / internship codes — from section headings and from
        # the global annotation block in the NSU course list area.
        for cap_match in re.finditer(
                r'^#{1,3}\s+(?:Capstone|Internship|Research)[^\n]*\n(.*?)(?=\n#{1,3}\s|\Z)',
                program_section, re.IGNORECASE | re.MULTILINE | re.DOTALL):
            for m in re.finditer(r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b', cap_match.group(1)):
                program_info['capstone_courses'].add(normalize_course_code(f"{m.group(1)}{m.group(2)}"))
        for cap_block in re.finditer(r'_Capstone[^_\n]*_\s*\n(.*?)(?=\n_|\n\n|\Z)',
                                     content, re.IGNORECASE | re.DOTALL):
            for entry in re.findall(r'"([^"]+)"', cap_block.group(1)):
                for part in entry.split('/'):
                    program_info['capstone_courses'].add(normalize_course_code(part.strip()))
        # Capstone codes remain in allowed_courses so letter-graded capstones
        # count toward CGPA through the normal counting path.

        major_match = re.search(r'^#{1,3}\s+.*?Major Electives.*?Trail Courses.*?\((\d+)\s*Credits?\)',
                                program_section, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if major_match:
            program_info['major_elective_credits'] = int(major_match.group(1))
            # Read from the global trail table (new structured format with prerequisites)
            trail_section = re.search(
                r'##\s+Major Electives\s*-\s*Trail Courses.*?(?=\n##[^#]|\Z)',
                content, re.IGNORECASE | re.DOTALL)
            if trail_section:
                for line in trail_section.group(0).splitlines():
                    if '|' not in line:
                        continue
                    clean = line.replace('**', '').strip().strip('|')
                    cols = [c.strip() for c in clean.split('|')]
                    if len(cols) < 2:
                        continue
                    course_cell = cols[0]
                    if re.match(r'^[-\s]+$', course_cell.replace('|', '')):
                        continue
                    if re.search(r'course', course_cell, re.IGNORECASE):
                        continue
                    for part in re.split(r'[/,]', course_cell):
                        m = re.match(r'^\s*([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\s*$', part.strip())
                        if m:
                            program_info['major_elective_courses'].add(
                                normalize_course_code(f"{m.group(1)}{m.group(2)}"))

        open_match = re.search(r'^#{1,3}\s+.*?(Open Elective|Free Elective).*?\((\d+)\s*Credits?\)',
                               program_section, re.IGNORECASE | re.MULTILINE)
        if open_match:
            program_info['open_elective_credits'] = int(open_match.group(2))

        elective_match = re.search(r'^#{1,3}\s+Electives.*?\((\d+)\s*Credits?\)',
                                   program_section, re.IGNORECASE | re.MULTILINE)
        if elective_match:
            program_info['elective_credits'] = int(elective_match.group(1))
            elective_section = re.search(r'##\s+Electives.*?(?=##|\Z)', program_section, re.IGNORECASE | re.DOTALL)
            if elective_section:
                elective_str = elective_section.group(0)
                table_rows = re.findall(r'^\|\s*([A-Z]{2,})\s*(\d{3,4}[A-Z]?)\s*\|', elective_str, re.MULTILINE | re.IGNORECASE)
                for dept, num in table_rows:
                    program_info['elective_courses'].add(f"{dept.upper()}{num.upper()}")

        alternative_groups = []
        if program_name.lower() in ('microbiology', 'mic'):
            university_core_section_match = re.search(
                r'##\s+University Core.*?(?=\n##[^#]|\Z)', program_section, re.IGNORECASE | re.DOTALL)
            if university_core_section_match:
                university_core_content = university_core_section_match.group(0)
                uc_clean = university_core_content.replace('**', '')
                subsections = re.split(r'(?=\n###\s)', uc_clean)

                # Identify subsections covered by _Choose one_ for Pass 1 exclusion
                choose_one_subs = [s for s in subsections if re.search(r'\n\s*_[Cc]hoose one', s)]

                for sub in subsections:
                    sub = sub.strip()
                    has_block_choose_one = bool(re.search(r'\n\s*_[Cc]hoose one', sub))
                    if has_block_choose_one:
                        # Science section handled separately by Pass 3
                        if re.search(r'###\s+Science', sub, re.IGNORECASE):
                            continue
                        # Read ONLY the first column of each table row to avoid
                        # picking up course codes from Prerequisites columns
                        table_match = re.search(r'(\|.*?)(?=\n\s*_[Cc]hoose one)', sub, re.DOTALL)
                        if table_match:
                            group = []
                            for line in table_match.group(1).splitlines():
                                if '|' not in line:
                                    continue
                                first_col = line.strip().strip('|').split('|')[0].strip()
                                if re.match(r'^[-\s]+$', first_col) or first_col.lower() in ('course', ''):
                                    continue
                                for dept, num in re.findall(
                                        r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b', first_col):
                                    code = f"{dept.upper()}{num.upper()}"
                                    if code not in group:
                                        group.append(code)
                            if len(group) >= 2:
                                if sorted(group) not in [sorted(g) for g in alternative_groups]:
                                    alternative_groups.append(group)
                        continue
                    # Per-row "Choose one" — skip rows inside a _Choose one_ section
                    for row_match in re.finditer(
                            r'^\|\s*([^|]+?)\s*\|(?:[^|\n]*\|)*\s*[Cc]hoose one\s*\|?',
                            sub, re.MULTILINE):
                        row_text = row_match.group(0)
                        if any(row_text in cs for cs in choose_one_subs):
                            continue
                        course_cell = row_match.group(1).strip()
                        codes_in_cell = re.findall(
                            r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b', course_cell)
                        if len(codes_in_cell) >= 2:
                            group = []
                            for dept, num in codes_in_cell:
                                code = f"{dept.upper()}{num.upper()}"
                                if code not in group:
                                    group.append(code)
                            if len(group) >= 2:
                                if sorted(group) not in [sorted(g) for g in alternative_groups]:
                                    alternative_groups.append(group)

                # Pass 3: Science section — group rows by Option column (A/B)
                sci_sec = re.search(
                    r'###\s+Science.*?(?=\n###|\n##[^#]|\Z)', uc_clean,
                    re.IGNORECASE | re.DOTALL)
                if sci_sec and re.search(r'[Cc]hoose one pair', sci_sec.group(0)):
                    options = {}
                    for line in sci_sec.group(0).splitlines():
                        if '|' not in line:
                            continue
                        cols = [c.strip() for c in line.strip().strip('|').split('|')]
                        if len(cols) < 3:
                            continue
                        course_cell, _, option_cell = cols[0], cols[1], cols[2]
                        m = re.match(r'^\s*([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\s*$', course_cell)
                        opt = option_cell.strip().upper()
                        if m and opt and opt not in ('-', ''):
                            code = normalize_course_code(f"{m.group(1)}{m.group(2)}")
                            options.setdefault(opt, []).append(code)
                    if len(options) >= 2:
                        all_sci = []
                        for codes_in_opt in options.values():
                            all_sci.extend(codes_in_opt)
                        if len(all_sci) >= 2 and sorted(all_sci) not in [sorted(g) for g in alternative_groups]:
                            alternative_groups.append(all_sci)
        else:
            for row_match in re.finditer(
                    r'^\|\s*([^|]+?)\s*\|(?:[^|\n]*\|)+\s*[Cc]hoose one[^|\n]*\|?',
                    program_section, re.MULTILINE):
                course_cell = row_match.group(1).strip()
                codes_in_cell = re.findall(
                    r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b', course_cell)
                if len(codes_in_cell) >= 2:
                    group = []
                    for dept, num in codes_in_cell:
                        code = f"{dept.upper()}{num.upper()}"
                        if code not in group:
                            group.append(code)
                    if len(group) >= 2:
                        sorted_new_group = sorted(group)
                        if sorted_new_group not in [sorted(g) for g in alternative_groups]:
                            alternative_groups.append(group)

        processed_groups = []
        for group in alternative_groups:
            lab_codes = [c for c in group if c.endswith('L')]
            theory_codes = [c for c in group if not c.endswith('L')]
            if lab_codes and theory_codes and len(group) > 2:
                paired = {}
                for lab in lab_codes:
                    base = lab[:-1]
                    if base in theory_codes:
                        paired[base] = lab
                if paired and len(paired) >= 2:
                    processed_groups.append(group)
                    if 'lab_pairs' not in program_info:
                        program_info['lab_pairs'] = {}
                    for theory, lab in paired.items():
                        program_info['lab_pairs'][theory] = lab
                        program_info['lab_pairs'][lab] = theory
                    continue
            processed_groups.append(group)
        alternative_groups = processed_groups
        program_info['alternative_courses'] = alternative_groups

        # ── Remove prereq-only codes from allowed_courses ──────────────────
        # The global scanner picks up course codes from Prerequisites columns
        # (e.g. MAT120 for PHY107). Only remove codes that never appear as
        # the course being defined (first column of a table row).
        course_col_codes = set()
        prereq_col_codes = set()
        for line in program_section.split('\n'):
            if '|' not in line:
                continue
            cols = [c.strip() for c in line.strip().strip('|').split('|')]
            if len(cols) < 2:
                continue
            first = cols[0]
            if re.match(r'^[-\s]+$', first) or first.lower() in ('course', ''):
                continue
            for d, n in re.findall(r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b', first):
                course_col_codes.add(normalize_course_code(f"{d}{n}"))
            for i, col in enumerate(cols[1:], 1):
                if i == 1:
                    continue  # Credits column
                for d, n in re.findall(r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b', col):
                    prereq_col_codes.add(normalize_course_code(f"{d}{n}"))
        prereq_only = prereq_col_codes - course_col_codes
        program_info['allowed_courses'] = {c for c in program_info.get('allowed_courses', set())
                                           if c not in prereq_only}
        program_info['not_mandatory_courses'] -= prereq_only

        not_mandatory_matches = re.findall(r'([A-Z]{2,})\s*(\d{3,})[^\n]*Not mandatory', program_section, re.IGNORECASE)
        for dept, num in not_mandatory_matches:
            program_info['not_mandatory_courses'].add(f"{dept.upper()}{num}")

        notes_pattern = re.findall(r'([A-Z]{2,})\s*(\d{3,})(?:\s+and\s+([A-Z]{2,})\s*(\d{3,}))*\s*are not mandatory', program_section, re.IGNORECASE)
        for match in notes_pattern:
            dept1, num1 = match[0], match[1]
            program_info['not_mandatory_courses'].add(f"{dept1.upper()}{num1}")
            if len(match) > 2 and match[2]:
                dept2, num2 = match[2], match[3]
                program_info['not_mandatory_courses'].add(f"{dept2.upper()}{num2}")

        all_alternative_codes = {code for group in alternative_groups for code in group}
        program_info['not_mandatory_courses'] -= all_alternative_codes

        for line in program_section.split('\n'):
            line_clean = line.replace('_', '').replace('*', '')
            if 'waiv' in line_clean.lower() and '|' in line:
                matches = re.findall(r'\b([A-Z]{2,})\s*(\d{3,})\b', line_clean, re.IGNORECASE)
                for dept, num in matches:
                    if len(dept) >= 2:
                        course_code = f"{dept.upper()}{num}"
                        if course_code not in program_info['waivable_courses']:
                            program_info['waivable_courses'].append(course_code)

        minor_programs = {}
        minor_sec = re.search(
            r'##\s+Minor Programs.*?(?=\n##[^#]|\Z)',
            program_section, re.IGNORECASE | re.DOTALL)
        if minor_sec:
            for block in re.split(r'(?=\n###\s)', minor_sec.group(0)):
                hdr = re.match(r'###\s+(.+?)(?:\s*\(\d+\s*Credits?\))?\s*$', block.strip(), re.MULTILINE)
                if not hdr:
                    continue
                minor_name = hdr.group(1).strip()
                # Only rows marked **Additional** (bold) are the extra courses.
                # If no **Additional** rows exist, include all course code rows (e.g. Minor in Physics).
                has_additional = bool(re.search(r'\*\*Additional\*\*', block))
                additional = set()
                for row in block.split('\n'):
                    if '|' not in row:
                        continue
                    if has_additional and '**additional**' not in row.lower():
                        continue
                    for dept, num in re.findall(r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b', row):
                        additional.add(normalize_course_code(f"{dept}{num}"))
                if additional:
                    minor_programs[minor_name] = additional
        program_info['minor_programs'] = minor_programs

    except Exception as e:
        print(f"Warning: Error reading program info: {e}")

    return program_info


def select_major_electives(courses, program_info, md_path):
    major_credits = program_info.get('major_elective_credits', 0)
    elective_credits = program_info.get('elective_credits', 0)
    total_credits = major_credits + elective_credits

    if total_credits <= 0:
        return [], set()

    major_courses = program_info.get('major_elective_courses', set())
    elective_courses = program_info.get('elective_courses', set())
    is_microbiology = elective_credits > 0 and major_credits == 0

    if is_microbiology and elective_courses:
        eligible = []
        seen = set()
        for course in courses:
            code = normalize_course_code(course['code'])
            if code in elective_courses and code not in seen:
                if course['grade'] in GRADE_POINTS and course['grade'] != 'F':
                    eligible.append(course)
                    seen.add(code)
        if not eligible:
            print("\nNo elective courses found in transcript.")
            return [], set()
        eligible.sort(key=lambda x: (-(x['grade_points'] or 0), x['semester']))
        course_options = {}
        for c in eligible:
            code = normalize_course_code(c['code'])
            if code not in course_options:
                course_options[code] = c
        codes = sorted(course_options.keys())
        max_courses = elective_credits // 3
        print(f"\n{'='*60}")
        print("ELECTIVES SELECTION (Microbiology)")
        print(f"{'='*60}")
        print(f"Program requires {elective_credits} credits of Electives (3 courses).")
        print(f"\nSelect up to {max_courses} course(s) to count as Electives:")
        print("\nAvailable elective courses in your transcript:")
        for i, code in enumerate(codes, 1):
            c = course_options[code]
            print(f"  {i}. {c['code']:<15} - {c['credits']:.1f} credits, Grade: {c['grade']}")
        print()
        selection = input("> ").strip()
        selected = []
        selected_codes = set()
        if selection:
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                total = 0
                for idx in indices:
                    if 0 <= idx < len(codes):
                        code = codes[idx]
                        c = course_options[code]
                        if total + c['credits'] <= elective_credits:
                            selected.append(c)
                            selected_codes.add(code)
                            total += c['credits']
                if selected:
                    print(f"Selected {len(selected)} course(s) ({total:.1f} credits) as Elective courses.")
            except:
                print("Invalid selection.")
        return selected, selected_codes

    all_elective = major_courses | elective_courses
    if not all_elective:
        return [], set()
    eligible = []
    seen = set()
    for course in courses:
        code = normalize_course_code(course['code'])
        if code in all_elective and code not in seen:
            if course['grade'] in GRADE_POINTS and course['grade'] != 'F':
                eligible.append(course)
                seen.add(code)
    if not eligible:
        print("\nNo major/elective courses found in transcript.")
        return [], set()
    eligible.sort(key=lambda x: (-(x['grade_points'] or 0), x['semester']))
    course_options = {}
    for c in eligible:
        code = normalize_course_code(c['code'])
        if code not in course_options:
            course_options[code] = c
    codes = sorted(course_options.keys())
    max_courses = total_credits // 3
    print(f"\n{'='*60}")
    print("MAJOR/ELECTIVE COURSES SELECTION")
    print(f"{'='*60}")
    print(f"Program requires {total_credits} credits of Major/Electives.")
    print(f"\nSelect up to {max_courses} course(s) to count as major/elective:")
    print("\nAvailable major/elective courses in your transcript:")
    for i, code in enumerate(codes, 1):
        c = course_options[code]
        course_type = "Major Elective" if code in major_courses else "Elective"
        print(f"  {i}. {c['code']:<15} - {c['credits']:.1f} credits, Grade: {c['grade']} [{course_type}]")
    print()
    selection = input("> ").strip()
    selected = []
    selected_codes = set()
    if selection:
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            total = 0
            for idx in indices:
                if 0 <= idx < len(codes):
                    code = codes[idx]
                    c = course_options[code]
                    if total + c['credits'] <= total_credits:
                        selected.append(c)
                        selected_codes.add(code)
                        total += c['credits']
            if selected:
                print(f"Selected {len(selected)} course(s) ({total:.1f} credits) as major/elective courses.")
        except:
            print("Invalid selection.")
    return selected, selected_codes


def find_courses_with_prerequisites(md_path):
    courses_with_prereqs = set()
    if not os.path.exists(md_path):
        return courses_with_prereqs
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        program_headers = list(re.finditer(r'^#\s+(.+?program.*)$', content, re.MULTILINE | re.IGNORECASE))
        for i, match in enumerate(program_headers):
            start_pos = match.start()
            end_pos = program_headers[i + 1].start() if i + 1 < len(program_headers) else len(content)
            program_section = content[start_pos:end_pos]
            for line in program_section.split('\n'):
                line_clean = line.replace('**', '').replace('_', '')
                match2 = re.search(r'^[\|\s]*([A-Z]{2,4})\s*(\d{3,4}[A-Z]?)[\s\|]+(\d+)[^|]*\|([^|]+)', line_clean, re.IGNORECASE)
                if match2:
                    dept = match2.group(1).upper()
                    num = match2.group(2).upper()
                    course_code = f"{dept}{num}"
                    prereq_part = match2.group(4).strip()
                    if prereq_part and prereq_part.lower() not in ['-', 'none', '']:
                        courses_with_prereqs.add(course_code)
    except:
        pass
    return courses_with_prereqs


def find_trail_courses(md_path):
    """
    Return the set of all trail course codes from the Major Electives table.
    Reads the new structured table (Course | Credits | Prerequisites | Trail | Notes).
    Falls back to bullet-list parsing for backward compatibility.
    """
    trail_courses = set()
    if not os.path.exists(md_path):
        return trail_courses
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        trail_section_match = re.search(
            r'##\s+Major Electives\s*-\s*Trail Courses.*?(?=\n##[^#]|\Z)',
            content, re.IGNORECASE | re.DOTALL)
        if trail_section_match:
            section = trail_section_match.group(0)
            for line in section.splitlines():
                if '|' not in line:
                    continue
                clean = line.replace('**', '').strip().strip('|')
                cols = [c.strip() for c in clean.split('|')]
                if len(cols) < 2:
                    continue
                course_cell = cols[0]
                if re.match(r'^[-\s]+$', course_cell.replace('|', '')):
                    continue
                # Skip header row
                if re.search(r'course', course_cell, re.IGNORECASE):
                    continue
                for part in re.split(r'[/,]', course_cell):
                    m = re.match(r'^\s*([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\s*$', part.strip())
                    if m:
                        trail_courses.add(normalize_course_code(f"{m.group(1)}{m.group(2)}"))
        else:
            # Fallback: bullet list format
            trail_match = re.search(r'##\s+Major Electives.*?##\s+Open Elective', content, re.IGNORECASE | re.DOTALL)
            if trail_match:
                for line in trail_match.group(0).split('\n'):
                    if line.strip().startswith('-'):
                        for dept, num in re.findall(r'\b([A-Z]{3,4})\s+(\d{3,4}[A-Z]?)\b', line, re.IGNORECASE):
                            trail_courses.add(f"{dept.upper()}{num.upper()}")
    except Exception as e:
        print(f"Warning: Could not read trail courses: {e}")
    return trail_courses


def read_trail_course_prerequisites(md_path):
    """
    Parse the Major Electives - Trail Courses table and return the set of
    course codes that carry a non-None prerequisite.

    These codes must NOT appear as open/free electives for non-CSE programs
    because their prerequisites are CSE-specific core courses.
    """
    trail_codes_with_prereqs = set()
    if not os.path.exists(md_path):
        return trail_codes_with_prereqs
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        trail_section_match = re.search(
            r'##\s+Major Electives\s*-\s*Trail Courses.*?(?=\n##[^#]|\Z)',
            content, re.IGNORECASE | re.DOTALL)
        if not trail_section_match:
            return trail_codes_with_prereqs
        section = trail_section_match.group(0)
        for line in section.splitlines():
            if '|' not in line:
                continue
            clean = line.replace('**', '').strip().strip('|')
            cols = [c.strip() for c in clean.split('|')]
            # Table: Course | Credits | Prerequisites | Trail | Notes
            if len(cols) < 3:
                continue
            course_cell = cols[0]
            if re.match(r'^[-\s]+$', course_cell.replace('|', '')):
                continue
            if re.search(r'course', course_cell, re.IGNORECASE):
                continue
            prereq_cell = cols[2].strip()
            prereq_clean = prereq_cell.lower()
            has_prereq = (prereq_clean and
                          prereq_clean not in ('none', '-', '', 'prerequisites') and
                          bool(re.search(r'[A-Za-z]{2,4}\s*\d{3}', prereq_cell)))
            for part in re.split(r'[/,]', course_cell):
                m = re.match(r'^\s*([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\s*$', part.strip())
                if m:
                    code = normalize_course_code(f"{m.group(1)}{m.group(2)}")
                    if has_prereq:
                        trail_codes_with_prereqs.add(code)
    except Exception as e:
        print(f"Warning: Could not read trail course prerequisites: {e}")
    return trail_codes_with_prereqs



def get_alternative_and_not_mandatory_codes(courses, program_info):
    auto_count_codes = set()
    open_elective_codes = set()
    excluded_alternative_codes = set()
    lab_pairs = program_info.get('lab_pairs', {})
    alternative_groups = program_info.get('alternative_courses', [])

    for group in alternative_groups:
        theory_in_group = [c for c in group if not c.endswith('L')]
        lab_in_group = [c for c in group if c.endswith('L')]
        if lab_in_group and theory_in_group:
            passing_theory = []
            theory_codes_in_transcript = set()
            for course in courses:
                code = normalize_course_code(course['code'])
                if code in theory_in_group:
                    theory_codes_in_transcript.add(code)
                    if course['grade'] in GRADE_POINTS and course['grade'] != 'F':
                        passing_theory.append((code, course.get('grade_points', 0) or 0, course))
            if len(passing_theory) > 1:
                passing_theory.sort(key=lambda x: -x[1])
                best_theory = passing_theory[0][0]
                auto_count_codes.add(best_theory)
                paired_lab = lab_pairs.get(best_theory)
                if paired_lab:
                    auto_count_codes.add(paired_lab)
                for i in range(1, len(passing_theory)):
                    excess_theory = passing_theory[i][0]
                    open_elective_codes.add(excess_theory)
                    excess_lab = lab_pairs.get(excess_theory)
                    if excess_lab:
                        open_elective_codes.add(excess_lab)
            elif len(passing_theory) == 1:
                best_theory = passing_theory[0][0]
                auto_count_codes.add(best_theory)
                paired_lab = lab_pairs.get(best_theory)
                if paired_lab:
                    auto_count_codes.add(paired_lab)
            for code in theory_codes_in_transcript:
                if code not in auto_count_codes and code not in open_elective_codes:
                    excluded_alternative_codes.add(code)
                    paired_lab = lab_pairs.get(code)
                    if paired_lab:
                        excluded_alternative_codes.add(paired_lab)
            for lab_code in lab_in_group:
                if (lab_code not in auto_count_codes and
                        lab_code not in open_elective_codes and
                        lab_code not in excluded_alternative_codes):
                    for course in courses:
                        if normalize_course_code(course['code']) == lab_code:
                            excluded_alternative_codes.add(lab_code)
                            break
        else:
            group_codes_in_transcript = set()
            passing_courses = []
            for course in courses:
                code = normalize_course_code(course['code'])
                if code in group:
                    group_codes_in_transcript.add(code)
                    if course['grade'] in GRADE_POINTS and course['grade'] != 'F':
                        passing_courses.append((code, course.get('grade_points', 0) or 0, course))
            if len(passing_courses) > 1:
                passing_courses.sort(key=lambda x: -x[1])
                auto_count_codes.add(passing_courses[0][0])
                for i in range(1, len(passing_courses)):
                    open_elective_codes.add(passing_courses[i][0])
            elif len(passing_courses) == 1:
                auto_count_codes.add(passing_courses[0][0])
            for code in group_codes_in_transcript:
                if code not in auto_count_codes and code not in open_elective_codes:
                    excluded_alternative_codes.add(code)

    not_mandatory = program_info.get('not_mandatory_courses', set())
    for course in courses:
        code = normalize_course_code(course['code'])
        if code in not_mandatory and course['grade'] in GRADE_POINTS and course['grade'] != 'F':
            open_elective_codes.add(code)

    open_elective_codes -= auto_count_codes
    return auto_count_codes, open_elective_codes, excluded_alternative_codes


def select_cse_trails_cgpa(all_transcript_courses, program_info):
    trail_courses = program_info.get('major_elective_courses', set())
    if not trail_courses:
        return [], set(), set()

    transcript_courses_by_code = {}
    for course in all_transcript_courses:
        code = normalize_course_code(course['code'])
        if code in trail_courses and course['grade'] in GRADE_POINTS and course['grade'] != 'F':
            if code not in transcript_courses_by_code:
                transcript_courses_by_code[code] = course

    if not transcript_courses_by_code:
        print("\n*No trail courses found in transcript.*")
        return [], set(), set()

    available_trails = {}
    for trail_name, trail_course_list in CSE_TRAILS.items():
        courses_in_transcript = [transcript_courses_by_code[c] for c in trail_course_list if c in transcript_courses_by_code]
        if courses_in_transcript:
            available_trails[trail_name] = sorted(courses_in_transcript, key=lambda x: (-(x['grade_points'] or 0), x['semester']))

    if not available_trails:
        print("\nNo trail courses found in transcript.")
        return [], set(), set()

    trail_names = list(available_trails.keys())

    print(f"\n{'='*60}")
    print("PRIMARY TRAIL SELECTION (CSE)")
    print(f"{'='*60}")
    print("Select your Primary Trail (minimum 2 courses = 6 credits):")
    print("\nAvailable Trails:")
    for i, name in enumerate(trail_names, 1):
        course_with_grades = ", ".join([f"{c['code']}({c['grade']})" for c in available_trails[name]])
        print(f"  {i}. {name}")
        print(f"     Courses: {course_with_grades}")

    print()
    selection = input("> ").strip()
    primary_trail = None
    primary_codes = set()
    if selection:
        try:
            idx = int(selection.strip()) - 1
            if 0 <= idx < len(trail_names):
                primary_trail = trail_names[idx]
        except:
            pass

    if primary_trail:
        primary_courses = available_trails[primary_trail]
        print(f"\nSelect up to 2 courses from {primary_trail}:")
        for i, c in enumerate(primary_courses, 1):
            print(f"  {i}. {c['code']:<15} - {c['credits']:.1f} credits, Grade: {c['grade']}")
        print()
        selection = input("> ").strip()
        if selection:
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                total = 0
                for idx in indices:
                    if 0 <= idx < len(primary_courses) and total < 6:
                        c = primary_courses[idx]
                        if total + c['credits'] <= 6:
                            primary_codes.add(normalize_course_code(c['code']))
                            total += c['credits']
            except:
                pass

    secondary_trail_names = [t for t in trail_names if t != primary_trail]
    print(f"\n{'='*60}")
    print("SECONDARY TRAIL SELECTION (CSE)")
    print(f"{'='*60}")
    print("Select your Secondary Trail (1 course = 3 credits):")
    print("\nAvailable Trails:")
    for i, name in enumerate(secondary_trail_names, 1):
        course_with_grades = ", ".join([f"{c['code']}({c['grade']})" for c in available_trails[name]])
        print(f"  {i}. {name}")
        print(f"     Courses: {course_with_grades}")

    print()
    selection = input("> ").strip()
    secondary_trail = None
    secondary_codes = set()
    if selection:
        try:
            idx = int(selection.strip()) - 1
            if 0 <= idx < len(secondary_trail_names):
                secondary_trail = secondary_trail_names[idx]
        except:
            pass

    if secondary_trail:
        secondary_courses = available_trails[secondary_trail]
        print(f"\nSelect 1 course from {secondary_trail}:")
        for i, c in enumerate(secondary_courses, 1):
            print(f"  {i}. {c['code']:<15} - {c['credits']:.1f} credits, Grade: {c['grade']}")
        print()
        selection = input("> ").strip()
        if selection:
            try:
                idx = int(selection.strip()) - 1
                if 0 <= idx < len(secondary_courses):
                    c = secondary_courses[idx]
                    if c['credits'] <= 3:
                        secondary_codes.add(normalize_course_code(c['code']))
            except:
                pass

    all_selected = primary_codes | secondary_codes
    excess_trail_codes = {code for code in transcript_courses_by_code if code not in all_selected}

    primary_out = [transcript_courses_by_code[c] for c in primary_codes if c in transcript_courses_by_code]
    secondary_out = [transcript_courses_by_code[c] for c in secondary_codes if c in transcript_courses_by_code]
    return primary_out + secondary_out, primary_codes | secondary_codes, excess_trail_codes


def select_open_electives(courses, program_info, selected_major_codes, md_path,
                          extra_excess_codes=None, alternative_codes=None,
                          auto_count_codes=None, minor_additional_codes=None,
                          transfer_codes=None, trail_prereq_codes=None):
    open_credits = program_info.get('open_elective_credits', 0)
    if open_credits <= 0:
        return [], set()

    allowed = program_info.get('allowed_courses', set())
    capstone_codes = {normalize_course_code(c) for c in program_info.get('capstone_courses', set())}
    courses_with_prereqs = find_courses_with_prerequisites(md_path)
    transfer = set(transfer_codes) if transfer_codes else set()
    trail_with_prereq = set(trail_prereq_codes) if trail_prereq_codes else set()

    excess_major = set()
    if program_info.get('major_elective_courses'):
        major_req = program_info['major_elective_credits'] // 3
        student_major = []
        for c in courses:
            code = normalize_course_code(c['code'])
            if code in program_info['major_elective_courses'] and c['grade'] in GRADE_POINTS and c['grade'] != 'F':
                student_major.append((code, c['grade_points'] or 0))
        student_major.sort(key=lambda x: -x[1])
        if len(student_major) > major_req:
            excess_major.update(x[0] for x in student_major[major_req:])

    if program_info.get('elective_courses'):
        for c in courses:
            code = normalize_course_code(c['code'])
            if (code in program_info['elective_courses']
                    and code not in selected_major_codes
                    and c['grade'] in GRADE_POINTS
                    and c['grade'] != 'F'):
                excess_major.add(code)

    excess_major.update(selected_major_codes)
    if extra_excess_codes:
        excess_major.update(extra_excess_codes)
    if alternative_codes:
        excess_major.update(alternative_codes)

    minor_extra = set(minor_additional_codes) if minor_additional_codes else set()
    if minor_extra:
        excess_major.update(minor_extra)
    # Minor courses appear in the open elective list labeled [Minor course].
    # The student may pick them here as open electives.
    # select_minor_courses() runs afterward and only fires on minor courses
    # that were NOT picked as open electives (not in already_open_codes).

    is_microbiology = program_info.get('elective_credits', 0) > 0 and program_info.get('major_elective_credits', 0) == 0
    auto_counted = set(auto_count_codes) if auto_count_codes else set()

    all_passing = []
    for course in courses:
        code = normalize_course_code(course['code'])
        if code in selected_major_codes:
            continue
        if code in auto_counted:
            continue
        if not course.get('is_best_attempt', True):
            continue
        if course['grade'] not in GRADE_POINTS or course['grade'] == 'F':
            continue
        if code.endswith('L'):
            continue
        # Transfer credits are never eligible as open electives
        if code in transfer:
            continue
        # Capstone/internship courses are never open electives
        if code in capstone_codes:
            continue
        # CSE trail courses with prerequisites are never eligible for non-CSE programs
        if code in trail_with_prereq:
            continue
        if code not in allowed or code in excess_major:
            if code not in courses_with_prereqs or code in excess_major:
                all_passing.append(course)

    if not all_passing:
        print("No passed courses available to select as open electives.")
        return [], set()

    all_passing.sort(key=lambda x: (-(x['grade_points'] or 0), x['semester']))
    course_options = {}
    for course in all_passing:
        code = normalize_course_code(course['code'])
        if code not in course_options:
            course_options[code] = course
    codes = sorted(course_options.keys())
    max_courses = open_credits // 3
    core_alternative_codes = set(alternative_codes) if alternative_codes else set()

    elective_label = "FREE ELECTIVES" if is_microbiology else "OPEN/FREE ELECTIVES"
    print(f"\n{'='*60}")
    print(f"{elective_label} SELECTION")
    print(f"{'='*60}")
    print(f"Program allows {open_credits} credits of {'free' if is_microbiology else 'open/free'} electives.")
    print(f"\nSelect up to {max_courses} course(s) to count as {'free' if is_microbiology else 'open/free'} electives:")
    print(f"\nAvailable courses that could be {'free' if is_microbiology else 'open'} electives:")
    for i, code in enumerate(codes, 1):
        c = course_options[code]
        if code in core_alternative_codes:
            source_label = " [University Core alternative - excess]"
        elif code in minor_extra:
            source_label = " [Minor course]"
        else:
            source_label = ""
        print(f"  {i}. {c['code']:<15} - {c['credits']:.1f} credits, Grade: {c['grade']}{source_label}")
    if core_alternative_codes:
        print("\n  Note: Courses marked [University Core alternative - excess] are extra courses")
        print("  you took from a 'Choose one' core group.")
    print()
    selection = input("> ").strip()
    selected = []
    selected_codes = set()
    if selection:
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            total = 0
            for idx in indices:
                if 0 <= idx < len(codes):
                    code = codes[idx]
                    c = course_options[code]
                    if total + c['credits'] <= open_credits:
                        selected.append(c)
                        selected_codes.add(code)
                        total += c['credits']
            if selected:
                print(f"Selected {len(selected)} course(s) ({total:.1f} credits) as open electives.")
        except:
            print("Invalid selection.")
    return selected, selected_codes


def ask_waivers(courses, waivable_courses, program_name=""):
    pn = program_name.lower()
    is_cse = pn == 'computer science'
    is_mic = pn == 'microbiology'

    if is_cse or is_mic:
        courses_to_ask = ['ENG102', 'MAT112']
    else:
        courses_to_ask = list(waivable_courses) if waivable_courses else []

    if not courses_to_ask:
        return {}

    print(f"\n{'='*60}")
    print("WAIVER QUESTIONS")
    print(f"{'='*60}")
    print("Note: Waived courses are exempt from requirement.")

    waivers = {}
    for course_code in courses_to_ask:
        try:
            answer = input(f"\nWas {course_code} waived for this student? (y/n): ").strip().lower()
            waivers[course_code] = answer in ['y', 'yes']
            if waivers[course_code]:
                print(f"  -> {course_code} marked as WAIVED")
            else:
                print(f"  -> {course_code} not waived")
        except EOFError:
            waivers[course_code] = False
    return waivers


def process_retakes(courses):
    course_groups = defaultdict(list)
    for idx, course in enumerate(courses):
        course_groups[normalize_course_code(course['code'])].append((idx, course))

    for code, attempts in course_groups.items():
        if len(attempts) > 1:
            sorted_attempts = sorted(
                attempts,
                key=lambda x: (-(x[1]['grade_points'] or 0), x[1]['semester'])
            )
            best_idx = sorted_attempts[0][0]
            courses[best_idx]['is_best_attempt'] = True
            for idx, _ in sorted_attempts[1:]:
                courses[idx]['is_best_attempt'] = False
        else:
            idx = attempts[0][0]
            courses[idx]['is_best_attempt'] = True
    return courses


def calculate_cgpa(all_courses, program_info, major_codes, open_codes, waivers,
                   excluded_alternative_codes=None, open_elective_selection_codes=None,
                   excess_elective_codes=None, minor_selected_codes=None,
                   minor_rejected_codes=None, transfer_codes=None):
    if excluded_alternative_codes is None:
        excluded_alternative_codes = set()
    if open_elective_selection_codes is None:
        open_elective_selection_codes = set()
    if excess_elective_codes is None:
        excess_elective_codes = set()
    if minor_selected_codes is None:
        minor_selected_codes = set()
    if minor_rejected_codes is None:
        minor_rejected_codes = set()
    transfer = set(transfer_codes) if transfer_codes else set()

    allowed = program_info.get('allowed_courses', set())
    not_mandatory = program_info.get('not_mandatory_courses', set())
    capstone_codes = {normalize_course_code(c) for c in program_info.get('capstone_courses', set())}
    # Capstone/internship only auto-count if this program has capstone requirements.
    # Foreign capstone codes (e.g. CSE299 under MIC) should not count.
    program_has_capstone = bool(program_info.get('capstone_required_courses') or
                                program_info.get('internship_required'))
    transcript_codes = {normalize_course_code(c['code']) for c in all_courses}

    total_grade_points = 0.0
    total_credits = 0.0
    cgpa_courses_for_calc = []
    retaken_courses = []
    excluded_from_cgpa_output = []

    for course in all_courses:
        code = normalize_course_code(course['code'])
        grade = course['grade']
        credits = course['credits']

        if code in NON_CREDIT_LABS:
            theory = NON_CREDIT_LABS[code]
            if theory in transcript_codes:
                continue

        if not course.get('is_best_attempt', True):
            retaken_courses.append({
                'code': course['code'], 'credits': credits,
                'grade': grade, 'semester': course['semester']
            })
            continue

        # Transfer credits — always excluded from CGPA
        if code in transfer:
            excluded_from_cgpa_output.append({
                'code': course['code'], 'credits': credits, 'grade': grade,
                'reason': 'Transfer credit (not counted)', 'semester': course['semester']
            })
            continue

        # Capstone/internship with S/P grades: excluded from CGPA, but let
        # letter-graded capstone courses fall through to normal counting below.
        if code in capstone_codes and (grade in NON_GRADE_ENTRIES or grade not in GRADE_POINTS):
            excluded_from_cgpa_output.append({
                'code': course['code'], 'credits': credits, 'grade': grade,
                'reason': 'Capstone/Internship (S/P grade, not in CGPA)', 'semester': course['semester']
            })
            continue

        if code in waivers and waivers[code]:
            excluded_from_cgpa_output.append({
                'code': course['code'], 'credits': credits, 'grade': 'WA',
                'reason': 'Waiver granted', 'semester': course['semester']
            })
            continue

        if grade in NON_GRADE_ENTRIES:
            excluded_from_cgpa_output.append({
                'code': course['code'], 'credits': credits, 'grade': grade,
                'reason': 'Non-grade entry', 'semester': course['semester']
            })
            continue

        if grade not in GRADE_POINTS:
            excluded_from_cgpa_output.append({
                'code': course['code'], 'credits': credits, 'grade': grade,
                'reason': 'Unknown grade', 'semester': course['semester']
            })
            continue

        if credits <= 0:
            # 0-credit lab whose theory course is also in transcript → silently absorbed
            if code.endswith('L') and code[:-1] in transcript_codes:
                continue
            # 0-credit capstone/internship counts only if this program owns it
            if code in capstone_codes and program_has_capstone:
                pass   # fall through to counting logic below
            else:
                excluded_from_cgpa_output.append({
                    'code': course['code'], 'credits': credits, 'grade': grade,
                    'reason': 'Zero credits', 'semester': course['semester']
                })
                continue

        if code in open_elective_selection_codes:
            counts = code in open_codes
            exclusion_reason = 'Elective not selected' if code in excess_elective_codes else 'University core excess'
        elif code in minor_rejected_codes:
            counts = False
            exclusion_reason = 'Minor not selected'
        else:
            in_allowed = (code in allowed) and (code not in not_mandatory) and (code not in excluded_alternative_codes)
            counts = (in_allowed or (code in major_codes) or (code in open_codes)
                      or (code in minor_selected_codes)
                      or (program_has_capstone and code in capstone_codes))
            if not counts:
                exclusion_reason = 'University core excess' if code in excluded_alternative_codes else 'Not in program'

        if counts:
            gp = GRADE_POINTS[grade]
            cgpa_courses_for_calc.append({
                'code': course['code'], 'credits': credits, 'grade': grade,
                'grade_points': gp, 'semester': course['semester']
            })
            total_grade_points += credits * gp
            total_credits += credits
        else:
            excluded_from_cgpa_output.append({
                'code': course['code'], 'credits': credits, 'grade': grade,
                'reason': exclusion_reason, 'semester': course['semester']
            })

    # MAT116 deduction (CSE only): if total counted credits >= 130,
    # MAT116's credits and grade points are removed from the CGPA calculation.
    mat116 = normalize_course_code('MAT116')
    if mat116 in capstone_codes:
        pass  # should not happen, but guard
    elif total_credits >= 130:
        for c in list(cgpa_courses_for_calc):
            if normalize_course_code(c['code']) == mat116:
                total_grade_points -= c['credits'] * c['grade_points']
                total_credits      -= c['credits']
                cgpa_courses_for_calc.remove(c)
                excluded_from_cgpa_output.append({
                    'code': c['code'], 'credits': c['credits'], 'grade': c['grade'],
                    'reason': 'MAT116 deducted (130+ credits completed)',
                    'semester': c.get('semester', '')
                })
                break

    # NSU: calculate to 3 decimal places (truncate), then ceiling to 2dp for display
    raw_cgpa = total_grade_points / total_credits if total_credits > 0 else 0.0
    cgpa = math.ceil(int(raw_cgpa * 1000) / 1000 * 100) / 100
    return cgpa, cgpa_courses_for_calc, excluded_from_cgpa_output, retaken_courses, total_grade_points, total_credits


def format_output(cgpa, cgpa_courses, excluded, retaken_courses, total_points, total_credits,
                  program_name, waivers=None):
    lines = []
    lines.append("\n" + "=" * 70)
    lines.append("CGPA ANALYSIS FOR " + program_name.upper())
    lines.append("=" * 70)
    lines.append("")

    lines.append("-" * 70)
    lines.append("COURSES COUNTED TOWARD CGPA (Best Attempts)")
    lines.append("-" * 70)
    lines.append(f"{'Course Code':<15} {'Credits':<10} {'Grade':<8} {'Semester':<12} {'Grade Points':<15}")
    lines.append("-" * 70)
    for c in cgpa_courses:
        earned = c['credits'] * c['grade_points']
        lines.append(f"{c['code']:<15} {c['credits']:<10.1f} {c['grade']:<8} {c['semester']:<12} {earned:<15.2f}")
    lines.append("-" * 70)
    lines.append(f"{'TOTAL':<15} {total_credits:<10.1f} {'':<8} {'':<12} {total_points:<15.1f}")
    lines.append("")

    if retaken_courses:
        lines.append("-" * 70)
        lines.append("RETAKEN COURSES (Not Used for CGPA Calculation)")
        lines.append("-" * 70)
        lines.append(f"{'Course Code':<15} {'Credits':<10} {'Grade':<8} {'Semester':<12} {'Note':<15}")
        lines.append("-" * 70)
        for c in retaken_courses:
            lines.append(f"{c['code']:<15} {c['credits']:<10.1f} {c['grade']:<8} {c['semester']:<12} {'Previous Attempt':<15}")
        lines.append("-" * 70)
        lines.append("")

    waiver_courses = [c for c in excluded if c.get('reason') == 'Waiver granted']
    other_excluded = [c for c in excluded if c.get('reason') != 'Waiver granted']

    if waiver_courses:
        lines.append("-" * 70)
        lines.append("WAIVED COURSES (Exempt — Not in CGPA)")
        lines.append("-" * 70)
        lines.append(f"{'Course Code':<15} {'Credits':<10} {'Grade':<8} {'Semester':<12} {'Status':<20}")
        lines.append("-" * 70)
        for c in waiver_courses:
            lines.append(f"{c['code']:<15} {c['credits']:<10.1f} {'WA':<8} {c.get('semester', ''):<12} {'Waiver granted':<20}")
        lines.append("-" * 70)
        lines.append("")

    if other_excluded:
        lines.append("-" * 70)
        lines.append("EXCLUDED COURSES (Not in CGPA)")
        lines.append("-" * 70)
        lines.append(f"{'Course Code':<15} {'Credits':<10} {'Grade':<8} {'Semester':<12} {'Reason':<30}")
        lines.append("-" * 70)
        for c in other_excluded:
            lines.append(f"{c['code']:<15} {c['credits']:<10.1f} {c['grade']:<8} {c.get('semester', ''):<12} {c['reason']:<30}")
        lines.append("-" * 70)
        lines.append("")

    lines.append("=" * 70)
    lines.append("CGPA SUMMARY")
    lines.append("=" * 70)
    lines.append(f"Total Credits Counted:                 {total_credits:.1f}")
    lines.append(f"Total Grade Points:                    {total_points:.2f}")
    lines.append(f"CGPA:                                  {cgpa:.2f}")
    lines.append("")
    if cgpa >= 2.0:
        lines.append("Status: CGPA meets minimum requirement (2.0)")
    else:
        lines.append("Status: CGPA below minimum requirement (2.0)")
    return "\n".join(lines)


def select_minor_courses(courses, program_info, already_open_codes=None):
    already_open = set(already_open_codes) if already_open_codes else set()
    minor_programs = program_info.get('minor_programs', {})
    if not minor_programs:
        return set(), set()

    passed_codes = set()
    for c in courses:
        if c['grade'] in GRADE_POINTS and c['grade'] != 'F':
            passed_codes.add(normalize_course_code(c['code']))

    eligible_minors = {}
    ineligible_rejected = set()
    for minor_name, add_codes in minor_programs.items():
        prereqs = MINOR_PREREQUISITES.get(minor_name, set())
        missing = prereqs - passed_codes
        if missing:
            ineligible_rejected |= add_codes
        else:
            eligible_minors[minor_name] = add_codes

    all_additional = set()
    for codes in minor_programs.values():
        all_additional |= codes
    eligible_additional = set()
    for codes in eligible_minors.values():
        eligible_additional |= codes

    in_transcript = {}
    for c in courses:
        code = normalize_course_code(c['code'])
        if (code in eligible_additional
                and code not in already_open
                and c.get('is_best_attempt', True)
                and c['grade'] in GRADE_POINTS
                and c['grade'] != 'F'
                and code not in in_transcript):
            in_transcript[code] = c

    if not in_transcript:
        rejected = set()
        for c in courses:
            code = normalize_course_code(c['code'])
            if (code in all_additional and code not in already_open
                    and c.get('is_best_attempt', True)
                    and c['grade'] in GRADE_POINTS and c['grade'] != 'F'):
                rejected.add(code)
        return set(), rejected

    detected = {}
    for name, add_codes in eligible_minors.items():
        found = sorted([in_transcript[c] for c in add_codes if c in in_transcript], key=lambda x: x['code'])
        if found:
            detected[name] = found

    if not detected:
        return set(), set(in_transcript.keys())

    print(f"\n{'='*60}")
    print("MINOR PROGRAM DETECTION")
    print(f"{'='*60}")
    print("Minor course(s) outside school core detected in transcript.\n")
    minor_names = list(detected.keys())
    for i, name in enumerate(minor_names, 1):
        course_str = ', '.join(f"{c['code']}({c['grade']})" for c in detected[name])
        print(f"  {i}. {name}")
        print(f"     Courses found: {course_str}")

    print("\nIs this student pursuing a minor? (y/n): ", end='')
    try:
        yn = input().strip().lower()
    except EOFError:
        yn = 'n'

    if yn not in ('y', 'yes'):
        print("  -> No minor declared. Minor-only courses will be excluded from CGPA.")
        return set(), set(in_transcript.keys())

    # If only one minor detected, auto-select it; otherwise ask which one
    if len(minor_names) == 1:
        answer = 1
    else:
        print("Which minor? (enter number):")
        for i, name in enumerate(minor_names, 1):
            print(f"  {i}. {name}")
        try:
            answer = int(input("> ").strip())
        except (ValueError, EOFError):
            answer = 1

    chosen = minor_names[answer - 1]
    available = detected[chosen]
    print(f"  -> Minor selected: {chosen}")

    print(f"\n{'='*60}")
    print(f"MINOR COURSE SELECTION ({chosen.upper()})")
    print(f"{'='*60}")
    print("Select which courses count toward CGPA")
    print("(comma-separated numbers, or press Enter to include all):\n")
    for i, c in enumerate(available, 1):
        print(f"  {i}. {c['code']:<15} - {c['credits']:.1f} credits, Grade: {c['grade']}")

    print()
    try:
        sel = input("> ").strip()
    except EOFError:
        sel = ''

    if not sel:
        selected = {normalize_course_code(c['code']) for c in available}
        print(f"Selected all {len(selected)} course(s) for {chosen}.")
    else:
        selected = set()
        try:
            for idx in [int(x.strip()) - 1 for x in sel.split(',')]:
                if 0 <= idx < len(available):
                    selected.add(normalize_course_code(available[idx]['code']))
        except ValueError:
            selected = {normalize_course_code(c['code']) for c in available}
        print(f"Selected {len(selected)} course(s) for {chosen}.")

    rejected = {code for code in in_transcript if code not in selected}
    return selected, rejected


def main():
    parser = argparse.ArgumentParser(
        description='L2 Logic Gate & Waiver Handler (Step 2 of 3) - Calculate CGPA with waiver support'
    )
    parser.add_argument('csv_file', help='Path to transcript CSV')
    parser.add_argument('program_name', help='Program name (e.g., cse, mic, eee, finance)')
    parser.add_argument('program_knowledge', help='Path to program MD file')
    args = parser.parse_args()

    # ── Validate program name first — exit immediately if not offered by NSU ──
    canonical_program = validate_program_name(args.program_name, args.program_knowledge)

    # ── Check if course structure is defined for this program ──────────────
    if canonical_program not in STRUCTURED_PROGRAMS:
        print(f"\n{'='*60}")
        print(f"  Program: {canonical_program}")
        print(f"{'='*60}")
        print(f"\nThe course structure for '{canonical_program}' is not yet defined")
        print("in the program knowledge file.")
        print("\nOnly GED courses will be counted toward graduation for this program.")
        print("For a full audit, the course structure must first be added to the MD file.")
        print(f"\n{'='*60}\n")
        sys.exit(0)

    structured_program = canonical_program
    print(f"Reading transcript: {args.csv_file}")
    courses = read_transcript(args.csv_file)
    if not courses:
        print("No courses found.")
        sys.exit(0)
    print(f"Program: {canonical_program}")

    # ── NSU course list check ─────────────────────────────────────────────
    nsu_course_list = read_nsu_course_list(args.program_knowledge)
    is_transfer, transfer_codes = check_non_nsu_courses(courses, nsu_course_list)

    program_info = get_program_info(args.program_knowledge, structured_program)
    courses = process_retakes(courses)

    is_cse = structured_program == "Computer Science"
    is_mic = structured_program == "Microbiology"

    excess_trail_codes = set()
    if is_cse and program_info.get('major_elective_credits', 0) > 0:
        major_courses, major_codes, excess_trail_codes = select_cse_trails_cgpa(courses, program_info)
    else:
        major_courses, major_codes = select_major_electives(courses, program_info, args.program_knowledge)

    auto_count_codes, open_elective_selection_codes, excluded_alternative_codes = \
        get_alternative_and_not_mandatory_codes(courses, program_info)

    passed_codes = {normalize_course_code(c['code'])
                    for c in courses
                    if c['grade'] in GRADE_POINTS and c['grade'] != 'F'}
    all_minor_additional = set()
    for minor_name, add_codes in program_info.get('minor_programs', {}).items():
        prereqs = MINOR_PREREQUISITES.get(minor_name, set())
        if not (prereqs - passed_codes):
            all_minor_additional |= add_codes

    # For non-CSE programs: trail courses that have CSE-specific prerequisites
    # must be blocked from the open/free elective pool entirely.
    if not is_cse:
        trail_prereq_codes = read_trail_course_prerequisites(args.program_knowledge)
    else:
        trail_prereq_codes = set()

    open_courses, open_codes = select_open_electives(
        courses, program_info, major_codes, args.program_knowledge,
        excess_trail_codes, open_elective_selection_codes, auto_count_codes,
        minor_additional_codes=all_minor_additional,
        transfer_codes=transfer_codes,
        trail_prereq_codes=trail_prereq_codes)

    all_open_codes = open_codes | auto_count_codes

    excess_elective_codes = set()
    if is_mic and program_info.get('elective_courses'):
        for c in courses:
            code = normalize_course_code(c['code'])
            if code in program_info['elective_courses'] and code not in major_codes:
                open_elective_selection_codes.add(code)
                excess_elective_codes.add(code)

    if is_cse and excess_trail_codes:
        for code in excess_trail_codes:
            open_elective_selection_codes.add(code)
            excess_elective_codes.add(code)

    minor_selected_codes, minor_rejected_codes = select_minor_courses(
        courses, program_info, already_open_codes=open_codes)

    waivers = ask_waivers(courses, program_info['waivable_courses'], structured_program)

    cgpa, cgpa_courses, excluded, retaken_courses, total_points, total_credits = calculate_cgpa(
        courses, program_info, major_codes, all_open_codes, waivers,
        excluded_alternative_codes, open_elective_selection_codes, excess_elective_codes,
        minor_selected_codes, minor_rejected_codes,
        transfer_codes=transfer_codes
    )

    # For non-CSE programs: trail courses with CSE-specific prerequisites that slipped
    # through to the counted list must be moved to excluded with an appropriate reason.
    if not is_cse and trail_prereq_codes:
        clean_cgpa_courses = []
        for c in cgpa_courses:
            if normalize_course_code(c['code']) in trail_prereq_codes:
                excluded.append({
                    'code': c['code'], 'credits': c['credits'], 'grade': c['grade'],
                    'reason': 'CSE trail course (not open elective)',
                    'semester': c.get('semester', '')
                })
            else:
                clean_cgpa_courses.append(c)
        if len(clean_cgpa_courses) != len(cgpa_courses):
            # Recalculate totals
            total_points = sum(c['credits'] * c['grade_points'] for c in clean_cgpa_courses)
            total_credits = sum(c['credits'] for c in clean_cgpa_courses)
            cgpa = total_points / total_credits if total_credits > 0 else 0.0
            cgpa_courses = clean_cgpa_courses

    output = format_output(cgpa, cgpa_courses, excluded, retaken_courses, total_points, total_credits,
                           canonical_program, waivers=waivers)
    print(output)


if __name__ == '__main__':
    main()