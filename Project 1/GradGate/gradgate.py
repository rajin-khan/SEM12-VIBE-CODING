#!/usr/bin/env python3
"""GradGate — Unified CLI entry point for the NSU Graduation Audit Engine."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.transcript import load_transcript, validate_grades, validate_courses, resolve_retakes
from engine.program_loader import (
    load_program, load_nsu_course_list, load_equivalences,
    resolve_program_name, PROGRAM_ALIASES,
)
from engine.waivers import get_waivers
from engine.credits import tally_credits
from engine.cgpa import compute_semester_progression, compute_grade_distribution
from engine.audit import run_audit
from display.formatter import (
    print_credit_tally, print_semester_progression, print_audit_report, console,
)

DEFAULT_KNOWLEDGE = str(Path(__file__).resolve().parent / "data" / "program_knowledge.md")

BANNER = r"""
   ____               _  ____       _
  / ___|_ __ __ _  __| |/ ___| __ _| |_ ___
 | |  _| '__/ _` |/ _` | |  _ / _` | __/ _ \
 | |_| | | | (_| | (_| | |_| | (_| | ||  __/
  \____|_|  \__,_|\__,_|\____|\__,_|\__\___|

  NSU Graduation Audit Engine v1.0
"""


def main():
    parser = argparse.ArgumentParser(
        description="GradGate — NSU Graduation Audit Engine",
        epilog=(
            "Examples:\n"
            "  python gradgate.py data/transcript.csv CSE data/program_knowledge.md\n"
            "  python gradgate.py data/transcript.csv BBA data/program_knowledge.md --level 2 --waivers ENG102,BUS112\n"
            "  python gradgate.py data/transcript.csv CSE --level all --report full\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("transcript", help="Path to transcript CSV file")
    parser.add_argument("program_name",
                        help=f"Program alias ({', '.join(PROGRAM_ALIASES.keys())})")
    parser.add_argument("program_knowledge", nargs="?", default=DEFAULT_KNOWLEDGE,
                        help="Path to program knowledge markdown file")
    parser.add_argument("--level", choices=["1", "2", "3", "all"], default="all",
                        help="Which level(s) to run (default: all)")
    parser.add_argument("--waivers", default=None,
                        help="Comma-separated course codes to waive (e.g., ENG102,MAT112)")
    parser.add_argument("--report", choices=["normal", "full"], default="normal",
                        help="Report verbosity for Level 3 (default: normal)")
    parser.add_argument("--concentration", default=None,
                        help="BBA concentration alias (e.g., FIN, MKT, ACT)")
    parser.add_argument("--minor", default=None, choices=["MATH", "PHYSICS"],
                        help="Declare a minor (MATH or PHYSICS)")
    parser.add_argument("-o", "--output", help="Save output to file")
    args = parser.parse_args()

    console.print(BANNER, style="bold cyan")

    records = load_transcript(args.transcript)

    grade_errors = validate_grades(records)
    if grade_errors:
        for err in grade_errors:
            console.print(f"[red]Error:[/] {err}")
        sys.exit(1)

    knowledge_path = args.program_knowledge
    if not Path(knowledge_path).exists():
        console.print(f"[red]Error:[/] Knowledge file '{knowledge_path}' not found.")
        sys.exit(1)

    nsu_courses = load_nsu_course_list(knowledge_path)
    equivalences = load_equivalences(knowledge_path)

    non_nsu = validate_courses(records, nsu_courses)
    if non_nsu:
        console.print(f"\n[yellow]Warning:[/] Non-NSU courses detected: {', '.join(non_nsu)}")
        for code in non_nsu:
            answer = input(f"  Is '{code}' a transfer credit? (y/n): ").strip().lower()
            if answer == "y":
                for r in records:
                    if r.course_code == code:
                        r.grade = "T"
                        r.status = "Transfer"

    program_info = load_program(knowledge_path, args.program_name)
    if not program_info:
        console.print(f"[red]Error:[/] Program '{args.program_name}' not found.")
        console.print(f"Available programs: {', '.join(PROGRAM_ALIASES.keys())}")
        sys.exit(1)

    resolve_retakes(records, equivalences)

    run_l1 = args.level in ("1", "all")
    run_l2 = args.level in ("2", "all")
    run_l3 = args.level in ("3", "all")

    waivers = set()
    if run_l2 or run_l3:
        waivers = get_waivers(
            program_info,
            cli_waivers=args.waivers,
            interactive=(args.waivers is None),
        )

    output_file = None
    original_console = None
    if args.output:
        try:
            import display.formatter
            original_console = display.formatter.console
            from rich.console import Console as RichConsole
            output_file = open(args.output, "w")
            display.formatter.console = RichConsole(file=output_file, force_terminal=True)
            console_ref = display.formatter.console
        except OSError as e:
            console.print(f"[red]Error:[/] Cannot write to '{args.output}': {e}")
            sys.exit(1)
    else:
        console_ref = console

    try:
        if run_l1:
            console_ref.rule("[bold blue]Level 1: Credit Tally Engine[/]")
            summary = tally_credits(records, program_info, waived_courses=waivers,
                                    equivalences=equivalences)
            print_credit_tally(summary, args.transcript, program_info.full_name)

        if run_l2:
            console_ref.rule("[bold blue]Level 2: Logic Gate & Waiver Handler[/]")
            snapshots = compute_semester_progression(records, waivers)
            grade_dist = compute_grade_distribution(records)
            print_semester_progression(snapshots, args.transcript, waivers, grade_dist)

        if run_l3:
            console_ref.rule("[bold blue]Level 3: Audit & Deficiency Reporter[/]")
            result = run_audit(records, program_info, waivers, equivalences,
                               concentration=args.concentration,
                               minor=args.minor)
            full = args.report == "full"
            print_audit_report(result, full_report=full)

    finally:
        if output_file:
            output_file.close()
            import display.formatter
            display.formatter.console = original_console
            print(f"Report saved to {args.output}")


if __name__ == "__main__":
    main()
