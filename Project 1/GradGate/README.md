# GradGate — NSU Graduation Audit Engine

A CLI-based graduation audit engine for North South University that reads student transcripts and program knowledge to compute credit tallies, CGPA, and graduation eligibility across three levels of analysis.

**Course:** CSE226.1 — Vibe Coding, Spring 2026

## Quick Start

```bash
pip install rich
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

### 1. Level 1 — Credit Tally (basic)

```bash
python3 level_1.py data/transcript.csv CSE
```

Shows: course table with pass/fail/retake status, credit summary (valid, attempted, program, elective).

### 2. Level 1 — Different programs

```bash
python3 level_1.py tests/tc01_cse_all_pass.csv CSE
python3 level_1.py tests/tc02_bba_all_pass.csv BBA
python3 level_1.py tests/tc05_cee_all_pass.csv CEE
```

### 3. Level 1 — Edge cases

```bash
# Retakes (best grade kept, old attempt marked "Retake Ignored")
python3 level_1.py tests/tc23_retake_pass.csv CSE

# Multiple retakes of same course
python3 level_1.py tests/tc25_multiple_retakes.csv CSE

# F, I, and W grades mixed
python3 level_1.py tests/tc17_cse_mixed_FIW.csv CSE

# Transfer credits (T grade)
python3 level_1.py tests/tc26_transfer_T_grade.csv CSE

# Zero-credit labs only
python3 level_1.py tests/tc36_zero_credit_labs_only.csv CSE

# Empty transcript
python3 level_1.py tests/tc29_empty_transcript.csv CSE
```

### 4. Level 2 — CGPA & Probation

```bash
# Semester-by-semester CGPA progression
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

### 5. Level 3 — Graduation Audit

```bash
# Full audit on a passing student
python3 level_3.py tests/tc01_cse_all_pass.csv CSE --report full

# Student far from graduating (shows roadmap)
python3 level_3.py data/transcript.csv CSE --report full

# Prerequisite violations
python3 level_3.py tests/tc35_prereq_violation.csv CSE --report full

# BBA with Finance concentration (auto-detected)
python3 level_3.py tests/tc33_bba_concentration_FIN.csv BBA --report full

# BBA undeclared concentration
python3 level_3.py tests/tc34_bba_undeclared.csv BBA --report full
```

### 6. Unified CLI — All levels at once

```bash
# Full report, all levels, with waivers
python3 gradgate.py data/transcript.csv CSE --level all --report full --waivers ENG102,MAT112

# Just Level 2
python3 gradgate.py data/transcript.csv CSE --level 2 --waivers ENG102

# Save to file
python3 gradgate.py tests/tc01_cse_all_pass.csv CSE --level all --report full -o audit_report.txt
```

### 7. All 8 programs — quick pass/fail check

```bash
python3 level_3.py tests/tc01_cse_all_pass.csv CSE --report normal
python3 level_3.py tests/tc02_bba_all_pass.csv BBA --report normal
python3 level_3.py tests/tc03_eee_all_pass.csv EEE --report normal
python3 level_3.py tests/tc04_ete_all_pass.csv ETE --report normal
python3 level_3.py tests/tc05_cee_all_pass.csv CEE --report normal
python3 level_3.py tests/tc06_env_all_pass.csv ENV --report normal
python3 level_3.py tests/tc07_eng_all_pass.csv ENG --report normal
python3 level_3.py tests/tc08_eco_all_pass.csv ECO --report normal
```

### 8. Test data generation

```bash
# Build the 42 manual test CSVs
python3 tests/_build_manual_tests.py

# Generate 2000 synthetic transcripts (14 scenarios × 8 programs)
python3 tests/generate_tests.py

# Quick run (fewer transcripts)
python3 tests/generate_tests.py --count 100
```

### 9. Batch validation (run all test cases through Level 1)

```bash
for f in tests/tc*.csv; do
  echo "--- $(basename $f) ---"
  python3 level_1.py "$f" CSE 2>&1 | grep "Total Valid"
done
```

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
├── gradgate.py              # Unified CLI (all levels)
├── level_1.py               # Level 1: Credit Tally Engine
├── level_2.py               # Level 2: Logic Gate & Waiver Handler
├── level_3.py               # Level 3: Audit & Deficiency Reporter
├── engine/
│   ├── transcript.py        # CSV parsing, retake resolution, validation
│   ├── credits.py           # Credit tally logic
│   ├── cgpa.py              # CGPA computation, probation phases
│   ├── audit.py             # Deficiency check, graduation audit
│   ├── prerequisites.py     # Prerequisite violation detection
│   ├── waivers.py           # Waiver handling (CLI + interactive)
│   └── program_loader.py    # Parse program_knowledge.md
├── display/
│   └── formatter.py         # Rich-based terminal output
├── data/
│   ├── program_knowledge.md # All 8 programs + NSU data
│   └── transcript.csv       # Sample transcript
└── tests/
    ├── test_L1.csv          # Level 1 deliverable test
    ├── test_L2.csv          # Level 2 deliverable test
    ├── test_L3.csv          # Level 3 deliverable test
    ├── test_retake.csv      # Retake scenario deliverable
    ├── tc01–tc38_*.csv      # 38 named edge-case tests
    └── generate_tests.py    # Generates 2000 transcripts
```

## Three Levels

### Level 1 — Credit Tally Engine

Reads a transcript CSV and computes total valid earned credits.

- Resolves retakes (best grade wins)
- Handles F, W, I, T, and 0-credit labs
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
- Grade distribution summary

```bash
python3 level_2.py tests/test_L2.csv CSE --waivers ENG102,MAT112
```

### Level 3 — Audit & Deficiency Reporter

Full graduation audit with deficiency detection and roadmap.

- Missing course detection by category (GED, Math, Science, Major, Capstone)
- Course equivalences and alternative groups
- Prerequisite violation detection
- BBA concentration CGPA check (≥ 2.50)
- Graduation roadmap with prioritized steps

```bash
python3 level_3.py tests/test_L3.csv CSE --report full
```

## Unified CLI

```bash
python3 gradgate.py <transcript.csv> <PROGRAM> [program_knowledge.md] [OPTIONS]

Options:
  --level 1|2|3|all        Which level(s) to run (default: all)
  --waivers ENG102,MAT112  Courses to waive (comma-separated)
  --report normal|full     Report verbosity (default: normal)
  --concentration FIN      BBA concentration (auto-detected if omitted)
  -o report.txt            Save output to file
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

### Manual Test Cases (55 files)

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
