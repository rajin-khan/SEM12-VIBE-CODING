"""
Level 1 — Credit Tallying Engine
Parses transcript CSV, identifies retakes, calculates credits attempted/earned,
and assigns status labels to each course attempt.
"""

import csv
import re
from collections import defaultdict

# ─── Academic Timeline ──────────────────────────────────
SEMESTERS = [
    "Spring2019", "Summer2019", "Fall2019",
    "Spring2020", "Summer2020", "Fall2020",
    "Spring2021", "Summer2021", "Fall2021",
    "Spring2022", "Summer2022", "Fall2022",
    "Spring2023", "Summer2023", "Fall2023",
    "Spring2024", "Summer2024", "Fall2024",
]

# Passing grades (D or better, plus T for transfer)
PASSING_GRADES = {"A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "T"}
NON_GPA_GRADES = {"W", "T"}  # Excluded from GPA calculation
GRADE_ORDER = {
    "A": 12, "A-": 11, "B+": 10, "B": 9, "B-": 8,
    "C+": 7, "C": 6, "C-": 5, "D+": 4, "D": 3,
    "F": 1, "I": 0, "W": -1, "T": 13
}


class CourseRecord:
    """Represents a single course attempt from the transcript."""

    def __init__(self, course_code, course_name, credits, grade, semester):
        self.course_code = course_code.strip()
        self.course_name = course_name.strip()
        self.credits = int(float(credits.strip()))
        self.grade = grade.strip()
        self.semester = semester.strip()
        self.status = ""  # Will be set by the engine

    def is_passing(self):
        return self.grade in PASSING_GRADES

    def is_withdrawn(self):
        return self.grade == "W"

    def is_transfer(self):
        return self.grade == "T"

    def is_incomplete(self):
        return self.grade == "I"

    def __repr__(self):
        return f"<{self.course_code} | {self.grade} | {self.semester} | {self.status}>"


def parse_transcript(filepath):
    """Parse a transcript CSV file into a list of CourseRecord objects."""
    records = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < 5:
                continue
            # Skip header row if present
            if row[0].strip().lower() == "course_code":
                continue
            records.append(CourseRecord(
                course_code=row[0],
                course_name=row[1],
                credits=row[2],
                grade=row[3],
                semester=row[4]
            ))
    return records


def _grade_rank(grade):
    """Return numeric rank for a grade (higher is better). I treated as F."""
    if grade == "I":
        return GRADE_ORDER.get("F", 0)
    return GRADE_ORDER.get(grade, -2)


def resolve_retakes(records):
    """
    Group records by course_code, pick the BEST attempt for each course,
    and assign status labels to every record.

    Status values:
      BEST           — the attempt that counts for credit/GPA
      RETAKE-IGNORED — a retake attempt superseded by a better grade
      WAIVED         — grade is T (transfer/waived)
      WITHDRAWN      — grade is W
      FAILED         — grade is F or I and no better attempt exists
    """
    # Group by course_code preserving order
    groups = defaultdict(list)
    for r in records:
        groups[r.course_code].append(r)

    for code, attempts in groups.items():
        if len(attempts) == 1:
            rec = attempts[0]
            if rec.is_withdrawn():
                rec.status = "WITHDRAWN"
            elif rec.is_transfer():
                rec.status = "WAIVED"
            elif rec.is_passing():
                rec.status = "BEST"
            elif rec.grade == "F" or rec.is_incomplete():
                rec.status = "FAILED"
            else:
                rec.status = "BEST"
        else:
            # Multiple attempts — find the best grade
            best = max(attempts, key=lambda r: _grade_rank(r.grade))
            for rec in attempts:
                if rec is best:
                    if rec.is_withdrawn():
                        rec.status = "WITHDRAWN"
                    elif rec.is_transfer():
                        rec.status = "WAIVED"
                    elif rec.is_passing():
                        rec.status = "BEST"
                    elif rec.grade == "F" or rec.is_incomplete():
                        rec.status = "FAILED"
                    else:
                        rec.status = "BEST"
                else:
                    if rec.is_withdrawn():
                        rec.status = "WITHDRAWN"
                    else:
                        rec.status = "RETAKE-IGNORED"

    return records


def calculate_credits(records):
    """
    Calculate credits attempted and credits earned.

    Credits Attempted:
      Count ALL credit-bearing course attempts regardless of grade,
      EXCLUDING W (Withdrawn), 0-credit courses, and T (Transfer/Waived).
      Each attempt counts (including retakes and F grades).

    Credits Earned:
      Count passed courses only, one instance per course (BEST attempt).
      T (transfer) credits count as earned.
      0-credit courses never count toward credit total.
    """
    credits_attempted = 0
    credits_earned = 0

    for r in records:
        # Credits Attempted: credit-bearing, not W, not T, not 0-credit
        if r.credits > 0 and r.grade != "W" and r.grade != "T":
            credits_attempted += r.credits

        # Credits Earned: only BEST or WAIVED status, passing, counted once
        if r.status in ("BEST", "WAIVED") and r.credits > 0:
            if r.is_passing():
                credits_earned += r.credits

    return credits_attempted, credits_earned


def process_transcript(filepath):
    """
    Full Level 1 pipeline: parse → resolve retakes → sort → calculate credits.
    Returns (records, credits_attempted, credits_earned).
    """
    records = parse_transcript(filepath)
    records = resolve_retakes(records)
    
    # Sort records: Primarily Numerical Ascending by Course Code, Secondarily Chronological (semester)
    sem_map = {sem: i for i, sem in enumerate(SEMESTERS)}
    
    def sort_key(r):
        code = r.course_code
        sem_idx = sem_map.get(r.semester, -1)
        
        # Split code into prefix, number, and suffix (e.g., 'CSE115L' -> 'CSE', 115, 'L')
        match = re.match(r'([A-Z]+)(\d+)([A-Z]*)', code)
        if match:
            prefix, num, suffix = match.groups()
            return (prefix, int(num), suffix, sem_idx)
        return (code, 0, "", sem_idx)  # Fallback
    
    records.sort(key=sort_key)
    
    credits_attempted, credits_earned = calculate_credits(records)
    return records, credits_attempted, credits_earned
