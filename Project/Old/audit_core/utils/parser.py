"""
Transcript Parser Module
Handles CSV parsing, retake logic, and data validation
"""

import csv
from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path

@dataclass
class CourseRecord:
    """Represents a single course entry from transcript"""
    course_code: str
    credits: int
    grade: str
    semester: str
    
    def is_valid_grade(self) -> bool:
        """Check if grade is valid (not F, W, or I)"""
        return self.grade.upper() not in ['F', 'W', 'I']
    
    def is_passing(self) -> bool:
        """Check if grade is passing (D or better)"""
        passing_grades = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D']
        return self.grade.upper() in passing_grades
    
    def has_zero_credits(self) -> bool:
        """Check if course has 0 credits (typically labs)"""
        return self.credits == 0


class TranscriptParser:
    """Parses and processes student transcript data"""
    
    # Valid NSU grades
    VALID_GRADES = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F', 'W', 'I']
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.raw_records: List[CourseRecord] = []
        self.processed_records: List[CourseRecord] = []
        self.retakes: Dict[str, List[CourseRecord]] = {}
        
    def parse(self) -> List[CourseRecord]:
        """Parse CSV file and return list of course records"""
        if not self.filepath.exists():
            raise FileNotFoundError(f"Transcript file not found: {self.filepath}")
        
        with open(self.filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Skip empty rows
                if not any(row.values()):
                    continue
                
                # Parse credits (handle 0 values for labs)
                try:
                    credits = int(row.get('Credits', 0))
                except (ValueError, TypeError):
                    credits = 0
                
                record = CourseRecord(
                    course_code=row.get('Course_Code', '').strip().upper(),
                    credits=credits,
                    grade=row.get('Grade', '').strip().upper(),
                    semester=row.get('Semester', '').strip()
                )
                
                # Validate grade
                if record.grade and record.grade not in self.VALID_GRADES:
                    print(f"Warning: Unknown grade '{record.grade}' for {record.course_code}")
                
                self.raw_records.append(record)
        
        return self.raw_records
    
    def process_retakes(self) -> List[CourseRecord]:
        """
        Process retakes - keep only the best grade for each course.
        If multiple attempts exist, keep the one with highest grade points.
        """
        if not self.raw_records:
            self.parse()
        
        # Group records by course code
        course_attempts: Dict[str, List[CourseRecord]] = {}
        for record in self.raw_records:
            if record.course_code not in course_attempts:
                course_attempts[record.course_code] = []
            course_attempts[record.course_code].append(record)
        
        # For each course, keep the best attempt
        for course_code, attempts in course_attempts.items():
            if len(attempts) > 1:
                self.retakes[course_code] = attempts
                # Sort by grade quality (best first)
                best_attempt = self._get_best_attempt(attempts)
                self.processed_records.append(best_attempt)
            else:
                self.processed_records.append(attempts[0])
        
        return self.processed_records
    
    def _get_best_attempt(self, attempts: List[CourseRecord]) -> CourseRecord:
        """Get the best grade attempt from multiple tries"""
        grade_points = {
            'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D+': 1.3, 'D': 1.0,
            'F': 0.0, 'W': 0.0, 'I': 0.0
        }
        
        # Sort by grade points (descending), then by semester (most recent first)
        sorted_attempts = sorted(
            attempts,
            key=lambda x: (grade_points.get(x.grade, 0), x.semester),
            reverse=True
        )
        
        return sorted_attempts[0]
    
    def get_valid_credits(self) -> int:
        """Calculate total valid credits (passing grades only, excluding 0-credit labs)"""
        if not self.processed_records:
            self.process_retakes()
        
        valid_credits = 0
        for record in self.processed_records:
            # Valid if: passing grade, not W/I/F, and has credits
            if record.is_passing() and not record.has_zero_credits():
                valid_credits += record.credits
        
        return valid_credits
    
    def get_all_credits(self) -> int:
        """Get total credits attempted (including failures)"""
        if not self.processed_records:
            self.process_retakes()
        
        return sum(r.credits for r in self.processed_records if not r.has_zero_credits())
    
    def get_retake_summary(self) -> Dict:
        """Get summary of retakes for reporting"""
        if not self.retakes:
            return {}
        
        summary = {}
        for course, attempts in self.retakes.items():
            grades = [a.grade for a in attempts]
            best = self._get_best_attempt(attempts)
            summary[course] = {
                'attempts': len(attempts),
                'grades': grades,
                'best_grade': best.grade,
                'semester': best.semester
            }
        
        return summary
    
    def get_courses_by_grade(self, grade_filter: List[str]) -> List[CourseRecord]:
        """Get courses filtered by specific grades"""
        if not self.processed_records:
            self.process_retakes()
        
        return [r for r in self.processed_records if r.grade in grade_filter]
    
    def get_failing_courses(self) -> List[CourseRecord]:
        """Get all courses with failing grades"""
        return self.get_courses_by_grade(['F'])
    
    def get_withdrawn_courses(self) -> List[CourseRecord]:
        """Get all withdrawn courses"""
        return self.get_courses_by_grade(['W'])
    
    def get_incomplete_courses(self) -> List[CourseRecord]:
        """Get all incomplete courses"""
        return self.get_courses_by_grade(['I'])
    
    def get_course_list(self) -> List[str]:
        """Get list of all unique course codes"""
        if not self.processed_records:
            self.process_retakes()
        return [r.course_code for r in self.processed_records]


if __name__ == "__main__":
    # Test the parser
    import sys
    if len(sys.argv) > 1:
        parser = TranscriptParser(sys.argv[1])
        records = parser.parse()
        print(f"Parsed {len(records)} raw records")
        
        processed = parser.process_retakes()
        print(f"Processed {len(processed)} unique courses (after retake handling)")
        
        print(f"\nValid credits: {parser.get_valid_credits()}")
        print(f"Total credits attempted: {parser.get_all_credits()}")
        
        retakes = parser.get_retake_summary()
        if retakes:
            print(f"\nRetakes found:")
            for course, info in retakes.items():
                print(f"  {course}: {info['attempts']} attempts, best: {info['best_grade']}")
