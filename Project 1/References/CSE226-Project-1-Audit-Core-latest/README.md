# The Credit Tally Engine

A Python-based CLI tool that analyzes student transcripts from CSV files and calculates passed credits based on NSU's official grading policy.

## Tools

This package includes two CLI tools:

1. **The Credit Tally Engine** (`credit_tally_engine.py`) - Analyzes transcript credits
2. **The Logic Gate & Waiver Handler** (`logic_gate_waiver_handler.py`) - Calculates CGPA with waiver support

## Features

- **CSV Transcript Parsing**: Reads student transcript data from CSV files
- **NSU Grading Policy Compliance**: Follows official NSU grading scale (A through D are passing, F/I/W are non-credit)
- **Retake Handling**: Shows all course attempts but counts only the best grade toward graduation
- **Program Requirements Integration**: Reads program requirements from markdown files
- **Comprehensive Statistics**: Provides detailed credit analysis and progress tracking
- **Tabular Output**: Clean, formatted output showing all relevant information
- **Waiver Support**: Handles course waivers interactively

## Installation

No external dependencies required. The tool uses only Python standard library modules:
- `argparse`
- `csv`
- `re`
- `collections`
- `pathlib`

Simply download the Python files and run with Python 3.8 or higher.

## Usage

### The Credit Tally Engine

```bash
python credit_tally_engine.py <transcript.csv> <program_name> <program_knowledge.md>
```

### The Logic Gate & Waiver Handler

```bash
python logic_gate_waiver_handler.py <transcript.csv> <program_name> <program_knowledge.md>
```

### Arguments (Credit Tally Engine)

1. **transcript.csv** - Path to the transcript CSV file
2. **program_name** - Name of the academic program (e.g., "Computer Science", "Business Administration")
3. **program_knowledge.md** - Path to the markdown file containing program requirements

### Arguments (Logic Gate & Waiver Handler)

1. **transcript.csv** - Path to the transcript CSV file
2. **program_name** - Name of the academic program (e.g., "Computer Science", "Business Administration")
3. **program_knowledge.md** - Path to the markdown file containing program requirements

### Optional Arguments (Credit Tally Engine)

- `-o, --output` - Save output to a file instead of printing to console
- `-v, --verbose` - Show detailed information (reserved for future use)
- `-e, --open-electives` - Course codes to count as open/free electives (comma-separated)

### Examples

```bash
# Credit Tally Engine - Basic usage
python credit_tally_engine.py transcript.csv "Computer Science" program.md

# Credit Tally Engine - Save output to file
python credit_tally_engine.py transcript.csv "Business Administration" program.md --output results.txt

# Logic Gate & Waiver Handler - Basic usage
python logic_gate_waiver_handler.py transcript.csv "Computer Science" program.md

# Logic Gate & Waiver Handler - Save output to file
python logic_gate_waiver_handler.py transcript.csv "Microbiology" program.md --output cgpa_results.txt
```

## File Formats

### Transcript CSV Format

The CSV file must contain the following columns:

```csv
Course_Code,Credits,Grade,Semester
ENG102,3,A,Spring 2023
MAT116,0,B,Spring 2023
CSE115,4,A-,Summer 2023
HIS103,3,F,Summer 2023
```

**Columns:**
- `Course_Code` - Course identifier (e.g., ENG102, CSE115)
- `Credits` - Credit hours (can be 0 for non-credit labs)
- `Grade` - Letter grade (A, A-, B+, B, B-, C+, C, C-, D+, D, F, I, W)
- `Semester` - Academic term (e.g., Spring 2023, Fall 2024)

### Program Knowledge Markdown Format

The markdown file should contain program information in this format:

```markdown
## [Program: Computer Science & Engineering]

- **Degree**: Bachelor of Science (BS)
- **Total Credits Required**: 130
- **Mandatory GED**: ENG102, ENG103, HIS103, PHI101
- **Core Math**: MAT116, MAT120, MAT250, MAT350, MAT361
- **Major Core**: CSE115, CSE173, CSE215, CSE225, CSE231, CSE311, CSE323, CSE327, CSE331, CSE332, CSE425
```

## Grading Policy

### Passing Grades (Credits Count Toward Graduation)

| Grade | Grade Points | Status |
|-------|-------------|--------|
| A     | 4.0         | ✓ Pass |
| A-    | 3.7         | ✓ Pass |
| B+    | 3.3         | ✓ Pass |
| B     | 3.0         | ✓ Pass |
| B-    | 2.7         | ✓ Pass |
| C+    | 2.3         | ✓ Pass |
| C     | 2.0         | ✓ Pass |
| C-    | 1.7         | ✓ Pass |
| D+    | 1.3         | ✓ Pass |
| D     | 1.0         | ✓ Pass |

### Non-Credit Grades (Credits Do NOT Count)

| Grade | Status |
|-------|--------|
| F     | ✗ Failure - No credit |
| I     | ✗ Incomplete - No credit |
| W     | ✗ Withdrawal - No credit |

## Output Explanation

The tool generates a comprehensive report with the following sections:

### Course Table

| Column | Description |
|--------|-------------|
| Course Code | Course identifier |
| Credits | Credit hours for the course |
| Grade | Letter grade received |
| Semester | Academic term |
| Passed? | Whether the grade is passing (Y/N) |
| Credit Counted | Whether credit counts toward graduation (best attempts only) |
| Note | Additional information (Retake, Best Attempt) |

### Summary Statistics

- **Total Credits Attempted**: Sum of all credits from courses with grades A-D and F (excluding W and I)
- **Total Credits Passed**: Sum of credits from all passing grades (A through D)
- **Total Credits Counted**: Sum of credits from best attempts only (for retaken courses)
- **Failed Courses (F)**: Count of courses with F grade
- **Withdrawals (W)**: Count of courses with W grade
- **Incomplete (I)**: Count of courses with I grade
- **Zero-Credit Courses**: Count of courses with 0 credits
- **Courses with Retakes**: Count of courses attempted multiple times

### Program Requirements Section

If program information is available in the markdown file:
- Program name
- Total credits required for graduation
- Credits completed (counted toward graduation)
- Remaining credits needed
- List of mandatory courses

## Retake Logic

When a course is taken multiple times:
1. All attempts are displayed in the table
2. Only the attempt with the highest grade points is marked as "Best Attempt"
3. Only the best attempt's credits are counted toward graduation
4. Other attempts are marked as "Retake" and their credits are not counted

Example:
```
HIS103    3.0    F    Fall 2022    [N] No    [N] No    (Retake)
HIS103    3.0    B+   Spring 2023  [Y] Yes   [Y] Yes   (Best Attempt)
```

## Error Handling

The tool handles various error conditions:
- Missing CSV file
- Missing required columns in CSV
- Invalid grade formats
- Missing program knowledge file
- Malformed program data

## Example Output

```
==============================================================================================================
NSU TRANSCRIPT CREDIT ANALYSIS
Program: Computer Science
==============================================================================================================

--------------------------------------------------------------------------------------------------------------
Course Code     Credits    Grade    Semester     Passed?    Credit Counted  Note                
--------------------------------------------------------------------------------------------------------------
ENG102          3.0        A        Spring 2023  [Y] Yes    [Y] Yes                             
MAT116          0.0        B        Spring 2023  [Y] Yes    [Y] Yes                             
CSE115          4.0        A-       Summer 2023  [Y] Yes    [Y] Yes                             
HIS103          3.0        F        Summer 2023  [N] No     [N] No          (Retake)            
HIS103          3.0        B+       Spring 2024  [Y] Yes    [Y] Yes         (Best Attempt)      
...
--------------------------------------------------------------------------------------------------------------

SUMMARY STATISTICS
--------------------------------------------------
Total Credits Attempted:     27.0
Total Credits Passed:        21.0
Total Credits Counted:       21.0 (best attempts only)

Failed Courses (F):          2
Withdrawals (W):             1
Incomplete (I):              0
Zero-Credit Courses:         3
Courses with Retakes:        1
--------------------------------------------------

PROGRAM REQUIREMENTS
--------------------------------------------------
Program:                     Computer Science & Engineering
Total Credits Required:      130
Credits Completed:           21.0
Remaining Credits:           109.0
Mandatory Courses:           ENG102, ENG103, HIS103, PHI101, MAT116, MAT120, MAT250, MAT350, MAT361
--------------------------------------------------
```

## Notes

- Courses with 0 credits (non-credit labs) are tracked but don't contribute to credit totals
- Withdrawal (W) and Incomplete (I) grades are not included in attempted credits per NSU policy
- The tool supports partial program name matching (e.g., "Computer Science" matches "Computer Science & Engineering")
- All grades are case-insensitive (A, a, A- all work)

## License

This tool is for educational use at North South University.

## Author

Created for NSU CSE226.1 coursework.
