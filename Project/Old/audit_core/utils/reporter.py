"""
Reporter Module
Generates audit reports and deficiency analysis
"""

from typing import List, Dict, Set
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.console import Console
from rich import box
import re

console = Console()

# Blue pastel color theme
COLORS = {
    'primary': '#5F9EA0',
    'secondary': '#87CEEB',
    'light': '#B0E0E6',
    'dark': '#4682B4',
    'accent': '#00CED1',
    'success': '#20B2AA',
    'warning': '#FFD700',
    'error': '#FF6B6B',
    'text': '#2C3E50',
}


class ProgramRequirements:
    """Parse and manage program requirements from markdown knowledge base"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.programs = {}
        self._parse()
    
    def _parse(self):
        """Parse program_knowledge.md file"""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by program sections
        sections = re.split(r'## \[Program: ([^\]]+)\]', content)
        
        if len(sections) > 1:
            for i in range(1, len(sections), 2):
                program_name = sections[i].strip()
                program_content = sections[i + 1]
                
                self.programs[program_name] = self._parse_program_section(program_content)
    
    def _parse_program_section(self, content: str) -> Dict:
        """Parse individual program section"""
        program = {
            'degree': '',
            'total_credits': 0,
            'mandatory_ged': [],
            'core_courses': [],
            'major_core': [],
        }
        
        lines = content.strip().split('\n')
        current_list = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse degree
            if line.startswith('- **Degree**:'):
                program['degree'] = line.split(':', 1)[1].strip()
            
            # Parse total credits
            elif line.startswith('- **Total Credits Required**:'):
                credits_str = line.split(':', 1)[1].strip()
                try:
                    program['total_credits'] = int(credits_str)
                except ValueError:
                    pass
            
            # Parse mandatory GED
            elif line.startswith('- **Mandatory GED**:'):
                courses_str = line.split(':', 1)[1].strip()
                program['mandatory_ged'] = [c.strip() for c in courses_str.split(',')]
            
            # Parse core courses
            elif line.startswith('- **Core') or line.startswith('- **Core Math**') or line.startswith('- **Core Business**'):
                courses_str = line.split(':', 1)[1].strip()
                program['core_courses'] = [c.strip() for c in courses_str.split(',')]
            
            # Parse major core
            elif line.startswith('- **Major Core**:'):
                courses_str = line.split(':', 1)[1].strip()
                program['major_core'] = [c.strip() for c in courses_str.split(',')]
        
        return program
    
    def get_program(self, name: str) -> Dict:
        """Get program requirements by name"""
        # Try exact match first
        if name in self.programs:
            return self.programs[name]
        
        # Try case-insensitive match
        for prog_name, prog_data in self.programs.items():
            if prog_name.lower() == name.lower():
                return prog_data
        
        return None
    
    def get_all_required_courses(self, program_name: str) -> Set[str]:
        """Get all required courses for a program"""
        program = self.get_program(program_name)
        if not program:
            return set()
        
        all_courses = set()
        all_courses.update(program.get('mandatory_ged', []))
        all_courses.update(program.get('core_courses', []))
        all_courses.update(program.get('major_core', []))
        
        return all_courses
    
    def get_required_credits(self, program_name: str) -> int:
        """Get total required credits for a program"""
        program = self.get_program(program_name)
        if not program:
            return 0
        return program.get('total_credits', 0)


class DeficiencyReporter:
    """Generates deficiency reports for Level 3"""
    
    def __init__(self, calculator, parser, program_requirements: ProgramRequirements, program_name: str):
        self.calculator = calculator
        self.parser = parser
        self.program_req = program_requirements
        self.program_name = program_name
        self.completed_courses = set(parser.get_course_list())
    
    def find_missing_courses(self) -> Dict[str, List[str]]:
        """Find missing required courses by category"""
        program = self.program_req.get_program(self.program_name)
        if not program:
            return {}
        
        missing = {
            'mandatory_ged': [],
            'core_courses': [],
            'major_core': []
        }
        
        # Check each category
        for category in ['mandatory_ged', 'core_courses', 'major_core']:
            required = set(program.get(category, []))
            completed = self.completed_courses
            missing_in_category = required - completed
            missing[category] = sorted(list(missing_in_category))
        
        return missing
    
    def generate_report(self) -> Dict:
        """Generate comprehensive deficiency report"""
        program = self.program_req.get_program(self.program_name)
        if not program:
            return {"error": f"Program '{self.program_name}' not found"}
        
        report = {
            'program': self.program_name,
            'degree': program.get('degree', ''),
            'required_credits': program.get('total_credits', 0),
            'current_credits': self.calculator.calculate_valid_credits(),
            'cgpa': round(self.calculator.calculate_cgpa(), 2),
            'on_probation': self.calculator.is_on_probation(),
            'missing_courses': self.find_missing_courses(),
            'can_graduate': False,
            'issues': []
        }
        
        # Check graduation eligibility
        can_grad, reasons = self.calculator.can_graduate(
            program.get('total_credits', 0),
            required_cgpa=2.0
        )
        report['can_graduate'] = can_grad
        report['issues'] = reasons
        
        return report
    
    def format_report_table(self, report: Dict) -> Table:
        """Format report as Rich Table"""
        table = Table(
            title=f"[bold {COLORS['dark']}]📋 Audit Report: {report['program']}[/]",
            box=box.ROUNDED,
            border_style=COLORS['primary']
        )
        
        table.add_column("Category", style=f"bold {COLORS['dark']}")
        table.add_column("Status", style=COLORS['text'])
        table.add_column("Details", style=COLORS['text'])
        
        # Credits
        req_credits = report['required_credits']
        curr_credits = report['current_credits']
        credits_pct = (curr_credits / req_credits * 100) if req_credits > 0 else 0
        credits_color = COLORS['success'] if curr_credits >= req_credits else COLORS['warning']
        
        table.add_row(
            "Credits",
            f"[{credits_color}]{curr_credits}/{req_credits}[/]",
            f"{credits_pct:.1f}% complete"
        )
        
        # CGPA
        cgpa = report['cgpa']
        cgpa_color = COLORS['success'] if cgpa >= 2.0 else COLORS['error']
        table.add_row(
            "CGPA",
            f"[{cgpa_color}]{cgpa:.2f}[/]",
            "Minimum: 2.0"
        )
        
        # Probation status
        if report['on_probation']:
            table.add_row(
                "Status",
                f"[{COLORS['error']}]⚠️ PROBATION[/]",
                "CGPA below 2.0"
            )
        
        # Missing courses
        missing = report['missing_courses']
        total_missing = sum(len(courses) for courses in missing.values())
        
        if total_missing > 0:
            for category, courses in missing.items():
                if courses:
                    category_name = category.replace('_', ' ').title()
                    table.add_row(
                        f"Missing {category_name}",
                        f"[{COLORS['error']}]{len(courses)} courses[/]",
                        ", ".join(courses[:3]) + ("..." if len(courses) > 3 else "")
                    )
        else:
            table.add_row(
                "Course Requirements",
                f"[{COLORS['success']}]✓ Complete[/]",
                "All required courses completed"
            )
        
        # Graduation status
        if report['can_graduate']:
            table.add_row(
                "Graduation",
                f"[{COLORS['success']}]✓ ELIGIBLE[/]",
                "All requirements met!"
            )
        else:
            table.add_row(
                "Graduation",
                f"[{COLORS['error']}]✗ NOT ELIGIBLE[/]",
                "See issues above"
            )
        
        return table
    
    def format_missing_courses_panel(self, report: Dict) -> Panel:
        """Create a panel showing missing courses in detail"""
        missing = report['missing_courses']
        
        content = []
        
        for category, courses in missing.items():
            if courses:
                category_name = category.replace('_', ' ').title()
                content.append(f"[bold {COLORS['dark']}]{category_name}:[/]")
                for course in courses:
                    content.append(f"  • {course}")
                content.append("")
        
        if not content:
            content.append(f"[bold {COLORS['success']}]✓ No missing courses! All requirements met.[/]")
        
        return Panel(
            "\n".join(content),
            title="[bold]Missing Requirements[/]",
            border_style=COLORS['warning'] if content else COLORS['success'],
            padding=(1, 2)
        )


if __name__ == "__main__":
    # Test the reporter
    import sys
    from parser import TranscriptParser
    from calculator import Calculator
    
    if len(sys.argv) >= 3:
        transcript_path = sys.argv[1]
        knowledge_path = sys.argv[2]
        program_name = sys.argv[3] if len(sys.argv) > 3 else "Computer Science & Engineering"
        
        # Parse transcript
        parser = TranscriptParser(transcript_path)
        parser.process_retakes()
        
        # Calculate
        calc = Calculator(parser.processed_records)
        
        # Parse program requirements
        prog_req = ProgramRequirements(knowledge_path)
        
        # Generate report
        reporter = DeficiencyReporter(calc, parser, prog_req, program_name)
        report = reporter.generate_report()
        
        # Display
        console.print(reporter.format_report_table(report))
        console.print()
        console.print(reporter.format_missing_courses_panel(report))
