# CGPA Calculator - Planning Document

## Grading Policy (from NSU_Program.md)

### Grading Scale
| Grade | Grade Points | Notes |
|-------|--------------|-------|
| A | 4.0 | Excellent |
| A- | 3.7 | |
| B+ | 3.3 | |
| B | 3.0 | Good |
| B- | 2.7 | |
| C+ | 2.3 | |
| C | 2.0 | Average |
| C- | 1.7 | |
| D+ | 1.3 | |
| D | 1.0 | Poor |
| F | 0.0 | Failure |
| I | 0.0 | Incomplete |
| W | 0.0 | Withdrawal |
| WA | 0.0 | Waiver (counts as 0 credits) |

### GPA Calculation Rules
- Only grades **A, A-, B+, B, B-, C+, C, C-, D+, D, and F** are used to determine credits attempted
- Only courses **required for a degree** are included in GPA calculation
- Grades in other courses appear on transcript but don't count toward GPA
- F grade remains in CGPA until course is retaken/replaced with better grade

## CGPA Calculation Formula

### Basic Formula
```
CGPA = Total Grade Points Earned ÷ Total Credits Attempted
```

Where:
- **Total Grade Points Earned** = Σ(Course Credits × Grade Points)
- **Total Credits Attempted** = Σ(Course Credits for graded courses)

### Grade Points Table
| Grade | Points |
|-------|--------|
| A | 4.0 |
| A- | 3.7 |
| B+ | 3.3 |
| B | 3.0 |
| B- | 2.7 |
| C+ | 2.3 |
| C | 2.0 |
| C- | 1.7 |
| D+ | 1.3 |
| D | 1.0 |
| F | 0.0 |

### Excluded from CGPA Calculation
- **I (Incomplete)** - Does not count
- **W (Withdrawal)** - Does not count
- **WA (Waiver)** - Does not count (0 credits)
- **S/P (Satisfactory/Pass)** - Not in grading policy, treat as not counted
- **IP (In Progress)** - Does not count

## Waiver Handling

### From Program Knowledge
Courses that can be waived are marked in the program:
- ENG 102: "0 if waived" in Microbiology program

### Waiver Process
1. Identify all courses in the program that can be waived
2. For each waivable course, ask user: "Waiver granted for [COURSE]?"
3. If waiver granted:
   - Course counts as 0 credits toward graduation
   - Course does NOT count in CGPA calculation
4. If no waiver:
   - Use actual grade (if any) for CGPA calculation

## CGPA Calculator Logic

### Step 1: Load Data
- Read transcript CSV
- Read program knowledge from MD file
- Identify waivable courses

### Step 2: Ask About Waivers
- For each waivable course in the program
- Ask user: "Waiver granted for [COURSE]?"
- Record waiver status

### Step 3: Filter Courses for CGPA
Only include courses that:
1. Are required for the program
2. Have a grade that counts (A through F)
3. Are NOT waived
4. Are NOT W, I, IP, S, P

### Step 4: Calculate CGPA
```
total_grade_points = Σ(credits × grade_points)
total_credits = Σ(credits)

CGPA = total_grade_points / total_credits
```

### Step 5: Output Results
- Display courses used in CGPA calculation
- Display excluded courses (with reasons)
- Display calculated CGPA
- Compare with minimum requirement (2.0)

## Test Cases

### Test Transcript (test_L2.csv)
- Mix of passing grades (A through D)
- Some F grades
- Some W (Withdrawal)
- Some I (Incomplete)
- Some retakes
- Courses that can be waived

### Expected Behavior
1. W, I should not affect CGPA
2. F should affect CGPA (0 points)
3. Retakes: only best grade counts
4. Waived courses: 0 credits, no effect on CGPA
5. Non-program courses: excluded from CGPA
