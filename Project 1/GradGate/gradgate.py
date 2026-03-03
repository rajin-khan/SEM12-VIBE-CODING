#!/usr/bin/env python3
"""GradGate — Unified CLI entry point for the NSU Graduation Audit Engine."""

import argparse
import os
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
    print_credit_tally, print_semester_progression, print_audit_report,
    print_grade_distribution, print_banner, console,
)

DEFAULT_KNOWLEDGE = str(Path(__file__).resolve().parent / "data" / "program_knowledge.md")
TESTS_DIR = str(Path(__file__).resolve().parent / "tests")


# ─── Interactive menu ────────────────────────────────────────────────

def _prompt_choice(prompt_text: str, choices: list[str],
                   default: str | None = None) -> str:
    """Display numbered choices and return the selected value."""
    console.print()
    console.print(f"[bold]{prompt_text}[/]")
    for i, c in enumerate(choices, 1):
        marker = " [dim](default)[/]" if c == default else ""
        console.print(f"  [cyan]{i}.[/] {c}{marker}")
    while True:
        raw = input("  Enter choice (number or value): ").strip()
        if not raw and default:
            return default
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return choices[int(raw) - 1]
        upper = raw.upper()
        for c in choices:
            if c.upper() == upper or c.upper().startswith(upper):
                return c
        console.print(f"  [red]Invalid choice.[/] Pick 1–{len(choices)} or type a value.")


def _prompt_input(prompt_text: str, default: str = "") -> str:
    """Simple text prompt with an optional default."""
    suffix = f" [dim](default: {default})[/]" if default else ""
    console.print(f"\n[bold]{prompt_text}[/]{suffix}")
    raw = input("  > ").strip()
    return raw if raw else default


def _list_test_csvs() -> list[str]:
    """Return sorted list of CSV files in the tests/ directory."""
    if not Path(TESTS_DIR).is_dir():
        return []
    return sorted(f for f in os.listdir(TESTS_DIR) if f.endswith(".csv"))


def _browse_transcript() -> str:
    """Let the user pick a transcript file interactively."""
    console.print("\n[bold]Select transcript source:[/]")
    console.print("  [cyan]1.[/] Enter a file path manually")
    console.print("  [cyan]2.[/] Use the sample transcript  [dim](data/transcript.csv)[/]")
    console.print("  [cyan]3.[/] Browse test cases")

    raw = input("  Enter choice: ").strip()

    if raw == "2":
        sample = str(Path(__file__).resolve().parent / "data" / "transcript.csv")
        if Path(sample).exists():
            return sample
        console.print("[yellow]  Sample not found, enter path manually.[/]")
        return _prompt_input("Transcript CSV path")

    if raw == "3":
        csvs = _list_test_csvs()
        if not csvs:
            console.print("[yellow]  No test CSVs found.[/]")
            return _prompt_input("Transcript CSV path")

        page_size = 15
        page = 0
        total_pages = (len(csvs) + page_size - 1) // page_size
        while True:
            start = page * page_size
            end = min(start + page_size, len(csvs))
            console.print(f"\n[bold]Test cases (page {page + 1}/{total_pages}):[/]")
            for i, name in enumerate(csvs[start:end], start + 1):
                console.print(f"  [cyan]{i:3d}.[/] {name}")
            nav = []
            if page > 0:
                nav.append("[dim]p=prev[/]")
            if end < len(csvs):
                nav.append("[dim]n=next[/]")
            nav.append("[dim]q=cancel[/]")
            console.print(f"  {' | '.join(nav)}")
            pick = input("  Enter number or nav: ").strip().lower()
            if pick == "n" and end < len(csvs):
                page += 1
            elif pick == "p" and page > 0:
                page -= 1
            elif pick == "q":
                return _prompt_input("Transcript CSV path")
            elif pick.isdigit() and 1 <= int(pick) <= len(csvs):
                return str(Path(TESTS_DIR) / csvs[int(pick) - 1])
            else:
                console.print("  [red]Invalid. Try again.[/]")
        return _prompt_input("Transcript CSV path")

    return _prompt_input("Transcript CSV path")


# ─── Test case catalog ────────────────────────────────────────────────

_TC_CATALOG: list[tuple[str, str, list[tuple[str, str, str, str]]]] = [
    # (category_name, emoji, [(filename, description, program, best_level)])
    ("Happy Path — All Pass", "🎓", [
        ("tc01_cse_all_pass.csv",  "CSE all courses passed",  "CSE", "3"),
        ("tc02_bba_all_pass.csv",  "BBA all courses passed",  "BBA", "3"),
        ("tc03_eee_all_pass.csv",  "EEE all courses passed",  "EEE", "3"),
        ("tc04_ete_all_pass.csv",  "ETE all courses passed",  "ETE", "3"),
        ("tc05_cee_all_pass.csv",  "CEE all courses passed",  "CEE", "3"),
        ("tc06_env_all_pass.csv",  "ENV all courses passed",  "ENV", "3"),
        ("tc07_eng_all_pass.csv",  "ENG all courses passed",  "ENG", "3"),
        ("tc08_eco_all_pass.csv",  "ECO all courses passed",  "ECO", "3"),
    ]),
    ("Extra Credits", "📦", [
        ("tc09_cse_extra_credits.csv", "CSE beyond credit requirement", "CSE", "1"),
        ("tc10_bba_extra_credits.csv", "BBA extra credits",             "BBA", "1"),
    ]),
    ("F / I / W Grades", "📉", [
        ("tc11_cse_with_F.csv",     "CSE with F grades",                "CSE", "1"),
        ("tc12_bba_with_F.csv",     "BBA with F grades",                "BBA", "1"),
        ("tc13_cse_with_I.csv",     "CSE with Incomplete grades",       "CSE", "1"),
        ("tc14_bba_with_I.csv",     "BBA with Incomplete grades",       "BBA", "1"),
        ("tc15_cse_with_W.csv",     "CSE with Withdrawals",             "CSE", "1"),
        ("tc16_bba_with_W.csv",     "BBA with Withdrawals",             "BBA", "1"),
        ("tc17_cse_mixed_FIW.csv",  "CSE mixed F + I + W grades",       "CSE", "1"),
        ("tc18_bba_mixed_FIW.csv",  "BBA mixed F + I + W grades",       "BBA", "1"),
    ]),
    ("Waivers", "🔓", [
        ("tc19_no_waivers.csv",      "No waivers applied",              "CSE", "2"),
        ("tc20_eng102_waived.csv",   "ENG102 waived only",              "CSE", "2"),
        ("tc21_mat112_waived.csv",   "MAT112 waived only",              "CSE", "2"),
        ("tc22_both_waived.csv",     "Both ENG102 + MAT112 waived",     "CSE", "2"),
    ]),
    ("Retakes", "🔄", [
        ("tc23_retake_pass.csv",         "Failed then passed on retake",                 "CSE", "1"),
        ("tc24_retake_still_fail.csv",   "Retook but still failed",                      "CSE", "1"),
        ("tc25_multiple_retakes.csv",    "Same course retaken 3+ times",                 "CSE", "1"),
        ("tc52_retake_worse_grade.csv",  "Retake got worse grade — best still counts",   "CSE", "1"),
        ("tc53_retake_ineligible.csv",   "Retake of B+ or above — NSU policy violation", "CSE", "1"),
    ]),
    ("Transfer / Invalid", "🚫", [
        ("tc26_transfer_T_grade.csv", "T grade (transfer credit)",      "CSE", "1"),
        ("tc27_non_nsu_courses.csv",  "Non-NSU course codes",           "CSE", "1"),
        ("tc28_invalid_grades.csv",   "Invalid grade values (errors)",  "CSE", "1"),
        ("tc29_empty_transcript.csv", "Completely empty transcript",    "CSE", "1"),
    ]),
    ("Probation", "⚠️", [
        ("tc30_probation_P1.csv", "First semester below 2.0 — P1",         "CSE", "2"),
        ("tc31_probation_P2.csv", "Two consecutive semesters below — P2",  "CSE", "2"),
        ("tc32_dismissal.csv",    "Three consecutive — academic dismissal", "CSE", "2"),
    ]),
    ("BBA Concentration", "🏢", [
        ("tc33_bba_concentration_FIN.csv",  "BBA with FIN concentration (auto-detected)", "BBA", "3"),
        ("tc34_bba_undeclared.csv",         "BBA without clear concentration",            "BBA", "3"),
        ("tc50_bba_wrong_concentration.csv","BBA FIN courses but forced MKT",             "BBA", "3"),
    ]),
    ("Prerequisites", "🔗", [
        ("tc35_prereq_violation.csv",         "CSE prereq chain violated",                "CSE", "3"),
        ("tc45_credit_prereq_violation.csv",  "CSE299 taken with < 60 credits",           "CSE", "3"),
        ("tc46_corequisite_same_semester.csv","Lab + lecture same semester (OK)",           "CSE", "3"),
        ("tc47_eee_prereq_violation.csv",     "EEE prereq chain violated",                "EEE", "3"),
        ("tc48_bba_prereq_violation.csv",     "BBA prereq chain violated",                "BBA", "3"),
    ]),
    ("Edge Cases", "🔬", [
        ("tc36_zero_credit_labs_only.csv", "Only 0-credit labs",             "CSE", "1"),
        ("tc37_high_cgpa_4.0.csv",         "Perfect 4.0 CGPA",              "CSE", "2"),
        ("tc38_borderline_2.0.csv",        "Borderline 2.0 CGPA",           "CSE", "2"),
    ]),
    ("Error / Robustness", "🛡️", [
        ("tc39_malformed_columns.csv",       "Wrong CSV column names",        "CSE", "1"),
        ("tc40_empty_fields.csv",            "Empty Course_Code / Grade",     "CSE", "1"),
        ("tc41_negative_credits.csv",        "Negative credit values",        "CSE", "1"),
        ("tc42_whitespace_grades.csv",       "Whitespace in grades",          "CSE", "1"),
        ("tc43_duplicate_same_semester.csv", "Duplicate course same semester", "CSE", "1"),
        ("tc44_p_grade.csv",                 "P (Pass) grade handling",       "CSE", "1"),
    ]),
    ("Advanced", "🧪", [
        ("tc49_cross_program_courses.csv", "CSE student with BBA courses",    "CSE", "1"),
        ("tc51_i_grade_resolved.csv",      "I grade resolved by later retake","CSE", "1"),
    ]),
    ("Minor Programs", "📐", [
        ("tc54_cse_math_minor_complete.csv",    "Complete Math Minor (3/3 electives)",    "CSE", "3"),
        ("tc55_cse_physics_minor_complete.csv",  "Complete Physics Minor (4 req + prereqs)","CSE", "3"),
        ("tc56_cse_math_minor_partial.csv",      "Partial Math Minor (1 of 3 electives)", "CSE", "3"),
        ("tc57_cse_minor_missing_prereqs.csv",   "Minor courses but missing prereqs",     "CSE", "3"),
    ]),
]

_LEVEL_LABELS = {
    "1": "Level 1 — Credit Tally",
    "2": "Level 2 — CGPA & Probation",
    "3": "Level 3 — Full Audit",
    "all": "All Levels",
    "dist": "Grade Distribution",
}


def _run_test_case(filename: str, program: str, level: str) -> None:
    """Load a test case and run the selected analysis level."""
    tc_path = str(Path(TESTS_DIR) / filename)
    if not Path(tc_path).exists():
        console.print(f"[red]Error:[/] File '{tc_path}' not found.")
        return

    knowledge_path = DEFAULT_KNOWLEDGE
    equivalences = {}
    if Path(knowledge_path).exists():
        equivalences = load_equivalences(knowledge_path)

    records = load_transcript(tc_path)
    grade_errors = validate_grades(records)
    if grade_errors:
        for err in grade_errors:
            console.print(f"[red]Error:[/] {err}")
        return

    if level == "dist":
        resolve_retakes(records, equivalences)
        dist = compute_grade_distribution(records)
        console.print()
        console.rule(f"[bold blue]Grade Distribution — {filename}[/]")
        console.print()
        print_grade_distribution(dist, tc_path)
        return

    if not Path(knowledge_path).exists():
        console.print(f"[red]Error:[/] Knowledge file not found.")
        return

    nsu_courses = load_nsu_course_list(knowledge_path)
    program_info = load_program(knowledge_path, program)
    if not program_info:
        console.print(f"[red]Error:[/] Program '{program}' not found.")
        return

    resolve_retakes(records, equivalences)

    run_l1 = level in ("1", "all")
    run_l2 = level in ("2", "all")
    run_l3 = level in ("3", "all")

    waivers: set[str] = set()

    console.print()
    console.rule(f"[bold green]{filename} — {program} — {_LEVEL_LABELS.get(level, level)}[/]")
    console.print()

    if run_l1:
        summary = tally_credits(records, program_info, waived_courses=waivers,
                                equivalences=equivalences)
        print_credit_tally(summary, tc_path, program_info.full_name)

    if run_l2:
        snapshots = compute_semester_progression(records, waivers)
        grade_dist = compute_grade_distribution(records)
        print_semester_progression(snapshots, tc_path, waivers, grade_dist)

    if run_l3:
        minor_arg = None
        if "minor" in filename:
            if "math" in filename:
                minor_arg = "MATH"
            elif "physics" in filename:
                minor_arg = "PHYSICS"
        concentration_arg = None
        if "wrong_concentration" in filename:
            concentration_arg = "MKT"
        result = run_audit(records, program_info, waivers, equivalences,
                           minor=minor_arg, concentration=concentration_arg)
        print_audit_report(result, full_report=True)


def _test_explorer() -> None:
    """Category-based test case explorer with run capability."""
    from rich.table import Table
    from rich import box

    while True:
        console.print()
        cat_table = Table(
            box=box.ROUNDED, show_header=False, padding=(0, 2),
            border_style="magenta",
            title="[bold]Test Case Explorer[/]",
            title_style="bold white on magenta",
        )
        cat_table.add_column("  #", style="bold magenta", min_width=4)
        cat_table.add_column("Category", min_width=20)
        cat_table.add_column("Tests", justify="right", style="dim")
        for i, (name, emoji, cases) in enumerate(_TC_CATALOG, 1):
            cat_table.add_row(str(i), f"{emoji}  {name}", str(len(cases)))
        cat_table.add_row("a", "  Run ALL test cases (batch)", "")
        cat_table.add_row("b", "  Back to main menu", "")
        console.print(cat_table)

        pick = input("\n  Select category: ").strip().lower()

        if pick == "b":
            return

        if pick == "a":
            _batch_run_all()
            continue

        if not pick.isdigit() or not (1 <= int(pick) <= len(_TC_CATALOG)):
            console.print("  [red]Invalid. Try again.[/]")
            continue

        cat_name, emoji, cases = _TC_CATALOG[int(pick) - 1]
        _browse_category(cat_name, emoji, cases)


def _browse_category(cat_name: str, emoji: str, cases: list[tuple[str, str, str, str]]) -> None:
    """Show test cases within a category and let user pick one to run."""
    from rich.table import Table
    from rich import box

    while True:
        console.print()
        tc_table = Table(
            box=box.ROUNDED, show_header=True, padding=(0, 1),
            border_style="cyan",
            title=f"[bold]{emoji}  {cat_name}[/]",
            title_style="bold white on cyan",
            header_style="bold cyan",
        )
        tc_table.add_column("#", justify="right", min_width=3)
        tc_table.add_column("File", min_width=20)
        tc_table.add_column("Description", min_width=30)
        tc_table.add_column("Program", justify="center", min_width=5)
        tc_table.add_column("Best Level", justify="center", min_width=6)

        for i, (fname, desc, prog, lvl) in enumerate(cases, 1):
            tc_table.add_row(
                str(i), fname, desc, prog,
                _LEVEL_LABELS.get(lvl, lvl),
            )
        console.print(tc_table)

        console.print("  [dim]Enter a number to run, or[/] [bold]b[/][dim]=back[/]")
        raw = input("  > ").strip().lower()

        if raw == "b":
            return

        if not raw.isdigit() or not (1 <= int(raw) <= len(cases)):
            console.print("  [red]Invalid. Try again.[/]")
            continue

        fname, desc, prog, best_lvl = cases[int(raw) - 1]
        _pick_and_run(fname, desc, prog, best_lvl)


def _pick_and_run(filename: str, description: str, program: str, best_level: str) -> None:
    """Let user choose how to run a specific test case."""
    from rich.panel import Panel

    console.print()
    console.print(Panel(
        f"[bold]{filename}[/]\n"
        f"{description}\n"
        f"Program: [cyan]{program}[/]  |  Recommended: [green]{_LEVEL_LABELS.get(best_level, best_level)}[/]",
        title="Selected Test Case",
        border_style="green",
        expand=False,
    ))

    console.print("  [bold]How would you like to run it?[/]")
    console.print(f"  [cyan]1.[/] {_LEVEL_LABELS['1']}")
    console.print(f"  [cyan]2.[/] {_LEVEL_LABELS['2']}")
    console.print(f"  [cyan]3.[/] {_LEVEL_LABELS['3']}")
    console.print(f"  [cyan]4.[/] {_LEVEL_LABELS['all']}")
    console.print(f"  [cyan]5.[/] {_LEVEL_LABELS['dist']}")
    console.print(f"  [cyan]r.[/] Run recommended ({_LEVEL_LABELS.get(best_level, best_level)})")
    console.print(f"  [cyan]b.[/] Back")

    action = input("  > ").strip().lower()
    action_map = {"1": "1", "2": "2", "3": "3", "4": "all", "5": "dist", "r": best_level}

    if action == "b":
        return

    level = action_map.get(action)
    if not level:
        console.print("  [red]Invalid choice.[/]")
        return

    _run_test_case(filename, program, level)

    console.print()
    nxt = input("  [r]un again / [b]ack to category / [m]ain menu? ").strip().lower()
    if nxt == "r":
        _pick_and_run(filename, description, program, best_level)
    elif nxt == "m":
        return


def _batch_run_all() -> None:
    """Run every test case at its recommended level and show pass/fail summary."""
    from rich.table import Table
    from rich import box

    console.print()
    console.rule("[bold magenta]Batch Run — All Test Cases[/]")
    console.print()

    results: list[tuple[str, str, str]] = []

    for _cat_name, _emoji, cases in _TC_CATALOG:
        for fname, desc, prog, best_lvl in cases:
            tc_path = str(Path(TESTS_DIR) / fname)
            if not Path(tc_path).exists():
                results.append((fname, "MISSING", "red"))
                continue
            try:
                records = load_transcript(tc_path)
                grade_errors = validate_grades(records)
                if grade_errors:
                    results.append((fname, "GRADE ERR", "yellow"))
                    continue
                results.append((fname, "OK", "green"))
            except SystemExit:
                results.append((fname, "EXIT", "yellow"))
            except Exception as e:
                results.append((fname, f"ERR: {e}", "red"))

    summary = Table(
        box=box.ROUNDED, show_header=True, padding=(0, 1),
        border_style="magenta",
        title="[bold]Batch Results[/]",
        title_style="bold white on magenta",
        header_style="bold",
    )
    summary.add_column("#", justify="right", min_width=3)
    summary.add_column("File", min_width=25)
    summary.add_column("Status", justify="center", min_width=10)

    for i, (fname, status, color) in enumerate(results, 1):
        summary.add_row(str(i), fname, f"[{color}]{status}[/]")

    console.print(summary)

    ok = sum(1 for _, s, _ in results if s == "OK")
    console.print(f"\n  [bold]{ok}/{len(results)}[/] test files loaded successfully.")
    console.print()
    input("  Press Enter to return to explorer...")


def _run_grade_distribution() -> None:
    """Standalone grade distribution viewer."""
    transcript_path = _browse_transcript()
    if not transcript_path or not Path(transcript_path).exists():
        console.print(f"[red]Error:[/] File '{transcript_path}' not found.")
        return

    knowledge_path = DEFAULT_KNOWLEDGE
    equivalences = {}
    if Path(knowledge_path).exists():
        equivalences = load_equivalences(knowledge_path)

    records = load_transcript(transcript_path)
    grade_errors = validate_grades(records)
    if grade_errors:
        for err in grade_errors:
            console.print(f"[red]Error:[/] {err}")
        return

    resolve_retakes(records, equivalences)

    dist = compute_grade_distribution(records)
    console.print()
    console.rule("[bold blue]Grade Distribution[/]")
    console.print()
    print_grade_distribution(dist, transcript_path)


def interactive_menu() -> None:
    """Full interactive session — prompted step by step."""
    from rich.panel import Panel
    from rich.table import Table
    from rich import box

    print_banner()

    menu = Table(box=box.ROUNDED, show_header=False, padding=(0, 2),
                 border_style="cyan", title="[bold]Main Menu[/]",
                 title_style="bold white on blue")
    menu.add_column("Option", style="bold cyan", min_width=4)
    menu.add_column("Description")
    menu.add_row("1", "Run Level 1 — Credit Tally Engine")
    menu.add_row("2", "Run Level 2 — Logic Gate & Waiver Handler")
    menu.add_row("3", "Run Level 3 — Audit & Deficiency Reporter")
    menu.add_row("4", "Run Full Audit (all levels)")
    menu.add_row("5", "View Grade Distribution")
    menu.add_row("6", "Explore & Run Test Cases")
    menu.add_row("q", "Quit")
    console.print(menu)

    choice = input("\n  Select an option: ").strip().lower()
    if choice == "q":
        console.print("[dim]Goodbye![/]")
        return
    if choice == "6":
        _test_explorer()
        interactive_menu()
        return

    if choice == "5":
        _run_grade_distribution()
        console.print()
        again = input("  Run another audit? (y/n): ").strip().lower()
        if again == "y":
            console.print()
            interactive_menu()
        return

    level_map = {"1": "1", "2": "2", "3": "3", "4": "all"}
    level = level_map.get(choice)
    if not level:
        console.print("[red]Invalid option.[/]")
        return

    transcript_path = _browse_transcript()
    if not transcript_path or not Path(transcript_path).exists():
        console.print(f"[red]Error:[/] File '{transcript_path}' not found.")
        return

    program_aliases = list(PROGRAM_ALIASES.keys())
    program_labels = [f"{a} — {PROGRAM_ALIASES[a]}" for a in program_aliases]
    selected_label = _prompt_choice("Select program:", program_labels, default=program_labels[0])
    program_name = selected_label.split(" — ")[0].strip()

    knowledge_path = DEFAULT_KNOWLEDGE
    custom_kb = _prompt_input(
        "Program knowledge file path",
        default=DEFAULT_KNOWLEDGE,
    )
    if custom_kb:
        knowledge_path = custom_kb

    waivers_str: str | None = None
    concentration: str | None = None
    minor: str | None = None
    report_mode = "normal"

    if level in ("2", "3", "all"):
        waivers_str = _prompt_input(
            "Waiver courses (comma-separated, or press Enter for interactive prompt)",
            default="",
        )
        if not waivers_str:
            waivers_str = None

    if level in ("3", "all"):
        report_mode = _prompt_choice(
            "Report verbosity:", ["normal", "full"], default="normal"
        )
        if program_name == "BBA":
            conc = _prompt_input("BBA concentration (FIN/MKT/ACT/HRM/MIS/SCM, or Enter to auto-detect)")
            concentration = conc if conc else None

        if program_name in ("CSE", "EEE", "ETE", "CEE"):
            minor_choice = _prompt_choice(
                "Declare a minor?", ["None", "MATH", "PHYSICS"], default="None"
            )
            minor = minor_choice if minor_choice != "None" else None

    output_path = _prompt_input("Save report to file? (path or Enter to skip)")

    console.print()
    console.rule("[bold green]Running GradGate...[/]")
    console.print()

    records = load_transcript(transcript_path)
    grade_errors = validate_grades(records)
    if grade_errors:
        for err in grade_errors:
            console.print(f"[red]Error:[/] {err}")
        return

    if not Path(knowledge_path).exists():
        console.print(f"[red]Error:[/] Knowledge file '{knowledge_path}' not found.")
        return

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

    program_info = load_program(knowledge_path, program_name)
    if not program_info:
        console.print(f"[red]Error:[/] Program '{program_name}' not found.")
        return

    resolve_retakes(records, equivalences)

    run_l1 = level in ("1", "all")
    run_l2 = level in ("2", "all")
    run_l3 = level in ("3", "all")

    waivers: set[str] = set()
    if run_l2 or run_l3:
        waivers = get_waivers(
            program_info,
            cli_waivers=waivers_str,
            interactive=(waivers_str is None),
        )

    output_file = None
    original_console = None
    if output_path:
        try:
            import display.formatter
            original_console = display.formatter.console
            from rich.console import Console as RichConsole
            output_file = open(output_path, "w")
            display.formatter.console = RichConsole(file=output_file, force_terminal=True)
        except OSError as e:
            console.print(f"[red]Error:[/] Cannot write to '{output_path}': {e}")
            return

    try:
        if run_l1:
            console.rule("[bold blue]Level 1: Credit Tally Engine[/]")
            summary = tally_credits(records, program_info, waived_courses=waivers,
                                    equivalences=equivalences)
            print_credit_tally(summary, transcript_path, program_info.full_name)

        if run_l2:
            console.rule("[bold blue]Level 2: Logic Gate & Waiver Handler[/]")
            snapshots = compute_semester_progression(records, waivers)
            grade_dist = compute_grade_distribution(records)
            print_semester_progression(snapshots, transcript_path, waivers, grade_dist)

        if run_l3:
            console.rule("[bold blue]Level 3: Audit & Deficiency Reporter[/]")
            result = run_audit(records, program_info, waivers, equivalences,
                               concentration=concentration, minor=minor)
            full = report_mode == "full"
            print_audit_report(result, full_report=full)
    finally:
        if output_file:
            output_file.close()
            import display.formatter
            display.formatter.console = original_console
            console.print(f"\n[green]Report saved to {output_path}[/]")

    console.print()
    again = input("  Run another audit? (y/n): ").strip().lower()
    if again == "y":
        console.print()
        interactive_menu()


# ─── CLI mode ────────────────────────────────────────────────────────

def cli_mode() -> None:
    """Standard argparse-driven CLI."""
    parser = argparse.ArgumentParser(
        description="GradGate — NSU Graduation Audit Engine",
        epilog=(
            "Examples:\n"
            "  python gradgate.py data/transcript.csv CSE data/program_knowledge.md\n"
            "  python gradgate.py data/transcript.csv BBA data/program_knowledge.md --level 2 --waivers ENG102,BUS112\n"
            "  python gradgate.py data/transcript.csv CSE --level all --report full\n"
            "\nRun with no arguments for interactive mode.\n"
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

    print_banner()

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

    waivers: set[str] = set()
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


def main() -> None:
    has_positional = any(
        not a.startswith("-") for a in sys.argv[1:]
    )
    if len(sys.argv) == 1 or (not has_positional and "--help" not in sys.argv
                               and "-h" not in sys.argv):
        interactive_menu()
    else:
        cli_mode()


if __name__ == "__main__":
    main()
