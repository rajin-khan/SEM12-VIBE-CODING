#!/usr/bin/env python3
"""
NSU Transcript Credit Counter
A CLI tool to analyze student transcripts and calculate passed credits based on NSU grading policy.
"""

import argparse
import csv
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


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
    # F, I, W, S do not count toward graduation
    # (S = Satisfactory for non-credit courses like Internship/Research)
    excluded = {'F', 'I', 'W', 'S'}
    return grade.strip().upper() not in excluded


def normalize_course_code(code):
    """Normalize course code by removing spaces and converting to uppercase."""
    return code.replace(' ', '').replace('\t', '').upper()


def extract_courses_from_section(content):
    """Extract all course codes from a program section."""
    courses = set()
    
    # Match patterns like "ENG 102", "CSE 115L", "Mic202", "Bio103L"
    # Handle various formats: "CSE 115 / CSE 115L", "CSE 115L (1 credit)", etc.
    course_patterns = [
        # Standard format: XXX 123 or XXX123
        r'\b([A-Z]{2,4})\s*(\d{3,4}[A-Z]?)\b',
        # Alternative format with slash options: XXX 123 / XXX 124
        r'\b([A-Z]{2,4})\s*(\d{3,4}[A-Z]?)\s*/\s*\1\s*(\d{3,4}[A-Z]?)\b',
    ]
    
    for pattern in course_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            if len(match.groups()) >= 2:
                dept = match.group(1).upper()
                num = match.group(2).upper()
                courses.add(f"{dept}{num}")
                # If there's a third group (from slash pattern), add it too
                if len(match.groups()) >= 3 and match.group(3):
                    courses.add(f"{dept}{match.group(3).upper()}")
    
    return courses


def find_program_section(content, program_name):
    """Find the program section in the markdown content."""
    program_name_lower = program_name.lower()
    
    # Find all major sections (starting with # at beginning of line followed by program)
    # Pattern matches lines like "# Microbiology Undergraduate Program"
    program_headers = list(re.finditer(r'^#\s+(.+?program.*)$', content, re.MULTILINE | re.IGNORECASE))
    
    for i, match in enumerate(program_headers):
        header = match.group(1).lower()
        
        # Check if this header matches the program name
        is_match = False
        if program_name_lower in header:
            is_match = True
        elif program_name_lower == 'microbiology' and 'microbiology' in header:
            is_match = True
        elif program_name_lower == 'computer science' and ('computer science' in header or 'cse' in header or 'computer' in header):
            is_match = True
        
        if is_match:
            start_pos = match.start()
            # Find the end of this section (start of next major program section or end of file)
            if i + 1 < len(program_headers):
                end_pos = program_headers[i + 1].start()
            else:
                end_pos = len(content)
            return content[start_pos:end_pos]
    
    return None


def read_program_knowledge(md_path, program_name):
    """
    Read program knowledge from markdown file.
    Returns dict with program requirements and allowed courses.
    """
    program_info = {
        'name': program_name,
        'total_credits_required': 0,
        'mandatory_courses': [],
        'core_courses': [],
        'ged_courses': [],
        'allowed_courses': set(),  # All courses valid for this program
        'open_elective_credits': 0,
        'open_elective_description': '',
        'major_elective_credits': 0,  # Credits required for Major Electives
        'major_elective_courses': set(),  # List of major elective/trail courses
        'elective_credits': 0,  # Credits required for Electives (Microbiology)
        'elective_courses': set(),  # List of elective courses (Microbiology)
        'alternative_courses': [],  # List of alternative course groups (e.g., [["POL101", "POL104"], ["ECO101", "ECO104"]])
        'not_mandatory_courses': set()  # Courses marked as "Not mandatory"
    }
    
    if not os.path.exists(md_path):
        print(f"Error: Program knowledge file not found: {md_path}")
        print("Available .md files in current directory:")
        for f in os.listdir('.'):
            if f.endswith('.md'):
                print(f"  - {f}")
        sys.exit(1)
    
    try:
        with open(md_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Find the program section
        program_section = find_program_section(content, program_name)
        
        if program_section:
            # Extract total credits
            credits_match = re.search(r'Total Credits[^:]*:\s*(\d+)', program_section, re.IGNORECASE)
            if credits_match:
                program_info['total_credits_required'] = int(credits_match.group(1))
            
            # Extract all courses from this program section
            program_info['allowed_courses'] = extract_courses_from_section(program_section)
            
            # Extract mandatory courses (GED + Major)
            mandatory_courses = []
            
            # Look for Mandatory GED
            ged_match = re.search(r'Mandatory GED[^:]*:\s*(.+?)(?=\n|$)', program_section, re.IGNORECASE)
            if ged_match:
                courses_str = ged_match.group(1)
                mandatory_courses.extend([c.strip() for c in courses_str.split(',')])
                program_info['ged_courses'] = [c.strip() for c in courses_str.split(',')]
            
            # Look for Mandatory (general)
            mandatory_match = re.search(r'Mandatory(?:\s+GED)?[^:]*:\s*(.+?)(?=\n|$)', program_section, re.IGNORECASE)
            if mandatory_match and not ged_match:
                courses_str = mandatory_match.group(1)
                mandatory_courses.extend([c.strip() for c in courses_str.split(',')])
            
            # Look for Major Core
            core_match = re.search(r'(?:Major Core|Core)[^:]*:\s*(.+?)(?=\n|$)', program_section, re.IGNORECASE)
            if core_match:
                courses_str = core_match.group(1)
                core_courses = [c.strip() for c in courses_str.split(',')]
                program_info['core_courses'] = core_courses
                mandatory_courses.extend(core_courses)
            
            program_info['mandatory_courses'] = list(set(mandatory_courses))
            
            # Extract alternative courses (e.g., "POL 101 / POL 104" or "Choose one")
            alternative_groups = []

            # For Microbiology: parse only the University Core section for "Choose one" groups.
            # The general alt_pattern would pick up SHLS Core slash-notations as false positives.
            if program_name.lower() == 'microbiology':
                # Use ##[^#] to avoid matching ### subsection headers as section boundaries
                university_core_section_match = re.search(
                    r'##\s+University Core.*?(?=\n##[^#]|\Z)', program_section, re.IGNORECASE | re.DOTALL)
                if university_core_section_match:
                    university_core_content = university_core_section_match.group(0)
                    # Strip bold markers (**) so course codes are plain text
                    uc_clean = university_core_content.replace('**', '')

                    # Split into individual ### subsections and look for "_Choose one" in each
                    subsections = re.split(r'(?=\n###\s)', uc_clean)
                    for sub in subsections:
                        sub = sub.strip()
                        has_block_choose_one = bool(re.search(r'\n\s*_[Cc]hoose one', sub))

                        # Pattern 1: entire subsection ends with _Choose one_ block —
                        # treat ALL courses in the table as a single "choose one" group.
                        if has_block_choose_one:
                            table_match = re.search(
                                r'(\|.*?)(?=\n\s*_[Cc]hoose one)', sub, re.DOTALL)
                            if table_match:
                                table_content = table_match.group(1)
                                courses_in_table = re.findall(
                                    r'\b([A-Za-z]{2,4})\s*(\d{3,4}[A-Za-z]?)\b', table_content)
                                if courses_in_table:
                                    group = []
                                    for dept, num in courses_in_table:
                                        code = f"{dept.upper()}{num.upper()}"
                                        if code not in group:
                                            group.append(code)
                                    if len(group) >= 2:
                                        sorted_new_group = sorted(group)
                                        if sorted_new_group not in [sorted(g) for g in alternative_groups]:
                                            alternative_groups.append(group)
                            # Block-level _Choose one_ already covers this subsection —
                            # don't also parse individual rows to avoid duplicate sub-groups.
                            continue

                        # Pattern 2: no block-level _Choose one_ — look for inline
                        # "Choose one" in individual table row Notes columns.
                        # e.g. | Eng111/Ben205 | 3 | Choose one |
                        for row_match in re.finditer(
                                r'^\|\s*([^|]+?)\s*\|\s*[\d.]+\s*\|\s*[Cc]hoose one\s*\|?',
                                sub, re.MULTILINE):
                            course_cell = row_match.group(1).strip()
                            # Extract all course codes from the cell (may contain / separator)
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
            else:
                # For non-Microbiology programs: scan all table rows with "Choose one" in Notes
                # This handles 2-way (POL101/POL104) and N-way (SOC101/ENV203/GEO205/ANT101) rows.
                for row_match in re.finditer(
                        r'^\|\s*([^|]+?)\s*\|\s*[^|]*\|\s*[Cc]hoose one[^|]*\|?',
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

                # Also keep trail course pairs (e.g. CSE257/CSE417) which don't use Choose one
                trail_pattern = re.findall(r'([A-Z]{2,})\s*(\d{3,})\s*/\s*([A-Z]{2,})\s*(\d{3,})\s*\(', program_section, re.IGNORECASE)
                for dept1, num1, dept2, num2 in trail_pattern:
                    group = [f"{dept1.upper()}{num1}", f"{dept2.upper()}{num2}"]
                    sorted_new_group = sorted(group)
                    if sorted_new_group not in [sorted(g) for g in alternative_groups]:
                        alternative_groups.append(group)

            # Post-process: detect "choose one with lab" groups and split into paired sub-groups
            # e.g. [BIO103, BIO103L, PHY107, PHY107L] -> paired as [(BIO103, BIO103L), (PHY107, PHY107L)]
            processed_groups = []
            for group in alternative_groups:
                lab_codes = [c for c in group if c.endswith('L')]
                theory_codes = [c for c in group if not c.endswith('L')]
                # If there are labs and theories, try to pair them
                if lab_codes and theory_codes and len(group) > 2:
                    # Build pairs: match each lab to its theory (e.g. BIO103L -> BIO103)
                    paired = {}
                    for lab in lab_codes:
                        base = lab[:-1]  # strip trailing 'L'
                        if base in theory_codes:
                            paired[base] = lab
                    unpaired_theory = [c for c in theory_codes if c not in paired]
                    unpaired_labs = [c for c in lab_codes if c not in paired.values()]
                    
                    if paired and len(paired) >= 2:
                        # Create sub-groups for each theory+lab pair
                        # The "choose one" logic will apply across pairs
                        # Store as a special "paired_group" structure
                        pair_list = [(t, paired[t]) for t in sorted(paired.keys())]
                        # Add as individual pairs to alternative_groups won't work directly
                        # Instead store the theory-only group for the "choose one" logic
                        # and remember the lab pairing for auto-counting
                        processed_groups.append(group)
                        # Store paired lab info in program_info for use in get_alternative_and_not_mandatory_codes
                        if 'lab_pairs' not in program_info:
                            program_info['lab_pairs'] = {}
                        for theory, lab in pair_list:
                            program_info['lab_pairs'][theory] = lab
                            program_info['lab_pairs'][lab] = theory  # reverse mapping too
                        continue
                processed_groups.append(group)
            alternative_groups = processed_groups

            program_info['alternative_courses'] = alternative_groups
            
            # Extract "Not mandatory" courses - look in both table rows and notes
            # First check table rows
            not_mandatory_matches = re.findall(r'([A-Z]{2,})\s*(\d{3,})[^\n]*Not mandatory', program_section, re.IGNORECASE)
            for dept, num in not_mandatory_matches:
                program_info['not_mandatory_courses'].add(f"{dept.upper()}{num}")
            
            # Also check notes section (e.g., "- *Ben205 and His103 are not mandatory")
            notes_pattern = re.findall(r'([A-Z]{2,})\s*(\d{3,})(?:\s+and\s+([A-Z]{2,})\s*(\d{3,}))*\s*are not mandatory', program_section, re.IGNORECASE)
            for match in notes_pattern:
                dept1, num1 = match[0], match[1]
                program_info['not_mandatory_courses'].add(f"{dept1.upper()}{num1}")
                if len(match) > 2 and match[2]:  # If there's a second course (and...)
                    dept2, num2 = match[2], match[3]
                    program_info['not_mandatory_courses'].add(f"{dept2.upper()}{num2}")
            
            # Any course that appears in an alternative group is handled by the "choose one"
            # logic already — remove it from not_mandatory so it isn't double-counted.
            all_alternative_codes = {code for group in alternative_groups for code in group}
            program_info['not_mandatory_courses'] -= all_alternative_codes
            
            # Extract Open/Free Electives info - match only header lines (## or ### prefix)
            open_elective_match = re.search(r'^#{1,3}\s+.*?(Open Elective|Free Elective).*?\((\d+)\s*Credits?\)', program_section, re.IGNORECASE | re.MULTILINE)
            if open_elective_match:
                program_info['open_elective_credits'] = int(open_elective_match.group(2))
                # Get description
                desc_start = open_elective_match.end()
                next_section = program_section.find('\n##', desc_start)
                if next_section == -1:
                    next_section = len(program_section)
                desc_text = program_section[desc_start:next_section].strip()
                program_info['open_elective_description'] = desc_text[:200]  # Limit length
            
            # Extract Major Electives / Trail Courses info (for CSE)
            major_elective_match = re.search(r'^#{1,3}\s+.*?Major Electives.*?Trail Courses.*?\((\d+)\s*Credits?\)', program_section, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if major_elective_match:
                program_info['major_elective_credits'] = int(major_elective_match.group(1))
                # Extract trail course codes - only from bullet lines
                trail_section_match = re.search(r'Major Electives.*?##\s+Open Elective', program_section, re.IGNORECASE | re.DOTALL)
                if trail_section_match:
                    trail_text = trail_section_match.group(0)
                    # Only get courses from bullet lines (3-4 letter dept + 3-4 digit number, exclude LO)
                    for line in trail_text.split('\n'):
                        if line.strip().startswith('-'):
                            trail_courses = re.findall(r'\b([A-Z]{3,4})\s+(\d{3,4}[A-Z]?)\b', line, re.IGNORECASE)
                            for dept, num in trail_courses:
                                program_info['major_elective_courses'].add(f"{dept.upper()}{num.upper()}")
            
            # Extract Electives section (for Microbiology)
            elective_match = re.search(r'^#{1,3}\s+Electives.*?\((\d+)\s*Credits?\)', program_section, re.IGNORECASE | re.MULTILINE)
            if elective_match:
                program_info['elective_credits'] = int(elective_match.group(1))
                # Extract elective course codes - only from first column of table
                elective_section_match = re.search(r'##\s+Electives.*?(?=##|\Z)', program_section, re.IGNORECASE | re.DOTALL)
                if elective_section_match:
                    elective_section = elective_section_match.group(0)
                    # Find table rows and extract only first column (Course)
                    table_rows = re.findall(r'^\|\s*([A-Z]{2,4})\s*(\d{3,4}[A-Z]?)\s*\|', elective_section, re.MULTILINE | re.IGNORECASE)
                    for dept, num in table_rows:
                        program_info['elective_courses'].add(f"{dept.upper()}{num.upper()}")
        else:
            print(f"Warning: Could not find program section for '{program_name}'")
                
    except FileNotFoundError:
        print(f"Warning: Program knowledge file not found: {md_path}")
    except Exception as e:
        print(f"Warning: Error reading program knowledge: {e}")
    
    return program_info


def find_courses_with_prerequisites(md_path):
    """Find all courses that have prerequisites across all programs."""
    courses_with_prereqs = set()
    
    if not os.path.exists(md_path):
        return courses_with_prereqs
    
    try:
        with open(md_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Find all program sections
        program_headers = list(re.finditer(r'^#\s+(.+?program.*)$', content, re.MULTILINE | re.IGNORECASE))
        
        for i, match in enumerate(program_headers):
            start_pos = match.start()
            if i + 1 < len(program_headers):
                end_pos = program_headers[i + 1].start()
            else:
                end_pos = len(content)
            
            program_section = content[start_pos:end_pos]
            
            # Look for course tables with prerequisites (3+ columns)
            # Pattern: Course | Credits | Prerequisites
            lines = program_section.split('\n')
            for line in lines:
                # Check if line has a course with prerequisites
                # Format: CSE 173 | 3 | MAT 120
                match2 = re.search(r'^[\|\s]*([A-Z]{2,4})\s*(\d{3,4}[A-Z]?)[\s\|]+(\d+)[^|]*\|(.+)$', line, re.IGNORECASE)
                if match2:
                    dept = match2.group(1).upper()
                    num = match2.group(2).upper()
                    course_code = f"{dept}{num}"
                    prereq_part = match2.group(4).strip()
                    
                    # Check if there's a prerequisite (not empty, not "-", not "None")
                    if prereq_part and prereq_part.lower() not in ['-', 'none', '']:
                        courses_with_prereqs.add(course_code)
                        
                        # Also extract the prereq courses
                        prereq_courses = re.findall(r'([A-Z]{2,4})\s*(\d{3,4}[A-Z]?)', prereq_part, re.IGNORECASE)
                        for pdept, pnum in prereq_courses:
                            courses_with_prereqs.add(f"{pdept.upper()}{pnum.upper()}")
    
    except Exception as e:
        print(f"Warning: Error parsing prerequisites: {e}")
    
    return courses_with_prereqs


def get_alternative_and_not_mandatory_codes(courses, program_info):
    """Get codes from alternative groups and not mandatory courses.
    
    For Microbiology University Core "Choose one" groups:
    - If a student takes more than one course from a group, the best attempt is
      auto-counted toward the core requirement.
    - The remaining courses go to free electives for the user to choose from.
    - Lab courses are paired with their theory course and follow the same fate
      (e.g. if BIO103 is the best choice, BIO103L is also auto-counted; if
      PHY107 is the excess alternative, PHY107L also goes to free electives).
    
    Returns:
        auto_count_codes: codes to automatically count (best alternative + single passing alternatives)
        open_elective_codes: codes to show in open electives for selection (excess alternatives)
        excluded_codes: codes to exclude (not passing alternatives)
    """
    auto_count_codes = set()
    open_elective_codes = set()
    excluded_alternative_codes = set()
    
    # Get lab pairing info (e.g. BIO103 <-> BIO103L, PHY107 <-> PHY107L)
    lab_pairs = program_info.get('lab_pairs', {})
    
    # Handle alternative courses
    alternative_groups = program_info.get('alternative_courses', [])
    for group in alternative_groups:
        # Separate theory and lab courses in this group
        theory_in_group = [c for c in group if not c.endswith('L')]
        lab_in_group = [c for c in group if c.endswith('L')]
        
        # If this is a "choose one with lab" group (has both theory and lab alternatives),
        # resolve at the theory level, then propagate to labs
        if lab_in_group and theory_in_group:
            # Get passing theory courses in transcript
            passing_theory = []
            theory_codes_in_transcript = set()
            for course in courses:
                code = normalize_course_code(course['code'])
                if code in theory_in_group:
                    theory_codes_in_transcript.add(code)
                    if course.get('passed'):
                        passing_theory.append((code, course.get('grade_points', 0), course))
            
            if len(passing_theory) > 1:
                # Sort by grade points descending — best theory wins
                passing_theory.sort(key=lambda x: -x[1])
                best_theory = passing_theory[0][0]
                auto_count_codes.add(best_theory)
                # Also auto-count the lab paired with the best theory
                paired_lab = lab_pairs.get(best_theory)
                if paired_lab:
                    auto_count_codes.add(paired_lab)
                
                # The remaining passing theory courses (and their labs) go to free electives
                for i in range(1, len(passing_theory)):
                    excess_theory = passing_theory[i][0]
                    open_elective_codes.add(excess_theory)
                    excess_lab = lab_pairs.get(excess_theory)
                    if excess_lab:
                        open_elective_codes.add(excess_lab)
            
            elif len(passing_theory) == 1:
                # Only one passing theory — auto-count it and its lab
                best_theory = passing_theory[0][0]
                auto_count_codes.add(best_theory)
                paired_lab = lab_pairs.get(best_theory)
                if paired_lab:
                    auto_count_codes.add(paired_lab)
            
            # Exclude non-passing theory and any labs not already handled
            for code in theory_codes_in_transcript:
                if code not in auto_count_codes and code not in open_elective_codes:
                    excluded_alternative_codes.add(code)
                    paired_lab = lab_pairs.get(code)
                    if paired_lab:
                        excluded_alternative_codes.add(paired_lab)
            
            # Any labs in the group not yet categorised — exclude them
            for lab_code in lab_in_group:
                if (lab_code not in auto_count_codes and
                        lab_code not in open_elective_codes and
                        lab_code not in excluded_alternative_codes):
                    # Check if it's in transcript
                    for course in courses:
                        if normalize_course_code(course['code']) == lab_code:
                            excluded_alternative_codes.add(lab_code)
                            break
        else:
            # Standard alternative group (theory only, no lab pairing)
            group_codes_in_transcript = set()
            passing_courses = []
            
            for course in courses:
                code = normalize_course_code(course['code'])
                if code in group:
                    group_codes_in_transcript.add(code)
                    if course.get('passed'):
                        passing_courses.append((code, course.get('grade_points', 0), course))
            
            if len(passing_courses) > 1:
                # Multiple passing: best auto-counted, rest go to open/free electives.
                # Even if the excess course is a program course, the student took it and
                # deserves to count it toward their open/free elective requirement.
                passing_courses.sort(key=lambda x: -x[1])
                auto_count_codes.add(passing_courses[0][0])
                for i in range(1, len(passing_courses)):
                    open_elective_codes.add(passing_courses[i][0])
            elif len(passing_courses) == 1:
                auto_count_codes.add(passing_courses[0][0])
            
            # Mark not-passing alternatives for exclusion
            for code in group_codes_in_transcript:
                if code not in auto_count_codes and code not in open_elective_codes:
                    excluded_alternative_codes.add(code)
    
    # Handle not mandatory courses - add to open electives for selection
    not_mandatory = program_info.get('not_mandatory_courses', set())
    for course in courses:
        code = normalize_course_code(course['code'])
        if code in not_mandatory and course.get('passed'):
            open_elective_codes.add(code)
    
    # A code cannot be both auto-counted (for a core requirement) and available as a free
    # elective choice. If a course ended up in both sets (e.g. HIS103 is the best Humanities
    # pick AND marked not-mandatory), remove it from open_elective_codes.
    open_elective_codes -= auto_count_codes

    return auto_count_codes, open_elective_codes, excluded_alternative_codes


CSE_TRAILS = {
    "Algorithms and Computation": ["CSE257", "CSE273", "CSE326", "CSE417", "CSE426", "CSE473"],
    "Software Engineering": ["CSE411"],
    "Networks": ["CSE338", "CSE422", "CSE438", "CSE482", "CSE485", "CSE486", "CSE562"],
    "Computer Architecture and VLSI": ["CSE413", "CSE414", "CSE435"],
    "Artificial Intelligence": ["CSE440", "CSE445", "CSE465", "CSE467", "CSE419", "CSE598"],
    "Bioinformatics": [],
}


def select_cse_trails(all_transcript_courses, program_info):
    """Select Primary and Secondary trails for CSE program."""
    trail_courses = program_info.get('major_elective_courses', set())
    
    if not trail_courses:
        return [], set(), set(), set()
    
    # Find trail courses in transcript
    transcript_courses_by_code = {}
    for course in all_transcript_courses:
        code = normalize_course_code(course['code'])
        if code in trail_courses and course['passed']:
            if code not in transcript_courses_by_code:
                transcript_courses_by_code[code] = course
    
    if not transcript_courses_by_code:
        print("No trail courses found in transcript.")
        return [], set(), set(), set()
    
    # Build available trails based on transcript
    available_trails = {}
    for trail_name, trail_course_list in CSE_TRAILS.items():
        courses_in_transcript = []
        for c in trail_course_list:
            if c in transcript_courses_by_code:
                courses_in_transcript.append(transcript_courses_by_code[c])
        if courses_in_transcript:
            available_trails[trail_name] = sorted(courses_in_transcript, key=lambda x: (-x['grade_points'], x['semester']))
    
    if not available_trails:
        print("No trail courses found in transcript.")
        return [], set(), set(), set()
    
    trail_names = list(available_trails.keys())
    
    # Select Primary Trail
    print(f"\n{'='*60}")
    print("PRIMARY TRAIL SELECTION (CSE)")
    print(f"{'='*60}")
    print("Select your Primary Trail (minimum 2 courses = 6 credits):")
    print("\nAvailable Trails:")
    for i, name in enumerate(trail_names, 1):
        courses = available_trails[name]
        course_with_grades = ", ".join([f"{c['code']}({c['grade']})" for c in courses])
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
    
    # Select Secondary Trail (cannot be same as primary)
    secondary_trail_names = [t for t in trail_names if t != primary_trail]
    secondary_available = {t: available_trails[t] for t in secondary_trail_names}
    
    print(f"\n{'='*60}")
    print("SECONDARY TRAIL SELECTION (CSE)")
    print(f"{'='*60}")
    print("Select your Secondary Trail (1 course = 3 credits):")
    print("\nAvailable Trails:")
    for i, name in enumerate(secondary_trail_names, 1):
        courses = available_trails[name]
        course_with_grades = ", ".join([f"{c['code']}({c['grade']})" for c in courses])
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
    
    # Excess trail courses (available for open electives)
    all_selected = primary_codes | secondary_codes
    excess_trail_codes = set()
    for code in transcript_courses_by_code:
        if code not in all_selected:
            excess_trail_codes.add(code)
    
    # Get course objects
    primary_courses = [transcript_courses_by_code[c] for c in primary_codes if c in transcript_courses_by_code]
    secondary_courses = [transcript_courses_by_code[c] for c in secondary_codes if c in transcript_courses_by_code]
    course_options = transcript_courses_by_code
    
    return primary_courses + secondary_courses, primary_codes | secondary_codes, excess_trail_codes, course_options


def select_major_electives(all_transcript_courses, program_info, md_path=None):
    """Select Major/Elective courses that count toward program requirements."""
    major_elective_credits = program_info.get('major_elective_credits', 0)
    elective_credits = program_info.get('elective_credits', 0)
    
    credits_needed = major_elective_credits + elective_credits
    
    if credits_needed <= 0:
        return [], set()
    
    # Get major elective and elective course lists
    major_courses = program_info.get('major_elective_courses', set())
    elective_courses = program_info.get('elective_courses', set())
    
    # Check if this is Microbiology (has elective_credits but no major_elective_credits)
    is_microbiology = elective_credits > 0 and major_elective_credits == 0
    
    # For Microbiology: first handle elective courses, then return for free electives
    if is_microbiology and elective_courses:
        # Find courses in transcript that are elective courses
        potential_electives = []
        seen_codes = set()
        
        for course in all_transcript_courses:
            code = normalize_course_code(course['code'])
            if code in elective_courses and code not in seen_codes:
                if course['passed']:
                    potential_electives.append(course)
                    seen_codes.add(code)
        
        if not potential_electives:
            print("No elective courses found in transcript.")
            return [], set()
        
        # Sort by grade points (best first)
        potential_electives.sort(key=lambda x: (-x['grade_points'], x['semester']))
        
        # Group by course code (keep best attempt)
        course_options = {}
        for course in potential_electives:
            code = normalize_course_code(course['code'])
            if code not in course_options:
                course_options[code] = course
        
        codes = sorted(course_options.keys())
        max_electives = elective_credits // 3
        
        # Interactive mode for Electives
        print(f"\n{'='*60}")
        print(f"ELECTIVES SELECTION (Microbiology)")
        print(f"{'='*60}")
        print(f"Program requires {elective_credits} credits of Electives (3 courses).")
        
        print(f"\nSelect up to {max_electives} course(s) to count as Electives.")
        print("Enter course numbers separated by commas (e.g., 1,3,5) or press Enter to skip:")
        
        print("\nAvailable elective courses in your transcript:")
        print("-" * 60)
        
        for i, code in enumerate(codes, 1):
            c = course_options[code]
            print(f"  {i}. {c['code']:<15} - {c['credits']:.1f} credits, Grade: {c['grade']}, Semester: {c['semester']}")
        
        print()
        
        selection = input("> ").strip()
        
        selected_electives = []
        selected_codes = set()
        if selection:
            try:
                selected_indices = [int(x.strip()) - 1 for x in selection.split(',')]
                total_credits = 0
                
                for idx in selected_indices:
                    if 0 <= idx < len(codes):
                        code = codes[idx]
                        course = course_options[code]
                        
                        if total_credits + course['credits'] <= elective_credits:
                            selected_electives.append(course)
                            selected_codes.add(code)
                            total_credits += course['credits']
                        else:
                            print(f"Warning: Skipping {code} - would exceed elective limit")
                
                print(f"\nSelected {len(selected_electives)} course(s) ({total_credits:.1f} credits) as Elective courses.")
                
            except (ValueError, IndexError):
                print("Invalid selection. No courses selected as Electives.")
        
        return selected_electives, selected_codes
    
    # For CSE or other programs: handle major electives + electives together
    all_elective_courses = major_courses | elective_courses
    
    if not all_elective_courses:
        return [], set()
    
    # Find courses in transcript that are major/elective courses
    potential_electives = []
    seen_codes = set()
    
    for course in all_transcript_courses:
        code = normalize_course_code(course['code'])
        if code in all_elective_courses and code not in seen_codes:
            if course['passed']:
                potential_electives.append(course)
                seen_codes.add(code)
    
    if not potential_electives:
        print("No major/elective courses found in transcript.")
        return [], set()
    
    # Sort by grade points (best first)
    potential_electives.sort(key=lambda x: (-x['grade_points'], x['semester']))
    
    # Group by course code (keep best attempt)
    course_options = {}
    for course in potential_electives:
        code = normalize_course_code(course['code'])
        if code not in course_options:
            course_options[code] = course
    
    codes = sorted(course_options.keys())
    max_electives = credits_needed // 3
    
    # Interactive mode
    print(f"\n{'='*60}")
    print(f"MAJOR/ELECTIVE COURSES SELECTION")
    print(f"{'='*60}")
    print(f"Program requires {credits_needed} credits of Major/Electives.")
    
    print(f"\nSelect up to {max_electives} course(s) to count as major/elective.")
    print("Enter course numbers separated by commas (e.g., 1,3,5) or press Enter to skip:")
    
    print("\nAvailable major/elective courses in your transcript:")
    print("-" * 60)
    
    for i, code in enumerate(codes, 1):
        c = course_options[code]
        course_type = "Major Elective" if code in major_courses else "Elective"
        print(f"  {i}. {c['code']:<15} - {c['credits']:.1f} credits, Grade: {c['grade']}, Semester: {c['semester']} [{course_type}]")
    
    print()
    
    selection = input("> ").strip()
    
    selected_electives = []
    selected_codes = set()
    if selection:
        try:
            selected_indices = [int(x.strip()) - 1 for x in selection.split(',')]
            total_credits = 0
            
            for idx in selected_indices:
                if 0 <= idx < len(codes):
                    code = codes[idx]
                    course = course_options[code]
                    
                    if total_credits + course['credits'] <= credits_needed:
                        selected_electives.append(course)
                        selected_codes.add(code)
                        total_credits += course['credits']
                    else:
                        print(f"Warning: Skipping {code} - would exceed major/elective limit")
            
            print(f"\nSelected {len(selected_electives)} course(s) ({total_credits:.1f} credits) as major/elective courses.")
            
        except (ValueError, IndexError):
            print("Invalid selection. No courses selected as major/elective.")
    
    return selected_electives, selected_codes


def select_open_electives(all_transcript_courses, program_courses, program_info, open_elective_args=None, md_path=None, extra_excluded_codes=None, extra_excess_codes=None, alternative_codes=None, auto_count_codes=None):
    """Ask user to select which courses count as open/free electives."""
    if program_info['open_elective_credits'] <= 0:
        return []
    
    program_course_codes = {normalize_course_code(c) for c in program_courses}
    
    # Find courses with prerequisites
    if md_path:
        courses_with_prereqs = find_courses_with_prerequisites(md_path)
    else:
        courses_with_prereqs = set()
    
    # Calculate excess major/elective courses
    excess_major_courses = set()
    
    # Check Major Electives (Trail courses for CSE)
    if program_info.get('major_elective_courses'):
        major_elective_required = program_info['major_elective_credits'] // 3  # Assume 3 credits per course
        student_major_courses = []
        for course in all_transcript_courses:
            code = normalize_course_code(course['code'])
            if code in program_info['major_elective_courses'] and course['passed']:
                student_major_courses.append((code, course['grade_points']))
        
        # Sort by grade points (best first) and take excess
        student_major_courses.sort(key=lambda x: -x[1])
        if len(student_major_courses) > major_elective_required:
            excess_codes = [c[0] for c in student_major_courses[major_elective_required:]]
            excess_major_courses.update(excess_codes)
    
    # Check Electives (for Microbiology)
    if program_info.get('elective_courses'):
        elective_required = program_info['elective_credits'] // 3
        student_elective_courses = []
        for course in all_transcript_courses:
            code = normalize_course_code(course['code'])
            if code in program_info['elective_courses'] and course['passed']:
                student_elective_courses.append((code, course['grade_points']))
        
        student_elective_courses.sort(key=lambda x: -x[1])
        if len(student_elective_courses) > elective_required:
            excess_codes = [c[0] for c in student_elective_courses[elective_required:]]
            excess_major_courses.update(excess_codes)
    
    # Merge extra excluded codes from main function (these are already selected as major/electives)
    if extra_excluded_codes:
        excess_major_courses.update(extra_excluded_codes)
    
    # Merge extra excess codes (e.g., excess trail courses from CSE) - these SHOULD be included in open electives
    if extra_excess_codes:
        excess_major_courses.update(extra_excess_codes)
    
    # Merge alternative course codes and not mandatory codes - these SHOULD be included in open electives
    if alternative_codes:
        excess_major_courses.update(alternative_codes)
    
    # Check if this is Microbiology (has elective_credits but no major_elective_credits)
    is_microbiology = program_info.get('elective_credits', 0) > 0 and program_info.get('major_elective_credits', 0) == 0
    elective_courses = program_info.get('elective_courses', set())
    elective_courses_normalized = {normalize_course_code(c) for c in elective_courses}
    
    # Find potential open elective courses - courses NOT in program, NOT with prerequisites.
    # Also include excess major/elective courses (but NOT already selected major/electives).
    # Only consider best attempts (is_best_attempt=True) — non-best attempts are retakes and
    # belong in the retaken courses table, not in the free electives pool.
    # Also exclude auto_count_codes — those are already serving a core requirement.
    excluded_codes_set = set(extra_excluded_codes) if extra_excluded_codes else set()
    auto_counted = set(auto_count_codes) if auto_count_codes else set()

    all_passing = []
    for course in all_transcript_courses:
        code = normalize_course_code(course['code'])
        # Skip courses already used as major/electives
        if code in excluded_codes_set:
            continue
        # Skip courses already auto-counted for a core requirement
        if code in auto_counted:
            continue
        # Only best attempts — non-best attempts are retakes, not free elective candidates
        if not course.get('is_best_attempt', True):
            continue
        if not course['passed']:
            continue
        # Include if: not in program, OR is excess major/elective
        if code not in program_course_codes or code in excess_major_courses:
            # Also check prerequisites - only include if no prereqs OR is excess
            if code not in courses_with_prereqs or code in excess_major_courses:
                all_passing.append(course)

    if not all_passing:
        print("No passed courses available to select as open electives.")
        return []

    # Each code appears at most once (already filtered to best attempts), so just sort and map
    all_passing.sort(key=lambda x: (-x['grade_points'], x['semester']))
    course_options = {}
    for course in all_passing:
        code = normalize_course_code(course['code'])
        if code not in course_options:
            course_options[code] = course
    
    codes = sorted(course_options.keys())
    
    # If command-line args provided, use them
    if open_elective_args:
        selected_electives = []
        total_credits = 0
        
        for arg in open_elective_args:
            normalized_arg = normalize_course_code(arg)
            # Try to match by course code
            matched = False
            for code in codes:
                if code == normalized_arg:
                    course = course_options[code]
                    if total_credits + course['credits'] <= program_info['open_elective_credits']:
                        selected_electives.append(course)
                        total_credits += course['credits']
                        matched = True
                        break
            
            if not matched:
                print(f"Warning: Could not find matching course for '{arg}'")
        
        if selected_electives:
            print(f"\nSelected {len(selected_electives)} course(s) ({total_credits:.1f} credits) as open electives based on command-line args.")
        
        return selected_electives
    
    # Interactive mode
    elective_label = "FREE ELECTIVES" if is_microbiology else "OPEN/FREE ELECTIVES"
    print(f"\n{'='*60}")
    print(f"{elective_label} SELECTION")
    print(f"{'='*60}")
    print(f"Program allows {program_info['open_elective_credits']} credits of {'free' if is_microbiology else 'open/free'} electives.")
    if program_info['open_elective_description']:
        print(f"Description: {program_info['open_elective_description']}")
    
    max_electives = program_info['open_elective_credits'] // 3  # Assume 3 credits per course
    print(f"\nSelect up to {max_electives} course(s) to count as {'free' if is_microbiology else 'open/free'} electives.")
    print("Enter course numbers separated by commas (e.g., 1,3,5) or press Enter to skip:")
    
    print(f"\nAvailable courses (not in your program) that could be {'free' if is_microbiology else 'open'} electives:")
    print("-" * 60)
    
    # Identify which codes came from university core alternatives (for labelling)
    core_alternative_codes = set(alternative_codes) if alternative_codes else set()
    
    for i, code in enumerate(codes, 1):
        c = course_options[code]
        source_label = " [University Core alternative - excess]" if code in core_alternative_codes else ""
        print(f"  {i}. {c['code']:<15} - {c['credits']:.1f} credits, Grade: {c['grade']}, Semester: {c['semester']}{source_label}")
    
    if core_alternative_codes:
        print("\n  Note: Courses marked [University Core alternative - excess] are extra courses")
        print("  you took from a 'Choose one' core group. The best grade was auto-counted for")
        print("  your University Core requirement; these can now count as Free Electives.")
    
    print()
    
    selection = input("> ").strip()
    
    if not selection:
        return []
    
    selected_electives = []
    try:
        selected_indices = [int(x.strip()) - 1 for x in selection.split(',')]
        total_credits = 0
        
        for idx in selected_indices:
            if 0 <= idx < len(codes):
                code = codes[idx]
                course = course_options[code]
                
                if total_credits + course['credits'] <= program_info['open_elective_credits']:
                    selected_electives.append(course)
                    total_credits += course['credits']
                else:
                    print(f"Warning: Skipping {code} - would exceed open elective limit")
        
        print(f"\nSelected {len(selected_electives)} course(s) ({total_credits:.1f} credits) as open electives.")
        
    except (ValueError, IndexError) as e:
        print("Invalid selection. No courses selected as open electives.")
    
    return selected_electives


def read_transcript(csv_path):
    """Read and parse the transcript CSV file."""
    courses = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Validate headers
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


def filter_courses_by_program(courses, program_info, extra_excluded_codes=None):
    """
    Filter courses to only include those valid for the declared program.
    Returns filtered list and list of excluded courses.
    extra_excluded_codes: additional codes to exclude even if in program
    """
    if not program_info['allowed_courses']:
        # If no program info available, accept all courses
        return courses, []
    
    allowed_codes = {normalize_course_code(code) for code in program_info['allowed_courses']}
    extra_excluded = extra_excluded_codes or set()
    
    filtered_courses = []
    excluded_courses = []
    
    for course in courses:
        normalized_code = normalize_course_code(course['code'])
        if normalized_code in allowed_codes and normalized_code not in extra_excluded:
            filtered_courses.append(course)
        else:
            excluded_courses.append(course)
    
    return filtered_courses, excluded_courses


def process_retakes(courses):
    """
    Process retaken courses.
    Returns modified list with 'is_best_attempt' flag for each course.
    """
    # Group courses by code
    course_groups = defaultdict(list)
    for idx, course in enumerate(courses):
        course_groups[course['code']].append((idx, course))
    
    # Mark best attempts
    for code, attempts in course_groups.items():
        if len(attempts) > 1:
            # Sort by grade points (descending), then by semester
            sorted_attempts = sorted(
                attempts,
                key=lambda x: (-x[1]['grade_points'], x[1]['semester'])
            )
            
            # Mark the best attempt
            best_idx = sorted_attempts[0][0]
            courses[best_idx]['is_best_attempt'] = True
            
            # Mark others as not best
            for idx, _ in sorted_attempts[1:]:
                courses[idx]['is_best_attempt'] = False
        else:
            # Single attempt is automatically the best
            idx = attempts[0][0]
            courses[idx]['is_best_attempt'] = True
    
    return courses


def calculate_statistics(courses):
    """Calculate summary statistics."""
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
    
    course_codes = set()
    for course in courses:
        course_codes.add(course['code'])
        
        # Count attempted credits (all courses with credits > 0, except W and I for some interpretations)
        # Based on NSU policy: "Only grades A, A-, B+, B, B-, C+, C, C-, D+, D, and F are used to determine credits attempted"
        if course['grade'].upper() not in {'W', 'I'} and course['credits'] > 0:
            stats['total_attempted'] += course['credits']
        
        # Count passed credits (all passing grades with credits > 0)
        if course['passed'] and course['credits'] > 0:
            stats['total_passed'] += course['credits']
        
        # Count credits that count toward graduation (only best attempts for retakes)
        if course.get('is_best_attempt') and course['counts_toward_graduation'] and course['credits'] > 0:
            stats['total_counted'] += course['credits']
        
        # Categorize grades
        grade = course['grade'].upper()
        if grade == 'F':
            stats['failed_courses'] += 1
        elif grade == 'W':
            stats['withdrawals'] += 1
        elif grade == 'I':
            stats['incomplete'] += 1
        
        if course['credits'] == 0:
            stats['zero_credit_courses'] += 1
    
    # Count retakes
    code_counts = defaultdict(int)
    for course in courses:
        code_counts[course['code']] += 1
    stats['retake_count'] = sum(1 for count in code_counts.values() if count > 1)
    
    return stats


def format_table(courses, stats, program_name="", excluded_courses=None):
    """Format output as a nice table."""
    lines = []
    
    # Split courses into best attempts and retakes
    best_attempts = [c for c in courses if c.get('is_best_attempt', True)]
    retakes = [c for c in courses if not c.get('is_best_attempt', False)]
    
    # Separate major/electives, open electives from regular courses
    major_electives = [c for c in best_attempts if c.get('is_major_elective', False)]
    open_electives = [c for c in best_attempts if c.get('is_open_elective', False)]
    regular_courses = [c for c in best_attempts if not c.get('is_major_elective', False) and not c.get('is_open_elective', False)]
    
    excluded_courses = excluded_courses or []
    
    # Header
    lines.append("=" * 110)
    lines.append("NSU TRANSCRIPT CREDIT ANALYSIS")
    if program_name:
        lines.append(f"Program: {program_name}")
    lines.append("=" * 110)
    lines.append("")
    
    # Table 1: Regular Best Attempts (Counted toward graduation)
    lines.append("-" * 110)
    lines.append("COURSES COUNTED TOWARD GRADUATION (Best Attempts)")
    lines.append("-" * 110)
    lines.append(f"{'Course Code':<15} {'Credits':<10} {'Grade':<8} {'Semester':<12} {'Passed':<12} {'Credits Counted':<15}")
    lines.append("-" * 110)
    
    for course in regular_courses:
        passed_str = "Passed" if course['passed'] else "Not Passed"
        
        # Show numerical value for credits counted
        if course['passed'] and course['credits'] > 0:
            counted_val = f"{course['credits']:.1f}"
        else:
            counted_val = "0.0"
        
        lines.append(
            f"{course['code']:<15} {course['credits']:<10.1f} {course['grade']:<8} "
            f"{course['semester']:<12} {passed_str:<12} {counted_val:<15}"
        )
    
    lines.append("-" * 110)
    
    # Table 1b: Major/Elective Courses
    if major_electives:
        lines.append("")
        lines.append("-" * 110)
        lines.append("MAJOR/ELECTIVE COURSES (Counted Toward Graduation)")
        lines.append("-" * 110)
        lines.append(f"{'Course Code':<15} {'Credits':<10} {'Grade':<8} {'Semester':<12} {'Passed':<12} {'Credits Counted':<15}")
        lines.append("-" * 110)
        
        for course in major_electives:
            passed_str = "Passed" if course['passed'] else "Not Passed"
            counted_val = f"{course['credits']:.1f}" if course['passed'] else "0.0"
            
            lines.append(
                f"{course['code']:<15} {course['credits']:<10.1f} {course['grade']:<8} "
                f"{course['semester']:<12} {passed_str:<12} {counted_val:<15}"
            )
        
        lines.append("-" * 110)
    
    # Table 2b: Open Electives (counted toward graduation)
    if open_electives:
        lines.append("")
        lines.append("-" * 110)
        lines.append("OPEN/FREE ELECTIVES (Counted Toward Graduation)")
        lines.append("-" * 110)
        lines.append(f"{'Course Code':<15} {'Credits':<10} {'Grade':<8} {'Semester':<12} {'Passed':<12} {'Credits Counted':<15}")
        lines.append("-" * 110)
        
        for course in open_electives:
            passed_str = "Passed" if course['passed'] else "Not Passed"
            counted_val = f"{course['credits']:.1f}" if course['passed'] else "0.0"
            
            lines.append(
                f"{course['code']:<15} {course['credits']:<10.1f} {course['grade']:<8} "
                f"{course['semester']:<12} {passed_str:<12} {counted_val:<15}"
            )
        
        lines.append("-" * 110)
    
    # Table 3: Excluded courses (not part of declared program)
    if excluded_courses:
        lines.append("")
        lines.append("-" * 110)
        lines.append(f"EXCLUDED COURSES (Not Part of {program_name} Program)")
        lines.append("-" * 110)
        lines.append(f"{'Course Code':<15} {'Credits':<10} {'Grade':<8} {'Semester':<12} {'Status':<30}")
        lines.append("-" * 110)
        
        for course in excluded_courses:
            status = "Does not count toward graduation"
            lines.append(
                f"{course['code']:<15} {course['credits']:<10.1f} {course['grade']:<8} "
                f"{course['semester']:<12} {status:<30}"
            )
        
        lines.append("-" * 110)
    
    # Table 4: Retakes (Not counted toward graduation)
    if retakes:
        lines.append("")
        lines.append("-" * 110)
        lines.append("RETAKEN COURSES (Not Counted - Previous Attempts)")
        lines.append("-" * 110)
        lines.append(f"{'Course Code':<15} {'Credits':<10} {'Grade':<8} {'Semester':<12} {'Passed':<12} {'Credits Counted':<15}")
        lines.append("-" * 110)
        
        for course in retakes:
            passed_str = "Passed" if course['passed'] else "Not Passed"
            counted_val = "0.0"
            
            lines.append(
                f"{course['code']:<15} {course['credits']:<10.1f} {course['grade']:<8} "
                f"{course['semester']:<12} {passed_str:<12} {counted_val:<15}"
            )
        
        lines.append("-" * 110)
    
    # Summary section
    lines.append("")
    lines.append("SUMMARY STATISTICS")
    lines.append("-" * 50)
    lines.append(f"Total Credits Attempted:     {stats['total_attempted']:.1f}")
    lines.append(f"Total Credits Passed:        {stats['total_passed']:.1f}")
    lines.append(f"Total Credits Counted:       {stats['total_counted']:.1f} (best attempts only)")
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
        description='The Credit Tally Engine - Analyze passed credits from transcript CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python credit_tally_engine.py transcript.csv "Computer Science" program.md
  python credit_tally_engine.py transcript.csv "Business Administration" program.md --output results.txt
        """
    )
    
    parser.add_argument(
        'csv_file',
        help='Path to the transcript CSV file'
    )
    
    parser.add_argument(
        'program_name',
        help='Name of the program (e.g., "Computer Science", "Business Administration")'
    )
    
    parser.add_argument(
        'program_knowledge',
        help='Path to the program knowledge markdown file'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Save output to file (default: print to console)',
        type=str,
        default=None
    )
    
    parser.add_argument(
        '-v', '--verbose',
        help='Show detailed information',
        action='store_true'
    )
    
    parser.add_argument(
        '-e', '--open-electives',
        help='Course codes to count as open/free electives (comma-separated, e.g., "MIC101,BIO201")',
        type=str,
        default=None
    )
    
    args = parser.parse_args()
    
    # Read and process transcript
    print(f"Reading transcript from: {args.csv_file}")
    courses = read_transcript(args.csv_file)
    
    if not courses:
        print("No courses found in transcript.")
        sys.exit(0)
    
    # Read program knowledge
    print(f"Loading program info for: {args.program_name}")
    program_info = read_program_knowledge(args.program_knowledge, args.program_name)
    
    # Handle major/elective selection FIRST
    major_elective_courses = []
    major_elective_codes = set()
    excess_trail_codes = set()
    all_courses = None
    extra_excluded_codes = set()
    
    # Check if CSE program (has trails)
    is_cse = 'computer science' in args.program_name.lower()
    
    if is_cse and program_info.get('major_elective_credits', 0) > 0:
        all_courses = read_transcript(args.csv_file)
        all_courses = process_retakes(all_courses)
        major_elective_courses, major_elective_codes, excess_trail_codes, trail_options = select_cse_trails(all_courses, program_info)
    elif program_info.get('major_elective_credits', 0) > 0 or program_info.get('elective_credits', 0) > 0:
        all_courses = read_transcript(args.csv_file)
        all_courses = process_retakes(all_courses)
        major_elective_courses, major_elective_codes = select_major_electives(all_courses, program_info, args.program_knowledge)
    
    # Handle open/free electives selection SECOND
    open_elective_courses = []
    extra_excluded_codes_for_filter = major_elective_codes.copy()
    auto_count_codes = set()
    open_elective_selection_codes = set()
    
    if program_info['open_elective_credits'] > 0:
        if not all_courses:
            all_courses = read_transcript(args.csv_file)
            all_courses = process_retakes(all_courses)
        open_elective_args = None
        if args.open_electives:
            open_elective_args = [x.strip() for x in args.open_electives.split(',')]
        
        # Exclude major elective codes already selected from main program
        extra_excluded_codes = major_elective_codes.copy()
        
        # Get alternative courses and not mandatory courses
        # - For alternatives: best is auto-counted, rest go to open electives, not-passing excluded
        # - For not mandatory: all go to open electives for selection
        auto_count_codes, open_elective_selection_codes, excluded_alternative_codes = get_alternative_and_not_mandatory_codes(all_courses, program_info)
        
        # Exclude not mandatory courses and not-passing alternatives from the main program
        # Also exclude alternatives that should go to open electives
        not_mandatory = program_info.get('not_mandatory_courses', set())
        extra_excluded_codes_for_filter = extra_excluded_codes.copy()
        extra_excluded_codes_for_filter.update(not_mandatory)
        extra_excluded_codes_for_filter.update(excluded_alternative_codes)
        # Also exclude alternatives that go to open electives - they'll only be counted if selected
        extra_excluded_codes_for_filter.update(open_elective_selection_codes)
        
        # For CSE, pass excess trail codes so they are included in open electives pool
        # Pass open_elective_selection_codes so select_open_electives knows these are available
        open_elective_courses = select_open_electives(all_courses, program_info['allowed_courses'], program_info, args.open_electives, args.program_knowledge, extra_excluded_codes, excess_trail_codes, open_elective_selection_codes, auto_count_codes)
    
    # Filter courses by program (including excess as excluded)
    if program_info['allowed_courses']:
        courses, excluded_courses = filter_courses_by_program(courses, program_info, extra_excluded_codes_for_filter)
        
        # Remove selected major/elective and open elective courses from excluded list
        excluded_codes = {normalize_course_code(c['code']) for c in open_elective_courses}
        excluded_codes.update({normalize_course_code(c['code']) for c in major_elective_courses})
        excluded_codes.update(auto_count_codes)  # Add auto-counted alternatives
        excluded_courses = [c for c in excluded_courses if normalize_course_code(c['code']) not in excluded_codes]
        
        # Get codes already in courses
        existing_codes = {normalize_course_code(c['code']) for c in courses}
        
        # Add major/elective courses to main courses list (skip if already there)
        for me in major_elective_courses:
            me_code = normalize_course_code(me['code'])
            if me_code not in existing_codes:
                me['is_major_elective'] = True
                me['is_best_attempt'] = True
                courses.append(me)
                existing_codes.add(me_code)
        
        # Add auto-counted alternative courses (best from each alternative group)
        for code in auto_count_codes:
            if code not in existing_codes:
                # Find this course in all_courses
                for c in all_courses:
                    if normalize_course_code(c['code']) == code and c.get('passed'):
                        c['is_alternative_auto'] = True
                        c['is_best_attempt'] = True
                        courses.append(c)
                        existing_codes.add(code)
                        break
        
        # Add open electives - either add new or mark existing (all attempts)
        for oe in open_elective_courses:
            oe_code = normalize_course_code(oe['code'])
            if oe_code not in existing_codes:
                oe['is_open_elective'] = True
                oe['is_best_attempt'] = True
                courses.append(oe)
                existing_codes.add(oe_code)
            else:
                # Mark ALL existing courses with this code as open elective
                for c in courses:
                    if normalize_course_code(c['code']) == oe_code and not c.get('is_major_elective', False):
                        c['is_open_elective'] = True
    else:
        excluded_courses = []
    
    if excluded_courses:
        print(f"Note: {len(excluded_courses)} course(s) excluded - not part of {args.program_name} program")
    
    # Process retakes
    courses = process_retakes(courses)
    
    # Calculate statistics
    stats = calculate_statistics(courses)
    
    # Format output
    output = format_table(courses, stats, args.program_name, excluded_courses)
    
    # Add program requirements info if available
    if program_info['total_credits_required'] > 0:
        output += f"\n\nPROGRAM REQUIREMENTS\n"
        output += "-" * 50 + "\n"
        output += f"Program:                     {program_info['name']}\n"
        output += f"Total Credits Required:      {program_info['total_credits_required']}\n"
        output += f"Credits Completed:           {stats['total_counted']:.1f}\n"
        output += f"Remaining Credits:           {max(0, program_info['total_credits_required'] - stats['total_counted']):.1f}\n"
        if program_info['mandatory_courses']:
            output += f"Mandatory Courses:           {', '.join(program_info['mandatory_courses'])}\n"
        output += "-" * 50 + "\n"
    
    # Output results
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\nResults saved to: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()