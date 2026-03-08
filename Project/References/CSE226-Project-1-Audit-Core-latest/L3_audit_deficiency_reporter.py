#!/usr/bin/env python3
"""
L3 Audit & Deficiency Reporter
Step 3 of 3: Compare a student's transcript against program requirements to
identify missing mandatory courses, unmet credit quotas, and graduation blockers.
Run this after L1 (credit tally) and L2 (CGPA) to get a full audit picture.

Output sections
───────────────
  COURSES COUNTED TOWARD GRADUATION  — best attempt, passing, counts
  RETAKEN COURSES                    — previous attempts
  WAIVED COURSES                     — courses with an approved waiver
  EXCLUDED / NOT COUNTED             — capstone, transfer credit, etc.
  TRAIL COURSES (CSE only)           — per-trail breakdown with courses taken
  ELECTIVES (MIC only)               — elective courses taken vs required
  OPEN / FREE ELECTIVES              — open elective courses selected
  DEFICIENCY REPORT                  — missing mandatory courses, unmet quotas
  GRADUATION SUMMARY                 — can graduate? CGPA status, probation flag
"""

import argparse
import csv
import math
import os
import re
import sys
from collections import defaultdict


# ═══════════════════════════════════════════════════════════════════════════════
# Shared constants & helpers  (mirrors L1/L2 — kept self-contained)
# ═══════════════════════════════════════════════════════════════════════════════

GRADE_POINTS = {
    'A': 4.0, 'A-': 3.7,
    'B+': 3.3, 'B': 3.0, 'B-': 2.7,
    'C+': 2.3, 'C': 2.0, 'C-': 1.7,
    'D+': 1.3, 'D': 1.0,
    'F': 0.0,
}
NON_GRADE_ENTRIES = {'W', 'I', 'WA', 'IP', 'S', 'P', 'N', ''}

# Non-credit labs: grade absorbed by theory course; suppress from CGPA denominator.
NON_CREDIT_LABS = {
    'CSE225L': 'CSE225',
    'CSE231L': 'CSE231',
    'CSE311L': 'CSE311',
    'CSE331L': 'CSE331',
    'CSE332L': 'CSE332',
}

# CSE trail definitions (same as L2)
CSE_TRAILS = {
    "Algorithms and Computation": ["CSE257", "CSE417", "CSE326", "CSE426", "CSE273", "CSE473"],
    "Software Engineering":       ["CSE411"],
    "Networks":                   ["CSE422", "CSE562", "CSE338", "CSE438", "CSE482", "CSE485", "CSE486"],
    "Computer Architecture and VLSI": ["CSE435", "CSE413", "CSE414"],
    "Artificial Intelligence":    ["CSE440", "CSE445", "CSE465", "CSE467", "CSE419", "CSE598"],
    "Bioinformatics":             [],
}

MINOR_PREREQUISITES = {
    "Minor in Math":    {"MAT116", "MAT120", "MAT125", "MAT130", "MAT250"},
    "Minor in Physics": {"PHY107", "PHY107L", "PHY108", "PHY108L"},
}

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
    "Public Health":  ["public health", "pbh", "ph"],
    "BPharm":         ["bpharm", "pharmacy", "phr", "b.pharm"],
    "BBA Accounting": ["bba accounting", "accounting", "act", "bba acc"],
    "BBA Economics":  ["bba economics", "economics", "eco", "bba eco"],
    "BBA Entrepreneurship": ["bba entrepreneurship", "entrepreneurship", "ent"],
    "BBA Finance":    ["bba finance", "finance", "fin"],
    "BBA Human Resource and Management": [
        "bba human resource and management", "human resource", "hrm",
        "bba hrm", "human resource management",
    ],
    "BBA International Business": ["bba international business", "international business", "inb"],
    "BBA Management": ["bba management", "management", "mgt", "bba mgt"],
    "BBA Management Information System": [
        "bba management information system", "management information system", "mis", "bba mis",
    ],
    "BBA Marketing":   ["bba marketing", "marketing", "mkt"],
    "BBA Supply Chain Management": [
        "bba supply chain management", "supply chain management", "scm", "supply chain",
    ],
    "BBA General": ["bba general", "bba", "bba gen"],
    "Economics":   ["economics (ba)", "ba economics"],
    "English":     ["english", "eng", "ba english"],
    "Law":         ["law", "llb", "llm"],
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


def resolve_program_name(name):
    return _ALIAS_TO_CANONICAL.get(name.strip().lower())


def normalize_course_code(code):
    return code.replace(' ', '').replace('-', '').upper()


# ═══════════════════════════════════════════════════════════════════════════════
# MD file readers
# ═══════════════════════════════════════════════════════════════════════════════

def read_programs_offered(md_path):
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
                c = resolve_program_name(clean)
                if c:
                    offered.add(c)
                else:
                    base = re.sub(r'\s*\(.*?\)', '', clean).strip()
                    c = resolve_program_name(base)
                    if c:
                        offered.add(c)
    except Exception as e:
        print(f"Warning: Could not read Programs Offered: {e}")
    return offered


def validate_program_name(program_name, md_path):
    canonical = resolve_program_name(program_name)
    if canonical is None:
        print(f"\n{'!'*60}")
        print(f"ERROR: NSU does not offer the program '{program_name}'.")
        print("Examples: cse, computer science, mic, microbiology, eee, bba, finance, law, mcj")
        print(f"{'!'*60}\n")
        sys.exit(1)
    offered = read_programs_offered(md_path)
    if offered and canonical not in offered:
        print(f"\n{'!'*60}")
        print(f"ERROR: NSU does not offer the program '{program_name}'.")
        print(f"(Resolved as '{canonical}', not found in Programs Offered list.)")
        print(f"{'!'*60}\n")
        sys.exit(1)
    return canonical


def read_nsu_course_list(md_path):
    nsu_courses = set()
    if not os.path.exists(md_path):
        return nsu_courses
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        sec = re.search(r'##\s+NSU Offered Course List(.*?)(?=\n#[^#]|\Z)',
                        content, re.IGNORECASE | re.DOTALL)
        if not sec:
            return nsu_courses
        for entry in re.findall(r'"([^"]+)"', sec.group(1)):
            for part in entry.split('/'):
                code = normalize_course_code(part.strip())
                if code:
                    nsu_courses.add(code)
        for m in re.finditer(r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b', sec.group(1)):
            nsu_courses.add(f"{m.group(1).upper()}{m.group(2).upper()}")
    except Exception as e:
        print(f"Warning: Could not read NSU course list: {e}")
    return nsu_courses


def check_non_nsu_courses(courses, nsu_course_list):
    if not nsu_course_list:
        return False, set()
    non_nsu = [c['code'] for c in courses
               if normalize_course_code(c['code']) not in nsu_course_list]
    if not non_nsu:
        return False, set()
    print(f"\n{'!'*60}")
    print("WARNING: Unrecognised course(s) in transcript:")
    for c in non_nsu:
        print(f"  - {c}")
    print(f"{'!'*60}")
    try:
        answer = input("\nIs this student a transfer student from a different university? (y/n): ").strip().lower()
    except EOFError:
        answer = 'n'
    if answer in ('y', 'yes'):
        print("\nTransfer student confirmed. Unrecognised courses will not be counted.")
        return True, {normalize_course_code(c) for c in non_nsu}
    print(f"\n{'!'*60}")
    print("ERROR: Transcript may not belong to an NSU student. Processing stopped.")
    print(f"{'!'*60}\n")
    sys.exit(1)


def find_program_section(content, program_name):
    pn = program_name.strip().lower()
    headers = list(re.finditer(r'^#\s+(.+?program.*)$', content, re.MULTILINE | re.IGNORECASE))
    for i, match in enumerate(headers):
        header = match.group(1).lower()
        is_match = False
        if pn == 'computer science':
            is_match = ('computer science' in header or 'cse' in header)
        elif pn == 'microbiology':
            is_match = 'microbiology' in header
        else:
            is_match = pn in header
        if is_match:
            start = match.start()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(content)
            return content[start:end]
    return None


def read_trail_course_prerequisites(md_path):
    """Return set of trail course codes that have real prerequisites."""
    trail_with_prereq = set()
    if not os.path.exists(md_path):
        return trail_with_prereq
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        sec = re.search(r'##\s+Major Electives\s*-\s*Trail Courses.*?(?=\n##[^#]|\Z)',
                        content, re.IGNORECASE | re.DOTALL)
        if not sec:
            return trail_with_prereq
        for line in sec.group(0).splitlines():
            if '|' not in line:
                continue
            clean = line.replace('**', '').strip().strip('|')
            cols = [c.strip() for c in clean.split('|')]
            if len(cols) < 3:
                continue
            course_cell = cols[0]
            if re.match(r'^[-\s]+$', course_cell.replace('|', '')):
                continue
            if re.search(r'course', course_cell, re.IGNORECASE):
                continue
            prereq_cell = cols[2].strip()
            has_prereq = (prereq_cell.lower() not in ('none', '-', '', 'prerequisites')
                          and bool(re.search(r'[A-Za-z]{2,4}\s*\d{3}', prereq_cell)))
            for part in re.split(r'[/,]', course_cell):
                m = re.match(r'^\s*([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\s*$', part.strip())
                if m and has_prereq:
                    trail_with_prereq.add(normalize_course_code(f"{m.group(1)}{m.group(2)}"))
    except Exception as e:
        print(f"Warning: Could not read trail prerequisites: {e}")
    return trail_with_prereq


def get_program_info(md_path, program_name):
    """
    Parse program section and return a comprehensive program_info dict.
    Keys:
        allowed_courses, capstone_courses, major_elective_credits,
        major_elective_courses, open_elective_credits, elective_credits,
        elective_courses, waivable_courses, alternative_courses,
        not_mandatory_courses, minor_programs, total_credits_required,
        internship_required, internship_codes
    """
    info = {
        'allowed_courses': set(),
        'capstone_courses': set(),
        'course_equivalences': {},   # code -> frozenset of alias codes
        'major_elective_credits': 0,
        'major_elective_courses': set(),
        'open_elective_credits': 0,
        'elective_credits': 0,
        'elective_courses': set(),
        'waivable_courses': [],
        'alternative_courses': [],
        'not_mandatory_courses': set(),
        'minor_programs': {},
        'total_credits_required': 0,
        'internship_required': False,
        'internship_codes': set(),
    }
    if not os.path.exists(md_path):
        return info
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        sec = find_program_section(content, program_name)
        if not sec:
            return info

        # ── Total credits ──────────────────────────────────────────────────
        cr_match = re.search(r'Total Credit[^|]*\|\s*\*{0,2}\s*(\d+)', sec, re.IGNORECASE)
        if cr_match:
            info['total_credits_required'] = int(cr_match.group(1))

        # ── All program courses ────────────────────────────────────────────
        for m in re.finditer(r'\b([A-Z]{2,})\s*(\d{3,4}[A-Z]?)\b', sec):
            dept, num = m.group(1).upper(), m.group(2).upper()
            if len(dept) >= 2 and len(num) >= 3:
                info['allowed_courses'].add(f"{dept}{num}")

        # ── Course equivalences (slash-pairs like BIO202/MIC101) ──────────
        # These are courses that share the same slot — satisfying ANY one of
        # the aliases satisfies the requirement for ALL of them.
        # Parse from table rows: | BIO202 / MIC101 | ...
        equivalences = {}   # code -> frozenset of equivalent codes (including itself)
        for line in sec.splitlines():
            if '|' not in line:
                continue
            clean = line.replace('**', '').replace('_', '').strip().strip('|')
            cols = [c.strip() for c in clean.split('|')]
            if not cols:
                continue
            course_cell = cols[0]
            # Must contain a slash to be an alias row
            if '/' not in course_cell:
                continue
            # Extract all course codes from this cell
            codes_in_cell = []
            for part in re.split(r'[/,]', course_cell):
                m2 = re.match(r'^\s*([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\s*$', part.strip())
                if m2:
                    codes_in_cell.append(normalize_course_code(f"{m2.group(1)}{m2.group(2)}"))
            if len(codes_in_cell) >= 2:
                group = frozenset(codes_in_cell)
                for code in codes_in_cell:
                    # Merge with any existing group this code belongs to
                    existing = equivalences.get(code, frozenset())
                    merged = group | existing
                    for c in merged:
                        equivalences[c] = merged
        info['course_equivalences'] = equivalences

        # ── Capstone / internship codes ───────────────────────────────────
        for cap_m in re.finditer(
                r'^#{1,3}\s+(?:Capstone|Internship|Research)[^\n]*\n(.*?)(?=\n#{1,3}\s|\Z)',
                sec, re.IGNORECASE | re.MULTILINE | re.DOTALL):
            for m in re.finditer(r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b', cap_m.group(1)):
                info['capstone_courses'].add(normalize_course_code(f"{m.group(1)}{m.group(2)}"))
        for cap_block in re.finditer(r'_Capstone[^_\n]*_\s*\n(.*?)(?=\n_|\n\n|\Z)',
                                     content, re.IGNORECASE | re.DOTALL):
            for entry in re.findall(r'"([^"]+)"', cap_block.group(1)):
                for part in entry.split('/'):
                    info['capstone_courses'].add(normalize_course_code(part.strip()))
        info['allowed_courses'] -= info['capstone_courses']

        # ── Internship/Research requirement ──────────────────────────────
        if re.search(r'Internship.*?mandatory|mandatory.*?Internship', sec, re.IGNORECASE | re.DOTALL):
            info['internship_required'] = True
        for m in re.finditer(r'\b(CSE\s*498[RI])\b', sec, re.IGNORECASE):
            info['internship_codes'].add(normalize_course_code(m.group(1)))
        # Also catch codes mentioned in the Internship section heading text
        internship_sec = re.search(
            r'##\s+Internship[^\n]*\n(.*?)(?=\n##|\Z)', sec, re.IGNORECASE | re.DOTALL)
        if internship_sec:
            info['internship_required'] = True
            for m in re.finditer(r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b',
                                  internship_sec.group(1)):
                info['internship_codes'].add(
                    normalize_course_code(f"{m.group(1)}{m.group(2)}"))

        # ── Major electives (CSE trail courses) ───────────────────────────
        maj_m = re.search(r'^#{1,3}\s+.*?Major Electives.*?Trail Courses.*?\((\d+)\s*Credits?\)',
                          sec, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if maj_m:
            info['major_elective_credits'] = int(maj_m.group(1))
            # Parse from the new table format
            trail_sec = re.search(
                r'##\s+Major Electives\s*-\s*Trail Courses.*?(?=\n##[^#]|\Z)',
                content, re.IGNORECASE | re.DOTALL)
            if trail_sec:
                prereq_only_codes = set()   # codes that appear ONLY in prerequisites column
                for line in trail_sec.group(0).splitlines():
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
                        m2 = re.match(r'^\s*([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\s*$', part.strip())
                        if m2:
                            info['major_elective_courses'].add(
                                normalize_course_code(f"{m2.group(1)}{m2.group(2)}"))
                    # Collect course codes from the prerequisites column (col index 2)
                    if len(cols) >= 3:
                        for d, n in re.findall(r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b', cols[2]):
                            prereq_only_codes.add(normalize_course_code(f"{d}{n}"))
                # Remove prereq-only codes that are not trail courses themselves
                # (they leaked into allowed_courses via the general course scanner)
                leak = prereq_only_codes - info['major_elective_courses']
                info['allowed_courses'] -= leak
                info['not_mandatory_courses'] -= leak
        # ── Open electives ────────────────────────────────────────────────
        oe_m = re.search(r'^#{1,3}\s+.*?(Open Elective|Free Elective).*?\((\d+)\s*Credits?\)',
                         sec, re.IGNORECASE | re.MULTILINE)
        if oe_m:
            info['open_elective_credits'] = int(oe_m.group(2))

        # ── Microbiology electives ─────────────────────────────────────────
        el_m = re.search(r'^#{1,3}\s+Electives.*?\((\d+)\s*Credits?\)', sec,
                         re.IGNORECASE | re.MULTILINE)
        if el_m:
            info['elective_credits'] = int(el_m.group(1))
            el_sec = re.search(r'##\s+Electives.*?(?=##|\Z)', sec, re.IGNORECASE | re.DOTALL)
            if el_sec:
                for dept, num in re.findall(
                        r'^\|\s*([A-Z]{2,})\s*(\d{3,4}[A-Z]?)\s*\|',
                        el_sec.group(0), re.MULTILINE | re.IGNORECASE):
                    info['elective_courses'].add(f"{dept.upper()}{num.upper()}")

        # ── Alternative / choose-one groups ──────────────────────────────
        alt_groups = []
        if program_name.lower() in ('microbiology', 'mic'):
            uc_sec = re.search(r'##\s+University Core.*?(?=\n##[^#]|\Z)', sec,
                               re.IGNORECASE | re.DOTALL)
            if uc_sec:
                uc_clean = uc_sec.group(0).replace('**', '')

                # Identify ranges covered by _Choose one_ sections so Pass 1
                # doesn't create sub-groups inside them.
                choose_one_ranges = []
                for sub in re.split(r'(?=\n###\s)', uc_clean):
                    if re.search(r'\n\s*_[Cc]hoose one', sub):
                        choose_one_ranges.append(sub)

                # Pass 1: per-row "Choose one" in Notes column → each slash-pair
                # is its own group, BUT only for rows NOT inside a _Choose one_ section
                for rm in re.finditer(
                        r'^\|\s*([^|]+?)\s*\|(?:[^|\n]*\|)*\s*[Cc]hoose one\s*\|?',
                        uc_clean, re.MULTILINE):
                    row_text = rm.group(0)
                    # Skip if this row is inside a _Choose one_ subsection
                    in_choose_one_section = any(row_text in sub for sub in choose_one_ranges)
                    if in_choose_one_section:
                        continue
                    codes_in_cell = re.findall(
                        r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b', rm.group(1))
                    if len(codes_in_cell) >= 2:
                        grp = []
                        for d, n in codes_in_cell:
                            code = f"{d.upper()}{n.upper()}"
                            if code not in grp:
                                grp.append(code)
                        if len(grp) >= 2 and sorted(grp) not in [sorted(g) for g in alt_groups]:
                            alt_groups.append(grp)

                # Pass 2: subsections with _Choose one_ label — ALL rows in the
                # table form ONE group (e.g. Social Sciences: choose 1 of 6 courses,
                # Humanities: choose 1 of 3).
                # Only read course codes from the FIRST column to avoid picking up
                # codes in Prerequisites/Notes columns.
                for sub in re.split(r'(?=\n###\s)', uc_clean):
                    sub = sub.strip()
                    if not re.search(r'\n\s*_[Cc]hoose one', sub):
                        continue
                    # Science section is handled by Pass 3 (option-column logic)
                    if re.search(r'###\s+Science', sub, re.IGNORECASE):
                        continue
                    tm = re.search(r'(\|.*?)(?=\n\s*_[Cc]hoose one)', sub, re.DOTALL)
                    if tm:
                        grp = []
                        for line in tm.group(1).splitlines():
                            if '|' not in line:
                                continue
                            first_col = line.strip().strip('|').split('|')[0].strip()
                            # Skip header/separator rows
                            if re.match(r'^[-\s]+$', first_col) or first_col.lower() == 'course':
                                continue
                            for d, n in re.findall(r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b',
                                                   first_col):
                                code = f"{d.upper()}{n.upper()}"
                                if code not in grp:
                                    grp.append(code)
                        if len(grp) >= 2 and sorted(grp) not in [sorted(g) for g in alt_groups]:
                            alt_groups.append(grp)
                # Pass 3: "Choose one pair" science section (BIO103/PHY107)
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
                        m = re.match(r'^\s*([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\s*$',
                                     course_cell)
                        opt = option_cell.strip().upper()
                        if m and opt and opt not in ('-', ''):
                            code = normalize_course_code(f"{m.group(1)}{m.group(2)}")
                            options.setdefault(opt, []).append(code)
                    if len(options) >= 2:
                        all_sci = []
                        for codes_in_opt in options.values():
                            all_sci.extend(codes_in_opt)
                        if len(all_sci) >= 2 and sorted(all_sci) not in [sorted(g) for g in alt_groups]:
                            alt_groups.append(all_sci)
        else:
            for rm in re.finditer(
                    r'^\|\s*([^|]+?)\s*\|(?:[^|\n]*\|)+\s*[Cc]hoose one[^|\n]*\|?',
                    sec, re.MULTILINE):
                codes_in_cell = re.findall(
                    r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b', rm.group(1))
                if len(codes_in_cell) >= 2:
                    grp = []
                    for d, n in codes_in_cell:
                        code = f"{d.upper()}{n.upper()}"
                        if code not in grp:
                            grp.append(code)
                    if len(grp) >= 2 and sorted(grp) not in [sorted(g) for g in alt_groups]:
                        alt_groups.append(grp)
        lab_pairs = {}
        processed_groups = []
        for grp in alt_groups:
            labs = [c for c in grp if c.endswith('L')]
            theories = [c for c in grp if not c.endswith('L')]
            if labs and theories and len(grp) > 2:
                paired = {lab[:-1]: lab for lab in labs if lab[:-1] in theories}
                if len(paired) >= 2:
                    for theory, lab in paired.items():
                        lab_pairs[theory] = lab
                        lab_pairs[lab] = theory
                    processed_groups.append(grp)
                    continue
            processed_groups.append(grp)
        alt_groups = processed_groups
        info['alternative_courses'] = alt_groups
        if lab_pairs:
            info['lab_pairs'] = lab_pairs

        # ── Remove prereq-only codes from allowed_courses ─────────────────
        # The global scanner picks up any course code in the section text,
        # including codes that only appear in Prerequisites columns (e.g. MAT120
        # for PHY107). Scan all table rows: collect course-column codes vs
        # prereq-column codes, then remove prereq-only ones.
        course_col_codes = set()
        prereq_col_codes = set()
        for line in sec.split('\n'):
            if '|' not in line:
                continue
            cols = [c.strip() for c in line.strip().strip('|').split('|')]
            if len(cols) < 2:
                continue
            # Course column is always col 0
            first = cols[0]
            if re.match(r'^[-\s]+$', first) or first.lower() in ('course', ''):
                continue
            for d, n in re.findall(r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b', first):
                course_col_codes.add(normalize_course_code(f"{d}{n}"))
            # Prerequisites column: typically col 2 (after Credits)
            for i, col in enumerate(cols[1:], 1):
                if i == 1:
                    continue  # Credits column — skip
                for d, n in re.findall(r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b', col):
                    prereq_col_codes.add(normalize_course_code(f"{d}{n}"))
        # Only remove codes that never appear in a course column
        prereq_only = prereq_col_codes - course_col_codes
        info['allowed_courses'] -= prereq_only
        info['not_mandatory_courses'] -= prereq_only

        # ── Not mandatory ─────────────────────────────────────────────────
        for d, n in re.findall(r'([A-Z]{2,})\s*(\d{3,})[^\n]*Not mandatory', sec, re.IGNORECASE):
            info['not_mandatory_courses'].add(f"{d.upper()}{n}")
        all_alt_codes = {code for g in alt_groups for code in g}
        info['not_mandatory_courses'] -= all_alt_codes

        # ── Waivable ──────────────────────────────────────────────────────
        for line in sec.split('\n'):
            lc = line.replace('_', '').replace('*', '')
            if 'waiv' in lc.lower() and '|' in line:
                for d, n in re.findall(r'\b([A-Z]{2,})\s*(\d{3,})\b', lc, re.IGNORECASE):
                    if len(d) >= 2:
                        code = f"{d.upper()}{n}"
                        if code not in info['waivable_courses']:
                            info['waivable_courses'].append(code)

        # ── Minor programs ────────────────────────────────────────────────
        minor_sec = re.search(r'##\s+Minor Programs.*?(?=\n##[^#]|\Z)', sec,
                              re.IGNORECASE | re.DOTALL)
        if minor_sec:
            for block in re.split(r'(?=\n###\s)', minor_sec.group(0)):
                hdr = re.match(r'###\s+(.+?)(?:\s*\(\d+\s*Credits?\))?\s*$',
                               block.strip(), re.MULTILINE)
                if not hdr:
                    continue
                minor_name = hdr.group(1).strip()
                # If any Notes column is marked **Additional**, only include those rows.
                # Otherwise (e.g. Minor in Physics) include all course code rows.
                has_additional = bool(re.search(r'\*\*Additional\*\*', block))
                minor_codes = set()
                for row in block.split('\n'):
                    if '|' not in row:
                        continue
                    if has_additional and '**additional**' not in row.lower():
                        continue
                    for d, n in re.findall(r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b', row):
                        minor_codes.add(normalize_course_code(f"{d}{n}"))
                if minor_codes:
                    info['minor_programs'][minor_name] = minor_codes
        # NOTE: not_mandatory update for minor courses is done AFTER all
        # category sets (ged, school_core, cse_core) are built below,
        # so required courses are never accidentally marked as optional.

        # ── CSE-specific: build category sets for audit ───────────────────
        if program_name.lower() in ('computer science', 'cse', 'cs'):
            # GED core
            ged_sec = re.search(r'##\s+GED.*?(?=\n##[^#]|\Z)', sec, re.IGNORECASE | re.DOTALL)
            if ged_sec:
                info['ged_courses'] = set()
                for m in re.finditer(r'\b([A-Z]{2,})\s*(\d{3,4}[A-Z]?)\b', ged_sec.group(0)):
                    d, n = m.group(1).upper(), m.group(2).upper()
                    if len(d) >= 2 and len(n) >= 3:
                        info['ged_courses'].add(f"{d}{n}")
            # School core
            school_sec = re.search(r'##\s+School Core.*?(?=\n##[^#]|\Z)', sec,
                                   re.IGNORECASE | re.DOTALL)
            if school_sec:
                info['school_core_courses'] = set()
                for m in re.finditer(r'\b([A-Z]{2,})\s*(\d{3,4}[A-Z]?)\b', school_sec.group(0)):
                    d, n = m.group(1).upper(), m.group(2).upper()
                    if len(d) >= 2 and len(n) >= 3:
                        info['school_core_courses'].add(f"{d}{n}")
            # CSE core
            cse_core_sec = re.search(r'##\s+CSE Core.*?(?=\n##[^#]|\Z)', sec,
                                     re.IGNORECASE | re.DOTALL)
            if cse_core_sec:
                info['cse_core_courses'] = set()
                for m in re.finditer(r'\b([A-Z]{2,})\s*(\d{3,4}[A-Z]?)\b', cse_core_sec.group(0)):
                    d, n = m.group(1).upper(), m.group(2).upper()
                    if len(d) >= 2 and len(n) >= 3:
                        info['cse_core_courses'].add(f"{d}{n}")
            # Capstone (4 credits)
            cap_sec = re.search(r'##\s+Capstone.*?(?=\n##[^#]|\Z)', sec,
                                re.IGNORECASE | re.DOTALL)
            if cap_sec:
                info['capstone_required_courses'] = set()
                for m in re.finditer(r'\b([A-Z]{2,})\s*(\d{3,4}[A-Z]?)\b', cap_sec.group(0)):
                    d, n = m.group(1).upper(), m.group(2).upper()
                    if len(d) >= 2 and len(n) >= 3:
                        info['capstone_required_courses'].add(f"{d}{n}")

            # MAT116 is required for CSE (prereq for MAT120/MAT125).
            # Its credits are deducted from CGPA when 130+ credits are completed,
            # but it is NOT optional — do not add to not_mandatory.

            # ── Ensure all category sets are in allowed_courses ───────────
            # The global course scanner may miss courses that only appear in
            # section headers or prerequisite text. Merge all known required
            # course sets so nothing is falsely excluded as "Not in program".
            info['allowed_courses'] |= info.get('ged_courses', set())
            info['allowed_courses'] |= info.get('school_core_courses', set())
            info['allowed_courses'] |= info.get('cse_core_courses', set())
            info['allowed_courses'] |= info.get('major_elective_courses', set())
            info['allowed_courses'] |= info.get('elective_courses', set())
            if info.get('capstone_required_courses'):
                info['allowed_courses'] |= info['capstone_required_courses']

        # ── Deferred: mark minor-only additional courses as not_mandatory ──
        # Done here (after all category sets are built) so required courses
        # that also appear in minor blocks (e.g. MAT120 in Minor in Math)
        # are NOT incorrectly marked as optional.
        required_courses = (info.get('ged_courses', set())
                            | info.get('school_core_courses', set())
                            | info.get('cse_core_courses', set()))
        for minor_codes in info['minor_programs'].values():
            optional_minor = minor_codes - required_courses
            info['not_mandatory_courses'] |= optional_minor

    except Exception as e:
        print(f"Warning: Error reading program info: {e}")
    return info


# ═══════════════════════════════════════════════════════════════════════════════
# Transcript reader & processing
# ═══════════════════════════════════════════════════════════════════════════════

def read_transcript(csv_path):
    courses = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                course = {
                    'code':     row.get('Course_Code', '').strip(),
                    'credits':  float(row.get('Credits', 0) or 0),
                    'grade':    row.get('Grade', '').strip().upper(),
                    'semester': row.get('Semester', '').strip(),
                }
                course['grade_points'] = GRADE_POINTS.get(course['grade'], None)
                course['passed'] = (course['grade'] in GRADE_POINTS
                                    and course['grade'] != 'F')
                courses.append(course)
    except FileNotFoundError:
        print(f"Error: Transcript not found: {csv_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading transcript: {e}")
        sys.exit(1)
    return courses


def process_retakes(courses):
    groups = defaultdict(list)
    for idx, course in enumerate(courses):
        groups[normalize_course_code(course['code'])].append((idx, course))
    for code, attempts in groups.items():
        if len(attempts) > 1:
            sorted_att = sorted(attempts,
                                key=lambda x: (-(x[1]['grade_points'] or 0), x[1]['semester']))
            courses[sorted_att[0][0]]['is_best_attempt'] = True
            for idx, _ in sorted_att[1:]:
                courses[idx]['is_best_attempt'] = False
        else:
            courses[attempts[0][0]]['is_best_attempt'] = True
    return courses


# ═══════════════════════════════════════════════════════════════════════════════
# Interactive selections  (mirrors L2 flow exactly)
# ═══════════════════════════════════════════════════════════════════════════════

def select_major_electives(courses, program_info, md_path):
    """Elective/trail selection for MIC; trail selection handled separately for CSE."""
    major_credits   = program_info.get('major_elective_credits', 0)
    elective_credits = program_info.get('elective_credits', 0)
    total_credits   = major_credits + elective_credits
    if total_credits <= 0:
        return [], set()

    elective_courses = program_info.get('elective_courses', set())
    major_courses    = program_info.get('major_elective_courses', set())
    is_microbiology  = elective_credits > 0 and major_credits == 0

    all_elective = elective_courses if is_microbiology else (major_courses | elective_courses)
    if not all_elective:
        return [], set()

    eligible = []
    seen = set()
    for c in courses:
        code = normalize_course_code(c['code'])
        if code in all_elective and code not in seen:
            if c['grade'] in GRADE_POINTS and c['grade'] != 'F':
                eligible.append(c)
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
    max_courses = total_credits // 3

    label = "ELECTIVES SELECTION (Microbiology)" if is_microbiology else "MAJOR/ELECTIVE COURSES SELECTION"
    print(f"\n{'='*60}\n{label}\n{'='*60}")
    print(f"Program requires {total_credits} credits of electives.")
    print(f"\nSelect up to {max_courses} course(s):")
    print("\nAvailable elective courses in your transcript:")
    for i, code in enumerate(codes, 1):
        c = course_options[code]
        print(f"  {i}. {c['code']:<15} - {c['credits']:.1f} credits, Grade: {c['grade']}")
    print()
    selection = input("> ").strip()
    selected, selected_codes = [], set()
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
                print(f"Selected {len(selected)} course(s) ({total:.1f} credits).")
        except:
            print("Invalid selection.")
    return selected, selected_codes


def select_cse_trails(all_transcript_courses, program_info):
    """CSE primary + secondary trail selection. Returns (selected_courses, selected_codes, excess_codes, primary_trail, secondary_trail, available_trails)."""
    trail_courses = program_info.get('major_elective_courses', set())
    if not trail_courses:
        return [], set(), set(), None, None, {}

    by_code = {}
    for c in all_transcript_courses:
        code = normalize_course_code(c['code'])
        if code in trail_courses and c['grade'] in GRADE_POINTS and c['grade'] != 'F':
            if code not in by_code:
                by_code[code] = c

    if not by_code:
        print("\n*No trail courses found in transcript.*")
        return [], set(), set(), None, None, {}

    available_trails = {}
    for trail_name, trail_list in CSE_TRAILS.items():
        found = [by_code[c] for c in trail_list if c in by_code]
        if found:
            available_trails[trail_name] = sorted(found, key=lambda x: (-(x['grade_points'] or 0), x['semester']))
    if not available_trails:
        print("\nNo trail courses found in transcript.")
        return [], set(), set()

    trail_names = list(available_trails.keys())

    # Primary
    print(f"\n{'='*60}\nPRIMARY TRAIL SELECTION (CSE)\n{'='*60}")
    print("Select your Primary Trail (minimum 2 courses = 6 credits):\n")
    for i, name in enumerate(trail_names, 1):
        cws = ", ".join(f"{c['code']}({c['grade']})" for c in available_trails[name])
        print(f"  {i}. {name}\n     Courses: {cws}")
    print()
    sel = input("> ").strip()
    primary_trail = None
    primary_codes = set()
    if sel:
        try:
            idx = int(sel.strip()) - 1
            if 0 <= idx < len(trail_names):
                primary_trail = trail_names[idx]
        except:
            pass
    if primary_trail:
        prim_courses = available_trails[primary_trail]
        print(f"\nSelect up to 2 courses from {primary_trail}:")
        for i, c in enumerate(prim_courses, 1):
            print(f"  {i}. {c['code']:<15} - {c['credits']:.1f} credits, Grade: {c['grade']}")
        print()
        sel2 = input("> ").strip()
        if sel2:
            try:
                total = 0
                for idx in [int(x.strip()) - 1 for x in sel2.split(',')]:
                    if 0 <= idx < len(prim_courses) and total < 6:
                        c = prim_courses[idx]
                        if total + c['credits'] <= 6:
                            primary_codes.add(normalize_course_code(c['code']))
                            total += c['credits']
            except:
                pass

    # Secondary
    sec_names = [t for t in trail_names if t != primary_trail]
    print(f"\n{'='*60}\nSECONDARY TRAIL SELECTION (CSE)\n{'='*60}")
    print("Select your Secondary Trail (1 course = 3 credits):\n")
    for i, name in enumerate(sec_names, 1):
        cws = ", ".join(f"{c['code']}({c['grade']})" for c in available_trails[name])
        print(f"  {i}. {name}\n     Courses: {cws}")
    print()
    sel3 = input("> ").strip()
    secondary_trail = None
    secondary_codes = set()
    if sel3:
        try:
            idx = int(sel3.strip()) - 1
            if 0 <= idx < len(sec_names):
                secondary_trail = sec_names[idx]
        except:
            pass
    if secondary_trail:
        sec_courses = available_trails[secondary_trail]
        print(f"\nSelect 1 course from {secondary_trail}:")
        for i, c in enumerate(sec_courses, 1):
            print(f"  {i}. {c['code']:<15} - {c['credits']:.1f} credits, Grade: {c['grade']}")
        print()
        sel4 = input("> ").strip()
        if sel4:
            try:
                idx = int(sel4.strip()) - 1
                if 0 <= idx < len(sec_courses) and sec_courses[idx]['credits'] <= 3:
                    secondary_codes.add(normalize_course_code(sec_courses[idx]['code']))
            except:
                pass

    all_selected = primary_codes | secondary_codes
    excess = {code for code in by_code if code not in all_selected}

    selected_objs = [by_code[c] for c in all_selected if c in by_code]
    return selected_objs, all_selected, excess, primary_trail, secondary_trail, available_trails


def find_courses_with_prerequisites(md_path):
    """Return set of course codes that have prerequisites listed in the program MD."""
    courses_with_prereqs = set()
    if not os.path.exists(md_path):
        return courses_with_prereqs
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        for line in content.split('\n'):
            line_clean = line.replace('**', '').replace('_', '')
            m = re.search(r'^[\|\s]*([A-Z]{2,4})\s*(\d{3,4}[A-Z]?)[\s\|]+(\d+)[^|]*\|([^|]+)',
                          line_clean, re.IGNORECASE)
            if m:
                prereq_part = m.group(4).strip()
                if prereq_part and prereq_part.lower() not in ['-', 'none', '']:
                    courses_with_prereqs.add(f"{m.group(1).upper()}{m.group(2).upper()}")
    except:
        pass
    return courses_with_prereqs


def select_open_electives(courses, program_info, selected_major_codes, md_path,
                          extra_excess_codes=None, alternative_codes=None,
                          auto_count_codes=None, minor_additional_codes=None,
                          transfer_codes=None, trail_prereq_codes=None):
    open_credits = program_info.get('open_elective_credits', 0)
    if open_credits <= 0:
        return [], set()

    allowed          = program_info.get('allowed_courses', set())
    capstone_codes   = {normalize_course_code(c) for c in program_info.get('capstone_courses', set())}
    internship_codes = {normalize_course_code(c) for c in program_info.get('internship_codes', set())}
    transfer         = set(transfer_codes) if transfer_codes else set()
    trail_with_prereq = set(trail_prereq_codes) if trail_prereq_codes else set()
    auto_counted     = set(auto_count_codes) if auto_count_codes else set()
    minor_extra      = set(minor_additional_codes) if minor_additional_codes else set()

    excess_major = set(selected_major_codes)
    if extra_excess_codes:
        excess_major.update(extra_excess_codes)
    if alternative_codes:
        excess_major.update(alternative_codes)
    if minor_extra:
        excess_major.update(minor_extra)
    # Minor courses appear in the open elective list labeled [Minor course].
    # select_minor_courses() runs afterward for any minor courses not picked here.

    if program_info.get('elective_courses'):
        for c in courses:
            code = normalize_course_code(c['code'])
            if (code in program_info['elective_courses']
                    and code not in selected_major_codes
                    and c['grade'] in GRADE_POINTS and c['grade'] != 'F'):
                excess_major.add(code)

    not_mandatory    = program_info.get('not_mandatory_courses', set())
    courses_with_prereqs = find_courses_with_prerequisites(md_path)

    all_passing = []
    for c in courses:
        code = normalize_course_code(c['code'])
        if code in selected_major_codes: continue
        if code in auto_counted:         continue
        if not c.get('is_best_attempt', True): continue
        if c['grade'] not in GRADE_POINTS or c['grade'] == 'F': continue
        if code.endswith('L'):           continue
        if code in transfer:             continue
        if code in capstone_codes:       continue
        if code in internship_codes:     continue
        if code in trail_with_prereq:    continue
        # Mirror L2 logic:
        # A course is an open elective candidate if it is outside the required
        # program structure (not in allowed) OR it is explicitly surplus/optional
        # (in excess_major or not_mandatory).
        # However courses that have prerequisites are excluded unless they are
        # already in excess_major (student took them and they count as surplus).
        if code not in allowed or code in excess_major or code in not_mandatory:
            if code not in courses_with_prereqs or code in excess_major:
                all_passing.append(c)

    if not all_passing:
        print("No passed courses available to select as open electives.")
        return [], set()

    all_passing.sort(key=lambda x: (-(x['grade_points'] or 0), x['semester']))
    course_options = {}
    for c in all_passing:
        code = normalize_course_code(c['code'])
        if code not in course_options:
            course_options[code] = c
    codes = sorted(course_options.keys())
    max_courses = open_credits // 3

    is_mic = program_info.get('elective_credits', 0) > 0 and program_info.get('major_elective_credits', 0) == 0
    label = "FREE ELECTIVES" if is_mic else "OPEN/FREE ELECTIVES"
    core_alt = set(alternative_codes) if alternative_codes else set()

    print(f"\n{'='*60}\n{label} SELECTION\n{'='*60}")
    print(f"Program allows {open_credits} credits of open/free electives.")
    print(f"\nSelect up to {max_courses} course(s):")
    print("\nAvailable courses:")
    for i, code in enumerate(codes, 1):
        c = course_options[code]
        lbl = " [University Core alternative]" if code in core_alt else \
              " [Minor course]" if code in minor_extra else ""
        print(f"  {i}. {c['code']:<15} - {c['credits']:.1f} credits, Grade: {c['grade']}{lbl}")
    print()
    selection = input("> ").strip()
    selected, selected_codes = [], set()
    if selection:
        try:
            total = 0
            for idx in [int(x.strip()) - 1 for x in selection.split(',')]:
                if 0 <= idx < len(codes):
                    code = codes[idx]
                    c = course_options[code]
                    if total + c['credits'] <= open_credits:
                        selected.append(c)
                        selected_codes.add(code)
                        total += c['credits']
            if selected:
                print(f"Selected {len(selected)} course(s) ({total:.1f} credits).")
        except:
            print("Invalid selection.")
    return selected, selected_codes


def select_minor_courses(courses, program_info, already_open_codes=None):
    """
    Detect minor program courses in transcript and ask if student is pursuing a minor.
    Returns (selected_codes, rejected_codes).
    selected_codes  — count toward graduation via minor
    rejected_codes  — in transcript but minor not pursued; will be excluded
    """
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
        found = sorted([in_transcript[c] for c in add_codes if c in in_transcript],
                       key=lambda x: x['code'])
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
        print("  -> No minor declared. Minor-only courses will be excluded from audit.")
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
    print("Select which courses count toward graduation")
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


def ask_waivers(courses, waivable_courses, program_name=""):
    pn = program_name.lower()
    if pn in ('computer science', 'microbiology'):
        to_ask = ['ENG102', 'MAT112']
    else:
        to_ask = list(waivable_courses) if waivable_courses else []
    if not to_ask:
        return {}
    print(f"\n{'='*60}\nWAIVER QUESTIONS\n{'='*60}")
    print("Waived courses are exempt from the requirement.")
    waivers = {}
    for code in to_ask:
        try:
            ans = input(f"\nWas {code} waived for this student? (y/n): ").strip().lower()
            waivers[code] = ans in ('y', 'yes')
            print(f"  -> {code} {'WAIVED' if waivers[code] else 'not waived'}")
        except EOFError:
            waivers[code] = False
    return waivers


def get_alternative_and_not_mandatory_codes(courses, program_info):
    auto_count_codes, open_elective_codes, excluded_alternative_codes = set(), set(), set()
    lab_pairs = program_info.get('lab_pairs', {})
    for group in program_info.get('alternative_courses', []):
        theory_in = [c for c in group if not c.endswith('L')]
        lab_in    = [c for c in group if c.endswith('L')]
        if lab_in and theory_in:
            passing_theory, in_transcript = [], set()
            for c in courses:
                code = normalize_course_code(c['code'])
                if code in theory_in:
                    in_transcript.add(code)
                    if c['grade'] in GRADE_POINTS and c['grade'] != 'F':
                        passing_theory.append((code, c.get('grade_points', 0) or 0, c))
            if len(passing_theory) > 1:
                passing_theory.sort(key=lambda x: -x[1])
                auto_count_codes.add(passing_theory[0][0])
                pl = lab_pairs.get(passing_theory[0][0])
                if pl: auto_count_codes.add(pl)
                for i in range(1, len(passing_theory)):
                    open_elective_codes.add(passing_theory[i][0])
                    el = lab_pairs.get(passing_theory[i][0])
                    if el: open_elective_codes.add(el)
            elif len(passing_theory) == 1:
                auto_count_codes.add(passing_theory[0][0])
                pl = lab_pairs.get(passing_theory[0][0])
                if pl: auto_count_codes.add(pl)
            for code in in_transcript:
                if code not in auto_count_codes and code not in open_elective_codes:
                    excluded_alternative_codes.add(code)
                    pl = lab_pairs.get(code)
                    if pl: excluded_alternative_codes.add(pl)
        else:
            passing, in_transcript = [], set()
            for c in courses:
                code = normalize_course_code(c['code'])
                if code in group:
                    in_transcript.add(code)
                    if c['grade'] in GRADE_POINTS and c['grade'] != 'F':
                        passing.append((code, c.get('grade_points', 0) or 0, c))
            if len(passing) > 1:
                passing.sort(key=lambda x: -x[1])
                auto_count_codes.add(passing[0][0])
                for i in range(1, len(passing)):
                    open_elective_codes.add(passing[i][0])
            elif len(passing) == 1:
                auto_count_codes.add(passing[0][0])
            for code in in_transcript:
                if code not in auto_count_codes and code not in open_elective_codes:
                    excluded_alternative_codes.add(code)

    open_elective_codes -= auto_count_codes
    return auto_count_codes, open_elective_codes, excluded_alternative_codes


# ═══════════════════════════════════════════════════════════════════════════════
# Audit engine
# ═══════════════════════════════════════════════════════════════════════════════

def run_audit(courses, program_info, major_codes, open_codes, waivers,
              excluded_alternative_codes, transfer_codes,
              trail_prereq_codes=None, minor_rejected_codes=None,
              primary_trail=None, secondary_trail=None, available_trails=None,
              open_elective_pool_codes=None):
    """
    Classify every course and build audit data structures.

    Returns
    -------
    counted_courses   : list — best attempt, passing, counts toward graduation
    retaken_courses   : list — non-best attempts
    waived_courses    : list — waived (excluded from CGPA)
    excluded_courses  : list — capstone, internship, transfer, non-credit, W/I/F
    passed_codes      : set  — normalised codes of all passing best-attempt courses
    total_credits_counted : float
    cgpa              : float
    total_grade_points: float
    cgpa_credits      : float
    """
    transfer       = set(transfer_codes) if transfer_codes else set()
    trail_prereq   = set(trail_prereq_codes) if trail_prereq_codes else set()
    minor_rejected = set(minor_rejected_codes) if minor_rejected_codes else set()
    oe_pool        = set(open_elective_pool_codes) if open_elective_pool_codes else set()
    allowed        = program_info.get('allowed_courses', set())
    capstone_codes = {normalize_course_code(c) for c in program_info.get('capstone_courses', set())}
    internship_codes = {normalize_course_code(c) for c in program_info.get('internship_codes', set())}
    not_mandatory  = program_info.get('not_mandatory_courses', set())
    transcript_codes = {normalize_course_code(c['code']) for c in courses}

    counted_courses = []
    retaken_courses = []
    waived_courses  = []
    excluded_courses = []
    passed_codes    = set()
    total_credits_counted = 0.0
    total_grade_points = 0.0
    cgpa_credits       = 0.0

    for course in courses:
        code    = normalize_course_code(course['code'])
        grade   = course['grade']
        credits = course['credits']

        # Suppress non-credit labs absorbed by theory course
        if code in NON_CREDIT_LABS and NON_CREDIT_LABS[code] in transcript_codes:
            continue

        # Retake
        if not course.get('is_best_attempt', True):
            retaken_courses.append(course)
            continue

        # Waived
        if code in waivers and waivers[code]:
            waived_courses.append(course)
            continue

        # Capstone / internship with non-letter grades (S, P etc.):
        # These can't enter GRADE_POINTS calculation but we still need to
        # record them as satisfied for the deficiency checker.
        # Capstone courses with regular letter grades fall through to the
        # normal counting path below and DO count toward CGPA.
        if code in capstone_codes or code in internship_codes:
            if grade in NON_GRADE_ENTRIES or grade not in GRADE_POINTS:
                # S/P/W/I grade — excluded from CGPA but mark as completed
                if grade in {'S', 'P'}:
                    passed_codes.add(code)
                excluded_courses.append({**course,
                                         '_reason': 'Capstone/Internship (S/P grade, not in CGPA)'})
                continue
            # Letter grade — fall through to normal CGPA counting below

        # Non-grade (W, I, S …) for regular courses
        if grade in NON_GRADE_ENTRIES or grade not in GRADE_POINTS:
            excluded_courses.append({**course, '_reason': f'Grade: {grade}'})
            continue

        # Zero credits
        if credits <= 0:
            # 0-credit lab whose theory course is also in transcript → absorbed
            # into the theory course, not shown separately at all.
            if code.endswith('L') and code[:-1] in transcript_codes:
                continue
            # 0-credit capstone/internship still counts (completion matters)
            if code in capstone_codes or code in internship_codes:
                pass   # fall through to counting logic below
            else:
                excluded_courses.append({**course, '_reason': 'Zero credits'})
                continue

        # Transfer credit
        if code in transfer:
            excluded_courses.append({**course, '_reason': 'Transfer credit (not counted)'})
            continue

        # Failed
        if grade == 'F':
            excluded_courses.append({**course, '_reason': 'Failed (F)'})
            continue

        # Passed regular course
        passed_codes.add(code)

        # Does it count toward graduation?
        # Capstone/internship only auto-counts if it belongs to this program
        # (i.e. the program has capstone requirements). Foreign capstone courses
        # (e.g. CSE299 when running under MIC) are excluded unless picked as open elective.
        program_has_capstone = bool(program_info.get('capstone_required_courses') or
                                    program_info.get('internship_required'))
        in_allowed = (code in allowed and code not in not_mandatory
                      and code not in excluded_alternative_codes
                      and code not in oe_pool)
        counts = in_allowed or code in major_codes or code in open_codes \
                 or (program_has_capstone and (code in capstone_codes or code in internship_codes))

        if counts:
            counted_courses.append(course)
            total_credits_counted += credits
            gp = GRADE_POINTS[grade]
            total_grade_points += credits * gp
            cgpa_credits       += credits
        else:
            if code in excluded_alternative_codes:
                reason = 'University core excess'
            elif code in oe_pool and code not in open_codes:
                reason = 'University core alternative (not selected)'
            elif code in minor_rejected:
                reason = 'Minor not pursued'
            elif code in trail_prereq and code not in major_codes:
                reason = 'CSE trail course (not open elective)'
            else:
                reason = 'Not in program'
            excluded_courses.append({**course, '_reason': reason})

    # MAT116 deduction (CSE only): if total counted credits >= 130,
    # MAT116's credits and grade points are removed from the CGPA calculation.
    mat116 = normalize_course_code('MAT116')
    if cgpa_credits >= 130:
        for c in list(counted_courses):
            if normalize_course_code(c['code']) == mat116:
                gp_deduct = GRADE_POINTS.get(c['grade'], 0)
                total_grade_points  -= c['credits'] * gp_deduct
                cgpa_credits        -= c['credits']
                total_credits_counted -= c['credits']
                counted_courses.remove(c)
                excluded_courses.append({**c,
                    '_reason': 'MAT116 deducted (130+ credits completed)'})
                break

    # NSU: calculate to 3 decimal places (truncate), then ceiling to 2dp for display
    raw_cgpa = total_grade_points / cgpa_credits if cgpa_credits > 0 else 0.0
    cgpa = math.ceil(int(raw_cgpa * 1000) / 1000 * 100) / 100
    return (counted_courses, retaken_courses, waived_courses, excluded_courses,
            passed_codes, total_credits_counted, cgpa, total_grade_points, cgpa_credits)


# ═══════════════════════════════════════════════════════════════════════════════
# Deficiency checker
# ═══════════════════════════════════════════════════════════════════════════════

def check_deficiencies(program_info, passed_codes, waivers, major_codes, open_codes,
                       total_credits_counted, cgpa,
                       elective_selected_codes, open_elective_selected_codes,
                       primary_trail, secondary_trail, available_trails,
                       program_name):
    """
    Identify all reasons a student cannot graduate yet.
    Returns list of deficiency dicts: {category, description, severity}
    severity: 'BLOCKER' | 'WARNING'
    """
    deficiencies = []
    pn = program_name.lower()
    is_cse = pn == 'computer science'
    is_mic = pn == 'microbiology'

    # ── Total credits ──────────────────────────────────────────────────────
    required_total = program_info.get('total_credits_required', 0)
    if required_total > 0 and total_credits_counted < required_total:
        deficit = required_total - total_credits_counted
        deficiencies.append({
            'category': 'Total Credits',
            'description': f"Need {required_total} credits to graduate; "
                           f"only {total_credits_counted:.1f} counted. "
                           f"Still need {deficit:.1f} more credits.",
            'severity': 'BLOCKER'
        })

    # ── CGPA ──────────────────────────────────────────────────────────────
    if cgpa < 2.0:
        deficiencies.append({
            'category': 'CGPA',
            'description': f"CGPA is {cgpa:.2f}, below the minimum 2.0 required for graduation. "
                           f"Student is on ACADEMIC PROBATION.",
            'severity': 'BLOCKER'
        })

    # ── Mandatory courses (allowed set minus optional/elective/capstone) ──
    allowed = program_info.get('allowed_courses', set())
    capstone_codes = {normalize_course_code(c) for c in program_info.get('capstone_courses', set())}
    internship_codes = {normalize_course_code(c) for c in program_info.get('internship_codes', set())}
    elective_courses = program_info.get('elective_courses', set())
    major_elective_courses = program_info.get('major_elective_courses', set())
    not_mandatory = program_info.get('not_mandatory_courses', set())
    alt_all = {code for g in program_info.get('alternative_courses', []) for code in g}
    equivalences = program_info.get('course_equivalences', {})

    # Minor additional courses are optional — never block graduation
    all_minor_codes = {normalize_course_code(c)
                       for codes in program_info.get('minor_programs', {}).values()
                       for c in codes}

    # Build set of courses that are fixed requirements (not optional/elective)
    mandatory_pool = (allowed
                      - elective_courses
                      - major_elective_courses
                      - not_mandatory
                      - alt_all
                      - all_minor_codes)

    # Build set of passed + waived codes
    satisfied = set(passed_codes)
    for code, waived in waivers.items():
        if waived:
            satisfied.add(normalize_course_code(code))

    def is_satisfied(code):
        """True if code itself OR any of its equivalents is in satisfied.
        0-credit labs are auto-satisfied when their theory course is satisfied."""
        if code in satisfied:
            return True
        for alias in equivalences.get(code, frozenset()):
            if alias in satisfied:
                return True
        # 0-credit lab: satisfied if the corresponding theory course is satisfied
        if code.endswith('L') and is_satisfied(code[:-1]):
            return True
        return False

    # Alternative groups: at least one from each group must be satisfied
    for group in program_info.get('alternative_courses', []):
        theory_group = [c for c in group if not c.endswith('L')]
        if any(is_satisfied(c) for c in theory_group):
            continue  # at least one taken — good
        options = ' / '.join(theory_group)
        deficiencies.append({
            'category': 'Missing Core Course (Choose One)',
            'description': f"None of the required alternatives taken: {options}",
            'severity': 'BLOCKER'
        })

    # Direct mandatory courses
    # Deduplicate: if several codes are equivalent, only report the group once
    # when none of them are satisfied.
    reported_groups = set()
    missing_mandatory = []
    for code in sorted(mandatory_pool):
        if is_satisfied(code):
            continue
        # Check if this equivalence group was already reported
        group_key = equivalences.get(code, frozenset({code}))
        canonical = min(group_key)   # use the alphabetically smallest as group key
        if canonical in reported_groups:
            continue
        reported_groups.add(canonical)
        # Show the full slash-pair so the output is informative
        if len(group_key) > 1:
            aliases = ' / '.join(sorted(group_key))
            missing_mandatory.append(aliases)
        else:
            missing_mandatory.append(code)

    if missing_mandatory:
        deficiencies.append({
            'category': 'Missing Mandatory Courses',
            'description': f"{len(missing_mandatory)} mandatory course(s) not yet passed: "
                           + ', '.join(missing_mandatory),
            'severity': 'BLOCKER'
        })

    # ── Capstone (CSE: CSE299, CSE499A, CSE499B) ──────────────────────────
    cap_required = program_info.get('capstone_required_courses', set())
    if cap_required:
        missing_cap = sorted(c for c in cap_required if not is_satisfied(c))
        if missing_cap:
            deficiencies.append({
                'category': 'Capstone',
                'description': f"Missing capstone course(s): {', '.join(missing_cap)}",
                'severity': 'BLOCKER'
            })

    # ── Internship/Research (CSE) ──────────────────────────────────────────
    if program_info.get('internship_required'):
        if not any(is_satisfied(normalize_course_code(c)) for c in internship_codes):
            deficiencies.append({
                'category': 'Internship/Research',
                'description': f"Mandatory Internship/Research not completed "
                               f"({' / '.join(sorted(internship_codes))})",
                'severity': 'BLOCKER'
            })

    # ── CSE: Trail courses ─────────────────────────────────────────────────
    if is_cse:
        trail_credits_required = program_info.get('major_elective_credits', 9)
        trail_credits_taken = sum(
            3 for c in major_codes  # each trail course = 3 credits
        )
        if not major_codes:
            deficiencies.append({
                'category': 'Trail Courses (Major Electives)',
                'description': f"No trail courses selected. {trail_credits_required} credits "
                               f"required (min 2 from one trail, 1 from another). "
                               "Student cannot graduate without completing trail courses.",
                'severity': 'BLOCKER'
            })
        elif len(major_codes) < 3:
            deficiencies.append({
                'category': 'Trail Courses (Major Electives)',
                'description': f"Only {len(major_codes)} trail course(s) selected "
                               f"({trail_credits_taken} credits); "
                               f"{trail_credits_required} credits required.",
                'severity': 'BLOCKER'
            })
        elif not primary_trail:
            deficiencies.append({
                'category': 'Trail Courses (Major Electives)',
                'description': "Primary trail not declared.",
                'severity': 'WARNING'
            })
        elif not secondary_trail:
            deficiencies.append({
                'category': 'Trail Courses (Major Electives)',
                'description': "Secondary trail not declared.",
                'severity': 'WARNING'
            })

    # ── MIC: Electives ─────────────────────────────────────────────────────
    if is_mic:
        el_required  = program_info.get('elective_credits', 9)
        el_taken_cred = len(elective_selected_codes) * 3
        if not elective_selected_codes:
            deficiencies.append({
                'category': 'Electives',
                'description': f"No elective courses selected. {el_required} credits "
                               f"required (3 courses from elective list). "
                               "Student cannot graduate without completing electives.",
                'severity': 'BLOCKER'
            })
        elif el_taken_cred < el_required:
            deficiencies.append({
                'category': 'Electives',
                'description': f"Only {el_taken_cred} elective credits selected; "
                               f"{el_required} required.",
                'severity': 'BLOCKER'
            })

    # ── Open / free electives ──────────────────────────────────────────────
    oe_required = program_info.get('open_elective_credits', 0)
    if oe_required > 0:
        oe_taken_cred = len(open_elective_selected_codes) * 3
        if not open_elective_selected_codes:
            deficiencies.append({
                'category': 'Open/Free Electives',
                'description': f"No open/free elective courses selected. "
                               f"{oe_required} credits required. "
                               "Student cannot graduate without completing open electives.",
                'severity': 'BLOCKER'
            })
        elif oe_taken_cred < oe_required:
            deficiencies.append({
                'category': 'Open/Free Electives',
                'description': f"Only {oe_taken_cred} open elective credits selected; "
                               f"{oe_required} required.",
                'severity': 'BLOCKER'
            })

    return deficiencies


# ═══════════════════════════════════════════════════════════════════════════════
# Output formatter
# ═══════════════════════════════════════════════════════════════════════════════

def format_report(program_name, counted_courses, retaken_courses, waived_courses,
                  excluded_courses, deficiencies,
                  total_credits_counted, cgpa, cgpa_credits, total_grade_points,
                  total_credits_required, waivers,
                  # CSE trail data
                  primary_trail=None, secondary_trail=None, available_trails=None, major_codes=None,
                  # MIC elective data
                  elective_selected=None, elective_required_credits=0,
                  # Open elective data
                  open_elective_selected=None, open_elective_required_credits=0):

    W = 110
    lines = []

    def section(title):
        lines.append("")
        lines.append("=" * W)
        lines.append(f"  {title}")
        lines.append("=" * W)

    def sub_section(title):
        lines.append("")
        lines.append("-" * W)
        lines.append(f"  {title}")
        lines.append("-" * W)

    is_cse = 'computer science' in program_name.lower() or program_name.lower() in ('cse', 'cs')
    is_mic = 'microbiology' in program_name.lower() or program_name.lower() == 'mic'

    section(f"NSU AUDIT & DEFICIENCY REPORT — {program_name.upper()}")
    lines.append("")

    # ── Counted courses ────────────────────────────────────────────────────
    sub_section("COURSES COUNTED TOWARD GRADUATION (Best Attempts)")
    lines.append(f"  {'Course':<14} {'Credits':>7}  {'Grade':<6}  {'Semester':<14}  "
                 f"{'Grade Pts':>9}")
    lines.append("  " + "-" * (W - 2))
    for c in counted_courses:
        gp = GRADE_POINTS.get(c['grade'], 0.0) * c['credits']
        lines.append(f"  {c['code']:<14} {c['credits']:>7.1f}  {c['grade']:<6}  "
                     f"{c['semester']:<14}  {gp:>9.2f}")
    lines.append("  " + "-" * (W - 2))
    lines.append(f"  {'TOTAL':<14} {total_credits_counted:>7.1f}  {'':6}  {'':14}  "
                 f"{total_grade_points:>9.2f}")

    # ── Retaken courses ────────────────────────────────────────────────────
    if retaken_courses:
        sub_section("RETAKEN COURSES (Previous Attempts — Not Counted)")
        lines.append(f"  {'Course':<14} {'Credits':>7}  {'Grade':<6}  {'Semester':<14}  Note")
        lines.append("  " + "-" * (W - 2))
        for c in retaken_courses:
            lines.append(f"  {c['code']:<14} {c['credits']:>7.1f}  {c['grade']:<6}  "
                         f"{c['semester']:<14}  Previous attempt")
        lines.append("  " + "-" * (W - 2))

    # ── Waived courses ─────────────────────────────────────────────────────
    if waived_courses:
        sub_section("WAIVED COURSES (Exempt — Not in CGPA)")
        lines.append(f"  {'Course':<14} {'Credits':>7}  {'Status':<20}")
        lines.append("  " + "-" * (W - 2))
        for c in waived_courses:
            lines.append(f"  {c['code']:<14} {c['credits']:>7.1f}  {'Waiver granted':<20}")
        lines.append("  " + "-" * (W - 2))

    # ── Excluded / not counted ─────────────────────────────────────────────
    if excluded_courses:
        sub_section("EXCLUDED / NOT COUNTED")
        lines.append(f"  {'Course':<14} {'Credits':>7}  {'Grade':<6}  {'Semester':<14}  Reason")
        lines.append("  " + "-" * (W - 2))
        for c in excluded_courses:
            reason = c.get('_reason', '')
            lines.append(f"  {c['code']:<14} {c['credits']:>7.1f}  {c['grade']:<6}  "
                         f"{c['semester']:<14}  {reason}")
        lines.append("  " + "-" * (W - 2))

    # ── CSE: Trail courses ─────────────────────────────────────────────────
    if is_cse:
        sub_section("TRAIL COURSES (Major Electives)")
        major_set = set(major_codes or [])
        if not major_set:
            lines.append("  No trail courses selected.")
        else:
            lines.append(f"  {'Trail':<40} {'Course':<12} {'Grade':<8} Counted")
            lines.append("  " + "-" * (W - 2))
            if available_trails:
                for trail_name, trail_courses_list in available_trails.items():
                    for c in trail_courses_list:
                        code = normalize_course_code(c['code'])
                        counted = "Yes" if code in major_set else "No (excess)"
                        lines.append(f"  {trail_name:<40} {c['code']:<12} {c['grade']:<8} {counted}")
            lines.append("  " + "-" * (W - 2))
            if primary_trail:
                lines.append(f"  Primary Trail:   {primary_trail}")
            if secondary_trail:
                lines.append(f"  Secondary Trail: {secondary_trail}")

    # ── MIC: Electives ─────────────────────────────────────────────────────
    if is_mic and elective_required_credits > 0:
        sub_section(f"ELECTIVES ({elective_required_credits} Credits Required)")
        elective_sel = elective_selected or []
        if not elective_sel:
            lines.append("  No elective courses selected.")
        else:
            lines.append(f"  {'Course':<14} {'Credits':>7}  {'Grade':<6}  {'Semester':<14}")
            lines.append("  " + "-" * (W - 2))
            for c in elective_sel:
                lines.append(f"  {c['code']:<14} {c['credits']:>7.1f}  {c['grade']:<6}  "
                             f"{c['semester']:<14}")
            lines.append("  " + "-" * (W - 2))
            el_cred = sum(c['credits'] for c in elective_sel)
            lines.append(f"  Elective credits taken: {el_cred:.1f} / {elective_required_credits} required")

    # ── Open / Free electives ──────────────────────────────────────────────
    if open_elective_required_credits > 0:
        sub_section(f"OPEN / FREE ELECTIVES ({open_elective_required_credits} Credits Required)")
        oe_list = open_elective_selected or []
        if not oe_list:
            lines.append("  No open/free elective courses selected.")
        else:
            lines.append(f"  {'Course':<14} {'Credits':>7}  {'Grade':<6}  {'Semester':<14}")
            lines.append("  " + "-" * (W - 2))
            for c in oe_list:
                lines.append(f"  {c['code']:<14} {c['credits']:>7.1f}  {c['grade']:<6}  "
                             f"{c['semester']:<14}")
            lines.append("  " + "-" * (W - 2))
            oe_cred = sum(c['credits'] for c in oe_list)
            lines.append(f"  Open elective credits taken: {oe_cred:.1f} / "
                         f"{open_elective_required_credits} required")

    # ── Deficiency Report ──────────────────────────────────────────────────
    sub_section("DEFICIENCY REPORT")
    blockers  = [d for d in deficiencies if d['severity'] == 'BLOCKER']
    warnings  = [d for d in deficiencies if d['severity'] == 'WARNING']

    if not deficiencies:
        lines.append("  ✓  No deficiencies found.")
    else:
        if blockers:
            lines.append(f"  BLOCKERS  ({len(blockers)} — student CANNOT graduate with these unresolved)")
            lines.append("  " + "-" * (W - 2))
            for i, d in enumerate(blockers, 1):
                lines.append(f"  [{i:02d}] [{d['category']}]")
                lines.append(f"       {d['description']}")
                lines.append("")
        if warnings:
            lines.append(f"  WARNINGS  ({len(warnings)})")
            lines.append("  " + "-" * (W - 2))
            for i, d in enumerate(warnings, 1):
                lines.append(f"  [{i:02d}] [{d['category']}]")
                lines.append(f"       {d['description']}")
                lines.append("")

    # ── Graduation Summary ─────────────────────────────────────────────────
    section("GRADUATION SUMMARY")
    can_graduate = len(blockers) == 0
    on_probation = cgpa < 2.0
    lines.append(f"  Program:               {program_name}")
    lines.append(f"  Credits Required:      {total_credits_required}")
    lines.append(f"  Credits Counted:       {total_credits_counted:.1f}")
    remaining = max(0.0, total_credits_required - total_credits_counted)
    lines.append(f"  Credits Remaining:     {remaining:.1f}")
    lines.append(f"  CGPA:                  {cgpa:.2f}")
    lines.append(f"  Graduation Status:     {'✓ CAN GRADUATE' if can_graduate else '✗ CANNOT GRADUATE'}")
    if on_probation:
        lines.append(f"  Academic Probation:    ⚠ YES — CGPA {cgpa:.2f} < 2.0")
    else:
        lines.append(f"  Academic Probation:    No")
    if deficiencies:
        lines.append(f"  Blockers:              {len(blockers)}")
        lines.append(f"  Warnings:              {len(warnings)}")
    else:
        lines.append("  Deficiencies:          None")
    lines.append("")
    lines.append("=" * W)
    lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='L3 Audit & Deficiency Reporter (Step 3 of 3)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python L3_audit_deficiency_reporter.py transcript.csv cse NSU_Program.md
  python L3_audit_deficiency_reporter.py transcript.csv mic NSU_Program.md -o audit.txt
        """
    )
    parser.add_argument('csv_file',           help='Path to transcript CSV')
    parser.add_argument('program_name',       help='Program name (e.g. cse, mic, eee)')
    parser.add_argument('program_knowledge',  help='Path to NSU_Program.md')
    parser.add_argument('-o', '--output',     help='Save report to file', default=None)
    args = parser.parse_args()

    # ── Validate program ──────────────────────────────────────────────────
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

    print(f"Program: {canonical_program}")

    # ── Read transcript ───────────────────────────────────────────────────
    print(f"Reading transcript: {args.csv_file}")
    courses = read_transcript(args.csv_file)
    if not courses:
        print("No courses found in transcript.")
        sys.exit(0)

    # ── NSU course list check ─────────────────────────────────────────────
    nsu_course_list = read_nsu_course_list(args.program_knowledge)
    is_transfer, transfer_codes = check_non_nsu_courses(courses, nsu_course_list)

    # ── Process retakes ───────────────────────────────────────────────────
    courses = process_retakes(courses)

    # ── Program info ──────────────────────────────────────────────────────
    program_info = get_program_info(args.program_knowledge, canonical_program)

    is_cse = canonical_program == "Computer Science"
    is_mic = canonical_program == "Microbiology"

    # ── Trail prereq codes (for non-CSE blocking) ─────────────────────────
    trail_prereq_codes = set() if is_cse else read_trail_course_prerequisites(args.program_knowledge)

    # ── Alternative / choose-one codes ───────────────────────────────────
    auto_count_codes, open_elective_pool_codes, excluded_alternative_codes = \
        get_alternative_and_not_mandatory_codes(courses, program_info)

    # ── Trail / elective selection (same flow as L2) ─────────────────────
    excess_trail_codes = set()
    primary_trail     = None
    secondary_trail   = None
    available_trails  = None
    major_codes       = set()
    elective_selected = []
    elective_selected_codes = set()

    if is_cse and program_info.get('major_elective_credits', 0) > 0:
        result = select_cse_trails(courses, program_info)
        # select_cse_trails returns 6-tuple now
        trail_objs, major_codes, excess_trail_codes, primary_trail, secondary_trail, available_trails = result
    else:
        elective_selected, elective_selected_codes = select_major_electives(
            courses, program_info, args.program_knowledge)
        major_codes = elective_selected_codes

    # For MIC: excess electives must go to open elective pool
    if is_mic and program_info.get('elective_courses'):
        for c in courses:
            code = normalize_course_code(c['code'])
            if (code in program_info['elective_courses']
                    and code not in major_codes
                    and c['grade'] in GRADE_POINTS and c['grade'] != 'F'):
                open_elective_pool_codes.add(code)

    # Collect eligible minor additional codes — only courses not already required by program
    passed_preview = {normalize_course_code(c['code'])
                      for c in courses
                      if c.get('is_best_attempt') and c['grade'] in GRADE_POINTS
                      and c['grade'] != 'F'}
    required_by_program = (program_info.get('ged_courses', set())
                           | program_info.get('school_core_courses', set())
                           | program_info.get('cse_core_courses', set()))
    all_minor_additional = set()
    for minor_name, add_codes in program_info.get('minor_programs', {}).items():
        prereqs = MINOR_PREREQUISITES.get(minor_name, set())
        if not (prereqs - passed_preview):
            all_minor_additional |= (add_codes - required_by_program)

    # ── Open elective selection ───────────────────────────────────────────
    open_elective_selected, open_codes = select_open_electives(
        courses, program_info, major_codes, args.program_knowledge,
        extra_excess_codes=excess_trail_codes,
        alternative_codes=open_elective_pool_codes,
        auto_count_codes=auto_count_codes,
        minor_additional_codes=all_minor_additional,
        transfer_codes=transfer_codes,
        trail_prereq_codes=trail_prereq_codes)

    all_open_codes = open_codes | auto_count_codes

    # ── Minor program detection ───────────────────────────────────────────
    minor_selected_codes, minor_rejected_codes = select_minor_courses(
        courses, program_info, already_open_codes=open_codes)
    all_open_codes = all_open_codes | minor_selected_codes

    # ── Waivers ───────────────────────────────────────────────────────────
    waivers = ask_waivers(courses, program_info['waivable_courses'], canonical_program)

    # ── Run audit ─────────────────────────────────────────────────────────
    (counted_courses, retaken_courses, waived_courses, excluded_courses,
     passed_codes, total_credits_counted, cgpa, total_grade_points, cgpa_credits) = run_audit(
        courses, program_info, major_codes, all_open_codes, waivers,
        excluded_alternative_codes, transfer_codes, trail_prereq_codes,
        minor_rejected_codes=minor_rejected_codes,
        open_elective_pool_codes=open_elective_pool_codes)

    # Add waived codes to satisfied set for deficiency check
    for code, waived in waivers.items():
        if waived:
            passed_codes.add(normalize_course_code(code))

    # ── Check deficiencies ────────────────────────────────────────────────
    deficiencies = check_deficiencies(
        program_info, passed_codes, waivers, major_codes, all_open_codes,
        total_credits_counted, cgpa,
        elective_selected_codes=elective_selected_codes,
        open_elective_selected_codes=open_codes,
        primary_trail=primary_trail,
        secondary_trail=secondary_trail,
        available_trails=available_trails,
        program_name=canonical_program)

    # ── Build the output from course objects for elective tables ──────────
    # Reconstruct elective_selected list from codes for MIC
    if is_mic and elective_selected_codes:
        by_code = {}
        for c in courses:
            code = normalize_course_code(c['code'])
            if c.get('is_best_attempt') and code not in by_code:
                by_code[code] = c
        elective_selected = [by_code[c] for c in elective_selected_codes if c in by_code]

    oe_by_code = {}
    for c in courses:
        code = normalize_course_code(c['code'])
        if c.get('is_best_attempt') and code not in oe_by_code:
            oe_by_code[code] = c
    open_elective_selected_list = [oe_by_code[c] for c in open_codes if c in oe_by_code]

    # ── Format report ─────────────────────────────────────────────────────
    report = format_report(
        program_name=canonical_program,
        counted_courses=counted_courses,
        retaken_courses=retaken_courses,
        waived_courses=waived_courses,
        excluded_courses=excluded_courses,
        deficiencies=deficiencies,
        total_credits_counted=total_credits_counted,
        cgpa=cgpa,
        cgpa_credits=cgpa_credits,
        total_grade_points=total_grade_points,
        total_credits_required=program_info.get('total_credits_required', 0),
        waivers=waivers,
        primary_trail=primary_trail,
        secondary_trail=secondary_trail,
        available_trails=available_trails,
        major_codes=major_codes,
        elective_selected=elective_selected,
        elective_required_credits=program_info.get('elective_credits', 0),
        open_elective_selected=open_elective_selected_list,
        open_elective_required_credits=program_info.get('open_elective_credits', 0),
    )

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\nAudit report saved to: {args.output}")
    else:
        print(report)


if __name__ == '__main__':
    main()