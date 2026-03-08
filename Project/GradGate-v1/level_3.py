#!/usr/bin/env python3
"""Level 3: Audit & Deficiency Reporter — standalone CLI."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.transcript import load_transcript, validate_grades, resolve_retakes
from engine.program_loader import load_program, load_equivalences
from engine.waivers import get_waivers
from engine.audit import run_audit
from display.formatter import print_audit_report, print_banner

DEFAULT_KNOWLEDGE = str(Path(__file__).resolve().parent / "data" / "program_knowledge.md")


def main():
    parser = argparse.ArgumentParser(
        description="GradGate Level 3: Audit & Deficiency Reporter",
        epilog="Example: python level_3.py data/transcript.csv CSE data/program_knowledge.md",
    )
    parser.add_argument("transcript", help="Path to transcript CSV file")
    parser.add_argument("program_name", default="CSE",
                        help="Program alias (CSE, BBA, EEE, etc.)")
    parser.add_argument("program_knowledge", nargs="?", default=DEFAULT_KNOWLEDGE,
                        help="Path to program knowledge markdown file")
    parser.add_argument("--waivers", default=None,
                        help="Comma-separated course codes to waive")
    parser.add_argument("--report", choices=["normal", "full"], default="normal",
                        help="Report verbosity (default: normal)")
    parser.add_argument("--concentration", default=None,
                        help="BBA concentration alias (e.g., FIN, MKT, ACT)")
    parser.add_argument("--minor", default=None, choices=["MATH", "PHYSICS"],
                        help="Declare a minor (MATH or PHYSICS)")
    parser.add_argument("-o", "--output", help="Save output to file")
    args = parser.parse_args()

    print_banner()

    records = load_transcript(args.transcript)

    grade_errors = validate_grades(records)
    if grade_errors:
        for err in grade_errors:
            print(f"Error: {err}")
        sys.exit(1)

    knowledge_path = args.program_knowledge
    if not Path(knowledge_path).exists():
        print(f"Error: Knowledge file '{knowledge_path}' not found.")
        sys.exit(1)

    equivalences = load_equivalences(knowledge_path)
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

    result = run_audit(records, program_info, waivers, equivalences,
                       concentration=args.concentration,
                       minor=args.minor)

    full = args.report == "full"

    if args.output:
        try:
            from rich.console import Console
            file_console = Console(file=open(args.output, "w"), force_terminal=True)
            import display.formatter
            original = display.formatter.console
            display.formatter.console = file_console
            print_audit_report(result, full_report=full)
            display.formatter.console = original
            print(f"Report saved to {args.output}")
        except OSError as e:
            print(f"Error: Cannot write to '{args.output}': {e}")
            sys.exit(1)
    else:
        print_audit_report(result, full_report=full)


if __name__ == "__main__":
    main()
