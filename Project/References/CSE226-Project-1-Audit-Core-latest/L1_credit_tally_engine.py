#!/usr/bin/env python3
"""
L1 Credit Tally Engine
Step 1 of 3: Analyze passed credits from a student transcript CSV.
Run this first to get a full breakdown of credits passed vs credits counted toward graduation.
"""

import argparse
import csv
import os
import re
import sys
from collections import defaultdict


def get_grade_points(grade):
    """Convert letter grade to grade points."""
    grade_map = {
        'A': 4.0,
        'A-': 3.7,
        'B+': 3.3,
        'B': 3.0,
        'B-': 2.7,
        'C+': 2.3,
        'C': 2.0,
        'C-': 1.7,
        'D+': 1.3,
        'D': 1.0,
        'F': 0.0,
        'I': 0.0,
        'W': 0.0
    }
    return grade_map.get(grade.strip().upper(), 0.0)


def is_passing(grade):
    """Check if grade is passing (D or above, excluding F, I, W)."""
    passing_grades = {'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D'}
    return grade.strip().upper() in passing_grades


def is_counted_toward_graduation(grade):
    """Check if grade credits count toward graduation."""
    excluded = {'F', 'I', 'W', 'S'}
    return grade.strip().upper() not in excluded


def normalize_course_code(code):
    """Normalize course code by removing spaces and converting to uppercase."""
    return code.replace(' ', '').replace('\t', '').upper()


# ---------------------------------------------------------------------------
# Program name resolution
# ---------------------------------------------------------------------------

# Map of canonical program name -> list of accepted aliases (all lowercase)
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

# Build reverse lookup: alias -> canonical name
_ALIAS_TO_CANONICAL = {}
for _canon, _aliases in PROGRAM_ALIASES.items():
    for _alias in _aliases:
        _ALIAS_TO_CANONICAL[_alias] = _canon

# Programs that have a full course-structure section defined in the MD file.
# All other valid NSU programs are recognised but lack a course structure definition.
STRUCTURED_PROGRAMS = {"Computer Science", "Microbiology"}


def resolve_program_name(program_name):
    """
    Resolve a user-supplied program name to its canonical form.
    Returns the canonical name string, or None if not recognised.
    """
    return _ALIAS_TO_CANONICAL.get(program_name.strip().lower())


def read_programs_offered(md_path):
    """
    Read the Programs Offered section from the markdown file.
    Returns a set of canonical program names found in the file.
    """
    offered = set()
    if not os.path.exists(md_path):
        return offered
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Look for the Programs Offered section
        section_match = re.search(
            r'#\s+North South University\s*-\s*Programs Offered(.*?)(?=\n#[^#]|\Z)',
            content, re.IGNORECASE | re.DOTALL)
        if not section_match:
            # If no Programs Offered section, return all known canonical names
            # so the check is effectively skipped (backward compat)
            return set(PROGRAM_ALIASES.keys())
        section_text = section_match.group(1)
        # Match bullet list items like "- Architecture"
        for line in section_text.splitlines():
            clean = re.sub(r'^[\s\-\*]+', '', line).strip()
            if clean:
                # Try direct match first
                canonical = resolve_program_name(clean)
                if canonical:
                    offered.add(canonical)
                else:
                    # Try stripping parenthetical suffixes e.g. "CEE (Civil...)"
                    base = re.sub(r'\s*\(.*?\)', '', clean).strip()
                    canonical = resolve_program_name(base)
                    if canonical:
                        offered.add(canonical)
    except Exception as e:
        print(f"Warning: Could not read Programs Offered section: {e}")
    return offered


def validate_program_name(program_name, md_path):
    """
    Validate that the program name is recognised AND offered by NSU.
    Exits with an error message if not.
    Returns the canonical program name on success.
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
# NSU course list helpers
# ---------------------------------------------------------------------------

def read_nsu_course_list(md_path):
    """
    Read the NSU Offered Course List from the markdown file.
    Returns a set of normalized course codes offered by NSU.
    """
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
    Check if any courses in the transcript are not in the NSU offered course list.

    If unknown courses are found, asks whether the student is a transfer student.
    - Yes → returns True  (caller should treat unknown courses as non-counted)
    - No  → prints error and exits
    Returns False when all courses are recognised (normal flow).
    """
    if not nsu_course_list:
        return False

    non_nsu = []
    for course in courses:
        code = normalize_course_code(course['code'])
        if code and code not in nsu_course_list:
            non_nsu.append(course['code'])

    if not non_nsu:
        return False

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
        print("Unrecognised courses will be placed in the 'Not Counted' section.")
        return True  # is_transfer
    else:
        print(f"\n{'!'*60}")
        print("ERROR: This transcript may not belong to an NSU student.")
        print("Processing stopped. Please verify the transcript and try again.")
        print(f"{'!'*60}\n")
        sys.exit(1)


def check_invalid_grades(courses):
    """
    Check if any courses in the transcript have grades not defined in NSU policy.
    """
    valid_grades = {'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F', 'I', 'W'}
    invalid = []
    for course in courses:
        if course['grade'].upper() not in valid_grades:
            invalid.append((course['code'], course['grade']))
    if invalid:
        print(f"\n{'!'*60}")
        print("ERROR: This transcript contains grade(s) not defined in NSU policy.")
        print("Valid grades are: A, A-, B+, B, B-, C+, C, C-, D+, D, F, I, W")
        print("The following course(s) have unrecognised grades:")
        for code, grade in invalid:
            print(f"  - {code}: '{grade}'")
        print(f"{'!'*60}\n")
        sys.exit(1)


def extract_courses_from_section(content):
    """Extract all course codes from a program section."""
    courses = set()
    course_patterns = [
        r'\b([A-Z]{2,4})\s*(\d{3,4}[A-Z]?)\b',
        r'\b([A-Z]{2,4})\s*(\d{3,4}[A-Z]?)\s*/\s*\1\s*(\d{3,4}[A-Z]?)\b',
    ]
    for pattern in course_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            if len(match.groups()) >= 2:
                dept = match.group(1).upper()
                num = match.group(2).upper()
                courses.add(f"{dept}{num}")
                if len(match.groups()) >= 3 and match.group(3):
                    courses.add(f"{dept}{match.group(3).upper()}")
    return courses


def find_program_section(content, program_name):
    """Find the program section in the markdown content."""
    pn = program_name.strip().lower()

    CSE_ALIASES = {'cse', 'cs', 'computer science', 'computer science engineering',
                   'computer science and engineering', 'bsc cse', 'b.sc cse',
                   'bsc computer science', 'b.sc. computer science', 'computer'}
    MIC_ALIASES = {'microbiology', 'mic', 'micro', 'bsc microbiology',
                   'b.sc microbiology', 'b.sc. microbiology', 'microbio'}

    is_cse = pn in CSE_ALIASES or 'computer' in pn or pn.startswith('cse') or pn == 'cs'
    is_mic = pn in MIC_ALIASES or 'microbiology' in pn or pn.startswith('mic')

    program_headers = list(re.finditer(r'^#\s+(.+?program.*)$', content, re.MULTILINE | re.IGNORECASE))

    for i, match in enumerate(program_headers):
        header = match.group(1).lower()
        is_match = False
        if pn in header:
            is_match = True
        elif is_cse and ('computer science' in header or 'cse' in header or 'computer' in header):
            is_match = True
        elif is_mic and 'microbiology' in header:
            is_match = True

        if is_match:
            start_pos = match.start()
            if i + 1 < len(program_headers):
                end_pos = program_headers[i + 1].start()
            else:
                end_pos = len(content)
            return content[start_pos:end_pos]

    return None


def read_program_knowledge(md_path, program_name):
    """Read program knowledge from markdown file."""
    program_info = {
        'name': program_name,
        'total_credits_required': 0,
        'mandatory_courses': [],
        'core_courses': [],
        'ged_courses': [],
        'allowed_courses': set(),
        'capstone_courses': set(),
    }

    if not os.path.exists(md_path):
        print(f"Error: Program knowledge file not found: {md_path}")
        sys.exit(1)

    try:
        with open(md_path, 'r', encoding='utf-8') as file:
            content = file.read()

        program_section = find_program_section(content, program_name)

        if program_section:
            credits_match = re.search(r'Total Credits[^:]*:\s*(\d+)', program_section, re.IGNORECASE)
            if credits_match:
                program_info['total_credits_required'] = int(credits_match.group(1))

            program_info['allowed_courses'] = extract_courses_from_section(program_section)

            for cap_match in re.finditer(
                    r'^#{1,3}\s+(?:Capstone|Internship|Research)[^\n]*\n(.*?)(?=\n#{1,3}\s|\Z)',
                    program_section, re.IGNORECASE | re.MULTILINE | re.DOTALL):
                for m in re.finditer(r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b',
                                     cap_match.group(1)):
                    program_info['capstone_courses'].add(
                        normalize_course_code(f"{m.group(1)}{m.group(2)}"))

            for cap_block in re.finditer(
                    r'_Capstone[^_\n]*_\s*\n(.*?)(?=\n_|\n\n|\Z)',
                    content, re.IGNORECASE | re.DOTALL):
                for entry in re.findall(r'"([^"]+)"', cap_block.group(1)):
                    for part in entry.split('/'):
                        program_info['capstone_courses'].add(normalize_course_code(part.strip()))

            mandatory_courses = []
            ged_match = re.search(r'Mandatory GED[^:]*:\s*(.+?)(?=\n|$)', program_section, re.IGNORECASE)
            if ged_match:
                courses_str = ged_match.group(1)
                mandatory_courses.extend([c.strip() for c in courses_str.split(',')])
                program_info['ged_courses'] = [c.strip() for c in courses_str.split(',')]

            mandatory_match = re.search(r'Mandatory(?:\s+GED)?[^:]*:\s*(.+?)(?=\n|$)', program_section, re.IGNORECASE)
            if mandatory_match and not ged_match:
                courses_str = mandatory_match.group(1)
                mandatory_courses.extend([c.strip() for c in courses_str.split(',')])

            core_match = re.search(r'(?:Major Core|Core)[^:]*:\s*(.+?)(?=\n|$)', program_section, re.IGNORECASE)
            if core_match:
                courses_str = core_match.group(1)
                core_courses = [c.strip() for c in courses_str.split(',')]
                program_info['core_courses'] = core_courses
                mandatory_courses.extend(core_courses)

            program_info['mandatory_courses'] = list(set(mandatory_courses))
        else:
            print(f"Warning: Could not find program section for '{program_name}'")

    except FileNotFoundError:
        print(f"Warning: Program knowledge file not found: {md_path}")
    except Exception as e:
        print(f"Warning: Error reading program knowledge: {e}")

    return program_info


def read_transcript(csv_path):
    """Read and parse the transcript CSV file."""
    courses = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            expected_headers = {'Course_Code', 'Credits', 'Grade', 'Semester'}
            fieldnames = reader.fieldnames or []
            if not expected_headers.issubset(set(fieldnames)):
                missing = expected_headers - set(fieldnames)
                print(f"Error: Missing required columns: {missing}")
                sys.exit(1)
            for row in reader:
                try:
                    course = {
                        'code': row['Course_Code'].strip(),
                        'credits': float(row['Credits']) if row['Credits'].strip() else 0.0,
                        'grade': row['Grade'].strip(),
                        'semester': row['Semester'].strip(),
                        'grade_points': get_grade_points(row['Grade'])
                    }
                    course['passed'] = is_passing(course['grade'])
                    course['counts_toward_graduation'] = is_counted_toward_graduation(course['grade']) and course['passed']
                    courses.append(course)
                except ValueError as e:
                    print(f"Warning: Skipping invalid row: {row}. Error: {e}")
                    continue
    except FileNotFoundError:
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    return courses


def read_courses_with_prerequisites(md_path):
    """Scan all program course tables and return codes that have prerequisites."""
    courses_with_prereqs = set()
    if not os.path.exists(md_path):
        return courses_with_prereqs
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        for line in content.splitlines():
            if '|' not in line:
                continue
            clean = line.replace('**', '').strip().strip('|')
            cols = [c.strip() for c in clean.split('|')]
            if len(cols) < 3:
                continue
            m = re.match(r'^([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)$', cols[0].replace(' ', ''))
            if not m:
                continue
            code = normalize_course_code(cols[0])
            for col in cols[2:]:
                col_clean = col.strip().strip('_').strip('*')
                if col_clean and col_clean.lower() not in ('none', '-', '', 'prerequisites', 'prereq'):
                    if re.search(r'[A-Za-z]{2,4}\s*\d{3}', col_clean):
                        courses_with_prereqs.add(code)
                        break
    except Exception as e:
        print(f"Warning: Could not read prerequisites: {e}")
    return courses_with_prereqs


def read_trail_course_prerequisites(md_path):
    """
    Parse the Major Electives - Trail Courses table in the CSE program section.

    Returns a set of normalized course codes for trail courses that have a
    non-None prerequisite.  These codes must never appear as open/free
    electives for a non-CSE program — they are CSE-specific courses whose
    prerequisites are themselves CSE core courses.
    """
    trail_codes_with_prereqs = set()
    if not os.path.exists(md_path):
        return trail_codes_with_prereqs
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Locate the trail table: sits between the "Trail Courses" heading and the
        # next ## section.  We look for table rows that have a Trail column.
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
            # Table columns: Course | Credits | Prerequisites | Trail | Notes
            if len(cols) < 3:
                continue
            course_cell = cols[0]
            # Skip header / separator rows
            if re.match(r'^[-\s]+$', course_cell.replace('|', '')):
                continue
            prereq_cell = cols[2].strip() if len(cols) > 2 else ''
            # Expand slash-separated aliases in the course cell
            # e.g. "CSE257 / CSE417"
            for part in re.split(r'[/,]', course_cell):
                m = re.match(r'^\s*([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\s*$', part.strip())
                if not m:
                    continue
                code = normalize_course_code(f"{m.group(1)}{m.group(2)}")
                prereq_clean = prereq_cell.strip().lower()
                if prereq_clean and prereq_clean not in ('none', '-', '', 'prerequisites'):
                    if re.search(r'[A-Za-z]{2,4}\s*\d{3}', prereq_cell):
                        trail_codes_with_prereqs.add(code)
    except Exception as e:
        print(f"Warning: Could not read trail course prerequisites: {e}")
    return trail_codes_with_prereqs


def filter_courses_by_program(courses, program_info, courses_with_prereqs=None,
                               non_nsu_codes=None, trail_prereq_codes=None):
    """
    Split transcript courses into three buckets:
      - program_courses:        in the declared program's allowed course list
      - open_elective_courses:  outside program, no prerequisites, not capstone,
                                not a trail course that carries CSE-specific prerequisites
      - excluded_courses:       cannot count (has prereqs, capstone, non-NSU transfer
                                credit, or is a CSE trail course with prerequisites
                                being evaluated for a non-CSE program)
    """
    if not program_info['allowed_courses']:
        return courses, [], []

    allowed_codes     = {normalize_course_code(c) for c in program_info['allowed_courses']}
    prereq_codes      = courses_with_prereqs or set()
    capstone_codes    = {normalize_course_code(c) for c in program_info.get('capstone_courses', set())}
    transfer_codes    = {normalize_course_code(c) for c in (non_nsu_codes or [])}
    trail_with_prereq = trail_prereq_codes or set()

    program_courses      = []
    open_elective_courses = []
    excluded_courses     = []

    for course in courses:
        code = normalize_course_code(course['code'])
        if code in transfer_codes:
            course['_reason'] = 'Transfer credit (not counted)'
            excluded_courses.append(course)
        elif code in allowed_codes:
            program_courses.append(course)
        elif code in capstone_codes:
            course['_reason'] = 'Not included in program'
            excluded_courses.append(course)
        elif code in trail_with_prereq:
            # CSE trail course with prerequisites — cannot count for other programs
            course['_reason'] = 'CSE trail course (not open elective)'
            excluded_courses.append(course)
        elif code in prereq_codes:
            course['_reason'] = 'Not included in program'
            excluded_courses.append(course)
        else:
            course['is_open_elective'] = True
            open_elective_courses.append(course)

    return program_courses, open_elective_courses, excluded_courses


def process_retakes(courses):
    """Process retaken courses — sets is_best_attempt flag."""
    course_groups = defaultdict(list)
    for idx, course in enumerate(courses):
        course_groups[course['code']].append((idx, course))

    for code, attempts in course_groups.items():
        if len(attempts) > 1:
            sorted_attempts = sorted(
                attempts,
                key=lambda x: (-x[1]['grade_points'], x[1]['semester'])
            )
            best_idx = sorted_attempts[0][0]
            courses[best_idx]['is_best_attempt'] = True
            for idx, _ in sorted_attempts[1:]:
                courses[idx]['is_best_attempt'] = False
        else:
            idx = attempts[0][0]
            courses[idx]['is_best_attempt'] = True

    return courses


def calculate_statistics(all_courses, counted_courses):
    """Calculate summary statistics per NSU policy."""
    stats = {
        'total_attempted': 0,
        'total_passed': 0,
        'total_counted': 0,
        'failed_courses': 0,
        'withdrawals': 0,
        'incomplete': 0,
        'zero_credit_courses': 0,
        'retake_count': 0
    }

    for course in all_courses:
        grade   = course['grade'].upper()
        credits = course['credits']
        if credits > 0:
            stats['total_attempted'] += credits
        if course.get('is_best_attempt') and course['passed'] and credits > 0:
            stats['total_passed'] += credits
        if grade == 'F':
            stats['failed_courses'] += 1
        elif grade == 'W':
            stats['withdrawals'] += 1
        elif grade == 'I':
            stats['incomplete'] += 1
        if credits == 0:
            stats['zero_credit_courses'] += 1

    for course in counted_courses:
        credits = course['credits']
        if course.get('is_best_attempt') and course['passed'] and credits > 0:
            stats['total_counted'] += credits

    from collections import Counter
    code_counts = Counter(normalize_course_code(c['code']) for c in all_courses)
    stats['retake_count'] = sum(1 for cnt in code_counts.values() if cnt > 1)

    return stats


def format_table(courses, stats, program_name="", excluded_courses=None, open_elective_courses=None):
    """Format output as a nice table."""
    lines = []

    oe_all = open_elective_courses or []
    for c in courses:
        c.setdefault('_type', 'Program')
    for c in oe_all:
        c['_type'] = 'Free Elective'

    all_courses = courses + oe_all
    best_attempts = [c for c in all_courses if c.get('is_best_attempt', True)]
    retakes       = [c for c in all_courses if not c.get('is_best_attempt', False)]
    excluded_courses = excluded_courses or []

    lines.append("=" * 120)
    lines.append("NSU TRANSCRIPT CREDIT ANALYSIS")
    if program_name:
        lines.append(f"Program: {program_name}")
    lines.append("=" * 120)
    lines.append("")

    lines.append("-" * 120)
    lines.append("COURSES COUNTED (Best Attempts)")
    lines.append("-" * 120)
    lines.append(f"{'Course Code':<15} {'Credits':<10} {'Grade':<8} {'Semester':<15} {'Type':<15} {'Passed':<12} {'Credits Counted':<15}")
    lines.append("-" * 120)

    for course in best_attempts:
        passed_str  = "Passed" if course['passed'] else "Not Passed"
        counted_val = f"{course['credits']:.1f}" if course['passed'] and course['credits'] > 0 else "0.0"
        lines.append(
            f"{course['code']:<15} {course['credits']:<10.1f} {course['grade']:<8} "
            f"{course['semester']:<15} {course['_type']:<15} {passed_str:<12} {counted_val:<15}"
        )
    lines.append("-" * 120)

    if excluded_courses:
        lines.append("")
        lines.append("-" * 120)
        lines.append("EXCLUDED COURSES (Outside Program — Does Not Count)")
        lines.append("-" * 120)
        lines.append(f"{'Course Code':<15} {'Credits':<10} {'Grade':<8} {'Semester':<15} {'Reason':<30}")
        lines.append("-" * 120)
        for course in excluded_courses:
            reason = course.get('_reason', 'Not included in program')
            lines.append(
                f"{course['code']:<15} {course['credits']:<10.1f} {course['grade']:<8} "
                f"{course['semester']:<15} {reason:<30}"
            )
        lines.append("-" * 120)

    if retakes:
        lines.append("")
        lines.append("-" * 120)
        lines.append("RETAKEN COURSES (Not Counted - Previous Attempts)")
        lines.append("-" * 120)
        lines.append(f"{'Course Code':<15} {'Credits':<10} {'Grade':<8} {'Semester':<15} {'Type':<15} {'Passed':<12} {'Credits Counted':<15}")
        lines.append("-" * 120)
        for course in retakes:
            passed_str = "Passed" if course['passed'] else "Not Passed"
            lines.append(
                f"{course['code']:<15} {course['credits']:<10.1f} {course['grade']:<8} "
                f"{course['semester']:<15} {course['_type']:<15} {passed_str:<12} {'0.0':<15}"
            )
        lines.append("-" * 120)

    lines.append("")
    lines.append("SUMMARY STATISTICS")
    lines.append("-" * 50)
    lines.append(f"Total Credits Attempted:     {stats['total_attempted']:.1f}")
    lines.append(f"Total Credits Passed:        {stats['total_passed']:.1f}")
    lines.append(f"Total Credits Counted:       {stats['total_counted']:.1f}")
    lines.append(f"")
    lines.append(f"Failed Courses (F):          {stats['failed_courses']}")
    lines.append(f"Withdrawals (W):             {stats['withdrawals']}")
    lines.append(f"Incomplete (I):              {stats['incomplete']}")
    lines.append(f"Zero-Credit Courses:         {stats['zero_credit_courses']}")
    lines.append(f"Courses with Retakes:        {stats['retake_count']}")
    lines.append("-" * 50)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='L1 Credit Tally Engine (Step 1 of 3) - Analyze passed credits from transcript CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python L1_credit_tally_engine.py transcript.csv "Computer Science" NSU_Program.md
  python L1_credit_tally_engine.py transcript.csv cse NSU_Program.md
  python L1_credit_tally_engine.py transcript.csv mic NSU_Program.md --output results.txt
        """
    )
    parser.add_argument('csv_file', help='Path to the transcript CSV file')
    parser.add_argument('program_name', help='Name of the program (e.g., "cse", "mic", "eee", "finance")')
    parser.add_argument('program_knowledge', help='Path to the program knowledge markdown file')
    parser.add_argument('-o', '--output', help='Save output to file (default: print to console)', type=str, default=None)

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

    print(f"Program: {canonical_program}")

    # Read transcript
    print(f"Reading transcript from: {args.csv_file}")
    courses = read_transcript(args.csv_file)

    if not courses:
        print("No courses found in transcript.")
        sys.exit(0)

    # Read program knowledge
    program_info = read_program_knowledge(args.program_knowledge, canonical_program)

    # NSU course list check — may prompt about transfer student
    nsu_course_list = read_nsu_course_list(args.program_knowledge)
    is_transfer = check_non_nsu_courses(courses, nsu_course_list)

    # Collect non-NSU course codes so they can be routed to excluded
    non_nsu_codes = set()
    if is_transfer:
        for course in courses:
            code = normalize_course_code(course['code'])
            if code and code not in nsu_course_list:
                non_nsu_codes.add(code)

    # Grade validity check
    check_invalid_grades(courses)

    # Build prerequisite set
    courses_with_prereqs = read_courses_with_prerequisites(args.program_knowledge)

    # For non-CSE programs: read trail course prerequisites so those courses
    # are blocked from appearing as open/free electives
    is_cse_program = canonical_program == "Computer Science"
    if not is_cse_program:
        trail_prereq_codes = read_trail_course_prerequisites(args.program_knowledge)
    else:
        trail_prereq_codes = set()

    # Process retakes
    all_courses = process_retakes(courses)

    # Split into buckets
    if program_info['allowed_courses']:
        program_courses, open_elective_courses, excluded_courses = filter_courses_by_program(
            all_courses, program_info, courses_with_prereqs, non_nsu_codes, trail_prereq_codes)
        if excluded_courses:
            print(f"Note: {len(excluded_courses)} course(s) excluded (outside program / transfer credit)")
        if open_elective_courses:
            print(f"Note: {len(open_elective_courses)} course(s) counted as free electives")
    else:
        program_courses = all_courses
        open_elective_courses = []
        excluded_courses = []

    counted_courses = program_courses + open_elective_courses
    stats = calculate_statistics(all_courses, counted_courses)

    output = format_table(program_courses, stats, canonical_program, excluded_courses,
                          open_elective_courses=open_elective_courses)

    if program_info['total_credits_required'] > 0:
        credits_counted = stats['total_counted']
        output += f"\n\nPROGRAM REQUIREMENTS\n"
        output += "-" * 50 + "\n"
        output += f"Program:                     {program_info['name']}\n"
        output += f"Total Credits Required:      {program_info['total_credits_required']}\n"
        output += f"Credits Counted:             {credits_counted:.1f}\n"
        remaining = max(0, program_info['total_credits_required'] - credits_counted)
        output += f"Remaining Credits:           {remaining:.1f}\n"
        if program_info['mandatory_courses']:
            output += f"Mandatory Courses:           {', '.join(program_info['mandatory_courses'])}\n"
        output += "-" * 50 + "\n"

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\nResults saved to: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()