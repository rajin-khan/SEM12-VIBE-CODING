#!/usr/bin/env python3
"""
NSU Audit Core — 2000 Unique Student Transcript Generator
Generates 2000 individual transcript CSV files in a 'transcripts/' directory,
each representing a different student with varied academic profiles.
"""

import csv
import os
import random
import sys
from engine.credit_engine import SEMESTERS
from engine.prerequisites import PREREQUISITES_CSE, PREREQUISITES_BBA

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# ─── Course Pools (Post-Fall 2014, 130-credit curriculum) ───

# CSE Major Core (42 credits)
CSE_MAJOR_CORE = {
    "CSE173": ("Discrete Mathematics", 3),
    "CSE215": ("Programming Language II", 3),
    "CSE215L": ("Programming Language II Lab", 1),
    "CSE225": ("Data Structures & Algorithms", 3),
    "CSE225L": ("Data Structures & Algorithms Lab", 1),
    "CSE231": ("Digital Logic Design", 3),
    "CSE231L": ("Digital Logic Design Lab", 1),
    "CSE299": ("Junior Design Project", 1),
    "CSE311": ("Database Management Systems", 3),
    "CSE311L": ("Database Management Systems Lab", 1),
    "CSE323": ("Operating Systems Design", 3),
    "CSE327": ("Software Engineering", 3),
    "CSE331": ("Microprocessor Interfacing", 3),
    "CSE331L": ("Microprocessor Interfacing Lab", 1),
    "CSE332": ("Computer Organization & Architecture", 3),
    "CSE373": ("Design & Analysis of Algorithms", 3),
    "CSE425": ("Concepts of Programming Languages", 3),
    "EEE141": ("Electrical Circuits I", 3),
    "EEE141L": ("Electrical Circuits I Lab", 1),
    "EEE111": ("Analog Electronics I", 3),
    "EEE111L": ("Analog Electronics I Lab", 1),
}

# CSE Capstone + Engineering Economics (7 credits)
CSE_CAPSTONE = {
    "CSE499A": ("Senior Capstone Design I", 2),
    "CSE499B": ("Senior Capstone Design II", 2),
    "EEE452": ("Engineering Economics", 3),
}

# SEPS Core (41 credits)
CSE_SEPS_CORE = {
    "CSE115": ("Programming Language I", 3),
    "CSE115L": ("Programming Language I Lab", 1),
    "MAT116": ("Pre-Calculus", 3),
    "MAT120": ("Calculus I", 3),
    "MAT125": ("Linear Algebra", 3),
    "MAT130": ("Calculus II", 3),
    "MAT250": ("Calculus III", 3),
    "MAT350": ("Complex Variables", 3),
    "MAT361": ("Discrete Mathematics II", 3),
    "PHY107": ("Physics I", 3),
    "PHY107L": ("Physics I Lab", 1),
    "PHY108": ("Physics II", 3),
    "PHY108L": ("Physics II Lab", 1),
    "CHE101": ("Chemistry I", 3),
    "CHE101L": ("Chemistry I Lab", 1),
    "BIO103": ("Biology I", 3),
    "BIO103L": ("Biology I Lab", 1),
    "CEE110": ("Engineering Drawing", 1),
}

# CSE GED (University Core)
CSE_GED = {
    "ENG103": ("Intermediate Composition", 3),
    "ENG105": ("Advanced Writing Skills", 3),
    "ENG111": ("Public Speaking", 3),
    "PHI104": ("Introduction to Ethics", 3),
    "HIS101": ("Bangladesh History & Culture", 3),
    "HIS102": ("World Civilization", 3),
    "CSE101": ("Introduction to Python Programming", 3),
    "CSE145": ("Introduction to Artificial Intelligence", 3),
    "CSE226": ("Fundamentals of Vibe Coding", 3),
}

CSE_GED_CHOICE_1 = {"ECO101": ("Intro to Microeconomics", 3), "ECO104": ("Intro to Macroeconomics", 3)}
CSE_GED_CHOICE_2 = {"POL101": ("Intro to Political Science", 3), "POL104": ("Political Science", 3)}
CSE_GED_CHOICE_3 = {"SOC101": ("Intro to Sociology", 3), "ANT101": ("Anthropology", 3),
                     "ENV203": ("Environmental Studies", 3), "GEO205": ("Geography", 3)}

CSE_ELECTIVES_400 = {
    "CSE421": ("Machine Learning", 3),
    "CSE423": ("Data Mining", 3),
    "CSE445": ("Computer Vision", 3),
    "CSE461": ("Robotics", 3),
    "CSE471": ("Compiler Design", 3),
}

OPEN_ELECTIVES = {
    "SOC201": ("Social Theory", 3),
    "PHI201": ("Logic", 3),
    "HIS201": ("Modern History", 3),
}

# BBA School Core (7 courses / 21 credits)
BBA_SCHOOL_CORE = {
    "ECO101": ("Intro to Microeconomics", 3),
    "ECO104": ("Intro to Macroeconomics", 3),
    "MIS107": ("Introduction to Computers", 3),
    "BUS251": ("Business Communication", 3),
    "BUS172": ("Introduction to Statistics", 3),
    "BUS173": ("Applied Statistics", 3),
    "BUS135": ("Business Mathematics", 3),
}

# BBA Core (12 courses / 36 credits)
BBA_CORE = {
    "ACT201": ("Intro to Financial Accounting", 3),
    "ACT202": ("Intro to Managerial Accounting", 3),
    "FIN254": ("Intro to Financial Management", 3),
    "LAW200": ("Legal Environment of Business", 3),
    "INB372": ("International Business", 3),
    "MKT202": ("Introduction to Marketing", 3),
    "MIS207": ("Management Information Systems", 3),
    "MGT212": ("Principles of Management", 3),
    "MGT351": ("Human Resource Management", 3),
    "MGT314": ("Production Management", 3),
    "MGT368": ("Entrepreneurship", 3),
    "MGT489": ("Strategic Management", 3),
}

# BBA GED — Fixed (always required)
BBA_GED = {
    "ENG103": ("Intermediate Composition", 3),
    "ENG105": ("Advanced Composition", 3),
    "PHI401": ("Ethics / Philosophy", 3),
}

# GED Choice Groups
BBA_GED_CHOICE_LANG = {"BEN205": ("Bengali Literature", 3), "ENG115": ("English Literature", 3), "CHN101": ("Chinese Language", 3)}
BBA_GED_CHOICE_HIS = {"HIS101": ("Bangladesh History", 3), "HIS102": ("World Civilization", 3),
                       "HIS103": ("History of South Asia", 3), "HIS205": ("Modern History", 3)}  # pick 2
BBA_GED_CHOICE_POL = {"POL101": ("Intro to Political Science", 3), "POL104": ("Political Science", 3),
                       "PAD201": ("Public Administration", 3)}
BBA_GED_CHOICE_SOC = {"SOC101": ("Intro to Sociology", 3), "GEO205": ("Geography", 3), "ANT101": ("Anthropology", 3)}
BBA_GED_CHOICE_SCI = {"BIO103": ("Biology I", 3), "ENV107": ("Environmental Science", 3), "PBH101": ("Public Health", 3),
                       "PSY101": ("Intro to Psychology", 3), "PHY107": ("Physics I", 3), "CHE101": ("Chemistry I", 3)}  # pick 3
BBA_GED_CHOICE_LAB = {"BIO103L": ("Biology I Lab", 1), "ENV107L": ("Environmental Science Lab", 1),
                       "PBH101L": ("Public Health Lab", 1), "PSY101L": ("Psychology Lab", 1),
                       "PHY107L": ("Physics I Lab", 1), "CHE101L": ("Chemistry I Lab", 1)}  # pick 1

BBA_INTERNSHIP = {"BUS498": ("Internship", 4)}

# BBA Concentration Course Pools — Curriculum 143 Major Map
BBA_CONC_COURSES = {
    "ACT": {
        "required": {"ACT310": ("Intermediate Accounting I", 3), "ACT320": ("Intermediate Accounting II", 3),
                     "ACT360": ("Advanced Managerial Accounting", 3), "ACT370": ("Taxation", 3)},
        "elective": {"ACT380": ("Audit and Assurance", 3), "ACT460": ("Advanced Financial Accounting", 3),
                     "ACT430": ("Accounting Information Systems", 3), "ACT410": ("Financial Statement Analysis", 3)},
    },
    "FIN": {
        "required": {"FIN433": ("Financial Markets and Institutions", 3), "FIN440": ("Corporate Finance", 3),
                     "FIN435": ("Investment Theory", 3), "FIN444": ("International Financial Management", 3)},
        "elective": {"FIN455": ("Financial Modelling Using Excel", 3), "FIN464": ("Derivatives", 3),
                     "FIN470": ("Insurance and Risk Management", 3), "FIN480": ("Behavioural Finance", 3),
                     "FIN410": ("Financial Statement Analysis", 3)},
    },
    "MKT": {
        "required": {"MKT337": ("Promotional Management", 3), "MKT344": ("Consumer Behaviour", 3),
                     "MKT460": ("Strategic Marketing", 3), "MKT470": ("Marketing Research", 3)},
        "elective": {"MKT412": ("Services Marketing", 3), "MKT465": ("Brand Management", 3),
                     "MKT382": ("International Marketing", 3), "MKT417": ("Export-Import Management", 3),
                     "MKT330": ("Retail Management", 3), "MKT450": ("Marketing Channels", 3),
                     "MKT355": ("Agricultural Marketing", 3), "MKT445": ("Sales Management", 3),
                     "MKT475": ("Marketing Analytics", 3)},
    },
    "MGT": {
        "required": {"MGT321": ("Organizational Behavior", 3), "MGT330": ("Designing Effective Organizations", 3),
                     "HRM370": ("Managerial Skill Development", 3), "MGT410": ("Entrepreneurship II", 3)},
        "elective": {"MGT350": ("Managing Quality", 3), "MGT490": ("Project Management", 3),
                     "HRM470": ("Negotiations", 3), "HRM450": ("Industrial Relations", 3),
                     "MIS320": ("IT for Managers", 3)},
    },
    "HRM": {
        "required": {"HRM340": ("Training and Development", 3), "HRM360": ("Planning and Staffing", 3),
                     "HRM380": ("Compensation Theory and Practice", 3), "HRM450": ("Industrial Relations", 3)},
        "elective": {"HRM370": ("Managerial Skill Development", 3), "HRM499": ("Special Topics in HRM", 3),
                     "HRM470": ("Negotiations", 3)},
    },
    "MIS": {
        "required": {"MIS210": ("Computer Programming", 3), "MIS310": ("Systems Analysis", 3),
                     "MIS320": ("IT for Managers", 3), "MIS470": ("IT Project Management", 3)},
        "elective": {"MIS330": ("Database Systems", 3), "MIS410": ("Systems Design", 3),
                     "MIS450": ("IS Security", 3), "MGT490": ("Project Management", 3),
                     "MIS499": ("Special Topics in MIS", 3)},
    },
    "SCM": {
        "required": {"SCM310": ("Supply Chain Management", 3), "SCM320": ("Procurement and Inventory", 3),
                     "SCM450": ("Supply Chain Analytics", 3), "MGT460": ("Logistics Management", 3)},
        "elective": {"MGT360": ("Global Supply Chain", 3), "MGT390": ("Warehouse Management", 3),
                     "MGT470": ("Quality Management", 3), "MGT490": ("Project Management", 3)},
    },
    "ECO": {
        "required": {"ECO201": ("Intermediate Microeconomics", 3), "ECO204": ("Intermediate Macroeconomics", 3),
                     "ECO348": ("Mathematical Economics", 3), "ECO328": ("Econometrics", 3)},
        "elective": {"ECO244": ("Economic Development", 3), "ECO301": ("Monetary Economics", 3),
                     "ECO304": ("International Economics", 3), "ECO317": ("Public Economics", 3),
                     "ECO354": ("Advanced Microeconomics", 3), "ECO410": ("Development Economics", 3),
                     "ECO415": ("Public Finance", 3), "ECO441": ("Labor Economics", 3),
                     "ECO450": ("Game Theory", 3), "ECO460": ("International Trade", 3)},
    },
    "INB": {
        "required": {"INB400": ("International Trade and Finance", 3), "INB490": ("Cross-Cultural Management", 3),
                     "INB480": ("Global Business Strategy", 3), "MKT382": ("International Marketing", 3)},
        "elective": {"INB410": ("International Competitiveness", 3), "INB350": ("International Business Negotiation", 3),
                     "INB355": ("Country Risk Analysis", 3), "INB415": ("Emerging Markets", 3),
                     "INB450": ("Global Entrepreneurship", 3), "INB495": ("Special Topics in INB", 3),
                     "MKT417": ("Export-Import Management", 3)},
    },
}

BBA_CONC_NAMES = list(BBA_CONC_COURSES.keys())  # ["ACT", "FIN", ...]

ALL_COURSES = {}
for d in [CSE_MAJOR_CORE, CSE_CAPSTONE, CSE_SEPS_CORE, CSE_GED, CSE_GED_CHOICE_1, CSE_GED_CHOICE_2,
          CSE_GED_CHOICE_3, CSE_ELECTIVES_400, OPEN_ELECTIVES, BBA_SCHOOL_CORE, BBA_CORE, BBA_GED,
          BBA_GED_CHOICE_LANG, BBA_GED_CHOICE_HIS, BBA_GED_CHOICE_POL, BBA_GED_CHOICE_SOC,
          BBA_GED_CHOICE_SCI, BBA_GED_CHOICE_LAB, BBA_INTERNSHIP]:
    ALL_COURSES.update(d)
for conc_data in BBA_CONC_COURSES.values():
    ALL_COURSES.update(conc_data["required"])
    ALL_COURSES.update(conc_data["elective"])
ALL_COURSES["ENG102"] = ("Introduction to Composition", 3)
ALL_COURSES["MAT112"] = ("College Algebra", 0)
ALL_COURSES["BUS112"] = ("Intro to Business Mathematics", 3)

# SEMESTERS imported from engine.credit_engine


# ─── Student Profile Types ───────────────────────────────

PROFILES = [
    "top_student",        # CGPA 3.5+, all courses done, eligible
    "good_student",       # CGPA 2.5-3.5, most courses done
    "struggling",         # CGPA 1.5-2.5, many retakes, probation risk
    "early_stage",        # Freshman/sophomore, few courses
    "mid_stage",          # Junior, about half done
    "nearly_done",        # Senior, missing 1-3 courses
    "retake_heavy",       # Many retakes and Fs
    "transfer_student",   # Several T grades
    "withdrawn_heavy",    # Many W grades
    "probation",          # CGPA < 2.0
]


def grade_for_profile(profile):
    """Return a weighted random grade based on student profile."""
    if profile == "top_student":
        return random.choices(
            ["A", "A-", "B+", "B", "B-", "C+"],
            weights=[30, 25, 20, 15, 7, 3], k=1)[0]
    elif profile == "good_student":
        return random.choices(
            ["A", "A-", "B+", "B", "B-", "C+", "C", "C-"],
            weights=[10, 15, 20, 20, 15, 10, 7, 3], k=1)[0]
    elif profile == "struggling":
        return random.choices(
            ["B", "B-", "C+", "C", "C-", "D+", "D", "F"],
            weights=[5, 8, 12, 20, 15, 15, 15, 10], k=1)[0]
    elif profile == "retake_heavy":
        return random.choices(
            ["C", "C-", "D+", "D", "F", "W"],
            weights=[15, 15, 15, 15, 25, 15], k=1)[0]
    elif profile == "probation":
        return random.choices(
            ["C-", "D+", "D", "F", "I"],
            weights=[15, 20, 25, 30, 10], k=1)[0]
    elif profile == "withdrawn_heavy":
        return random.choices(
            ["A", "B+", "B", "C+", "C", "D", "F", "W"],
            weights=[8, 10, 12, 10, 10, 5, 5, 40], k=1)[0]
    elif profile == "transfer_student":
        return random.choices(
            ["A", "A-", "B+", "B", "C+", "C", "T"],
            weights=[12, 12, 15, 15, 10, 10, 26], k=1)[0]
    else:
        return random.choices(
            ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F", "W"],
            weights=[8, 8, 10, 12, 10, 10, 10, 8, 7, 7, 6, 4], k=1)[0]


def sort_rows(rows):
    """Sort transcript rows chronologically by semester."""
    # Create a mapping for quick lookup
    sem_map = {sem: i for i, sem in enumerate(SEMESTERS)}
    # If a semester is not in the list (e.g. transfer), give it index -1
    return sorted(rows, key=lambda r: sem_map.get(r[4], -1))


def pick_semesters(n, start_idx=None):
    """Pick n sequential semesters starting from a random point."""
    if start_idx is None:
        start_idx = random.randint(0, max(0, len(SEMESTERS) - n))
    end = min(start_idx + n, len(SEMESTERS))
    return SEMESTERS[start_idx:end]


def get_eligible_courses(pool_codes, passed_set, prereq_map, credits_earned):
    """Filter a pool of course codes based on prerequisites and credits earned."""
    eligible = []
    for code in pool_codes:
        if code in passed_set:
            continue
        
        reqs = prereq_map.get(code, [])
        met = True
        for req in reqs:
            if req == "_SENIOR_":
                if credits_earned < 100:
                    met = False
                    break
            elif req not in passed_set:
                met = False
                break
        
        if met:
            # Special case for Labs: Prefer taking with theory or after
            # However, for simplicity here, we just ensure theory is passed or we could allow same-sem
            # Let's keep it simple: if theory is in passed_set, lab is eligible.
            if code.endswith("L"):
                theory = code[:-1]
                if theory not in passed_set:
                    # Allow same-semester theory+lab by not adding to eligible yet if theory not passed,
                    # but we'll handle same-semester selection in the main loop.
                    pass
            eligible.append(code)
    return eligible


def generate_cse_student(profile, student_id):
    """Generate a CSE student transcript strictly following prerequisites."""
    rows = []
    passed_courses = set()
    credits_earned = 0
    
    # ── Simulation Parameters ──
    # Determine progress based on profile
    if profile == "top_student":
        target_credits = 130
        pref_load = 5  # courses/sem
    elif profile == "good_student":
        target_credits = random.randint(100, 130)
        pref_load = random.randint(4, 5)
    elif profile == "nearly_done":
        target_credits = random.randint(115, 128)
        pref_load = 4
    elif profile == "mid_stage":
        target_credits = random.randint(50, 80)
        pref_load = random.randint(3, 4)
    elif profile == "early_stage":
        target_credits = random.randint(12, 40)
        pref_load = random.randint(3, 4)
    else:
        target_credits = random.randint(30, 110)
        pref_load = random.randint(2, 4)

    # ── Waivers ──
    # Simulating admission waivers (MAT112/116, ENG102)
    # These count as "passed" for prerequisite purposes and need to be in the transcript
    if random.random() < 0.6: 
         passed_courses.add("MAT112")
         rows.append(["MAT112", "College Algebra", "0", "T", SEMESTERS[0]])
    if random.random() < 0.4: 
         passed_courses.add("MAT116")
         rows.append(["MAT116", "Pre-Calculus", "0", "T", SEMESTERS[0]])
    if random.random() < 0.5: 
         passed_courses.add("ENG102")
         rows.append(["ENG102", "Introduction to Composition", "3", "T", SEMESTERS[0]])

    # ── Semester Loop ──
    n_semesters = random.randint(2, len(SEMESTERS))
    start_idx = random.randint(0, len(SEMESTERS) - n_semesters)
    avail_sems = SEMESTERS[start_idx : start_idx + n_semesters]
    
    # Define pools
    major_core = list(CSE_MAJOR_CORE.keys())
    seps_core = list(CSE_SEPS_CORE.keys())
    ged_req = list(CSE_GED.keys())
    capstone = list(CSE_CAPSTONE.keys())
    
    for sem in avail_sems:
        if credits_earned >= target_credits:
            break
            
        # 1. Identify all eligible courses from all pools
        all_eligible = []
        all_eligible += get_eligible_courses(major_core, passed_courses, PREREQUISITES_CSE, credits_earned)
        all_eligible += get_eligible_courses(seps_core, passed_courses, PREREQUISITES_CSE, credits_earned)
        all_eligible += get_eligible_courses(ged_req, passed_courses, PREREQUISITES_CSE, credits_earned)
        all_eligible += get_eligible_courses(capstone, passed_courses, PREREQUISITES_CSE, credits_earned)
        
        # Handle choice groups (one from each)
        for choice_pool in [CSE_GED_CHOICE_1, CSE_GED_CHOICE_2, CSE_GED_CHOICE_3]:
            if not any(c in passed_courses for c in choice_pool):
                all_eligible += get_eligible_courses(list(choice_pool.keys()), passed_courses, PREREQUISITES_CSE, credits_earned)

        # 2. Add Electives if eligible
        if credits_earned > 60:
            all_eligible += get_eligible_courses(list(CSE_ELECTIVES_400.keys()), passed_courses, PREREQUISITES_CSE, credits_earned)
            all_eligible += get_eligible_courses(list(OPEN_ELECTIVES.keys()), passed_courses, PREREQUISITES_CSE, credits_earned)

        if not all_eligible:
            continue
            
        # 3. Select load for this semester
        # Prioritize lower-level courses (shorter strings or specific prefixes usually)
        # Or just random sample from eligible
        current_load = min(len(all_eligible), pref_load + random.randint(-1, 1))
        if current_load <= 0: continue
        
        # Sort eligible to prioritize "foundational" (e.g. MAT120 before CSE311)
        # Simple heuristic: courses with more children in prereq map are higher priority
        priority_map = {c: 0 for c in all_eligible}
        for target, reqs in PREREQUISITES_CSE.items():
            for r in reqs:
                if r in priority_map: priority_map[r] += 1
        
        all_eligible.sort(key=lambda c: priority_map.get(c, 0), reverse=True)
        # Take some top ones and some random ones
        n_top = min(current_load, 2)
        taking = all_eligible[:n_top]
        if current_load > n_top:
            taking += random.sample(all_eligible[n_top:], current_load - n_top)

        # 4. Process the selected courses
        sem_passed = []
        for code in taking:
            name, credits = ALL_COURSES[code]
            grade = grade_for_profile(profile)
            rows.append([code, name, str(credits), grade, sem])
            
            if grade not in ("F", "W", "I"):
                sem_passed.append(code)
                credits_earned += credits
                
                # If theory passed, allow lab in next sem (already covered by get_eligible)
                # If lab is in all_eligible and theory is also taken this sem, let's just allow it
                if not code.endswith("L") and code + "L" in ALL_COURSES and code + "L" in all_eligible:
                    if random.random() < 0.8: # Take lab with theory
                         l_code = code + "L"
                         l_name, l_credits = ALL_COURSES[l_code]
                         l_grade = grade_for_profile(profile)
                         rows.append([l_code, l_name, str(l_credits), l_grade, sem])
                         if l_grade not in ("F", "W", "I"):
                             sem_passed.append(l_code)
                             credits_earned += l_credits

        passed_courses.update(sem_passed)

    return sort_rows(rows)


def generate_bba_student(profile, student_id, concentration=None):
    """Generate a BBA student transcript strictly following prerequisites."""
    rows = []
    if concentration is None:
        concentration = random.choice(BBA_CONC_NAMES)
        
    passed_courses = set()
    credits_earned = 0
    
    # ── Simulation Parameters ──
    if profile == "top_student":
        target_credits = 130
        pref_load = 5
    elif profile == "good_student":
        target_credits = random.randint(100, 130)
        pref_load = random.randint(4, 5)
    elif profile == "nearly_done":
        target_credits = random.randint(115, 128)
        pref_load = 4
    elif profile == "mid_stage":
        target_credits = random.randint(50, 80)
        pref_load = random.randint(3, 4)
    elif profile == "early_stage":
        target_credits = random.randint(12, 40)
        pref_load = random.randint(3, 4)
    else:
        target_credits = random.randint(30, 110)
        pref_load = random.randint(2, 4)

    # ── Waivers ──
    if random.random() < 0.5: 
        passed_courses.add("BUS112")
        rows.append(["BUS112", "Intro to Business Mathematics", "3", "T", SEMESTERS[0]])
    if random.random() < 0.5: 
        passed_courses.add("ENG102")
        rows.append(["ENG102", "Introduction to Composition", "3", "T", SEMESTERS[0]])

    # ── Semester Loop ──
    n_semesters = random.randint(2, len(SEMESTERS))
    start_idx = random.randint(0, len(SEMESTERS) - n_semesters)
    avail_sems = SEMESTERS[start_idx : start_idx + n_semesters]
    
    # Pools
    school_core = list(BBA_SCHOOL_CORE.keys())
    bba_core = list(BBA_CORE.keys())
    ged_req = list(BBA_GED.keys())
    conc_data = BBA_CONC_COURSES[concentration]
    conc_req = list(conc_data["required"].keys())
    conc_elec = list(conc_data["elective"].keys())
    
    for sem in avail_sems:
        if credits_earned >= target_credits:
            break
            
        all_eligible = []
        all_eligible += get_eligible_courses(school_core, passed_courses, PREREQUISITES_BBA, credits_earned)
        all_eligible += get_eligible_courses(bba_core, passed_courses, PREREQUISITES_BBA, credits_earned)
        all_eligible += get_eligible_courses(ged_req, passed_courses, PREREQUISITES_BBA, credits_earned)
        
        # GED Choices
        for choice_pool in [BBA_GED_CHOICE_LANG, BBA_GED_CHOICE_POL, BBA_GED_CHOICE_SOC, BBA_GED_CHOICE_SCI]:
             if not any(c in passed_courses for c in choice_pool):
                 all_eligible += get_eligible_courses(list(choice_pool.keys()), passed_courses, PREREQUISITES_BBA, credits_earned)
        
        # History needs 2
        his_passed = [c for c in BBA_GED_CHOICE_HIS if c in passed_courses]
        if len(his_passed) < 2:
             all_eligible += get_eligible_courses(list(BBA_GED_CHOICE_HIS.keys()), passed_courses, PREREQUISITES_BBA, credits_earned)

        # Concentration
        if credits_earned >= 30: # Realistic threshold to start major
            all_eligible += get_eligible_courses(conc_req, passed_courses, PREREQUISITES_BBA, credits_earned)
            all_eligible += get_eligible_courses(conc_elec, passed_courses, PREREQUISITES_BBA, credits_earned)

        if not all_eligible:
            continue

        current_load = min(len(all_eligible), pref_load + random.randint(-1, 1))
        if current_load <= 0: continue
        
        # Prioritize foundational
        priority_map = {c: 0 for c in all_eligible}
        for target, reqs in PREREQUISITES_BBA.items():
            for r in reqs:
                if r in priority_map: priority_map[r] += 1
        
        all_eligible.sort(key=lambda c: priority_map.get(c, 0), reverse=True)
        taking = random.sample(all_eligible[:min(len(all_eligible), current_load+2)], current_load)

        sem_passed = []
        for code in taking:
            name, credits = ALL_COURSES[code]
            grade = grade_for_profile(profile)
            rows.append([code, name, str(credits), grade, sem])
            if grade not in ("F", "W", "I"):
                sem_passed.append(code)
                credits_earned += credits
                
                # Matching Lab
                if code in BBA_GED_CHOICE_SCI and code + "L" in ALL_COURSES:
                    if random.random() < 0.7:
                        l_code = code + "L"
                        l_name, l_credits = ALL_COURSES[l_code]
                        l_grade = grade_for_profile(profile)
                        rows.append([l_code, l_name, str(l_credits), l_grade, sem])
                        if l_grade not in ("F", "W", "I"):
                            sem_passed.append(l_code)
                            credits_earned += l_credits

        passed_courses.update(sem_passed)

    # Internship
    if credits_earned >= 100 and profile in ("top_student", "good_student", "nearly_done"):
        rows.append(["BUS498", "Internship", "4", grade_for_profile(profile), avail_sems[-1]])

    return sort_rows(rows), concentration


def generate_dept_change_student(student_id, current_program, previous_program):
    """Generate a student who switched from previous_program to current_program, following prerequisites."""
    rows = []
    passed_courses = set()
    credits_earned = 0
    concentration = None
    
    # Selection of semesters
    n_semesters = random.randint(8, 12)
    start_idx = random.randint(0, len(SEMESTERS) - n_semesters)
    avail_sems = SEMESTERS[start_idx : start_idx + n_semesters]
    
    # Split: first 3-4 semesters in old program, rest in new
    switch_sem_idx = random.randint(3, 4)
    
    # Pools
    if previous_program == "CSE":
        old_pool = list(CSE_SEPS_CORE.keys()) + list(CSE_MAJOR_CORE.keys()) + list(CSE_GED.keys())
        old_prereqs = PREREQUISITES_CSE
    else:
        old_pool = list(BBA_SCHOOL_CORE.keys()) + list(BBA_CORE.keys()) + list(BBA_GED.keys())
        old_prereqs = PREREQUISITES_BBA
        
    if current_program == "CSE":
        new_pool = list(CSE_SEPS_CORE.keys()) + list(CSE_MAJOR_CORE.keys()) + list(CSE_GED.keys()) + list(CSE_CAPSTONE.keys())
        new_prereqs = PREREQUISITES_CSE
    else:
        concentration = random.choice(BBA_CONC_NAMES)
        new_pool = list(BBA_SCHOOL_CORE.keys()) + list(BBA_CORE.keys()) + list(BBA_GED.keys())
        conc_data = BBA_CONC_COURSES[concentration]
        new_pool += list(conc_data["required"].keys()) + list(conc_data["elective"].keys())
        new_prereqs = PREREQUISITES_BBA

    # Loop through semesters
    for i, sem in enumerate(avail_sems):
        is_old = i < switch_sem_idx
        pool = old_pool if is_old else new_pool
        p_map = old_prereqs if is_old else new_prereqs
        
        # Determine eligible
        eligible = get_eligible_courses(pool, passed_courses, p_map, credits_earned)
        if not eligible: continue
        
        # Load
        load = random.randint(3, 5)
        taking = random.sample(eligible, min(len(eligible), load))
        
        sem_passed = []
        for code in taking:
            name, credits = ALL_COURSES[code]
            grade = grade_for_profile("good_student" if is_old else "mid_stage")
            rows.append([code, name, str(credits), grade, sem])
            if grade not in ("F", "W", "I"):
                sem_passed.append(code)
                credits_earned += credits
                
                # Lab logic
                if code + "L" in ALL_COURSES and code + "L" in eligible:
                    l_code = code + "L"
                    l_name, l_credits = ALL_COURSES[l_code]
                    rows.append([l_code, l_name, str(l_credits), grade_for_profile("good_student"), sem])
                    sem_passed.append(l_code)
                    credits_earned += l_credits

        passed_courses.update(sem_passed)
            
    return sort_rows(rows), concentration


def generate_all():
    random.seed(2024)
    output_dir = os.path.join(os.path.dirname(__file__) or ".", "transcripts")
    os.makedirs(output_dir, exist_ok=True)

    # Clean old transcripts
    import glob
    for old_file in glob.glob(os.path.join(output_dir, "*.csv")):
        try:
            os.remove(old_file)
        except PermissionError:
            pass # Skip locked files

    # Profile distribution across 2000 students
    profile_weights = {
        "top_student": 200,
        "good_student": 350,
        "struggling": 200,
        "early_stage": 150,
        "mid_stage": 200,
        "nearly_done": 250,
        "retake_heavy": 150,
        "transfer_student": 100,
        "withdrawn_heavy": 100,
        "probation": 200,
        "dept_change": 100,
    }

    students = []
    for profile, count in profile_weights.items():
        students.extend([profile] * count)
    random.shuffle(students)

    # Stats tracking
    stats = {
        "total": 0, "cse": 0, "bba": 0,
        "eligible_count": 0,
        "probation_count": 0,
        "profile_counts": {p: 0 for p in PROFILES + ["dept_change"]},
        "total_rows": 0,
        "retake_rows": 0,
        "w_rows": 0, "f_rows": 0, "t_rows": 0, "i_rows": 0,
    }

    for i, profile in enumerate(students):
        student_id = i + 1
        program = random.choices(["CSE", "BBA"], weights=[65, 35], k=1)[0]
        concentration = None
        ex_major = None

        if profile == "dept_change":
            ex_major = "BBA" if program == "CSE" else "CSE"
            rows, concentration = generate_dept_change_student(student_id, program, ex_major)
        elif program == "CSE":
            rows = generate_cse_student(profile, student_id)
            stats["cse"] += 1
        else:
            rows, concentration = generate_bba_student(profile, student_id)
            stats["bba"] += 1

        if profile == "dept_change":
            if program == "CSE": stats["cse"] += 1
            else: stats["bba"] += 1

        stats["profile_counts"][profile] += 1
        stats["total"] += 1

        # Count stats
        course_attempts = {}
        for row in rows:
            code, name, cr, grade, sem = row
            stats["total_rows"] += 1
            if grade == "W": stats["w_rows"] += 1
            if grade == "F": stats["f_rows"] += 1
            if grade == "T": stats["t_rows"] += 1
            if grade == "I": stats["i_rows"] += 1
            course_attempts.setdefault(code, []).append(grade)

        for code, attempts in course_attempts.items():
            if len(attempts) > 1:
                stats["retake_rows"] += len(attempts)

        # Write CSV — encode concentration and department change in filenames
        parts = [f"student_{student_id:04d}", program]
        if concentration:
            parts.append(concentration)
        if ex_major:
            parts.append(f"ex_{ex_major}")
        parts.append(profile)
        
        filename = "_".join(parts) + ".csv"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["course_code", "course_name", "credits", "grade", "semester"])
            for row in rows:
                writer.writerow(row)

    return stats, output_dir


def print_summary(stats, output_dir):
    print("=" * 60)
    print("  NSU 2000 UNIQUE TRANSCRIPT GENERATOR - SUMMARY")
    print("=" * 60)
    print(f"  Output directory     : {output_dir}")
    print(f"  Total transcripts    : {stats['total']}")
    print(f"  CSE students         : {stats['cse']}")
    print(f"  BBA students         : {stats['bba']}")
    print(f"  Total course rows    : {stats['total_rows']}")
    print(f"  Retake rows          : {stats['retake_rows']}")
    print(f"  W (Withdrawn) rows   : {stats['w_rows']}")
    print(f"  F (Failed) rows      : {stats['f_rows']}")
    print(f"  T (Transfer) rows    : {stats['t_rows']}")
    print(f"  I (Incomplete) rows  : {stats['i_rows']}")
    print()
    print("  Profile Distribution:")
    for profile, count in stats["profile_counts"].items():
        bar = "#" * (count // 10)
        print(f"    {profile:20s}: {count:4d}  {bar}")
    print("=" * 60)


if __name__ == "__main__":
    stats, output_dir = generate_all()
    print_summary(stats, output_dir)
