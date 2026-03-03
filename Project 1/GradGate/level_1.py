#!/usr/bin/env python3
"""Level 1: Credit Tally Engine — standalone CLI."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.transcript import load_transcript, validate_grades, validate_courses, resolve_retakes
from engine.credits import tally_credits
from engine.program_loader import load_program, load_nsu_course_list, load_equivalences, resolve_program_name
from display.formatter import print_credit_tally

DEFAULT_KNOWLEDGE = str(Path(__file__).resolve().parent / "data" / "program_knowledge.md")


def main():
    parser = argparse.ArgumentParser(
        description="GradGate Level 1: Credit Tally Engine",
        epilog="Example: python level_1.py data/transcript.csv CSE data/program_knowledge.md",
    )
    parser.add_argument("transcript", help="Path to transcript CSV file")
    parser.add_argument("program_name", nargs="?", default=None,
                        help="Program alias (CSE, BBA, EEE, etc.)")
    parser.add_argument("program_knowledge", nargs="?", default=DEFAULT_KNOWLEDGE,
                        help="Path to program knowledge markdown file")
    parser.add_argument("-o", "--output", help="Save output to file")
    args = parser.parse_args()

    records = load_transcript(args.transcript)

    grade_errors = validate_grades(records)
    if grade_errors:
        for err in grade_errors:
            print(f"Error: {err}")
        sys.exit(1)

    knowledge_path = args.program_knowledge
    equivalences = {}
    nsu_courses = set()
    program_info = None

    if not Path(knowledge_path).exists():
        if args.program_name:
            print(f"Warning: Knowledge file '{knowledge_path}' not found. Running without program data.")
    elif Path(knowledge_path).exists():
        nsu_courses = load_nsu_course_list(knowledge_path)
        equivalences = load_equivalences(knowledge_path)

        non_nsu = validate_courses(records, nsu_courses)
        if non_nsu:
            print(f"\nWarning: Non-NSU courses detected: {', '.join(non_nsu)}")
            for code in non_nsu:
                answer = input(f"  Is '{code}' a transfer credit? (y/n): ").strip().lower()
                if answer == "y":
                    for r in records:
                        if r.course_code == code:
                            r.grade = "T"
                            r.status = "Transfer"

        if args.program_name:
            program_info = load_program(knowledge_path, args.program_name)
            if not program_info:
                print(f"Error: Program '{args.program_name}' not found in {knowledge_path}")
                sys.exit(1)

    resolve_retakes(records, equivalences)

    summary = tally_credits(records, program_info, equivalences=equivalences)

    if args.output:
        try:
            from rich.console import Console
            file_console = Console(file=open(args.output, "w"), force_terminal=True)
            from display.formatter import console as display_console
            original = display_console
            import display.formatter
            display.formatter.console = file_console
            print_credit_tally(summary, args.transcript,
                               program_info.full_name if program_info else args.program_name)
            display.formatter.console = original
            print(f"Report saved to {args.output}")
        except OSError as e:
            print(f"Error: Cannot write to '{args.output}': {e}")
            sys.exit(1)
    else:
        print_credit_tally(summary, args.transcript,
                           program_info.full_name if program_info else args.program_name)


if __name__ == "__main__":
    main()
