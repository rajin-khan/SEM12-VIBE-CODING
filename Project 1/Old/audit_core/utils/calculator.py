"""
Calculator Module
Handles NSU grade scale, CGPA calculations, and credit logic
"""

from typing import List, Dict
from dataclasses import dataclass

@dataclass
class GradeInfo:
    """Information about a grade"""
    letter: str
    points: float
    is_passing: bool
    counts_for_credit: bool
    counts_for_gpa: bool


class NSUGradingScale:
    """NSU Grading Scale based on official policy"""
    
    # Grade points mapping
    GRADE_POINTS = {
        'A': 4.0,    # 93 and above
        'A-': 3.7,   # 90-92
        'B+': 3.3,   # 87-89
        'B': 3.0,    # 83-86
        'B-': 2.7,   # 80-82
        'C+': 2.3,   # 77-79
        'C': 2.0,    # 73-76
        'C-': 1.7,   # 70-72
        'D+': 1.3,   # 67-69
        'D': 1.0,    # 60-66
        'F': 0.0,    # Below 60
        'I': 0.0,    # Incomplete
        'W': 0.0,    # Withdrawal
    }
    
    # Grades that count toward graduation credits
    PASSING_GRADES = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D']
    
    # Grades that count in CGPA calculation
    GPA_GRADES = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F']
    
    @classmethod
    def get_grade_info(cls, grade: str) -> GradeInfo:
        """Get comprehensive info about a grade"""
        grade = grade.upper().strip()
        points = cls.GRADE_POINTS.get(grade, 0.0)
        
        return GradeInfo(
            letter=grade,
            points=points,
            is_passing=grade in cls.PASSING_GRADES,
            counts_for_credit=grade in cls.PASSING_GRADES,
            counts_for_gpa=grade in cls.GPA_GRADES
        )
    
    @classmethod
    def get_points(cls, grade: str) -> float:
        """Get grade points for a letter grade"""
        return cls.GRADE_POINTS.get(grade.upper().strip(), 0.0)
    
    @classmethod
    def is_passing(cls, grade: str) -> bool:
        """Check if grade is passing"""
        return grade.upper().strip() in cls.PASSING_GRADES
    
    @classmethod
    def counts_for_credit(cls, grade: str) -> bool:
        """Check if grade counts toward graduation credits"""
        return grade.upper().strip() in cls.PASSING_GRADES
    
    @classmethod
    def counts_for_gpa(cls, grade: str) -> bool:
        """Check if grade counts in CGPA calculation"""
        return grade.upper().strip() in cls.GPA_GRADES


class Calculator:
    """Main calculator for audit operations"""
    
    def __init__(self, records: list):
        self.records = records
    
    def calculate_valid_credits(self) -> int:
        """
        Level 1: Calculate total valid credits
        Valid credits = passing grades (D or better) with non-zero credits
        Excludes: F, W, I grades and 0-credit courses
        """
        valid_credits = 0
        
        for record in self.records:
            # Must be passing grade
            if not NSUGradingScale.is_passing(record.grade):
                continue
            
            # Must have credits (excludes 0-credit labs)
            if record.credits <= 0:
                continue
            
            valid_credits += record.credits
        
        return valid_credits
    
    def calculate_cgpa(self) -> float:
        """
        Level 2: Calculate weighted CGPA
        CGPA = Sum(Grade Points × Credits) / Total Credits Attempted
        Only includes grades that count for GPA (excludes W, I)
        """
        total_quality_points = 0.0
        total_credits_attempted = 0
        
        for record in self.records:
            # Skip if doesn't count for GPA (W, I)
            if not NSUGradingScale.counts_for_gpa(record.grade):
                continue
            
            # Skip 0-credit courses
            if record.credits <= 0:
                continue
            
            grade_points = NSUGradingScale.get_points(record.grade)
            quality_points = grade_points * record.credits
            
            total_quality_points += quality_points
            total_credits_attempted += record.credits
        
        if total_credits_attempted == 0:
            return 0.0
        
        return total_quality_points / total_credits_attempted
    
    def is_on_probation(self) -> bool:
        """Check if student is on probation (CGPA < 2.0)"""
        cgpa = self.calculate_cgpa()
        return cgpa < 2.0
    
    def calculate_completion_percentage(self, required_credits: int) -> float:
        """Calculate percentage of required credits completed"""
        if required_credits <= 0:
            return 0.0
        
        valid_credits = self.calculate_valid_credits()
        return (valid_credits / required_credits) * 100
    
    def get_grade_distribution(self) -> Dict[str, int]:
        """Get distribution of grades"""
        distribution = {}
        
        for record in self.records:
            grade = record.grade
            if grade not in distribution:
                distribution[grade] = 0
            distribution[grade] += 1
        
        return distribution
    
    def get_credits_by_category(self) -> Dict[str, int]:
        """Break down credits by category"""
        categories = {
            'valid_completed': 0,      # Passing grades with credits
            'failed': 0,               # F grades
            'withdrawn': 0,            # W grades
            'incomplete': 0,           # I grades
            'zero_credit_courses': 0,  # 0-credit labs (any grade)
        }
        
        for record in self.records:
            if record.credits == 0:
                categories['zero_credit_courses'] += 1
                continue
            
            if record.grade == 'F':
                categories['failed'] += record.credits
            elif record.grade == 'W':
                categories['withdrawn'] += record.credits
            elif record.grade == 'I':
                categories['incomplete'] += record.credits
            elif NSUGradingScale.is_passing(record.grade):
                categories['valid_completed'] += record.credits
        
        return categories
    
    def can_graduate(self, required_credits: int, required_cgpa: float = 2.0) -> tuple:
        """
        Check if student can graduate
        Returns: (can_graduate: bool, reasons: list)
        """
        reasons = []
        
        # Check credits
        valid_credits = self.calculate_valid_credits()
        if valid_credits < required_credits:
            missing = required_credits - valid_credits
            reasons.append(f"Missing {missing} credits (have {valid_credits}, need {required_credits})")
        
        # Check CGPA
        cgpa = self.calculate_cgpa()
        if cgpa < required_cgpa:
            reasons.append(f"CGPA too low: {cgpa:.2f} (minimum {required_cgpa})")
        
        # Check probation
        if self.is_on_probation():
            reasons.append("Student is on probation (CGPA < 2.0)")
        
        can_graduate = len(reasons) == 0
        return can_graduate, reasons


if __name__ == "__main__":
    # Test the calculator
    from parser import TranscriptParser
    
    import sys
    if len(sys.argv) > 1:
        parser = TranscriptParser(sys.argv[1])
        parser.process_retakes()
        
        calc = Calculator(parser.processed_records)
        
        print(f"Valid Credits: {calc.calculate_valid_credits()}")
        print(f"CGPA: {calc.calculate_cgpa():.2f}")
        print(f"On Probation: {calc.is_on_probation()}")
        print(f"Grade Distribution: {calc.get_grade_distribution()}")
        print(f"Credits by Category: {calc.get_credits_by_category()}")
