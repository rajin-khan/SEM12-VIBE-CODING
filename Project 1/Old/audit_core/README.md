# 🎓 NSU Graduation Auditor

A Claude Code-inspired CLI tool for auditing student transcripts and checking graduation eligibility. Features an adorable 8-bit style mascot!

## 🦀 The Mascot

Inspired by Claude Code's **Clawd**, the NSU Graduation Auditor features its own 8-bit mascot:

```
      ██████████      
    ██░░████░░██    
  ██░░██████░░██  
  ██░░██████░░██  
██████████████████████
██░░██            ██░░██
██░░██   AUDIT    ██░░██
██░░██            ██░░██
  ░░██            ██░░  
  ░░██            ██░░  

╭──────────────────────────────────────────╮
│     NSU GRADUATION AUDITOR              │
│     Checking your path to success       │
╰──────────────────────────────────────────╯
```

**Available mascot styles:** `clawd` (default), `cap`, `bot`, `shield`

## ✨ Features

### Level 1: Credit Tally Engine
- Calculates valid earned credits
- Excludes: F grades, W withdrawals, 0-credit labs
- Shows breakdown: completed/failed/withdrawn

### Level 2: CGPA Calculator + Waiver Handler
- Weighted CGPA using NSU grade scale
- Flags probation status (CGPA < 2.0)
- Interactive waiver prompts for missing courses

### Level 3: Deficiency Reporter
- Compares transcript against program requirements
- Identifies missing: Mandatory GED, Core, Major Core courses
- Retake handling (keeps best grade only)
- Final eligibility determination

## 🚀 Usage

```bash
python audit_core.py <transcript.csv> <program_name> <program_knowledge.md>

# Run specific level only
python audit_core.py transcript.csv "Computer Science & Engineering" program_knowledge.md --level 1

# Run with pre-set waivers (non-interactive)
python audit_core.py transcript.csv "Computer Science & Engineering" program_knowledge.md --waivers ENG103 PHI101
```

## 📊 NSU Grade Scale

| Grade | Points | Status |
|-------|--------|--------|
| A | 4.0 | ✓ Passing |
| A- | 3.7 | ✓ Passing |
| B+ | 3.3 | ✓ Passing |
| B | 3.0 | ✓ Passing |
| B- | 2.7 | ✓ Passing |
| C+ | 2.3 | ✓ Passing |
| C | 2.0 | ✓ Passing |
| C- | 1.7 | ✓ Passing |
| D+ | 1.3 | ✓ Passing |
| D | 1.0 | ✓ Passing |
| F | 0.0 | ✗ Failing |
| W | 0.0 | ✗ Withdrawn |
| I | 0.0 | ✗ Incomplete |

## 🧪 Test Files

- `test_L1.csv` - Tests credit tally, F grades, W withdrawals, 0-credit labs
- `test_L2.csv` - Tests CGPA calculation across all grade levels
- `test_L3.csv` - Tests retake scenarios (multiple attempts, best grade kept)

## 📁 Project Structure

```
audit_core/
├── audit_core.py          # Main CLI tool
├── mascot/               # 🎨 8-bit mascot module
│   └── __init__.py       # Clawd-inspired mascot
├── utils/
│   ├── parser.py         # CSV parsing, retake logic
│   ├── calculator.py     # Credits, CGPA calculations
│   └── reporter.py       # Deficiency reports
├── test_cases/           # Test CSV files
├── program_knowledge.md  # Program requirements
└── requirements.txt      # Python dependencies
```

## 🎨 Example Output

```
      ██████████      
    ██░░████░░██    
  ██░░██████░░██  
  ██░░██████░░██  
██████████████████████
██░░██            ██░░██
██░░██   AUDIT    ██░░██
██░░██            ██░░██
  ░░██            ██░░  
  ░░██            ██░░  

╭──────────────────────────────────────────╮
│     NSU GRADUATION AUDITOR              │
│     Checking your path to success       │
╰──────────────────────────────────────────╯

Program: Computer Science & Engineering
Audit started...

◈ Auditor is reviewing your transcript...
Loaded 12 courses

━━━ Level 1: Credit Tally ━━━

✗ Valid Credits: 21/130 (16.2%)
   Completed: 21 | Failed: 3 | Withdrawn: 3
   0-credit labs: 3 (excluded)

━━━ Level 2: CGPA & Waivers ━━━

✓ CGPA: 2.95
   Grades: A:4 A-:1 B:2 B+:1 B-:1 C+:1 F:1 W:1

━━━ Level 3: Deficiency Report ━━━

✗ Mandatory Ged: ENG103, PHI101
✗ Core Courses: MAT250, MAT350, MAT361
✗ Major Core: CSE231, CSE311, CSE323, CSE327, CSE331, CSE332, CSE425

Retakes: 1 courses (best grade kept)
   HIS103: ['F', 'B+'] → B+

✗ NOT ELIGIBLE
   • Missing 109 credits (have 21, need 130)

✦ Audit Complete ✦
```

## 📦 Requirements

- Python 3.7+
- rich library (`pip install rich`)

## 🎓 Implementation Notes

**Retake Logic:** When course appears multiple times, keeps best grade for CGPA calculation.

**Waiver Handling:** Admin can grant waivers interactively; waived courses removed from missing list.

**Credit Validity:** Valid credits = passing grades (D or better) with non-zero credits.

**Probation:** CGPA < 2.0 triggers probation warning.

**Mascot:** Inspired by Claude Code's Clawd - an 8-bit style character in NSU blue & gold colors.

---

Built for CSE226.1 - Vibe Coding (Spring 2026)  
🎓 NSU North South University
