#!/usr/bin/env python3
"""
NSU CGPA Calculator
Calculates CGPA based on transcript and program requirements.
Similar flow to transcript analyzer: select major/electives, then open electives, then calculate CGPA.
"""

import argparse
import csv
import os
import re
import sys
from collections import defaultdict


GRADE_POINTS = {
    'A': 4.0, 'A-': 3.7,
    'B+': 3.3, 'B': 3.0, 'B-': 2.7,
    'C+': 2.3, 'C': 2.0, 'C-': 1.7,
    'D+': 1.3, 'D': 1.0,
    'F': 0.0
}

NON_GRADE_ENTRIES = {'W', 'I', 'WA', 'IP', 'S', 'P', 'N', ''}

CSE_TRAILS = {
    "Algorithms and Computation": ["CSE257", "CSE273", "CSE326", "CSE417", "CSE426", "CSE473"],
    "Software Engineering": ["CSE411"],
    "Networks": ["CSE338", "CSE422", "CSE438", "CSE482", "CSE485", "CSE486", "CSE562"],
    "Computer Architecture and VLSI": ["CSE413", "CSE414", "CSE435"],
    "Artificial Intelligence": ["CSE440", "CSE445", "CSE465", "CSE467", "CSE419", "CSE598"],
    "Bioinformatics": [],
}


def read_transcript(csv_path):
    """Read transcript CSV and return list of course records."""
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
    """Find the program section in the markdown content."""
    program_name_lower = program_name.lower()
    program_headers = list(re.finditer(r'^#\s+(.+?program.*)$', content, re.MULTILINE | re.IGNORECASE))
    
    for i, match in enumerate(program_headers):
        header = match.group(1).lower()
        if program_name_lower in header:
            start_pos = match.start()
            if i + 1 < len(program_headers):
                end_pos = program_headers[i + 1].start()
            else:
                end_pos = len(content)
            return content[start_pos:end_pos]
    
    return None


def normalize_course_code(code):
    """Normalize course code."""
    return code.replace(' ', '').replace('-', '').upper()


def get_program_courses(md_path, program_name):
    """Get all courses required for the program."""
    program_courses = set()
    
    if not os.path.exists(md_path):
        return program_courses
    
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        program_section = find_program_section(content, program_name)
        if not program_section:
            return program_courses
        
        course_pattern = r'\b([A-Z]{2,})\s*(\d{3,4}[A-Z]?)\b'
        for match in re.finditer(course_pattern, program_section):
            dept = match.group(1).upper()
            num = match.group(2).upper()
            course_code = f"{dept}{num}"
            
            if len(dept) >= 2 and len(num) >= 3:
                program_courses.add(course_code)
    
    except Exception as e:
        print(f"Warning: Error reading program courses: {e}")
    
    return program_courses


def find_waivable_courses(md_path, program_name):
    """Find courses that can be waived in the program."""
    waivable = []
    
    if not os.path.exists(md_path):
        return waivable
    
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        program_section = find_program_section(content, program_name)
        if not program_section:
            return waivable
        
        lines = program_section.split('\n')
        for line in lines:
            line_clean = line.replace('_', '').replace('*', '')
            # Only look for waivable courses in table rows (contain |)
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
    """Get program info including major electives and open electives."""
    program_info = {
        'allowed_courses': set(),
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
        
        # Extract all program courses
        course_pattern = r'\b([A-Z]{2,})\s*(\d{3,4}[A-Z]?)\b'
        for match in re.finditer(course_pattern, program_section):
            dept = match.group(1).upper()
            num = match.group(2).upper()
            course_code = f"{dept}{num}"
            if len(dept) >= 2 and len(num) >= 3:
                program_info['allowed_courses'].add(course_code)
        
        # Major Electives / Trail Courses
        major_match = re.search(r'^#{1,3}\s+.*?Major Electives.*?Trail Courses.*?\((\d+)\s*Credits?\)', 
                               program_section, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if major_match:
            program_info['major_elective_credits'] = int(major_match.group(1))
            trail_match = re.search(r'Major Electives.*?##\s+Open Elective', program_section, re.IGNORECASE | re.DOTALL)
            if trail_match:
                for line in trail_match.group(0).split('\n'):
                    if line.strip().startswith('-'):
                        matches = re.findall(r'\b([A-Z]{3,})\s+(\d{3,4}[A-Z]?)\b', line, re.IGNORECASE)
                        for dept, num in matches:
                            program_info['major_elective_courses'].add(f"{dept.upper()}{num.upper()}")
        
        # Open Electives
        open_match = re.search(r'^#{1,3}\s+.*?(Open Elective|Free Elective).*?\((\d+)\s*Credits?\)', 
                               program_section, re.IGNORECASE | re.MULTILINE)
        if open_match:
            program_info['open_elective_credits'] = int(open_match.group(2))
        
        # Electives (Microbiology)
        elective_match = re.search(r'^#{1,3}\s+Electives.*?\((\d+)\s*Credits?\)', 
                                  program_section, re.IGNORECASE | re.MULTILINE)
        if elective_match:
            program_info['elective_credits'] = int(elective_match.group(1))
            elective_section = re.search(r'##\s+Electives.*?(?=##|\Z)', program_section, re.IGNORECASE | re.DOTALL)
            if elective_section:
                elective_str = elective_section.group(0)
                # Extract only first column of table (Course column)
                table_rows = re.findall(r'^\|\s*([A-Z]{2,})\s*(\d{3,4}[A-Z]?)\s*\|', elective_str, re.MULTILINE | re.IGNORECASE)
                for dept, num in table_rows:
                    program_info['elective_courses'].add(f"{dept.upper()}{num.upper()}")
        
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

                    # Pattern 1: entire subsection ends with _Choose one_ block
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
                        continue  # block-level covers this subsection; skip row-level

                    # Pattern 2: inline "Choose one" in individual table row Notes columns
                    for row_match in re.finditer(
                            r'^\|\s*([^|]+?)\s*\|\s*[\d.]+\s*\|\s*[Cc]hoose one\s*\|?',
                            sub, re.MULTILINE):
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
        else:
            # For non-Microbiology programs: scan all table rows with "Choose one" in Notes
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
            if len(match) > 2 and match[2]:
                dept2, num2 = match[2], match[3]
                program_info['not_mandatory_courses'].add(f"{dept2.upper()}{num2}")

        # Any course already in an alternative group is handled by "choose one" logic.
        # Remove it from not_mandatory to avoid double-counting.
        all_alternative_codes = {code for group in alternative_groups for code in group}
        program_info['not_mandatory_courses'] -= all_alternative_codes
        
        # Waivable courses
        for line in program_section.split('\n'):
            line_clean = line.replace('_', '').replace('*', '')
            if 'waiv' in line_clean.lower() and '|' in line:
                matches = re.findall(r'\b([A-Z]{2,})\s*(\d{3,})\b', line_clean, re.IGNORECASE)
                for dept, num in matches:
                    if len(dept) >= 2:
                        course_code = f"{dept.upper()}{num}"
                        if course_code not in program_info['waivable_courses']:
                            program_info['waivable_courses'].append(course_code)
    
    except Exception as e:
        print(f"Warning: Error reading program info: {e}")
    
    return program_info


def select_major_electives(courses, program_info, md_path):
    """Select major/elective courses for CGPA calculation - same logic as transcript analyzer."""
    major_credits = program_info.get('major_elective_credits', 0)
    elective_credits = program_info.get('elective_credits', 0)
    total_credits = major_credits + elective_credits
    
    if total_credits <= 0:
        return [], set()
    
    major_courses = program_info.get('major_elective_courses', set())
    elective_courses = program_info.get('elective_courses', set())
    
    # Check if this is Microbiology (has elective_credits but no major_elective_credits)
    is_microbiology = elective_credits > 0 and major_credits == 0
    
    # For Microbiology: first handle elective courses
    if is_microbiology and elective_courses:
        # Find courses in transcript that are elective courses
        eligible = []
        seen = set()
        for course in courses:
            code = normalize_course_code(course['code'])
            if code in elective_courses and code not in seen:
                if course['grade'] in GRADE_POINTS and course['grade'] != 'F':
                    eligible.append(course)
                    seen.add(code)
        
        if not eligible:
            print("No elective courses found in transcript.")
            return [], set()
        
        # Sort by grade points (best first)
        eligible.sort(key=lambda x: (-(x['grade_points'] or 0), x['semester']))
        
        # Group by code
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
    
    # For other programs: handle major electives + electives together
    all_elective = major_courses | elective_courses
    
    if not all_elective:
        return [], set()
    
    # Find courses in transcript that are major/elective courses
    eligible = []
    seen = set()
    for course in courses:
        code = normalize_course_code(course['code'])
        if code in all_elective and code not in seen:
            if course['grade'] in GRADE_POINTS and course['grade'] != 'F':
                eligible.append(course)
                seen.add(code)
    
    if not eligible:
        print("No major/elective courses found in transcript.")
        return [], set()
    
    # Sort by grade points (best first)
    eligible.sort(key=lambda x: (-(x['grade_points'] or 0), x['semester']))
    
    # Group by code
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
    """Find all courses that have prerequisites - same as transcript analyzer."""
    courses_with_prereqs = set()
    
    if not os.path.exists(md_path):
        return courses_with_prereqs
    
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        program_headers = list(re.finditer(r'^#\s+(.+?program.*)$', content, re.MULTILINE | re.IGNORECASE))
        
        for i, match in enumerate(program_headers):
            start_pos = match.start()
            if i + 1 < len(program_headers):
                end_pos = program_headers[i + 1].start()
            else:
                end_pos = len(content)
            
            program_section = content[start_pos:end_pos]
            
            lines = program_section.split('\n')
            for line in lines:
                match2 = re.search(r'^[\|\s]*([A-Z]{2,4})\s*(\d{3,4}[A-Z]?)[\s\|]+(\d+)[^|]*\|(.+)$', line, re.IGNORECASE)
                if match2:
                    dept = match2.group(1).upper()
                    num = match2.group(2).upper()
                    course_code = f"{dept}{num}"
                    prereq_part = match2.group(4).strip()
                    
                    if prereq_part and prereq_part.lower() not in ['-', 'none', '']:
                        courses_with_prereqs.add(course_code)
                        prereq_courses = re.findall(r'([A-Z]{2,4})\s*(\d{3,4}[A-Z]?)', prereq_part, re.IGNORECASE)
                        for pdept, pnum in prereq_courses:
                            courses_with_prereqs.add(f"{pdept.upper()}{pnum.upper()}")
    except:
        pass
    
    return courses_with_prereqs


def find_trail_courses(md_path):
    """Find all trail/major elective courses - same as transcript analyzer."""
    trail_courses = set()
    
    if not os.path.exists(md_path):
        return trail_courses
    
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        trail_match = re.search(r'##\s+Major Electives.*?##\s+Open Elective', content, re.IGNORECASE | re.DOTALL)
        if trail_match:
            trail_section = trail_match.group(0)
            bullet_lines = [line for line in trail_section.split('\n') if line.strip().startswith('-')]
            for line in bullet_lines:
                trail_found = re.findall(r'\b([A-Z]{3,4})\s+(\d{3,4}[A-Z]?)\b', line, re.IGNORECASE)
                for dept, num in trail_found:
                    trail_courses.add(f"{dept.upper()}{num.upper()}")
    except:
        pass
    
    return trail_courses


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
        theory_in_group = [c for c in group if not c.endswith('L')]
        lab_in_group = [c for c in group if c.endswith('L')]
        
        if lab_in_group and theory_in_group:
            # "Choose one with lab" group — resolve at theory level, propagate to labs
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
            # Standard alternative group (no lab pairing)
            group_codes_in_transcript = set()
            passing_courses = []
            
            for course in courses:
                code = normalize_course_code(course['code'])
                if code in group:
                    group_codes_in_transcript.add(code)
                    if course['grade'] in GRADE_POINTS and course['grade'] != 'F':
                        passing_courses.append((code, course.get('grade_points', 0) or 0, course))
            
            if len(passing_courses) > 1:
                # Multiple passing: best auto-counted, rest go to open/free electives.
                passing_courses.sort(key=lambda x: -x[1])
                auto_count_codes.add(passing_courses[0][0])
                for i in range(1, len(passing_courses)):
                    open_elective_codes.add(passing_courses[i][0])
            elif len(passing_courses) == 1:
                auto_count_codes.add(passing_courses[0][0])
            
            for code in group_codes_in_transcript:
                if code not in auto_count_codes and code not in open_elective_codes:
                    excluded_alternative_codes.add(code)
    
    # Handle not mandatory courses - add to open electives for selection
    not_mandatory = program_info.get('not_mandatory_courses', set())
    for course in courses:
        code = normalize_course_code(course['code'])
        if code in not_mandatory and course['grade'] in GRADE_POINTS and course['grade'] != 'F':
            open_elective_codes.add(code)
    
    # A code cannot be both auto-counted (for a core requirement) and available as a free
    # elective choice. Remove any overlap.
    open_elective_codes -= auto_count_codes

    return auto_count_codes, open_elective_codes, excluded_alternative_codes


def select_cse_trails_cgpa(all_transcript_courses, program_info):
    """Select Primary and Secondary trails for CSE program - for CGPA calculation."""
    trail_courses = program_info.get('major_elective_courses', set())
    
    if not trail_courses:
        return [], set(), set()
    
    # Find trail courses in transcript
    transcript_courses_by_code = {}
    for course in all_transcript_courses:
        code = normalize_course_code(course['code'])
        if code in trail_courses and course['grade'] in GRADE_POINTS and course['grade'] != 'F':
            if code not in transcript_courses_by_code:
                transcript_courses_by_code[code] = course
    
    if not transcript_courses_by_code:
        print("No trail courses found in transcript.")
        return [], set(), set()
    
    # Build available trails based on transcript
    available_trails = {}
    for trail_name, trail_course_list in CSE_TRAILS.items():
        courses_in_transcript = []
        for c in trail_course_list:
            if c in transcript_courses_by_code:
                courses_in_transcript.append(transcript_courses_by_code[c])
        if courses_in_transcript:
            available_trails[trail_name] = sorted(courses_in_transcript, key=lambda x: (-(x['grade_points'] or 0), x['semester']))
    
    if not available_trails:
        print("No trail courses found in transcript.")
        return [], set(), set()
    
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
    
    return primary_courses + secondary_courses, primary_codes | secondary_codes, excess_trail_codes


def select_open_electives(courses, program_info, selected_major_codes, md_path, extra_excess_codes=None, alternative_codes=None, auto_count_codes=None):
    """Select open/free electives - same logic as transcript analyzer."""
    open_credits = program_info.get('open_elective_credits', 0)
    
    if open_credits <= 0:
        return [], set()
    
    allowed = program_info.get('allowed_courses', set())
    courses_with_prereqs = find_courses_with_prerequisites(md_path)
    trail_courses = find_trail_courses(md_path)
    
    # Calculate excess major courses for open electives
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
            excess = [x[0] for x in student_major[major_req:]]
            excess_major.update(excess)
    
    if program_info.get('elective_courses'):
        elective_req = program_info['elective_credits'] // 3
        student_elective = []
        for c in courses:
            code = normalize_course_code(c['code'])
            if code in program_info['elective_courses'] and c['grade'] in GRADE_POINTS and c['grade'] != 'F':
                student_elective.append((code, c['grade_points'] or 0))
        student_elective.sort(key=lambda x: -x[1])
        if len(student_elective) > elective_req:
            excess = [x[0] for x in student_elective[elective_req:]]
            excess_major.update(excess)
    
    # Merge selected major codes (excludes them from open electives)
    excess_major.update(selected_major_codes)
    
    # Add extra excess codes (e.g., excess trail courses) - these SHOULD be included in open electives
    if extra_excess_codes:
        excess_major.update(extra_excess_codes)
    
    # Merge alternative course codes and not mandatory codes - these SHOULD be included in open electives
    if alternative_codes:
        excess_major.update(alternative_codes)
    
    # Check if this is Microbiology (has elective_credits but no major_elective_credits)
    is_microbiology = program_info.get('elective_credits', 0) > 0 and program_info.get('major_elective_credits', 0) == 0
    elective_courses = program_info.get('elective_courses', set())
    
    # Find potential open electives. Only consider best attempts (is_best_attempt=True).
    # Non-best attempts are retakes and belong in the retaken courses table, not free electives.
    # Also exclude auto_count_codes — those are already serving a core requirement.
    auto_counted = set(auto_count_codes) if auto_count_codes else set()
    all_passing = []

    for course in courses:
        code = normalize_course_code(course['code'])
        if code in selected_major_codes:
            continue
        # Skip courses already auto-counted for a core requirement
        if code in auto_counted:
            continue
        # Only best attempts — non-best attempts are retakes, not free elective candidates
        if not course.get('is_best_attempt', True):
            continue
        if course['grade'] not in GRADE_POINTS or course['grade'] == 'F':
            continue
        if code not in allowed or code in excess_major:
            if code not in courses_with_prereqs or code in excess_major:
                all_passing.append(course)

    if not all_passing:
        print("No passed courses available to select as open electives.")
        return [], set()

    # Each code appears at most once (already filtered to best attempts), so just sort and map
    all_passing.sort(key=lambda x: (-(x['grade_points'] or 0), x['semester']))
    course_options = {}
    for course in all_passing:
        code = normalize_course_code(course['code'])
        if code not in course_options:
            course_options[code] = course
    codes = sorted(course_options.keys())
    max_courses = open_credits // 3
    
    elective_label = "FREE ELECTIVES" if is_microbiology else "OPEN/FREE ELECTIVES"
    print(f"\n{'='*60}")
    print(f"{elective_label} SELECTION")
    print(f"{'='*60}")
    print(f"Program allows {open_credits} credits of {'free' if is_microbiology else 'open/free'} electives.")
    
    print(f"\nSelect up to {max_courses} course(s) to count as {'free' if is_microbiology else 'open/free'} electives:")
    
    print(f"\nAvailable courses (not in your program) that could be {'free' if is_microbiology else 'open'} electives:")
    # Identify which codes came from university core alternatives (for labelling)
    core_alternative_codes = set(alternative_codes) if alternative_codes else set()
    
    for i, code in enumerate(codes, 1):
        c = course_options[code]
        source_label = " [University Core alternative - excess]" if code in core_alternative_codes else ""
        print(f"  {i}. {c['code']:<15} - {c['credits']:.1f} credits, Grade: {c['grade']}{source_label}")
    
    if core_alternative_codes:
        print("\n  Note: Courses marked [University Core alternative - excess] are extra courses")
        print("  you took from a 'Choose one' core group. The best grade was auto-counted for")
        print("  your University Core requirement; these can now count as Free Electives.")
    
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


def ask_waivers(courses, waivable_courses):
    """Ask user about waiver status."""
    if not waivable_courses:
        return {}
    
    print(f"\n{'='*60}")
    print("WAIVER QUESTIONS")
    print(f"{'='*60}")
    
    waivers = {}
    for course_code in waivable_courses:
        # Check if course exists in transcript
        in_transcript = any(normalize_course_code(c['code']) == course_code for c in courses)
        if not in_transcript:
            continue
            
        print(f"Waiver granted for {course_code}? (y/n): ", end="")
        try:
            answer = input().strip().lower()
            waivers[course_code] = answer in ['y', 'yes']
            if waivers[course_code]:
                print(f"  -> {course_code} marked as WAIVED")
            else:
                print(f"  -> {course_code} will use actual grade")
        except EOFError:
            waivers[course_code] = False
    
    return waivers


def process_retakes(courses):
    """
    Process retaken courses.
    Returns modified list with 'is_best_attempt' flag for each course.
    """
    course_groups = defaultdict(list)
    for idx, course in enumerate(courses):
        course_groups[normalize_course_code(course['code'])].append((idx, course))
    
    # Mark best attempts
    for code, attempts in course_groups.items():
        if len(attempts) > 1:
            # Sort by grade points (descending), then by semester (to ensure stable sort if grade points are equal)
            # Assuming semester can be compared lexicographically for sorting (e.g., "Fall 2022" < "Spring 2023")
            sorted_attempts = sorted(
                attempts,
                key=lambda x: (-(x[1]['grade_points'] or 0), x[1]['semester'])
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


def calculate_cgpa(all_courses, program_info, major_codes, open_codes, waivers, excluded_alternative_codes=None, open_elective_selection_codes=None):
    """Calculate CGPA."""
    if excluded_alternative_codes is None:
        excluded_alternative_codes = set()
    if open_elective_selection_codes is None:
        open_elective_selection_codes = set()
    
    allowed = program_info.get('allowed_courses', set())
    not_mandatory = program_info.get('not_mandatory_courses', set())
    
    total_grade_points = 0.0
    total_credits = 0.0
    
    cgpa_courses_for_calc = [] # Only best attempts used for calculation
    retaken_courses = [] # Courses that are not best attempts
    excluded_from_cgpa_output = [] # Courses excluded from CGPA and not retakes
    
    for course in all_courses: # Iterate through all courses
        code = normalize_course_code(course['code'])
        grade = course['grade']
        credits = course['credits']

        # If it's not the best attempt, it's a retake for display, but not for CGPA calculation
        if not course.get('is_best_attempt', True):
            retaken_courses.append({
                'code': course['code'],
                'credits': credits,
                'grade': grade,
                'semester': course['semester']
            })
            continue # Skip to next course, as this won't be used for CGPA calculation
        
        # --- The rest of the logic below only applies to best attempts for CGPA calculation ---
        # Check waiver
        if code in waivers and waivers[code]:
            excluded_from_cgpa_output.append({'code': course['code'], 'credits': credits, 'grade': 'WA', 'reason': 'Waiver granted', 'semester': course['semester']}) # Added semester
            continue
        
        # Non-grade entries
        if grade in NON_GRADE_ENTRIES:
            excluded_from_cgpa_output.append({'code': course['code'], 'credits': credits, 'grade': grade, 'reason': 'Non-grade entry', 'semester': course['semester']}) # Added semester
            continue
        
        # Unknown grades
        if grade not in GRADE_POINTS:
            excluded_from_cgpa_output.append({'code': course['code'], 'credits': credits, 'grade': grade, 'reason': 'Unknown grade', 'semester': course['semester']}) # Added semester
            continue
        
        # Zero credits
        if credits <= 0:
            excluded_from_cgpa_output.append({'code': course['code'], 'credits': credits, 'grade': grade, 'reason': 'Zero credits', 'semester': course['semester']}) # Added semester
            continue
        
        # Check if course counts for CGPA
        in_allowed = (code in allowed) and (code not in not_mandatory) and (code not in excluded_alternative_codes)
        if code in open_elective_selection_codes:
            in_allowed = code in open_codes
        counts = in_allowed or (code in major_codes) or (code in open_codes)
        
        if counts:
            gp = GRADE_POINTS[grade]
            cgpa_courses_for_calc.append({
                'code': course['code'],
                'credits': credits,
                'grade': grade,
                'grade_points': gp,
                'semester': course['semester'] # Added for display
            })
            total_grade_points += credits * gp
            total_credits += credits
        else:
            excluded_from_cgpa_output.append({'code': course['code'], 'credits': credits, 'grade': grade, 'reason': 'Not in program', 'semester': course['semester']}) # Added semester
    
    cgpa = total_grade_points / total_credits if total_credits > 0 else 0.0
    
    return cgpa, cgpa_courses_for_calc, excluded_from_cgpa_output, retaken_courses, total_grade_points, total_credits


def format_output(cgpa, cgpa_courses, excluded, retaken_courses, total_points, total_credits, program_name):
    """Format CGPA output."""
    lines = []
    
    lines.append("\n" + "=" * 70)
    lines.append("CGPA ANALYSIS FOR " + program_name.upper()) # More descriptive header
    lines.append("=" * 70)
    lines.append("")

    # Display best attempts that count towards CGPA
    lines.append("-" * 70)
    lines.append("COURSES COUNTED TOWARD CGPA (Best Attempts)")
    lines.append("-" * 70)
    lines.append(f"{'Course Code':<15} {'Credits':<10} {'Grade':<8} {'Semester':<12} {'Grade Points':<15}")
    lines.append("-" * 70)
    
    for c in cgpa_courses:
        lines.append(f"{c['code']:<15} {c['credits']:<10.1f} {c['grade']:<8} {c['semester']:<12} {c['grade_points']:<15.1f}")
    
    lines.append("-" * 70)
    lines.append(f"{'TOTAL':<15} {total_credits:<10.1f} {'':<8} {'':<12} {total_points:<15.1f}")
    lines.append("")
    
    # Retaken courses table
    if retaken_courses:
        lines.append("-" * 70)
        lines.append("RETAKEN COURSES (Not Used for CGPA Calculation)")
        lines.append("-" * 70)
        lines.append(f"{'Course Code':<15} {'Credits':<10} {'Grade':<8} {'Semester':<12} {'Note':<15}")
        lines.append("-" * 70)
        for c in retaken_courses:
            lines.append(
                f"{c['code']:<15} {c['credits']:<10.1f} {c['grade']:<8} "
                f"{c['semester']:<12} {'Previous Attempt':<15}"
            )
        lines.append("-" * 70)
        lines.append("")

    # Excluded courses table
    if excluded:
        lines.append("-" * 70) # Changed from "=" to "-" for consistency with other tables
        lines.append("EXCLUDED COURSES (Not in CGPA)")
        lines.append("-" * 70) # Changed from "=" to "-"
        lines.append(f"{'Course Code':<15} {'Credits':<10} {'Grade':<8} {'Semester':<12} {'Reason':<30}") # Added semester
        lines.append("-" * 70)
        
        for c in excluded:
            semester_info = c.get('semester', '') 
            lines.append(f"{c['code']:<15} {c['credits']:<10.1f} {c['grade']:<8} {semester_info:<12} {c['reason']:<30}")
        lines.append("-" * 70)
        lines.append("")
    
    lines.append("=" * 70)
    lines.append("CGPA SUMMARY")
    lines.append("=" * 70)
    lines.append(f"Total Credits Attempted (for CGPA):    {total_credits:.1f}") # Clarified "Attempted"
    lines.append(f"Total Grade Points:                    {total_points:.2f}")
    lines.append(f"CGPA:                                  {cgpa:.2f}")
    lines.append("")
    
    if cgpa >= 2.0:
        lines.append("Status: CGPA meets minimum requirement (2.0)")
    else:
        lines.append("Status: CGPA below minimum requirement (2.0)")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='The Logic Gate & Waiver Handler - Calculate CGPA with waiver support')
    parser.add_argument('csv_file', help='Path to transcript CSV')
    parser.add_argument('program_name', help='Program name')
    parser.add_argument('program_knowledge', help='Path to program MD file')
    args = parser.parse_args()
    
    print(f"Reading transcript: {args.csv_file}")
    courses = read_transcript(args.csv_file)
    
    if not courses:
        print("No courses found.")
        sys.exit(0)
    
    print(f"Program: {args.program_name}")
    
    program_info = get_program_info(args.program_knowledge, args.program_name)
    
    # Process retakes
    courses = process_retakes(courses)
    
    # Check if CSE program (has trails)
    is_cse = 'computer science' in args.program_name.lower()
    
    # Select major/electives
    excess_trail_codes = set()
    if is_cse and program_info.get('major_elective_credits', 0) > 0:
        major_courses, major_codes, excess_trail_codes = select_cse_trails_cgpa(courses, program_info)
    else:
        major_courses, major_codes = select_major_electives(courses, program_info, args.program_knowledge)
    
    # Get alternative courses and not mandatory courses
    auto_count_codes, open_elective_selection_codes, excluded_alternative_codes = get_alternative_and_not_mandatory_codes(courses, program_info)
    
    # Select open electives - exclude major codes, include excess trail codes and alternative codes as available
    open_courses, open_codes = select_open_electives(courses, program_info, major_codes, args.program_knowledge, excess_trail_codes, open_elective_selection_codes, auto_count_codes)
    
    # Combine open_codes with auto_count_codes for CGPA calculation
    all_open_codes = open_codes | auto_count_codes
    
    # Ask about waivers
    waivers = ask_waivers(courses, program_info['waivable_courses'])
    
    # Calculate CGPA - pass excluded_alternative_codes and open_elective_selection_codes
    cgpa, cgpa_courses, excluded, retaken_courses, total_points, total_credits = calculate_cgpa(
        courses, program_info, major_codes, all_open_codes, waivers, excluded_alternative_codes, open_elective_selection_codes
    )
    
    # Output
    output = format_output(cgpa, cgpa_courses, excluded, retaken_courses, total_points, total_credits, args.program_name)
    print(output)


if __name__ == '__main__':
    main()