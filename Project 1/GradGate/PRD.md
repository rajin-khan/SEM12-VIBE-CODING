# GradGate — Product Requirements Document

## 1. Overview

GradGate is a CLI-based graduation audit engine for North South University (NSU). It reads a student's transcript CSV and a program knowledge markdown file, then computes credit tallies, CGPA, and graduation eligibility across three escalating levels of complexity.

**Course:** CSE226.1 — Vibe Coding, Spring 2026
**Target users:** Department administrators auditing student transcripts
**Interface:** Command-line (terminal)

---

## 2. Supported Programs

| Alias | Full Name | Degree | Credits |
|-------|-----------|--------|---------|
| CSE | Computer Science & Engineering | BS | 130–136* |
| EEE | Electrical & Electronic Engineering | BS | 130 |
| ETE | Electronic & Telecom Engineering | BS | 130 |
| CEE | Civil & Environmental Engineering | BS | 149 |
| ENV | Environmental Science & Management | BS | 130 |
| ENG | English | BA | 123 |
| BBA | Business Administration | BBA | 120 |
| ECO | Economics | BS | 120 |

\* CSE credits depend on waiver status of ENG102 and MAT112.

**Extensibility:** New programs are added by appending a `## [Program: ...]` section to `program_knowledge.md`. No code changes required.

---

## 3. Feature Specification

### 3.1 Level 1 — Credit Tally Engine (10 marks)

**Input:** `transcript.csv`, optional `program_name`, optional `program_knowledge.md`
**Output:** Formatted table of courses with status labels and total valid credits.

**Requirements:**
- Parse transcript CSV with columns: `Course_Code`, `Credits`, `Grade`, `Semester`
- Validate courses against master NSU course list (from program_knowledge.md)
- Detect non-NSU courses; prompt whether they are transfer credits
- Resolve retakes: keep best grade by grade points, then by semester recency; mark others `Retake (Ignored)`
- Assign status labels per course:
  - `Counted` — passing grade, best attempt
  - `Retake (Ignored)` — superseded by better attempt
  - `Failed` — F grade
  - `Withdrawn` — W grade
  - `Incomplete` — I grade
  - `Waived` — waiver granted
  - `Transfer` — transfer credit (T grade)
- Handle 0-credit labs: tracked in output but excluded from credit totals
- Handle special grades:
  - F: 0.0 grade points, counts in attempted credits, not earned
  - W: fully excluded from credits and GPA
  - I: excluded from GPA (treated as F if unresolved)
  - T: credit earned, excluded from CGPA
- Compute total valid earned credits
- Split credits by category when program is specified (program required / elective / excluded)

### 3.2 Level 2 — Logic Gate & Waiver Handler (10 marks)

**Input:** `transcript.csv`, `program_name`, `program_knowledge.md`, optional `--waivers`
**Output:** Semester-by-semester CGPA progression, waiver status, probation alerts.

**Requirements:**
- NSU grade scale:

  | Grade | Points | Grade | Points |
  |-------|--------|-------|--------|
  | A | 4.0 | C | 2.0 |
  | A- | 3.7 | C- | 1.7 |
  | B+ | 3.3 | D+ | 1.3 |
  | B | 3.0 | D | 1.0 |
  | B- | 2.7 | F | 0.0 |
  | C+ | 2.3 | | |

- Special grades: W (excluded), I (treated as F=0.0), T (credit earned, excluded from CGPA)
- Compute weighted CGPA using best attempt per course
- Semester-by-semester tracking: TGPA per semester + cumulative CGPA after each semester
- Waiver handling:
  - CSE: ENG102, MAT112 waivable
  - BBA: ENG102, BUS112 waivable
  - MIC: ENG102, MAT112 waivable
  - Other programs: as defined in program_knowledge.md
  - Support both `--waivers` CLI argument and interactive prompts
  - Waived courses: credit counts toward completion, excluded from CGPA
- Probation phases (consecutive semesters with cumulative CGPA < 2.0):
  - P1: first semester below 2.0
  - P2: second consecutive semester below 2.0
  - Dismissal: third consecutive semester below 2.0
  - Normal: CGPA >= 2.0 (resets counter)
- MAT116: 0 credits, prerequisite only, never counted in CGPA
- Grade distribution summary

### 3.3 Level 3 — Audit & Deficiency Reporter (10 marks)

**Input:** `transcript.csv`, `program_name`, `program_knowledge.md`, optional flags
**Output:** Graduation audit with eligibility verdict, deficiency report, graduation roadmap.

**Requirements:**
- Parse program_knowledge.md for per-program requirements
- Category-by-category missing course detection:
  - Mandatory GED
  - Core Math / Core Science / Core Business
  - Major Core
  - Capstone / Internship
  - Trail / Elective requirements
- Course equivalences: slash-pairs (e.g., MAT112/BUS112, BIO202/MIC101, POL101/POL104)
- Alternative course groups: "Choose one from [X, Y, Z]"
- Prerequisite violation detection:
  - Chronological check per semester
  - Verify all prerequisites passed in earlier semesters
- Graduation eligibility verdict with reasons:
  - Sufficient credits
  - CGPA >= 2.0
  - All required courses completed
  - No prerequisite violations (warning only)
- Graduation roadmap (priority-ordered steps):
  1. Credits still needed
  2. CGPA improvement needed
  3. Major CGPA (CSE) or Concentration CGPA (BBA >= 2.50)
  4. Missing required courses by category
  5. Retake suggestions for failed courses
- BBA concentration detection and concentration CGPA check
- CSE trail selection (interactive: primary + secondary trail)
- Minor detection for CSE (Math, Physics)
- Report modes: `--report normal` (default) and `--report full`

---

## 4. Data Format Specification

### 4.1 Transcript CSV

```csv
Course_Code,Credits,Grade,Semester
CSE115,3,A-,Summer 2023
MAT116,0,B,Spring 2023
HIS103,3,F,Summer 2023
HIS103,3,B+,Spring 2024
```

**Columns:**
- `Course_Code`: NSU course code (e.g., CSE115, CSE115L, MAT120)
- `Credits`: numeric credit value (0 for non-credit labs/courses)
- `Grade`: letter grade (A, A-, B+, B, B-, C+, C, C-, D+, D, F, W, I, T, P)
- `Semester`: format "Season Year" (e.g., "Spring 2023", "Summer 2024", "Fall 2025")

### 4.2 Program Knowledge Markdown

Extensible format with sections:
- `# NSU Grading Policy` — grade scale table, special grades
- `# NSU Course List` — master list of valid course codes
- `## [Program: Full Name]` — per-program section containing:
  - Degree, Total Credits Required, Minimum CGPA
  - Waivable Courses
  - Mandatory GED (with alternative groups)
  - Core Math / Core Science / Core Business
  - Major Core
  - Capstone / Internship
  - Trail / Concentration options
  - Prerequisite chains
  - Course equivalences
  - Credit adjustment rules (e.g., waiver-dependent credit totals)

---

## 5. CLI Interface

### 5.1 Unified CLI

```bash
python gradgate.py <transcript.csv> <PROGRAM> <program_knowledge.md> [OPTIONS]
```

Options:
- `--level 1|2|3|all` — which level(s) to run (default: all)
- `--waivers ENG102,MAT112` — courses to waive (comma-separated)
- `--report normal|full` — report verbosity (default: normal)
- `--concentration FIN` — BBA concentration (auto-detected if not given)
- `--output report.txt` — save output to file

### 5.2 Standalone Scripts

```bash
python level_1.py <transcript.csv> [PROGRAM] [program_knowledge.md]
python level_2.py <transcript.csv> <PROGRAM> <program_knowledge.md> [--waivers ...]
python level_3.py <transcript.csv> <PROGRAM> <program_knowledge.md> [--report full]
```

### 5.3 Program Aliases

Case-insensitive: CSE, EEE, ETE, CEE, ENV, ENG, BBA, ECO

---

## 6. Architecture

```
GradGate/
├── gradgate.py                   # Unified CLI
├── level_1.py                    # Standalone L1 CLI
├── level_2.py                    # Standalone L2 CLI
├── level_3.py                    # Standalone L3 CLI
├── engine/
│   ├── transcript.py             # CSV parsing, retake resolution, validation
│   ├── credits.py                # Credit tally logic
│   ├── cgpa.py                   # CGPA computation, probation phases
│   ├── audit.py                  # Deficiency check, graduation audit
│   ├── prerequisites.py          # Prerequisite violation detection
│   ├── waivers.py                # Waiver prompt + CLI handling
│   └── program_loader.py         # Parse program_knowledge.md
├── display/
│   └── formatter.py              # Rich-based output formatting
├── data/
│   ├── program_knowledge.md      # All programs + NSU data
│   └── transcript.csv            # Sample transcript
└── tests/
    ├── test_L1.csv ... test_retake.csv
    ├── tc01_*.csv ... tc38_*.csv
    └── generate_tests.py
```

---

## 7. Test Strategy

### 7.1 Manual Test Cases (30+ CSVs)

| Category | Test Cases |
|----------|-----------|
| Happy path | All-pass exact credits per program |
| Extra credits | Credits beyond requirement |
| F / I / W grades | Single and mixed grade types |
| Waivers | None, single, both waived |
| Retakes | Pass after fail, still failing, multiple retakes |
| Transfer | T grade, non-NSU courses |
| Invalid | Invalid grades, empty transcript |
| Probation | P1, P2, Dismissal phases |
| BBA-specific | Concentration, undeclared major |
| Prerequisites | Violation scenarios |
| Edge cases | 0-credit labs only, perfect 4.0, borderline 2.0 |

### 7.2 Generated Test Data

`generate_tests.py` produces 2000 transcripts across 14 scenarios for all 8 programs:
- eligible_top, eligible_good, eligible_borderline
- missing_ged, missing_core
- retake_pass, retake_fail
- withdrawal_heavy
- probation, probation_recovery
- partial, near_grad
- incomplete, mixed_complex

### 7.3 Required Deliverables

- `test_L1.csv` — validates credit tally logic
- `test_L2.csv` — validates CGPA computation
- `test_L3.csv` — validates deficiency detection
- `test_retake.csv` — validates retake handling

---

## 8. Edge Case Handling

| Case | Behavior |
|------|----------|
| Retakes | Best grade by grade points wins; ties broken by later semester |
| 0-credit labs | Tracked with status, excluded from credit totals |
| F grade | 0.0 points, counts in attempted credits, not in earned |
| W grade | Fully excluded from credits and GPA |
| I grade | Treated as F (0.0) until resolved; excluded from earned |
| T grade | Credit earned, excluded from CGPA calculation |
| P grade | Pass for 0-credit courses; no GPA impact |
| Non-NSU courses | Flagged; user prompted for transfer status |
| Invalid grades | Error with message; abort processing |
| Empty transcript | Graceful error message |
| MAT116 | 0 credits, prerequisite only, never in CGPA |
| Waived ENG102/MAT112 | +3 credits toward completion, excluded from CGPA |
