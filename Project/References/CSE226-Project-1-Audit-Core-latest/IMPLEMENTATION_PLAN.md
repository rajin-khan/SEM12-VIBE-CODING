# NSU Transcript Credit Counter - Implementation Plan

## Overview
A Python-based CLI tool that reads NSU student transcript CSV files and calculates passed credits based on the official NSU grading policy.

---

## Key Findings

### 1. Grading Policy (from NSU Program.md)

**Passing Grades (Credits COUNT toward graduation):**
| Grade | Points | Status |
|-------|--------|--------|
| A | 4.0 | ✓ Passed |
| A- | 3.7 | ✓ Passed |
| B+ | 3.3 | ✓ Passed |
| B | 3.0 | ✓ Passed |
| B- | 2.7 | ✓ Passed |
| C+ | 2.3 | ✓ Passed |
| C | 2.0 | ✓ Passed |
| C- | 1.7 | ✓ Passed |
| D+ | 1.3 | ✓ Passed |
| D | 1.0 | ✓ Passed |

**Failing/Non-Credit Grades (Credits do NOT count):**
| Grade | Status |
|-------|--------|
| F | ✗ Failed - No credit |
| I | ✗ Incomplete - No credit |
| W | ✗ Withdrawal - No credit |

**Special Rules:**
- F grade: Credits do not apply toward graduation
- I (Incomplete): Credits do not apply and not included in GPA
- W (Withdrawal): Credits do not apply and not included in GPA
- Courses with 0 credits (like non-credit labs) are tracked but don't contribute to totals

### 2. Transcript CSV Format

**Columns:**
- `Course_Code`: Course identifier (e.g., ENG102, CSE115)
- `Credits`: Credit hours (can be 0 for non-credit labs)
- `Grade`: Letter grade (A, A-, B+, B, B-, C+, C, C-, D+, D, F, I, W)
- `Semester`: Academic term (e.g., Spring 2023, Fall 2024)

**Sample Data:**
```csv
Course_Code,Credits,Grade,Semester
ENG102,3,A,Spring 2023
MAT116,0,B,Spring 2023
HIS103,3,F,Summer 2023
CSE173,3,W,Fall 2023
```

---

## Proposed Solution

### Features

1. **CLI Interface**
   - Accept CSV file path as command-line argument
   - Support optional flags for output format
   - Error handling for missing/invalid files

2. **Credit Calculation Logic**
   - Parse CSV file
   - For each course:
     - Check if grade is passing (D or above, excluding F, I, W)
     - Track attempted credits (all courses except W and I for GPA rules)
     - Track passed credits (only passing grades)
     - Mark whether credit is counted toward graduation
   - Handle duplicate courses (retakes) - show all attempts but identify the best grade

3. **Output Format (Tabular)**
   ```
   +-------------+----------+--------+----------+---------------+---------------+
   | Course Code | Credits  | Grade  | Semester | Passed?       | Credit Counted|
   +-------------+----------+--------+----------+---------------+---------------+
   | ENG102      | 3        | A      | Spring23 | ✓ Yes         | ✓ Yes         |
   | HIS103      | 3        | F      | Summer23 | ✗ No          | ✗ No          |
   | HIS103      | 3        | B+     | Spring24 | ✓ Yes         | ✓ Yes         |
   +-------------+----------+--------+----------+---------------+---------------+
   | TOTALS      | Attempted: 30    |          | Passed: 24    | Counted: 24   |
   +-------------+------------------+----------+---------------+---------------+
   ```

4. **Summary Statistics**
   - Total credits attempted
   - Total credits passed
   - Total credits counted toward graduation
   - Number of failed courses
   - Number of withdrawals
   - Number of incomplete courses

### Technical Stack

- **Language:** Python 3.8+
- **Libraries:** 
  - `csv` (built-in) - for reading CSV files
  - `argparse` (built-in) - for CLI interface
  - `tabulate` - for beautiful table formatting
  - `colorama` - for colored terminal output (optional)

### File Structure

```
Project1/
├── credit_tally_engine.py    # Main CLI tool
├── requirements.txt          # Python dependencies
├── README.md                 # Usage documentation
└── Proxy Files/
    ├── transcript.csv        # Sample data
    └── program.md           # Program knowledge base
```

### CLI Usage Examples

```bash
# Basic usage
python credit_tally_engine.py "Proxy Files/transcript.csv"

# With verbose output
python credit_tally_engine.py transcript.csv --verbose

# Export to file
python credit_tally_engine.py transcript.csv --output results.txt
```

---

## Implementation Steps

1. Create the main Python script with CLI argument parsing
2. Implement CSV reading and validation
3. Create grading policy validation logic
4. Build tabular output formatter
5. Add summary calculations
6. Test with provided sample data
7. Add error handling and edge cases

---

## Questions for Approval

1. **Grade Threshold**: Should D (1.0) be considered passing for credit counting? (Currently: Yes)
2. **Retake Logic**: For retaken courses, should we only count the best grade or show all attempts? (Currently: Show all, mark best as counted)
3. **Withdrawal/Incomplete**: Confirm these receive 0 credit and don't count toward attempted credits for graduation
4. **Zero-Credit Courses**: Should non-credit labs (0 credits) be included in the table? (Currently: Yes, for completeness)
5. **Output Format**: Is the proposed table format acceptable, or would you prefer CSV/JSON output option?

---

## Next Steps

Upon approval, I will:
1. Create the Python CLI tool
2. Test with the provided sample transcript
3. Provide usage documentation

**Please review and approve this plan before I proceed with implementation.**
