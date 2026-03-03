# GradGate — NSU Graduation Audit Engine

A CLI-based graduation audit engine for North South University that reads student transcripts and program knowledge to compute credit tallies, CGPA, and graduation eligibility across three levels of analysis.

**Course:** CSE226.1 — Vibe Coding, Spring 2026

## Quick Start

```bash
pip install rich

# Interactive mode (recommended for first-time use)
python3 gradgate.py

# Direct CLI mode
python3 gradgate.py data/transcript.csv CSE --waivers ENG102,MAT112
```

---

## Running Book — Demo Cheatsheet

> Copy-paste these commands in order to showcase every feature. Run from the `GradGate/` directory.

### 0. Setup

```bash
pip install rich
cd GradGate
```

### 1. Interactive Mode

Run with no arguments to launch the interactive menu with transcript browser, program selector, and step-by-step prompts:

```bash
python3 gradgate.py
```

The menu offers:
1. Run Level 1 — Credit Tally Engine
2. Run Level 2 — Logic Gate & Waiver Handler
3. Run Level 3 — Audit & Deficiency Reporter
4. Run Full Audit (all levels)
5. View Grade Distribution
6. Browse test cases (paginated, 61 files)

### 2. Level 1 — Credit Tally (basic)

```bash
python3 level_1.py data/transcript.csv CSE
```

Shows: course table with pass/fail/retake status, credit summary (valid, attempted, program, elective).

### 3. Level 1 — Different programs

```bash
python3 level_1.py tests/tc01_cse_all_pass.csv CSE
python3 level_1.py tests/tc02_bba_all_pass.csv BBA
python3 level_1.py tests/tc05_cee_all_pass.csv CEE
```

### 4. Level 1 — Edge cases

```bash
# Retakes (best grade kept, old attempt marked "Retake Ignored")
python3 level_1.py tests/tc23_retake_pass.csv CSE

# Multiple retakes of same course
python3 level_1.py tests/tc25_multiple_retakes.csv CSE

# Retake with worse grade (best grade still wins)
python3 level_1.py tests/tc52_retake_worse_grade.csv CSE

# Retake of B+ or above (ineligible per NSU policy, flagged as "Retake Ineligible")
python3 level_1.py tests/tc53_retake_ineligible.csv CSE

# F, I, and W grades mixed
python3 level_1.py tests/tc17_cse_mixed_FIW.csv CSE

# Transfer credits (T grade)
python3 level_1.py tests/tc26_transfer_T_grade.csv CSE

# Zero-credit labs only
python3 level_1.py tests/tc36_zero_credit_labs_only.csv CSE

# Empty transcript
python3 level_1.py tests/tc29_empty_transcript.csv CSE
```

### 5. Level 2 — CGPA & Probation

```bash
# Semester-by-semester CGPA progression + grade distribution
python3 level_2.py data/transcript.csv CSE

# With waivers applied
python3 level_2.py tests/test_L2.csv CSE --waivers ENG102,MAT112

# Probation P1 (1st semester below 2.0)
python3 level_2.py tests/tc30_probation_P1.csv CSE --waivers ""

# Probation escalation P1 → P2
python3 level_2.py tests/tc31_probation_P2.csv CSE --waivers ""

# Full dismissal (3+ consecutive semesters below 2.0)
python3 level_2.py tests/tc32_dismissal.csv CSE --waivers ""

# Perfect 4.0 CGPA
python3 level_2.py tests/tc37_high_cgpa_4.0.csv CSE --waivers ""

# Borderline 2.0 CGPA
python3 level_2.py tests/tc38_borderline_2.0.csv CSE --waivers ""
```

### 6. Level 3 — Graduation Audit

```bash
# Full audit on a passing student
python3 level_3.py tests/tc01_cse_all_pass.csv CSE --report full --waivers ""

# Student far from graduating (shows roadmap)
python3 level_3.py data/transcript.csv CSE --report full --waivers ""

# Prerequisite violations
python3 level_3.py tests/tc35_prereq_violation.csv CSE --report full --waivers ""

# BBA with Finance concentration (auto-detected)
python3 level_3.py tests/tc33_bba_concentration_FIN.csv BBA --report full --waivers ""

# BBA undeclared concentration
python3 level_3.py tests/tc34_bba_undeclared.csv BBA --report full --waivers ""
```

### 7. Minor Programs

```bash
# CSE student with complete Math Minor
python3 level_3.py tests/tc54_cse_math_minor_complete.csv CSE --minor MATH --waivers ""

# CSE student with complete Physics Minor
python3 level_3.py tests/tc55_cse_physics_minor_complete.csv CSE --minor PHYSICS --waivers ""

# Partial Math Minor (1 of 3 electives taken)
python3 level_3.py tests/tc56_cse_math_minor_partial.csv CSE --minor MATH --waivers ""

# Minor courses present but missing prerequisites
python3 level_3.py tests/tc57_cse_minor_missing_prereqs.csv CSE --minor MATH --waivers ""

# Auto-detect minor from transcript (no --minor flag needed)
python3 level_3.py tests/tc54_cse_math_minor_complete.csv CSE --waivers ""
```

### 8. Grade Distribution

```bash
# Via interactive menu (option 5)
python3 gradgate.py

# Via Level 2 (shown automatically at the end)
python3 level_2.py tests/tc01_cse_all_pass.csv CSE --waivers ""
```

Shows visual bar chart, percentages, tier summaries (A-range, B-range, etc.), and pass rate.

### 9. Unified CLI — All levels at once

```bash
# Full report, all levels, with waivers
python3 gradgate.py data/transcript.csv CSE --level all --report full --waivers ENG102,MAT112

# Just Level 2
python3 gradgate.py data/transcript.csv CSE --level 2 --waivers ENG102

# With minor declaration
python3 gradgate.py tests/tc54_cse_math_minor_complete.csv CSE --level 3 --minor MATH --waivers ""

# Save to file
python3 gradgate.py tests/tc01_cse_all_pass.csv CSE --level all --report full --waivers "" -o audit_report.txt
```

### 10. All 8 programs — quick pass/fail check

```bash
python3 level_3.py tests/tc01_cse_all_pass.csv CSE --waivers ""
python3 level_3.py tests/tc02_bba_all_pass.csv BBA --waivers ""
python3 level_3.py tests/tc03_eee_all_pass.csv EEE --waivers ""
python3 level_3.py tests/tc04_ete_all_pass.csv ETE --waivers ""
python3 level_3.py tests/tc05_cee_all_pass.csv CEE --waivers ""
python3 level_3.py tests/tc06_env_all_pass.csv ENV --waivers ""
python3 level_3.py tests/tc07_eng_all_pass.csv ENG --waivers ""
python3 level_3.py tests/tc08_eco_all_pass.csv ECO --waivers ""
```

### 11. Test data generation

```bash
# Build the 61 manual test CSVs
python3 tests/_build_manual_tests.py

# Generate 2000 synthetic transcripts (16 scenarios × 8 programs)
python3 tests/generate_tests.py

# Quick run (fewer transcripts)
python3 tests/generate_tests.py --count 100
```

### 12. Batch validation (run all test cases through Level 1)

```bash
for f in tests/tc*.csv; do
  echo "--- $(basename $f) ---"
  python3 level_1.py "$f" CSE 2>&1 | grep "Total Valid"
done
```

---

## Complete Test Case Reference

Every `tc*.csv` file with its purpose and the command to run it.

### Happy Path (tc01–tc08)

| File | Description | Command |
|------|-------------|---------|
| `tc01_cse_all_pass.csv` | CSE student, all courses passed, meets credit requirement | `python3 level_3.py tests/tc01_cse_all_pass.csv CSE --waivers ""` |
| `tc02_bba_all_pass.csv` | BBA student, all courses passed | `python3 level_3.py tests/tc02_bba_all_pass.csv BBA --waivers ""` |
| `tc03_eee_all_pass.csv` | EEE student, all courses passed | `python3 level_3.py tests/tc03_eee_all_pass.csv EEE --waivers ""` |
| `tc04_ete_all_pass.csv` | ETE student, all courses passed | `python3 level_3.py tests/tc04_ete_all_pass.csv ETE --waivers ""` |
| `tc05_cee_all_pass.csv` | CEE student, all courses passed | `python3 level_3.py tests/tc05_cee_all_pass.csv CEE --waivers ""` |
| `tc06_env_all_pass.csv` | ENV student, all courses passed | `python3 level_3.py tests/tc06_env_all_pass.csv ENV --waivers ""` |
| `tc07_eng_all_pass.csv` | ENG student, all courses passed | `python3 level_3.py tests/tc07_eng_all_pass.csv ENG --waivers ""` |
| `tc08_eco_all_pass.csv` | ECO student, all courses passed | `python3 level_3.py tests/tc08_eco_all_pass.csv ECO --waivers ""` |

### Extra Credits (tc09–tc10)

| File | Description | Command |
|------|-------------|---------|
| `tc09_cse_extra_credits.csv` | CSE student with credits beyond requirement | `python3 level_1.py tests/tc09_cse_extra_credits.csv CSE` |
| `tc10_bba_extra_credits.csv` | BBA student with extra credits | `python3 level_1.py tests/tc10_bba_extra_credits.csv BBA` |

### F / I / W Grades (tc11–tc18)

| File | Description | Command |
|------|-------------|---------|
| `tc11_cse_with_F.csv` | CSE with F grades (0.0 points, in attempted not earned) | `python3 level_1.py tests/tc11_cse_with_F.csv CSE` |
| `tc12_bba_with_F.csv` | BBA with F grades | `python3 level_1.py tests/tc12_bba_with_F.csv BBA` |
| `tc13_cse_with_I.csv` | CSE with I grades (treated as F until resolved) | `python3 level_1.py tests/tc13_cse_with_I.csv CSE` |
| `tc14_bba_with_I.csv` | BBA with I grades | `python3 level_1.py tests/tc14_bba_with_I.csv BBA` |
| `tc15_cse_with_W.csv` | CSE with W grades (fully excluded from GPA) | `python3 level_1.py tests/tc15_cse_with_W.csv CSE` |
| `tc16_bba_with_W.csv` | BBA with W grades | `python3 level_1.py tests/tc16_bba_with_W.csv BBA` |
| `tc17_cse_mixed_FIW.csv` | CSE with mix of F, I, and W grades | `python3 level_1.py tests/tc17_cse_mixed_FIW.csv CSE` |
| `tc18_bba_mixed_FIW.csv` | BBA with mix of F, I, and W grades | `python3 level_1.py tests/tc18_bba_mixed_FIW.csv BBA` |

### Waivers (tc19–tc22)

| File | Description | Command |
|------|-------------|---------|
| `tc19_no_waivers.csv` | CSE student, no waivers applied | `python3 level_2.py tests/tc19_no_waivers.csv CSE --waivers ""` |
| `tc20_eng102_waived.csv` | ENG102 waived only | `python3 level_2.py tests/tc20_eng102_waived.csv CSE --waivers ENG102` |
| `tc21_mat112_waived.csv` | MAT112 waived only | `python3 level_2.py tests/tc21_mat112_waived.csv CSE --waivers MAT112` |
| `tc22_both_waived.csv` | Both ENG102 and MAT112 waived | `python3 level_2.py tests/tc22_both_waived.csv CSE --waivers ENG102,MAT112` |

### Retakes (tc23–tc25, tc52–tc53)

| File | Description | Command |
|------|-------------|---------|
| `tc23_retake_pass.csv` | Failed then passed on retake (best grade wins) | `python3 level_1.py tests/tc23_retake_pass.csv CSE` |
| `tc24_retake_still_fail.csv` | Retook but still failed | `python3 level_1.py tests/tc24_retake_still_fail.csv CSE` |
| `tc25_multiple_retakes.csv` | Same course retaken 3+ times | `python3 level_1.py tests/tc25_multiple_retakes.csv CSE` |
| `tc52_retake_worse_grade.csv` | Retake got a worse grade — best grade still counted | `python3 level_1.py tests/tc52_retake_worse_grade.csv CSE` |
| `tc53_retake_ineligible.csv` | Retake of B+ or above — flagged as "Retake (Ineligible)" per NSU policy | `python3 level_1.py tests/tc53_retake_ineligible.csv CSE` |

### Transfer / Invalid (tc26–tc29)

| File | Description | Command |
|------|-------------|---------|
| `tc26_transfer_T_grade.csv` | T grade (transfer credit) — credit earned, excluded from CGPA | `python3 level_1.py tests/tc26_transfer_T_grade.csv CSE` |
| `tc27_non_nsu_courses.csv` | Non-NSU course codes — triggers transfer prompt | `python3 level_1.py tests/tc27_non_nsu_courses.csv CSE` |
| `tc28_invalid_grades.csv` | Invalid grade values — should error and abort | `python3 level_1.py tests/tc28_invalid_grades.csv CSE` |
| `tc29_empty_transcript.csv` | Completely empty transcript | `python3 level_1.py tests/tc29_empty_transcript.csv CSE` |

### Probation (tc30–tc32)

| File | Description | Command |
|------|-------------|---------|
| `tc30_probation_P1.csv` | 1st semester below 2.0 — triggers P1 | `python3 level_2.py tests/tc30_probation_P1.csv CSE --waivers ""` |
| `tc31_probation_P2.csv` | 2nd consecutive semester below 2.0 — P1 → P2 | `python3 level_2.py tests/tc31_probation_P2.csv CSE --waivers ""` |
| `tc32_dismissal.csv` | 3+ consecutive semesters below 2.0 — academic dismissal | `python3 level_2.py tests/tc32_dismissal.csv CSE --waivers ""` |

### BBA-Specific (tc33–tc34)

| File | Description | Command |
|------|-------------|---------|
| `tc33_bba_concentration_FIN.csv` | BBA with FIN concentration courses — auto-detected | `python3 level_3.py tests/tc33_bba_concentration_FIN.csv BBA --report full --waivers ""` |
| `tc34_bba_undeclared.csv` | BBA student without clear concentration | `python3 level_3.py tests/tc34_bba_undeclared.csv BBA --report full --waivers ""` |

### Prerequisites (tc35)

| File | Description | Command |
|------|-------------|---------|
| `tc35_prereq_violation.csv` | CSE prerequisite chain violated | `python3 level_3.py tests/tc35_prereq_violation.csv CSE --report full --waivers ""` |

### Edge Cases (tc36–tc38)

| File | Description | Command |
|------|-------------|---------|
| `tc36_zero_credit_labs_only.csv` | Only 0-credit labs in transcript | `python3 level_1.py tests/tc36_zero_credit_labs_only.csv CSE` |
| `tc37_high_cgpa_4.0.csv` | Perfect 4.0 CGPA student | `python3 level_2.py tests/tc37_high_cgpa_4.0.csv CSE --waivers ""` |
| `tc38_borderline_2.0.csv` | Borderline 2.0 CGPA (just at graduation minimum) | `python3 level_2.py tests/tc38_borderline_2.0.csv CSE --waivers ""` |

### Error / Robustness (tc39–tc44)

| File | Description | Command |
|------|-------------|---------|
| `tc39_malformed_columns.csv` | Wrong column names (e.g., `Course Code` instead of `Course_Code`) | `python3 level_1.py tests/tc39_malformed_columns.csv CSE` |
| `tc40_empty_fields.csv` | Rows with empty Course_Code, Grade, or Credits | `python3 level_1.py tests/tc40_empty_fields.csv CSE` |
| `tc41_negative_credits.csv` | Negative credit values — clamped to 0 | `python3 level_1.py tests/tc41_negative_credits.csv CSE` |
| `tc42_whitespace_grades.csv` | Grades with leading/trailing whitespace | `python3 level_1.py tests/tc42_whitespace_grades.csv CSE` |
| `tc43_duplicate_same_semester.csv` | Same course twice in the same semester | `python3 level_1.py tests/tc43_duplicate_same_semester.csv CSE` |
| `tc44_p_grade.csv` | P (Pass) grade — credit earned, excluded from CGPA | `python3 level_1.py tests/tc44_p_grade.csv CSE` |

### Prerequisite Tests (tc45–tc48)

| File | Description | Command |
|------|-------------|---------|
| `tc45_credit_prereq_violation.csv` | CSE299 taken with < 60 earned credits | `python3 level_3.py tests/tc45_credit_prereq_violation.csv CSE --report full --waivers ""` |
| `tc46_corequisite_same_semester.csv` | CSE115 + CSE115L in same semester — not flagged | `python3 level_3.py tests/tc46_corequisite_same_semester.csv CSE --report full --waivers ""` |
| `tc47_eee_prereq_violation.csv` | EEE prerequisite chain violated | `python3 level_3.py tests/tc47_eee_prereq_violation.csv EEE --report full --waivers ""` |
| `tc48_bba_prereq_violation.csv` | BBA prerequisite chain violated | `python3 level_3.py tests/tc48_bba_prereq_violation.csv BBA --report full --waivers ""` |

### Advanced (tc49–tc51)

| File | Description | Command |
|------|-------------|---------|
| `tc49_cross_program_courses.csv` | CSE student with BBA courses (classified as electives) | `python3 level_1.py tests/tc49_cross_program_courses.csv CSE` |
| `tc50_bba_wrong_concentration.csv` | BBA with FIN courses but `--concentration MKT` forced | `python3 level_3.py tests/tc50_bba_wrong_concentration.csv BBA --concentration MKT --report full --waivers ""` |
| `tc51_i_grade_resolved.csv` | I grade in one semester, real grade in the next (retake) | `python3 level_1.py tests/tc51_i_grade_resolved.csv CSE` |

### Retake Policy (tc52–tc53)

| File | Description | Command |
|------|-------------|---------|
| `tc52_retake_worse_grade.csv` | Retake with worse grade — best grade always counted | `python3 level_1.py tests/tc52_retake_worse_grade.csv CSE` |
| `tc53_retake_ineligible.csv` | Retake of course originally graded B+ or above — marked ineligible | `python3 level_1.py tests/tc53_retake_ineligible.csv CSE` |

### Minor Programs (tc54–tc57)

| File | Description | Command |
|------|-------------|---------|
| `tc54_cse_math_minor_complete.csv` | CSE + complete Math Minor (3/3 electives, all prereqs met) | `python3 level_3.py tests/tc54_cse_math_minor_complete.csv CSE --minor MATH --waivers ""` |
| `tc55_cse_physics_minor_complete.csv` | CSE + complete Physics Minor (4 required + prereqs met) | `python3 level_3.py tests/tc55_cse_physics_minor_complete.csv CSE --minor PHYSICS --waivers ""` |
| `tc56_cse_math_minor_partial.csv` | CSE + partial Math Minor (1 of 3 needed electives) | `python3 level_3.py tests/tc56_cse_math_minor_partial.csv CSE --minor MATH --waivers ""` |
| `tc57_cse_minor_missing_prereqs.csv` | CSE + minor electives but missing MAT125/MAT130/MAT250 prereqs | `python3 level_3.py tests/tc57_cse_minor_missing_prereqs.csv CSE --minor MATH --waivers ""` |

---

## Supported Programs

| Alias | Program | Credits |
|-------|---------|---------|
| CSE | Computer Science & Engineering | 130–136 |
| EEE | Electrical & Electronic Engineering | 130 |
| ETE | Electronic & Telecom Engineering | 130 |
| CEE | Civil & Environmental Engineering | 149 |
| ENV | Environmental Science & Management | 130 |
| ENG | English | 123 |
| BBA | Business Administration | 120–126 |
| ECO | Economics | 120 |

New programs can be added by appending a section to `data/program_knowledge.md` — no code changes needed.

## Architecture

```
GradGate/
├── gradgate.py              # Unified CLI + interactive menu
├── level_1.py               # Level 1: Credit Tally Engine
├── level_2.py               # Level 2: Logic Gate & Waiver Handler
├── level_3.py               # Level 3: Audit & Deficiency Reporter
├── engine/
│   ├── transcript.py        # CSV parsing, retake resolution, validation
│   ├── credits.py           # Credit tally logic
│   ├── cgpa.py              # CGPA computation, probation, grade distribution
│   ├── audit.py             # Deficiency check, graduation audit, minor tracking
│   ├── prerequisites.py     # Prerequisite & co-requisite validation
│   ├── waivers.py           # Waiver handling (CLI + interactive)
│   └── program_loader.py    # Parse program_knowledge.md (programs + minors)
├── display/
│   └── formatter.py         # Rich-based terminal output + grade distribution
├── data/
│   ├── program_knowledge.md # All 8 programs + minors + NSU data
│   └── transcript.csv       # Sample transcript
└── tests/
    ├── test_L1.csv          # Level 1 deliverable test
    ├── test_L2.csv          # Level 2 deliverable test
    ├── test_L3.csv          # Level 3 deliverable test
    ├── test_retake.csv      # Retake scenario deliverable
    ├── tc01–tc57_*.csv      # 57 named edge-case tests
    ├── _build_manual_tests.py  # Generates the tc* files
    └── generate_tests.py    # Generates 2000 synthetic transcripts
```

## Three Levels

### Level 1 — Credit Tally Engine

Reads a transcript CSV and computes total valid earned credits.

- Resolves retakes (best grade wins; B+ or above not eligible for retake per NSU policy)
- Handles F, W, I, T, P, and 0-credit labs
- Validates courses against NSU course list
- Categorizes credits: program required vs. elective

```bash
python3 level_1.py tests/test_L1.csv CSE
```

### Level 2 — Logic Gate & Waiver Handler

Computes semester-by-semester TGPA and cumulative CGPA with waiver support.

- NSU grade scale (A=4.0 through D=1.0, F=0.0)
- Waiver handling: ENG102/MAT112 (CSE), ENG102/BUS112 (BBA)
- Probation detection: P1 → P2 → Dismissal
- Enhanced grade distribution with visual bars, percentages, tier summaries, and pass rate

```bash
python3 level_2.py tests/test_L2.csv CSE --waivers ENG102,MAT112
```

### Level 3 — Audit & Deficiency Reporter

Full graduation audit with deficiency detection and roadmap.

- Missing course detection by category (GED, Math, Science, Major, Capstone)
- Course equivalences and alternative groups
- Prerequisite and co-requisite validation
- BBA concentration CGPA check (>= 2.50)
- Minor program tracking (Math and Physics minors for engineering programs)
- Graduation roadmap with prioritized steps

```bash
python3 level_3.py tests/test_L3.csv CSE --report full --waivers ""
```

## Unified CLI

```bash
python3 gradgate.py <transcript.csv> <PROGRAM> [program_knowledge.md] [OPTIONS]

Options:
  --level 1|2|3|all        Which level(s) to run (default: all)
  --waivers ENG102,MAT112  Courses to waive (comma-separated)
  --report normal|full     Report verbosity (default: normal)
  --concentration FIN      BBA concentration (auto-detected if omitted)
  --minor MATH|PHYSICS     Declare a minor (auto-detected if omitted)
  -o report.txt            Save output to file
```

Run with no arguments for the interactive menu:

```bash
python3 gradgate.py
```

## Transcript CSV Format

```csv
Course_Code,Credits,Grade,Semester
CSE115,3,A-,Summer 2023
MAT116,0,B,Spring 2023
HIS103,3,F,Summer 2023
HIS103,3,B+,Spring 2024
```

Valid grades: A, A-, B+, B, B-, C+, C, C-, D+, D, F, W, I, T, P

## Test Data

### Manual Test Cases (61 files)

| Category | Files |
|----------|-------|
| Deliverables | `test_L1.csv`, `test_L2.csv`, `test_L3.csv`, `test_retake.csv` |
| All-pass (8 programs) | `tc01`–`tc08` |
| Extra credits | `tc09`, `tc10` |
| F / I / W grades | `tc11`–`tc18` |
| Waivers | `tc19`–`tc22` |
| Retakes | `tc23`–`tc25` |
| Transfer / Invalid | `tc26`–`tc29` |
| Probation | `tc30`–`tc32` |
| BBA-specific | `tc33`, `tc34` |
| Prerequisites (CSE) | `tc35` |
| Edge cases | `tc36`–`tc38` |
| Error handling | `tc39`–`tc44` (malformed CSV, empty fields, negative credits, whitespace, duplicates, P grade) |
| Prerequisites (multi-program) | `tc45`–`tc48` (credit-based, co-requisite, EEE, BBA) |
| Advanced | `tc49`–`tc51` (cross-program, BBA concentration mismatch, I-grade resolution) |
| Retake policy | `tc52`–`tc53` (worse grade retake, ineligible retake of B+ or above) |
| Minor programs | `tc54`–`tc57` (complete Math/Physics minor, partial minor, missing prereqs) |

### Generated Test Data (2000 transcripts)

```bash
python3 tests/generate_tests.py              # default 2000
python3 tests/generate_tests.py --count 500  # quick run
```

16 scenarios: eligible_top, eligible_good, eligible_borderline, missing_ged, missing_core, retake_pass, retake_fail, withdrawal_heavy, probation, probation_recovery, partial, near_grad, incomplete, mixed_complex, cross_program, transfer_heavy

## Edge Case Handling

| Case | Behavior |
|------|----------|
| Retakes | Best grade wins; ties broken by later semester |
| Retake of B+ or above | Flagged as "Retake (Ineligible)" per NSU policy; original grade kept |
| 0-credit labs | Tracked, excluded from credit totals |
| F grade | 0.0 points, in attempted but not earned |
| W grade | Fully excluded from credits and GPA |
| I grade | Treated as F (0.0) until resolved; retake with real grade wins |
| T grade | Credit earned, excluded from CGPA |
| P grade | Credit earned, excluded from CGPA |
| Non-NSU courses | Flagged with transfer prompt |
| Invalid grades | Error and abort |
| Malformed CSV | Missing columns detected and reported |
| Negative credits | Clamped to 0 |
| Empty course codes | Silently skipped |
| Co-requisites | Lab+lecture in same semester not flagged as prereq violation |
| Probation | P1 → P2 → Dismissal (consecutive semesters < 2.0) |
| Minor programs | Auto-detected or declared via `--minor`; shows completion status and missing courses |

## Minor Programs

Engineering students (CSE, EEE, ETE, CEE) can pursue optional minors:

**Math Minor (21 credits):** 3 additional courses from MAT370, MAT480, MAT481, MAT482, MAT483, MAT485. Prerequisites: MAT116, MAT120, MAT125, MAT130, MAT250.

**Physics Minor (20 credits):** PHY230, PHY240, PHY250, PHY260 + 1 additional physics course. Prerequisites: PHY107, PHY107L, PHY108, PHY108L.

The audit engine auto-detects minors from the transcript or accepts `--minor MATH` / `--minor PHYSICS` explicitly. The report shows a dedicated minor panel with courses completed, courses remaining, and prerequisite status.
