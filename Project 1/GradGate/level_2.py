#!/usr/bin/env python3
"""Level 2: Logic Gate & Waiver Handler — standalone CLI."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.transcript import load_transcript, validate_grades, validate_courses, resolve_retakes
from engine.program_loader import load_program, load_nsu_course_list, load_equivalences, resolve_program_name
from engine.waivers import get_waivers
from engine.cgpa import compute_semester_progression, compute_grade_distribution
from display.formatter import print_semester_progression

DEFAULT_KNOWLEDGE = str(Path(__file__).resolve().parent / "data" / "program_knowledge.md")


def main():
    parser = argparse.ArgumentParser(
        description="GradGate Level 2: Logic Gate & Waiver Handler",
        epilog="Example: python level_2.py data/transcript.csv CSE data/program_knowledge.md --waivers ENG102,MAT112",
    )
    parser.add_argument("transcript", help="Path to transcript CSV file")
    parser.add_argument("program_name", nargs="?", default="CSE",
                        help="Program alias (CSE, BBA, EEE, etc.)")
    parser.add_argument("program_knowledge", nargs="?", default=DEFAULT_KNOWLEDGE,
                        help="Path to program knowledge markdown file")
    parser.add_argument("--waivers", default=None,
                        help="Comma-separated course codes to waive (e.g., ENG102,MAT112)")
    args = parser.parse_args()

    records = load_transcript(args.transcript)

    grade_errors = validate_grades(records)
    if grade_errors:
        for err in grade_errors:
            print(f"Error: {err}")
        sys.exit(1)

    knowledge_path = args.program_knowledge
    equivalences = {}
    program_info = None

    if not Path(knowledge_path).exists():
        print(f"Warning: Knowledge file '{knowledge_path}' not found. Running without program data.")
    else:
        nsu_courses = load_nsu_course_list(knowledge_path)
        equivalences = load_equivalences(knowledge_path)

        non_nsu = validate_courses(records, nsu_courses)
        if non_nsu:
            print(f"\nWarning: Non-NSU courses detected: {', '.join(non_nsu)}")

        program_info = load_program(knowledge_path, args.program_name)
        if not program_info:
            print(f"Error: Program '{args.program_name}' not found in {knowledge_path}")
            sys.exit(1)

    resolve_retakes(records, equivalences)

    waivers = get_waivers(
        program_info,
        cli_waivers=args.waivers,
        interactive=(args.waivers is None),
    )

    snapshots = compute_semester_progression(records, waivers)
    grade_dist = compute_grade_distribution(records)

    print_semester_progression(snapshots, args.transcript, waivers, grade_dist)


if __name__ == "__main__":
    main()
