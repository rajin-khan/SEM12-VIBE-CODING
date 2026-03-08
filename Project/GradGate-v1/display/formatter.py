"""Rich-based terminal output formatting for GradGate."""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from engine.transcript import CourseRecord
from engine.credits import CreditSummary
from engine.cgpa import SemesterSnapshot
from engine.audit import AuditResult, DeficiencyReport
from engine.prerequisites import PrereqViolation

console = Console()

BANNER = r"""
   ____               _  ____       _
  / ___|_ __ __ _  __| |/ ___| __ _| |_ ___
 | |  _| '__/ _` |/ _` | |  _ / _` | __/ _ \
 | |_| | | | (_| | (_| | |_| | (_| | ||  __/
  \____|_|  \__,_|\__,_|\____|\__,_|\__\___|

  NSU Graduation Audit Engine v1.0
"""


def print_banner() -> None:
    """Print the GradGate ASCII banner."""
    console.print(BANNER, style="bold cyan")


STATUS_STYLES = {
    "Counted": ("bold green", "✓"),
    "Retake (Ignored)": ("yellow", "↻"),
    "Retake (Ineligible)": ("bold yellow", "⚠"),
    "Failed": ("bold red", "✗"),
    "Withdrawn": ("yellow", "~"),
    "Incomplete": ("yellow", "?"),
    "Waived": ("cyan", "⊘"),
    "Transfer": ("cyan", "T"),
}


def _grade_color(grade: str) -> str:
    g = grade.upper()
    if g in ("A", "A-"):
        return "bold green"
    if g in ("B+", "B", "B-"):
        return "green"
    if g in ("C+", "C"):
        return "yellow"
    if g in ("C-", "D+", "D"):
        return "red"
    if g == "F":
        return "bold red"
    if g == "W":
        return "dim yellow"
    if g == "I":
        return "dim yellow"
    if g == "T":
        return "cyan"
    return "white"


def _cgpa_color(cgpa: float) -> str:
    if cgpa >= 3.5:
        return "bold green"
    if cgpa >= 3.0:
        return "green"
    if cgpa >= 2.0:
        return "yellow"
    return "bold red"


def print_credit_tally(summary: CreditSummary, transcript_path: str,
                       program_name: Optional[str] = None) -> None:
    """Print Level 1 credit tally report."""
    title = "CREDIT TALLY REPORT"
    subtitle = f"Transcript: {transcript_path}"
    if program_name:
        subtitle += f"  |  Program: {program_name}"

    table = Table(
        title=title,
        caption=subtitle,
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        title_style="bold white on blue",
        caption_style="dim",
        padding=(0, 1),
    )

    table.add_column("Course", style="bold", min_width=10)
    table.add_column("Credits", justify="right", min_width=7)
    table.add_column("Grade", justify="center", min_width=5)
    table.add_column("Semester", min_width=12)
    table.add_column("Status", min_width=18)

    for r, category in summary.course_statuses:
        style_info = STATUS_STYLES.get(r.status, ("white", "·"))
        style, icon = style_info
        status_text = Text(f"{icon} {r.status}", style=style)
        grade_text = Text(r.grade, style=_grade_color(r.grade))
        credits_str = f"{r.credits:.1f}" if r.credits > 0 else "0"

        table.add_row(
            r.course_code,
            credits_str,
            grade_text,
            r.semester,
            status_text,
        )

    console.print()
    console.print(table)

    summary_panel = Table(box=None, show_header=False, padding=(0, 2))
    summary_panel.add_column("Label", style="bold")
    summary_panel.add_column("Value", justify="right")

    summary_panel.add_row("Total Valid Credits", f"[bold green]{summary.total_earned:.1f}[/]")
    if summary.waived_credits > 0:
        summary_panel.add_row("Waived Credits", f"[cyan]{summary.waived_credits:.1f}[/]")
    summary_panel.add_row("Credits Attempted", f"{summary.total_attempted:.1f}")

    if summary.program_credits > 0 or summary.elective_credits > 0:
        summary_panel.add_row("Program Credits", f"{summary.program_credits:.1f}")
        summary_panel.add_row("Elective Credits", f"{summary.elective_credits:.1f}")

    console.print(Panel(summary_panel, title="Summary", border_style="green", expand=False))
    console.print()


def print_semester_progression(snapshots: List[SemesterSnapshot],
                               transcript_path: str,
                               waivers: Set[str],
                               grade_distribution: Dict[str, int]) -> None:
    """Print Level 2 semester-by-semester CGPA report."""
    console.print()
    header = Text("SEMESTER-BY-SEMESTER CGPA REPORT", style="bold white on blue")
    console.print(Panel(header, expand=False))
    console.print(f"  [dim]Transcript: {transcript_path}[/]")
    if waivers:
        console.print(f"  [dim]Waivers: {', '.join(sorted(waivers))}[/]")
    console.print()

    for snap in snapshots:
        sem_table = Table(
            title=f"[bold]{snap.semester}[/]",
            box=box.SIMPLE_HEAVY,
            show_header=True,
            header_style="bold cyan",
            padding=(0, 1),
        )
        sem_table.add_column("Course", style="bold", min_width=10)
        sem_table.add_column("Credits", justify="right", min_width=7)
        sem_table.add_column("Grade", justify="center", min_width=5)
        sem_table.add_column("Status", min_width=18)

        for r in snap.courses:
            style_info = STATUS_STYLES.get(r.status, ("white", "·"))
            style, icon = style_info

            if r.course_code.upper() in waivers:
                style, icon = "cyan", "⊘"
                status_text = Text(f"{icon} Waived", style=style)
            else:
                status_text = Text(f"{icon} {r.status}", style=style)

            grade_text = Text(r.grade, style=_grade_color(r.grade))

            sem_table.add_row(
                r.course_code,
                f"{r.credits:.1f}" if r.credits > 0 else "0",
                grade_text,
                status_text,
            )

        console.print(sem_table)

        tgpa_color = _cgpa_color(snap.tgpa)
        cgpa_color = _cgpa_color(snap.cumulative_cgpa)

        info_line = (
            f"  Sem Credits: [bold]{snap.sem_credits:.1f}[/]  |  "
            f"TGPA: [{tgpa_color}]{snap.tgpa:.2f}[/]  |  "
            f"Cumulative CGPA: [{cgpa_color}]{snap.cumulative_cgpa:.2f}[/]"
        )
        console.print(info_line)

        if snap.probation_status != "NORMAL":
            prob_labels = {
                "P1": "ACADEMIC PROBATION (P1 — 1st semester below 2.00)",
                "P2": "ACADEMIC PROBATION (P2 — 2nd consecutive semester below 2.00)",
                "DISMISSAL": "ACADEMIC DISMISSAL (3+ consecutive semesters below 2.00)",
            }
            msg = prob_labels.get(snap.probation_status, "PROBATION")
            console.print(f"  [bold red]⚠ {msg}[/]")
        else:
            console.print("  [green]✓ Good Standing[/]")
        console.print()

    if snapshots:
        final = snapshots[-1]
        fc = _cgpa_color(final.cumulative_cgpa)
        console.print(Panel(
            f"[bold]Final CGPA:[/] [{fc}]{final.cumulative_cgpa:.2f}[/]  |  "
            f"[bold]GPA-Bearing Credits:[/] {final.sem_credits:.1f}  |  "
            f"[bold]Status:[/] {'[green]Good Standing[/]' if final.probation_status == 'NORMAL' else f'[red]{final.probation_status}[/]'}",
            title="Final Summary",
            border_style="bold blue",
            expand=False,
        ))

    if grade_distribution:
        console.print()
        print_grade_distribution(grade_distribution)

    console.print()


GRADE_TIERS = {
    "A-range": ("bold green", {"A", "A-"}),
    "B-range": ("green", {"B+", "B", "B-"}),
    "C-range": ("yellow", {"C+", "C", "C-"}),
    "D-range": ("red", {"D+", "D"}),
    "F": ("bold red", {"F"}),
    "Other": ("dim", {"W", "I", "T", "P"}),
}

BAR_CHAR = "█"
BAR_WIDTH = 25


def print_grade_distribution(grade_distribution: Dict[str, int],
                             transcript_path: str = "") -> None:
    """Print a rich grade distribution panel with visual bars and statistics."""
    if not grade_distribution:
        return

    total = sum(grade_distribution.values())

    table = Table(
        title="GRADE DISTRIBUTION",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        title_style="bold white on blue",
        padding=(0, 1),
    )
    table.add_column("Grade", justify="center", min_width=5)
    table.add_column("Count", justify="right", min_width=5)
    table.add_column("  %", justify="right", min_width=6)
    table.add_column("", min_width=BAR_WIDTH + 2)

    for grade, count in grade_distribution.items():
        pct = (count / total * 100) if total else 0
        filled = round(pct / 100 * BAR_WIDTH)
        bar = BAR_CHAR * filled
        color = _grade_color(grade)
        bar_text = Text(bar, style=color)
        table.add_row(
            Text(grade, style=color),
            str(count),
            f"{pct:5.1f}%",
            bar_text,
        )

    console.print(table)

    tier_counts: Dict[str, int] = {}
    for tier_name, (_, grade_set) in GRADE_TIERS.items():
        tier_counts[tier_name] = sum(
            grade_distribution.get(g, 0) for g in grade_set
        )

    stats = Table(box=None, show_header=False, padding=(0, 2))
    stats.add_column("Label", style="bold")
    stats.add_column("Value", justify="right")

    stats.add_row("Total Grades", f"[bold]{total}[/]")

    a_count = tier_counts.get("A-range", 0)
    b_count = tier_counts.get("B-range", 0)
    c_count = tier_counts.get("C-range", 0)
    d_count = tier_counts.get("D-range", 0)
    f_count = tier_counts.get("F", 0)

    if a_count:
        stats.add_row("A-range (A, A-)", f"[bold green]{a_count}[/]")
    if b_count:
        stats.add_row("B-range (B+, B, B-)", f"[green]{b_count}[/]")
    if c_count:
        stats.add_row("C-range (C+, C, C-)", f"[yellow]{c_count}[/]")
    if d_count:
        stats.add_row("D-range (D+, D)", f"[red]{d_count}[/]")
    if f_count:
        stats.add_row("Failed (F)", f"[bold red]{f_count}[/]")

    other = tier_counts.get("Other", 0)
    if other:
        stats.add_row("Other (W/I/T/P)", f"[dim]{other}[/]")

    gpa_grades = total - tier_counts.get("Other", 0)
    if gpa_grades > 0:
        pass_count = a_count + b_count + c_count + d_count
        pass_rate = pass_count / gpa_grades * 100
        color = "green" if pass_rate >= 80 else ("yellow" if pass_rate >= 60 else "red")
        stats.add_row("Pass Rate", f"[{color}]{pass_rate:.0f}%[/]")

    console.print(Panel(stats, title="Summary", border_style="green", expand=False))

    if transcript_path:
        console.print(f"  [dim]Transcript: {transcript_path}[/]")


def print_audit_report(result: AuditResult, full_report: bool = False) -> None:
    """Print Level 3 graduation audit report."""
    console.print()

    header_table = Table(box=None, show_header=False, padding=(0, 2))
    header_table.add_column("Label", style="bold")
    header_table.add_column("Value")

    header_table.add_row("Program", f"{result.program.full_name} ({result.program.alias})")
    header_table.add_row("Credits Required", str(result.credits_required))

    c_color = "green" if result.credits_completed >= result.credits_required else "red"
    credits_str = f"[{c_color}]{result.credits_completed:.1f}[/]"
    if result.waiver_bonus > 0:
        credits_str += f" [dim](earned: {result.credits_earned:.1f} + waiver: {result.waiver_bonus:.0f})[/]"
    header_table.add_row("Credits Completed", credits_str)

    cgpa_color = _cgpa_color(result.cgpa)
    header_table.add_row("CGPA", f"[{cgpa_color}]{result.cgpa:.2f}[/] (min: {result.program.min_cgpa:.2f})")

    if result.major_cgpa > 0:
        mc = _cgpa_color(result.major_cgpa)
        header_table.add_row("Major CGPA", f"[{mc}]{result.major_cgpa:.2f}[/]")

    if result.concentration_name:
        cc = _cgpa_color(result.concentration_cgpa)
        min_str = ""
        if result.program.concentration_min_cgpa > 0:
            min_str = f" (min: {result.program.concentration_min_cgpa:.2f})"
        header_table.add_row(
            f"{result.concentration_name} Concentration CGPA",
            f"[{cc}]{result.concentration_cgpa:.2f}[/]{min_str}"
        )

    if result.minor_name:
        status = "[bold green]Complete ✓[/]" if result.minor_completed else "[yellow]Incomplete[/]"
        header_table.add_row(f"Minor ({result.minor_name})", status)

    console.print(Panel(header_table, title="GRADUATION AUDIT REPORT",
                        title_align="center", border_style="bold blue"))

    if result.minor_name:
        _print_minor_status(result)

    if result.eligible:
        console.print(Panel(
            "[bold green]✓ ELIGIBLE FOR GRADUATION[/]",
            border_style="green",
            expand=False,
        ))
    else:
        reasons_text = "\n".join(f"  • {r}" for r in result.reasons)
        console.print(Panel(
            f"[bold red]✗ NOT ELIGIBLE FOR GRADUATION[/]\n\n{reasons_text}",
            border_style="red",
            expand=False,
        ))

    if result.deficiencies.has_missing or full_report:
        _print_deficiencies(result.deficiencies)

    if result.prereq_violations and full_report:
        _print_prereq_violations(result.prereq_violations)

    if result.roadmap:
        _print_roadmap(result.roadmap)

    if result.failed_courses and full_report:
        console.print(Panel(
            "[bold]Failed Courses (retake recommended):[/]\n" +
            "\n".join(f"  [red]• {c}[/]" for c in sorted(result.failed_courses)),
            title="Retake Suggestions",
            border_style="yellow",
            expand=False,
        ))

    console.print()


def _print_minor_status(result: AuditResult) -> None:
    """Print minor program status panel."""
    lines: list[str] = []

    if result.minor_courses_taken:
        lines.append("[bold]Courses Completed:[/]")
        for c in result.minor_courses_taken:
            lines.append(f"  [green]✓[/] {c}")

    if result.minor_courses_missing:
        lines.append("[bold]Courses Remaining:[/]")
        for c in result.minor_courses_missing:
            lines.append(f"  [red]✗[/] {c}")

    if result.minor_prereqs_met:
        lines.append("[green]✓ All minor prerequisites met[/]")
    else:
        lines.append("[yellow]⚠ Missing minor prerequisites:[/]")
        for c in result.minor_prereqs_missing:
            lines.append(f"  [red]✗[/] {c}")

    border = "green" if result.minor_completed else "yellow"
    console.print(Panel(
        "\n".join(lines),
        title=f"Minor in {result.minor_name}",
        title_align="center",
        border_style=border,
        expand=False,
    ))


def _print_deficiencies(deficiencies: DeficiencyReport) -> None:
    """Print missing courses by category."""
    console.print()
    console.print("[bold]DEFICIENCY REPORT[/]")
    console.print("─" * 50)

    categories = [
        ("General Education (GED)", deficiencies.missing_ged),
        ("Core Math / School Core", deficiencies.missing_math),
        ("Core Science", deficiencies.missing_science),
        ("Core Business", deficiencies.missing_business),
        ("Major Core", deficiencies.missing_major),
        ("Capstone", deficiencies.missing_capstone),
        ("Internship", deficiencies.missing_internship),
    ]

    any_printed = False
    for cat_name, missing in categories:
        if missing:
            any_printed = True
            n = len(missing)
            console.print(f"\n  [red]✗ Missing {cat_name}[/] ({n} course{'s' if n > 1 else ''})")
            for c in missing:
                console.print(f"      • {c}")

    if deficiencies.missing_trail > 0:
        any_printed = True
        console.print(f"\n  [yellow]⚠ Missing {deficiencies.missing_trail} trail/elective course(s)[/]")

    if deficiencies.missing_concentration > 0:
        any_printed = True
        console.print(f"\n  [yellow]⚠ Missing {deficiencies.missing_concentration} concentration course(s)[/]")

    if deficiencies.missing_open_elective > 0:
        any_printed = True
        console.print(f"\n  [yellow]⚠ Missing {deficiencies.missing_open_elective} open elective course(s)[/]")

    if not any_printed:
        console.print("\n  [green]✓ All course requirements satisfied[/]")

    console.print()


def _print_prereq_violations(violations: List[PrereqViolation]) -> None:
    """Print prerequisite violations."""
    if not violations:
        return

    console.print()
    table = Table(
        title="Prerequisite Violations",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold red",
    )
    table.add_column("Course", style="bold")
    table.add_column("Semester")
    table.add_column("Missing Prerequisites", style="red")
    table.add_column("Type")

    for v in violations:
        table.add_row(
            v.course,
            v.semester,
            ", ".join(v.missing_prereqs),
            v.violation_type,
        )

    console.print(table)


def _print_roadmap(steps: List[str]) -> None:
    """Print graduation roadmap."""
    if not steps:
        return

    roadmap_text = ""
    for i, step in enumerate(steps, 1):
        roadmap_text += f"  [bold]{i}.[/] {step}\n"

    console.print(Panel(
        roadmap_text.rstrip(),
        title="GRADUATION ROADMAP",
        title_align="center",
        border_style="bold cyan",
        expand=False,
    ))
