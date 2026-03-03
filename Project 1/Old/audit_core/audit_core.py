#!/usr/bin/env python3
"""
Audit Core - NSU Transcript Auditor
Level 1: Credit Tally | Level 2: CGPA + Waivers | Level 3: Deficiency Report

Inspired by Claude Code's Clawd mascot - featuring 8-bit style NSU Graduation Auditor
"""

import argparse
import sys
from pathlib import Path
from typing import List, Set

from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.text import Text

from mascot import mascot
from utils.parser import TranscriptParser
from utils.calculator import Calculator, NSUGradingScale
from utils.reporter import DeficiencyReporter, ProgramRequirements

console = Console()

# Bright Colors
BRIGHT_BLUE = "#00BFFF"  # Deep Sky Blue - very bright
VERMILLION = "#FF4500"   # Orange Red - bright vermillion


class AuditCore:
    def __init__(self, transcript_path: str, program_name: str, knowledge_path: str):
        self.transcript_path = Path(transcript_path)
        self.program_name = program_name
        self.knowledge_path = Path(knowledge_path)
        self.waivers: List[str] = []
        
        # Will be initialized in load()
        self.parser = None
        self.calc = None
        self.prog_req = None
        self.reporter = None
    
    def load(self):
        """Load all data sources"""
        if not self.transcript_path.exists():
            raise FileNotFoundError(f"Transcript not found: {self.transcript_path}")
        if not self.knowledge_path.exists():
            raise FileNotFoundError(f"Knowledge base not found: {self.knowledge_path}")
        
        mascot.show_thinking()
        
        self.parser = TranscriptParser(str(self.transcript_path))
        self.parser.process_retakes()
        self.prog_req = ProgramRequirements(str(self.knowledge_path))
        self.calc = Calculator(self.parser.processed_records)
        self.reporter = DeficiencyReporter(self.calc, self.parser, self.prog_req, self.program_name)
    
    def run_level_1(self) -> dict:
        """
        Level 1: Credit Tally Engine
        - Calculate total valid credits
        - Filter F grades, W withdrawals, 0-credit labs
        """
        console.print(f"[bold {BRIGHT_BLUE}]━━━ Level 1: Credit Tally ━━━[/]\n")
        
        valid_credits = self.calc.calculate_valid_credits()
        required_credits = self.prog_req.get_required_credits(self.program_name)
        total_attempted = self.calc.get_credits_by_category()
        
        # Calculate completion percentage
        pct = (valid_credits / required_credits * 100) if required_credits > 0 else 0
        
        # Display results with NSU colors
        status = "✓" if valid_credits >= required_credits else "✗"
        color = f"#{VERMILLION.replace('#', '')}" if valid_credits >= required_credits else "red"
        
        console.print(f"[{color}]{status}[/{color}] Valid Credits: {valid_credits}/{required_credits} ({pct:.1f}%)")
        console.print(f"   Completed: {total_attempted['valid_completed']} | Failed: {total_attempted['failed']} | Withdrawn: {total_attempted['withdrawn']}")
        
        if total_attempted['zero_credit_courses'] > 0:
            console.print(f"   0-credit labs: {total_attempted['zero_credit_courses']} (excluded)")
        
        console.print()
        
        return {
            'valid_credits': valid_credits,
            'required_credits': required_credits,
            'percentage': pct
        }
    
    def run_level_2(self) -> dict:
        """
        Level 2: CGPA Calculator + Waiver Handler
        - Calculate weighted CGPA using NSU scale
        - Interactive waiver prompts
        """
        console.print(f"[bold {BRIGHT_BLUE}]━━━ Level 2: CGPA & Waivers ━━━[/]\n")
        
        cgpa = self.calc.calculate_cgpa()
        
        # Display CGPA
        status = "✓" if cgpa >= 2.0 else "⚠️"
        color = f"#{VERMILLION.replace('#', '')}" if cgpa >= 2.0 else "yellow"
        probation = " (Probation)" if cgpa < 2.0 else ""
        
        console.print(f"[{color}]{status}[/{color}] CGPA: {cgpa:.2f}{probation}")
        
        # Grade distribution (compact)
        dist = self.calc.get_grade_distribution()
        if dist:
            grades_str = " ".join([f"{g}:{c}" for g, c in sorted(dist.items()) if c > 0])
            console.print(f"   Grades: {grades_str}")
        
        console.print()
        
        # Waiver handling - skip interactive prompts if waivers already provided via CLI
        required_courses = self.prog_req.get_all_required_courses(self.program_name)
        completed_courses = set(self.parser.get_course_list())
        missing_courses = required_courses - completed_courses
        
        if missing_courses and not self.waivers:
            console.print(f"[bold {VERMILLION}]Grant waivers? (y/n)[/]")
            for course in sorted(missing_courses)[:10]:  # Limit to 10 prompts
                try:
                    response = input(f"  {course}? ").strip().lower()
                    if response == 'y':
                        self.waivers.append(course)
                        console.print(f"     [bold {VERMILLION}]✓ Waiver granted[/]")
                except EOFError:
                    break
            console.print()
        elif self.waivers:
            console.print(f"[dim]Pre-set waivers: {', '.join(self.waivers)}[/]")
            console.print()
        
        return {
            'cgpa': cgpa,
            'on_probation': cgpa < 2.0,
            'waivers': self.waivers
        }
    
    def run_level_3(self) -> dict:
        """
        Level 3: Deficiency Reporter
        - Compare against program requirements
        - Identify missing courses
        - Flag probation status
        - Handle retakes
        """
        console.print(f"[bold {BRIGHT_BLUE}]━━━ Level 3: Deficiency Report ━━━[/]\n")
        
        report = self.reporter.generate_report()
        
        # Apply waivers
        if self.waivers:
            for category in report['missing_courses']:
                report['missing_courses'][category] = [
                    c for c in report['missing_courses'][category] 
                    if c not in self.waivers
                ]
        
        # Display missing courses by category
        has_missing = False
        for category, courses in report['missing_courses'].items():
            if courses:
                has_missing = True
                cat_name = category.replace('_', ' ').title()
                console.print(f"[red]✗[/] {cat_name}: {', '.join(courses[:8])}{'...' if len(courses) > 8 else ''}")
        
        if not has_missing:
            console.print(f"[bold {VERMILLION}]✓ All course requirements met[/]")
        
        # Retake summary
        retakes = self.parser.get_retake_summary()
        if retakes:
            console.print(f"\n[dim]Retakes: {len(retakes)} courses (best grade kept)[/]")
            for course, info in retakes.items():
                console.print(f"   {course}: {info['grades']} → [bold {VERMILLION}]{info['best_grade']}[/]")
        
        # Final status
        if report['can_graduate']:
            console.print(f"\n[bold {VERMILLION}]✓ ELIGIBLE FOR GRADUATION[/]")
        else:
            console.print(f"\n[bold red]✗ NOT ELIGIBLE[/]")
        
        if not report['can_graduate'] and report['issues']:
            for issue in report['issues']:
                console.print(f"   [red]• {issue}[/]")
        
        return report
    
    def run(self, level: str = 'all'):
        """Run audit levels"""
        # Show mascot at top
        mascot.show()
        
        # Header with NSU branding
        console.print(f"[bold {BRIGHT_BLUE}]Program:[/] {self.program_name}")
        console.print(f"[dim]Audit started...[/]\n")
        
        # Load data
        try:
            self.load()
            console.print(f"[dim]Loaded {len(self.parser.processed_records)} courses[/]\n")
        except Exception as e:
            console.print(f"[red]Error loading data: {e}[/]")
            sys.exit(1)
        
        # Run requested levels
        results = {}
        
        if level in ('1', 'all'):
            results['level1'] = self.run_level_1()
        
        if level in ('2', 'all'):
            results['level2'] = self.run_level_2()
        
        if level in ('3', 'all'):
            results['level3'] = self.run_level_3()
        
        # Show completion
        mascot.show_complete()
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description='NSU Audit Core - Student Transcript Auditor',
        epilog='Example: python audit_core.py transcript.csv "Computer Science & Engineering" program_knowledge.md',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('transcript', help='Path to transcript CSV file')
    parser.add_argument('program', help='Program name (e.g., "Computer Science & Engineering")')
    parser.add_argument('knowledge', help='Path to program_knowledge.md')
    parser.add_argument('--level', choices=['1', '2', '3', 'all'], default='all',
                        help='Run specific level only (default: all)')
    parser.add_argument('--waivers', nargs='*', default=[],
                        help='List of course codes to waive (non-interactive mode)')
    
    args = parser.parse_args()
    
    # Run audit
    audit = AuditCore(args.transcript, args.program, args.knowledge)
    
    # Pre-set waivers if provided
    audit.waivers = args.waivers
    
    audit.run(args.level)


if __name__ == "__main__":
    main()
