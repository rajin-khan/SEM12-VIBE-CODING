#!/usr/bin/env python3
"""GradGate — Unified CLI entry point for the NSU Graduation Audit Engine."""

import argparse
import os
import sys
from pathlib import Path

from rich.table import Table

CLI_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CLI_DIR.parent

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(CLI_DIR))

from auth_session import (
    fetch_history,
    get_current_user_email,
    print_history_table,
    save_local_audit,
    sign_in_with_google,
    sign_out,
    submit_reviewed_audit,
    submit_scanned_audit,
)
from display.formatter import (
    console,
    print_audit_report,
    print_banner,
    print_credit_tally,
    print_grade_distribution,
    print_semester_progression,
)
from engine.audit import AuditResult, DeficiencyReport, run_audit
from engine.cgpa import SemesterSnapshot, compute_grade_distribution, compute_semester_progression
from engine.credits import CreditSummary, tally_credits
from engine.program_loader import (
    ProgramInfo,
    PROGRAM_ALIASES,
    load_equivalences,
    load_nsu_course_list,
    load_program,
)
from engine.prerequisites import PrereqViolation
from engine.transcript import CourseRecord, load_transcript, resolve_retakes, validate_courses, validate_grades
from engine.waivers import get_waivers

DEFAULT_KNOWLEDGE = str(PROJECT_ROOT / "data" / "curriculum" / "catalog.json")
TESTS_DIR = str(PROJECT_ROOT / "tests")
SCANNED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".bmp",
    ".webp",
    ".heic",
    ".heif",
    ".gif",
}


# ─── Interactive menu ────────────────────────────────────────────────


def _prompt_choice(prompt_text: str, choices: list[str], default: str | None = None) -> str:
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


def _fixture_label(filename: str) -> str:
    return "legacy" if filename.startswith("tc") else "canonical"


def _is_scanned_document(path: str) -> bool:
    return Path(path).suffix.lower() in SCANNED_EXTENSIONS


def _redirect_formatter_console(output_path: str):
    import display.formatter
    from rich.console import Console as RichConsole

    output_file = open(output_path, "w")
    original_console = display.formatter.console
    display.formatter.console = RichConsole(file=output_file, force_terminal=True)
    return output_file, original_console


def _restore_formatter_console(output_file, original_console, output_path: str) -> None:
    output_file.close()
    import display.formatter

    display.formatter.console = original_console
    console.print(f"\n[green]Report saved to {output_path}[/]")


def _browse_transcript() -> str:
    """Let the user pick a transcript file interactively."""
    console.print("\n[bold]Select transcript source:[/]")
    console.print("  [cyan]1.[/] Enter a file path manually [dim](CSV, PDF, PNG, JPG, TIFF, BMP, WEBP, HEIC, GIF)[/]")
    console.print("  [cyan]2.[/] Use the sample transcript  [dim](data/transcript.csv)[/]")
    console.print("  [cyan]3.[/] Browse test cases")

    raw = input("  Enter choice: ").strip()

    if raw == "2":
        sample = str(PROJECT_ROOT / "data" / "transcript.csv")
        if Path(sample).exists():
            return sample
        console.print("[yellow]  Sample not found, enter path manually.[/]")
        return _prompt_input("Transcript file path")

    if raw == "3":
        csvs = _list_test_csvs()
        if not csvs:
            console.print("[yellow]  No test CSVs found.[/]")
            return _prompt_input("Transcript file path")

        page_size = 15
        page = 0
        total_pages = (len(csvs) + page_size - 1) // page_size
        while True:
            start = page * page_size
            end = min(start + page_size, len(csvs))
            console.print(f"\n[bold]Test cases (page {page + 1}/{total_pages}):[/]")
            for i, name in enumerate(csvs[start:end], start + 1):
                tag = _fixture_label(name)
                style = "yellow" if tag == "legacy" else "green"
                console.print(f"  [cyan]{i:3d}.[/] {name}  [{style}]{tag}[/]")
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
                return _prompt_input("Transcript file path")
            elif pick.isdigit() and 1 <= int(pick) <= len(csvs):
                return str(Path(TESTS_DIR) / csvs[int(pick) - 1])
            else:
                console.print("  [red]Invalid. Try again.[/]")
        return _prompt_input("Transcript CSV path")

    return _prompt_input("Transcript file path")


def _auth_status_label() -> str:
    try:
        email = get_current_user_email()
    except Exception as exc:
        return f"[yellow]Cloud session unavailable[/] ({exc})"
    if email:
        return f"[green]Signed in[/] as [bold]{email}[/]"
    return "[yellow]Not signed in[/]"


def _print_auth_status() -> None:
    from rich.panel import Panel

    label = _auth_status_label()
    console.print(
        Panel(
            label,
            title="Cloud Session",
            border_style="green" if "Signed in" in label else "yellow",
            expand=False,
        )
    )


def _view_cloud_history() -> None:
    from rich.panel import Panel
    from rich.json import JSON

    try:
        email = get_current_user_email()
    except Exception as exc:
        console.print(f"[yellow]Could not refresh the cloud session:[/] {exc}")
        return
    if not email:
        console.print("[yellow]Cloud history requires Google sign-in first.[/]")
        return

    scans = fetch_history()
    if not scans:
        console.print("[dim]No cloud history found for this account yet.[/]")
        return

    print_history_table(console, scans)

    while True:
        raw = input("\n  Enter a row number to inspect, or press Enter to return: ").strip()
        if not raw:
            return
        if not raw.isdigit() or not (1 <= int(raw) <= len(scans)):
            console.print("[red]Invalid selection.[/]")
            continue

        selected = scans[int(raw) - 1]
        detail = fetch_history(str(selected["id"]))
        console.print()
        console.print(
            Panel(
                f"[bold]{detail['program']}[/]  |  {detail['input_type']}  |  {detail.get('file_name') or '-'}",
                title=f"Scan {str(detail['id'])[:8]}",
                border_style="blue",
            )
        )
        console.print(JSON.from_data(detail["result"]))
        return


# ─── Test case catalog ────────────────────────────────────────────────

_TC_CATALOG: list[tuple[str, str, list[tuple[str, str, str, str]]]] = [
    # (category_name, emoji, [(filename, description, program, best_level)])
    (
        "Happy Path — Canonical",
        "🎓",
        [
            ("happy_cse_default.csv", "CSE canonical happy path", "CSE", "3"),
            ("happy_bba_finance.csv", "BBA canonical happy path (FIN concentration)", "BBA", "3"),
            ("happy_eee_default.csv", "EEE canonical happy path", "EEE", "3"),
            ("happy_ete_default.csv", "ETE canonical happy path", "ETE", "3"),
            ("happy_cee_default.csv", "CEE canonical happy path", "CEE", "3"),
            ("happy_env_default.csv", "ENV canonical happy path", "ENV", "3"),
            ("happy_eng_default.csv", "ENG canonical happy path", "ENG", "3"),
            ("happy_eco_default.csv", "ECO canonical happy path", "ECO", "3"),
        ],
    ),
    (
        "Near Complete — Credit Short",
        "🧮",
        [
            ("short_cse_credit_gap.csv", "CSE near-complete, one filler course short", "CSE", "3"),
            ("short_bba_credit_gap.csv", "BBA near-complete, one filler course short", "BBA", "3"),
            ("short_eee_credit_gap.csv", "EEE near-complete, one filler course short", "EEE", "3"),
            ("short_ete_credit_gap.csv", "ETE near-complete, one filler course short", "ETE", "3"),
            ("short_cee_credit_gap.csv", "CEE near-complete, one filler course short", "CEE", "3"),
            ("short_env_credit_gap.csv", "ENV near-complete, one filler course short", "ENV", "3"),
            ("short_eng_credit_gap.csv", "ENG near-complete, one filler course short", "ENG", "3"),
            ("short_eco_credit_gap.csv", "ECO near-complete, one filler course short", "ECO", "3"),
        ],
    ),
    (
        "Concentration / Minor",
        "📚",
        [
            ("concentration_bba_finance.csv", "BBA FIN concentration complete", "BBA", "3"),
            ("concentration_bba_undeclared.csv", "BBA concentration incomplete / under-declared", "BBA", "3"),
            ("concentration_bba_finance_low_gpa.csv", "BBA FIN concentration below minimum GPA", "BBA", "3"),
            ("minor_cse_math_complete.csv", "CSE with completed Math minor", "CSE", "3"),
            ("minor_cse_physics_complete.csv", "CSE with completed Physics minor", "CSE", "3"),
            ("minor_cse_math_partial.csv", "CSE with partial Math minor", "CSE", "3"),
            ("minor_cse_math_missing_prereqs.csv", "CSE Math minor attempt missing prerequisites", "CSE", "3"),
        ],
    ),
    (
        "Status Edge Cases",
        "📉",
        [
            ("failed_cse_core.csv", "CSE with a failed core course", "CSE", "1"),
            ("failed_bba_core.csv", "BBA with a failed core course", "BBA", "1"),
            ("incomplete_cse_hold.csv", "CSE with an unresolved incomplete", "CSE", "1"),
            ("incomplete_cse_resolved.csv", "CSE with incomplete later resolved", "CSE", "1"),
            ("incomplete_bba_hold.csv", "BBA with an unresolved incomplete", "BBA", "1"),
            ("withdrawn_cse_hold.csv", "CSE with a withdrawn course", "CSE", "1"),
            ("withdrawn_bba_hold.csv", "BBA with a withdrawn course", "BBA", "1"),
            ("mixed_cse_statuses.csv", "CSE with mixed F/I/W statuses", "CSE", "1"),
            ("mixed_bba_statuses.csv", "BBA with mixed F/I/W statuses", "BBA", "1"),
        ],
    ),
    (
        "Waivers",
        "🔓",
        [
            ("waiver_cse_eng102.csv", "CSE with ENG102 waiver applied", "CSE", "2"),
            ("waiver_cse_mat112.csv", "CSE with MAT112 waiver applied", "CSE", "2"),
            ("waiver_cse_both.csv", "CSE with ENG102 + MAT112 waivers applied", "CSE", "2"),
        ],
    ),
    (
        "Retakes",
        "🔄",
        [
            ("retake_cse_recovered.csv", "CSE failed then recovered on retake", "CSE", "1"),
            ("retake_cse_unresolved.csv", "CSE retook but still failed", "CSE", "1"),
            ("retake_cse_multiple.csv", "CSE multiple retake attempts", "CSE", "1"),
            ("retake_cse_worse_second_attempt.csv", "CSE worse second attempt", "CSE", "1"),
            ("retake_cse_ineligible.csv", "CSE ineligible retake after A grade", "CSE", "1"),
        ],
    ),
    (
        "Prerequisites / Progression",
        "🔗",
        [
            ("prereq_cse_database_early.csv", "CSE database course taken before data structures", "CSE", "3"),
            ("prereq_eee_circuits_early.csv", "EEE advanced circuits taken before prerequisites", "EEE", "3"),
            ("prereq_bba_finance_early.csv", "BBA finance course taken before ACT201", "BBA", "3"),
            ("prereq_bba_internship_early.csv", "BBA internship taken before credit threshold", "BBA", "3"),
            ("probation_bba_borderline.csv", "BBA borderline probation profile", "BBA", "2"),
            ("probation_bba_recovery.csv", "BBA probation then recovery", "BBA", "2"),
            ("probation_bba_dismissal_risk.csv", "BBA three-term dismissal risk profile", "BBA", "2"),
        ],
    ),
    (
        "Transfer / Cross Credit",
        "🚫",
        [
            ("transfer_cse_external_credit.csv", "CSE transcript with external transfer credit", "CSE", "1"),
        ],
    ),
]

_LEVEL_LABELS = {
    "1": "Level 1 — Credit Tally",
    "2": "Level 2 — CGPA & Probation",
    "3": "Level 3 — Full Audit",
    "all": "All Levels",
    "dist": "Grade Distribution",
}


def _build_result_payload(
    records,
    program_info,
    waivers: set[str],
    equivalences: dict[str, set[str]],
    non_nsu: list[str],
    concentration: str | None = None,
    minor: str | None = None,
):
    credit_summary = tally_credits(
        records,
        program_info,
        waived_courses=waivers,
        equivalences=equivalences,
    )
    snapshots = compute_semester_progression(records, waived=waivers)
    grade_dist = compute_grade_distribution(records)
    audit_result = run_audit(
        records,
        program_info,
        waivers,
        equivalences,
        concentration=concentration,
        minor=minor,
    )

    return {
        "program": program_info.full_name,
        "program_alias": program_info.alias,
        "non_nsu_courses_flagged": non_nsu,
        "waivers_applied": sorted(waivers),
        "credits": {
            "total_earned": credit_summary.total_earned,
            "total_attempted": credit_summary.total_attempted,
            "program_required": credit_summary.program_credits,
            "elective": credit_summary.elective_credits,
            "excluded": credit_summary.excluded_credits,
            "waived": credit_summary.waived_credits,
        },
        "cgpa": {
            "final": round(snapshots[-1].cumulative_cgpa, 3) if snapshots else 0.0,
            "semesters": [
                {
                    "semester": s.semester,
                    "tgpa": round(s.tgpa, 3),
                    "cumulative_cgpa": round(s.cumulative_cgpa, 3),
                    "probation_status": s.probation_status,
                }
                for s in snapshots
            ],
        },
        "grade_distribution": grade_dist,
        "audit": {
            "eligible": audit_result.eligible,
            "reasons": audit_result.reasons,
            "roadmap": audit_result.roadmap,
            "cgpa": round(audit_result.cgpa, 3),
            "major_cgpa": round(audit_result.major_cgpa, 3),
            "credits_completed": audit_result.credits_completed,
            "credits_required": audit_result.credits_required,
            "failed_courses": audit_result.failed_courses,
            "missing_courses": {
                "ged": audit_result.deficiencies.missing_ged,
                "math": audit_result.deficiencies.missing_math,
                "science": audit_result.deficiencies.missing_science,
                "business": audit_result.deficiencies.missing_business,
                "major": audit_result.deficiencies.missing_major,
                "capstone": audit_result.deficiencies.missing_capstone,
                "internship": audit_result.deficiencies.missing_internship,
                "trail_credits_missing": audit_result.deficiencies.missing_trail,
                "open_elective_credits_missing": audit_result.deficiencies.missing_open_elective,
            },
            "prerequisite_violations": [
                {
                    "course": v.course,
                    "missing_prereqs": v.missing_prereqs,
                    "semester": v.semester,
                }
                for v in audit_result.prereq_violations
            ],
            "minor": {
                "name": audit_result.minor_name,
                "completed": audit_result.minor_completed,
                "courses_taken": audit_result.minor_courses_taken,
                "courses_missing": audit_result.minor_courses_missing,
                "prereqs_met": audit_result.minor_prereqs_met,
                "prereqs_missing": audit_result.minor_prereqs_missing,
            }
            if audit_result.minor_name
            else None,
        },
    }


def _record_from_payload(payload: dict) -> CourseRecord:
    return CourseRecord(
        course_code=payload["course_code"],
        credits=float(payload.get("credits", 0)),
        grade=payload.get("grade", ""),
        semester=payload.get("semester", ""),
        status=payload.get("status", ""),
        grade_points=float(payload.get("grade_points", 0)),
    )


def _credit_summary_from_payload(payload: dict) -> CreditSummary:
    return CreditSummary(
        total_earned=float(payload.get("total_earned", 0)),
        total_attempted=float(payload.get("total_attempted", 0)),
        program_credits=float(payload.get("program_required", 0)),
        elective_credits=float(payload.get("elective", 0)),
        excluded_credits=float(payload.get("excluded", 0)),
        waived_credits=float(payload.get("waived", 0)),
        course_statuses=[
            (_record_from_payload(item), item.get("bucket", "earned"))
            for item in payload.get("course_statuses", [])
        ],
    )


def _snapshots_from_payload(payload: dict) -> list[SemesterSnapshot]:
    snapshots: list[SemesterSnapshot] = []
    for item in payload.get("semesters", []):
        snapshots.append(
            SemesterSnapshot(
                semester=item["semester"],
                courses=[_record_from_payload(course) for course in item.get("courses", [])],
                sem_credits=float(item.get("sem_credits", 0)),
                sem_points=float(item.get("sem_points", 0)),
                tgpa=float(item.get("tgpa", 0)),
                cumulative_cgpa=float(item.get("cumulative_cgpa", 0)),
                probation_status=item.get("probation_status", "NORMAL"),
                consecutive_prob_count=int(item.get("consecutive_prob_count", 0)),
            )
        )
    return snapshots


def _audit_result_from_payload(
    payload: dict,
    program_info: ProgramInfo,
) -> AuditResult:
    audit_payload = payload.get("audit", {})
    missing = audit_payload.get("missing_courses", {})
    prereq_violations = [
        PrereqViolation(
            course=item["course"],
            missing_prereqs=list(item.get("missing_prereqs", [])),
            semester=item.get("semester", ""),
            violation_type=item.get("violation_type", "course"),
        )
        for item in audit_payload.get("prerequisite_violations", [])
    ]
    minor_payload = audit_payload.get("minor") or {}
    concentration_payload = audit_payload.get("concentration") or {}
    return AuditResult(
        program=program_info,
        credits_earned=float(audit_payload.get("credits_earned", 0)),
        credits_required=int(audit_payload.get("credits_required", 0)),
        waiver_bonus=float(audit_payload.get("waiver_bonus", 0)),
        credits_completed=float(audit_payload.get("credits_completed", 0)),
        cgpa=float(audit_payload.get("cgpa", 0)),
        gpa_credits=float(audit_payload.get("gpa_credits", 0)),
        grade_points=float(audit_payload.get("grade_points", 0)),
        major_cgpa=float(audit_payload.get("major_cgpa", 0)),
        concentration_cgpa=float(concentration_payload.get("cgpa", 0)),
        concentration_name=concentration_payload.get("name", "") or "",
        deficiencies=DeficiencyReport(
            missing_ged=list(missing.get("ged", [])),
            missing_math=list(missing.get("math", [])),
            missing_science=list(missing.get("science", [])),
            missing_business=list(missing.get("business", [])),
            missing_major=list(missing.get("major", [])),
            missing_capstone=list(missing.get("capstone", [])),
            missing_internship=list(missing.get("internship", [])),
            missing_trail=int(missing.get("trail_credits_missing", 0)),
            missing_concentration=int(missing.get("concentration_credits_missing", 0)),
            missing_open_elective=int(missing.get("open_elective_credits_missing", 0)),
        ),
        prereq_violations=prereq_violations,
        eligible=bool(audit_payload.get("eligible", False)),
        reasons=list(audit_payload.get("reasons", [])),
        roadmap=list(audit_payload.get("roadmap", [])),
        failed_courses=list(audit_payload.get("failed_courses", [])),
        minor_name=minor_payload.get("name", "") or "",
        minor_completed=bool(minor_payload.get("completed", False)),
        minor_courses_taken=list(minor_payload.get("courses_taken", [])),
        minor_courses_missing=list(minor_payload.get("courses_missing", [])),
        minor_prereqs_met=bool(minor_payload.get("prereqs_met", True)),
        minor_prereqs_missing=list(minor_payload.get("prereqs_missing", [])),
        bucket_gpas={key: float(value) for key, value in audit_payload.get("bucket_gpas", {}).items()},
    )


def _render_result_payload(
    result_payload: dict,
    transcript_path: str,
    program_info: ProgramInfo,
    level: str,
    report_mode: str,
    waivers: set[str],
) -> None:
    requested_level = result_payload.get("metadata", {}).get("requested_level", level)
    credit_summary = _credit_summary_from_payload(result_payload.get("credits", {}))
    snapshots = _snapshots_from_payload(result_payload.get("cgpa", {}))
    grade_dist = result_payload.get("grade_distribution", {})
    audit_result = _audit_result_from_payload(result_payload, program_info)

    if requested_level in ("1", "all"):
        console.rule("[bold blue]Level 1: Credit Tally Engine[/]")
        print_credit_tally(credit_summary, transcript_path, program_info.full_name)

    if requested_level in ("2", "all"):
        console.rule("[bold blue]Level 2: Logic Gate & Waiver Handler[/]")
        print_semester_progression(snapshots, transcript_path, waivers, grade_dist)

    if requested_level in ("3", "all"):
        console.rule("[bold blue]Level 3: Audit & Deficiency Reporter[/]")
        print_audit_report(audit_result, full_report=(report_mode == "full"))

    if requested_level == "dist":
        console.rule("[bold blue]Grade Distribution[/]")
        print_grade_distribution(grade_dist, transcript_path)


def _run_remote_scanned_audit(
    transcript_path: str,
    program_name: str,
    knowledge_path: str,
    *,
    level: str,
    report_mode: str,
    waivers_value: str | None,
    concentration: str | None,
    minor: str | None,
) -> dict | None:
    console.print(f"[cyan]Uploading '{Path(transcript_path).name}' to the API for transcript extraction...[/]")
    response = submit_scanned_audit(
        transcript_path,
        program_name,
        waivers=waivers_value,
        level=level,
        report=report_mode,
        concentration=concentration,
        minor=minor,
    )
    if response.get("status") == "review_required":
        review = response.get("review") or {}
        warnings = review.get("warnings") or []
        preview_rows = review.get("extracted_preview_rows") or []

        console.print("\n[yellow]OCR review required before running the audit.[/]")
        for warning in warnings:
            console.print(f"  [yellow]-[/] {warning}")

        if preview_rows:
            preview_table = Table(title="Extracted Transcript Preview", border_style="yellow")
            preview_table.add_column("Course")
            preview_table.add_column("Credits")
            preview_table.add_column("Grade")
            preview_table.add_column("Semester")
            preview_table.add_column("Confidence", justify="right")
            for row in preview_rows[:12]:
                preview_table.add_row(
                    row.get("course_code", "—"),
                    str(row.get("credits", "—")),
                    row.get("grade", "—"),
                    row.get("semester", "—"),
                    f"{float(row.get('confidence', 0)):.2f}",
                )
            console.print(preview_table)

        if not sys.stdin.isatty():
            raise RuntimeError(
                "Transcript extraction needs review. Re-run this command interactively to confirm the extracted rows."
            )

        confirm = input("  Continue with these extracted rows? (y/n): ").strip().lower()
        if confirm != "y":
            raise RuntimeError("Audit cancelled after OCR review.")

        response = submit_reviewed_audit(
            program=program_name,
            input_type=response.get("input_type", "image"),
            file_name=Path(transcript_path).name,
            extracted_csv=review.get("extracted_csv", ""),
            waivers=waivers_value,
            level=level,
            report=report_mode,
            concentration=concentration,
            minor=minor,
            extraction_mode=review.get("extraction_mode"),
            warnings=warnings,
        )

    program_info = load_program(knowledge_path, program_name)
    if not program_info:
        raise RuntimeError(f"Program '{program_name}' not found in local catalog.")
    waivers_set: set[str] = set()
    if level in ("2", "3", "all"):
        waivers_set = get_waivers(
            program_info,
            cli_waivers=waivers_value,
            interactive=False,
        )
    _render_result_payload(
        response["result"],
        transcript_path,
        program_info,
        level,
        report_mode,
        waivers_set,
    )
    try:
        email = get_current_user_email()
    except Exception as exc:
        console.print(
            f"\n[yellow]Audit finished, but the cloud session could not be refreshed:[/] {exc}"
        )
        email = None
    scan_id = str(response.get("scan_id", ""))[:8]
    if email and scan_id:
        console.print(
            f"\n[green]Saved this audit to cloud history[/] for [bold]{email}[/] ([cyan]{scan_id}[/])."
        )
    return response["result"]


def _maybe_log_cloud_audit(
    transcript_path: str,
    program_name: str,
    result_payload: dict | None,
    input_type: str = "csv",
) -> None:
    if not result_payload:
        return

    try:
        email = get_current_user_email()
    except Exception as exc:
        console.print(
            f"\n[yellow]Audit finished locally, but the cloud session could not be refreshed:[/] {exc}"
        )
        return
    if not email:
        return

    file_name = Path(transcript_path).name if transcript_path else None
    try:
        saved = save_local_audit(
            program=program_name,
            input_type=input_type,
            file_name=file_name,
            result=result_payload,
        )
        scan_id = str(saved.get("scan_id", ""))[:8]
        console.print(f"\n[green]Saved this audit to cloud history[/] for [bold]{email}[/] ([cyan]{scan_id}[/]).")
    except Exception as exc:
        console.print(f"\n[yellow]Signed in, but could not save this audit to cloud history:[/] {exc}")


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
        result_payload = {
            "program": program,
            "program_alias": program,
            "non_nsu_courses_flagged": [],
            "waivers_applied": [],
            "credits": {},
            "cgpa": {},
            "grade_distribution": dist,
            "audit": {},
        }
        _maybe_log_cloud_audit(tc_path, program, result_payload)
        return

    if not Path(knowledge_path).exists():
        console.print("[red]Error:[/] Knowledge file not found.")
        return

    program_info = load_program(knowledge_path, program)
    if not program_info:
        console.print(f"[red]Error:[/] Program '{program}' not found.")
        return

    resolve_retakes(records, equivalences)

    run_l1 = level in ("1", "all")
    run_l2 = level in ("2", "all")
    run_l3 = level in ("3", "all")

    waivers: set[str] = set()
    result_payload = None
    minor_arg = None
    concentration_arg = None

    console.print()
    console.rule(f"[bold green]{filename} — {program} — {_LEVEL_LABELS.get(level, level)}[/]")
    console.print()

    if run_l1:
        summary = tally_credits(
            records, program_info, waived_courses=waivers, equivalences=equivalences
        )
        print_credit_tally(summary, tc_path, program_info.full_name)

    if run_l2:
        snapshots = compute_semester_progression(records, waivers)
        grade_dist = compute_grade_distribution(records)
        print_semester_progression(snapshots, tc_path, waivers, grade_dist)

    if run_l3:
        if "minor" in filename:
            if "math" in filename:
                minor_arg = "MATH"
            elif "physics" in filename:
                minor_arg = "PHYSICS"
        if "wrong_concentration" in filename:
            concentration_arg = "MKT"
        result = run_audit(
            records,
            program_info,
            waivers,
            equivalences,
            minor=minor_arg,
            concentration=concentration_arg,
        )
        print_audit_report(result, full_report=True)

    result_payload = _build_result_payload(
        records,
        program_info,
        waivers,
        equivalences,
        [],
        concentration=concentration_arg,
        minor=minor_arg,
    )
    _maybe_log_cloud_audit(tc_path, program, result_payload)


def _test_explorer() -> None:
    """Category-based test case explorer with run capability."""
    from rich import box
    from rich.table import Table

    while True:
        console.print()
        cat_table = Table(
            box=box.ROUNDED,
            show_header=False,
            padding=(0, 2),
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
    from rich import box
    from rich.table import Table

    while True:
        console.print()
        tc_table = Table(
            box=box.ROUNDED,
            show_header=True,
            padding=(0, 1),
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
                str(i),
                fname,
                desc,
                prog,
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
    console.print(
        Panel(
            f"[bold]{filename}[/]\n"
            f"{description}\n"
            f"Program: [cyan]{program}[/]  |  Recommended: [green]{_LEVEL_LABELS.get(best_level, best_level)}[/]",
            title="Selected Test Case",
            border_style="green",
            expand=False,
        )
    )

    console.print("  [bold]How would you like to run it?[/]")
    console.print(f"  [cyan]1.[/] {_LEVEL_LABELS['1']}")
    console.print(f"  [cyan]2.[/] {_LEVEL_LABELS['2']}")
    console.print(f"  [cyan]3.[/] {_LEVEL_LABELS['3']}")
    console.print(f"  [cyan]4.[/] {_LEVEL_LABELS['all']}")
    console.print(f"  [cyan]5.[/] {_LEVEL_LABELS['dist']}")
    console.print(f"  [cyan]r.[/] Run recommended ({_LEVEL_LABELS.get(best_level, best_level)})")
    console.print("  [cyan]b.[/] Back")

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
    from rich import box
    from rich.table import Table

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
        box=box.ROUNDED,
        show_header=True,
        padding=(0, 1),
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

    result_payload = {
        "program": "",
        "program_alias": "",
        "non_nsu_courses_flagged": [],
        "waivers_applied": [],
        "credits": {},
        "cgpa": {},
        "grade_distribution": dist,
        "audit": {},
    }
    _maybe_log_cloud_audit(transcript_path, "GRADE-DIST", result_payload)


def interactive_menu() -> None:
    """Full interactive session — prompted step by step."""
    from rich import box
    from rich.table import Table

    print_banner()
    try:
        _print_auth_status()
    except Exception as exc:
        console.print(f"[yellow]Cloud auth unavailable:[/] {exc}")

    menu = Table(
        box=box.ROUNDED,
        show_header=False,
        padding=(0, 2),
        border_style="cyan",
        title="[bold]Main Menu[/]",
        title_style="bold white on blue",
    )
    menu.add_column("Option", style="bold cyan", min_width=4)
    menu.add_column("Description")
    menu.add_row("1", "Run Level 1 — Credit Tally Engine")
    menu.add_row("2", "Run Level 2 — Logic Gate & Waiver Handler")
    menu.add_row("3", "Run Level 3 — Audit & Deficiency Reporter")
    menu.add_row("4", "Run Full Audit (all levels)")
    menu.add_row("5", "View Grade Distribution")
    menu.add_row("6", "Explore & Run Test Cases")
    menu.add_row("7", "Sign in with Google")
    menu.add_row("8", "View Cloud History")
    menu.add_row("9", "Sign out of Cloud Session")
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

    if choice == "7":
        try:
            email = sign_in_with_google(console)
            console.print(f"[green]Signed in successfully as {email}.[/]")
        except Exception as exc:
            console.print(f"[red]Sign-in failed:[/] {exc}")
        interactive_menu()
        return

    if choice == "8":
        try:
            _view_cloud_history()
        except Exception as exc:
            console.print(f"[red]Could not load cloud history:[/] {exc}")
        console.print()
        interactive_menu()
        return

    if choice == "9":
        try:
            sign_out()
            console.print("[green]Cloud session cleared.[/]")
        except Exception as exc:
            console.print(f"[red]Sign-out failed:[/] {exc}")
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
        report_mode = _prompt_choice("Report verbosity:", ["normal", "full"], default="normal")
        if program_name == "BBA":
            conc = _prompt_input(
                "BBA concentration (FIN/MKT/ACT/HRM/MIS/SCM, or Enter to auto-detect)"
            )
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

    if _is_scanned_document(transcript_path):
        if not Path(knowledge_path).exists():
            console.print(f"[red]Error:[/] Knowledge file '{knowledge_path}' not found.")
            return
        output_file = None
        original_console = None
        if output_path:
            try:
                output_file, original_console = _redirect_formatter_console(output_path)
            except OSError as e:
                console.print(f"[red]Error:[/] Cannot write to '{output_path}': {e}")
                return
        try:
            _run_remote_scanned_audit(
                transcript_path,
                program_name,
                knowledge_path,
                level=level,
                report_mode=report_mode,
                waivers_value=waivers_str,
                concentration=concentration,
                minor=minor,
            )
        except Exception as exc:
            console.print(f"[red]Scanned transcript upload failed:[/] {exc}")
            return
        finally:
            if output_file:
                _restore_formatter_console(output_file, original_console, output_path)
        console.print()
        again = input("  Run another audit? (y/n): ").strip().lower()
        if again == "y":
            console.print()
            interactive_menu()
        return

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
    result_payload = None
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
            summary = tally_credits(
                records, program_info, waived_courses=waivers, equivalences=equivalences
            )
            print_credit_tally(summary, transcript_path, program_info.full_name)

        if run_l2:
            console.rule("[bold blue]Level 2: Logic Gate & Waiver Handler[/]")
            snapshots = compute_semester_progression(records, waivers)
            grade_dist = compute_grade_distribution(records)
            print_semester_progression(snapshots, transcript_path, waivers, grade_dist)

        if run_l3:
            console.rule("[bold blue]Level 3: Audit & Deficiency Reporter[/]")
            result = run_audit(
                records,
                program_info,
                waivers,
                equivalences,
                concentration=concentration,
                minor=minor,
            )
            full = report_mode == "full"
            print_audit_report(result, full_report=full)

        result_payload = _build_result_payload(
            records,
            program_info,
            waivers,
            equivalences,
            non_nsu,
            concentration=concentration,
            minor=minor,
        )
    finally:
        if output_file:
            output_file.close()
            import display.formatter

            display.formatter.console = original_console
            console.print(f"\n[green]Report saved to {output_path}[/]")

    _maybe_log_cloud_audit(transcript_path, program_name, result_payload)

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
            "  python gradgate.py data/transcript.csv CSE data/curriculum/catalog.json\n"
            "  python gradgate.py data/transcript.csv BBA data/curriculum/catalog.json --level 2 --waivers ENG102,BUS112\n"
            "  python gradgate.py data/transcript.csv CSE --level all --report full\n"
            "  python gradgate.py transcript.pdf CSE --upload --level 3\n"
            "\nRun with no arguments for interactive mode.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("transcript", help="Path to transcript CSV, PDF, or image file")
    parser.add_argument("program_name", help=f"Program alias ({', '.join(PROGRAM_ALIASES.keys())})")
    parser.add_argument(
        "program_knowledge",
        nargs="?",
        default=DEFAULT_KNOWLEDGE,
        help="Path to the structured curriculum catalog file",
    )
    parser.add_argument(
        "--level",
        choices=["1", "2", "3", "all", "dist"],
        default="all",
        help="Which level(s) to run (default: all)",
    )
    parser.add_argument(
        "--waivers",
        default=None,
        help="Comma-separated course codes to waive (e.g., ENG102,MAT112)",
    )
    parser.add_argument(
        "--report",
        choices=["normal", "full"],
        default="normal",
        help="Report verbosity for Level 3 (default: normal)",
    )
    parser.add_argument(
        "--concentration", default=None, help="BBA concentration alias (e.g., FIN, MKT, ACT)"
    )
    parser.add_argument(
        "--minor",
        default=None,
        choices=["MATH", "PHYSICS"],
        help="Declare a minor (MATH or PHYSICS)",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Treat the transcript argument as an image/PDF to run OCR on instead of a CSV",
    )
    parser.add_argument("-o", "--output", help="Save output to file")
    args = parser.parse_args()

    print_banner()
    source_transcript_path = args.transcript
    is_scanned_input = args.upload or _is_scanned_document(args.transcript)

    if is_scanned_input:
        knowledge_path = args.program_knowledge
        if not Path(knowledge_path).exists():
            console.print(f"[red]Error:[/] Knowledge file '{knowledge_path}' not found.")
            sys.exit(1)

        output_file = None
        original_console = None
        if args.output:
            try:
                output_file, original_console = _redirect_formatter_console(args.output)
            except OSError as e:
                console.print(f"[red]Error:[/] Cannot write to '{args.output}': {e}")
                sys.exit(1)

        try:
            _run_remote_scanned_audit(
                args.transcript,
                args.program_name,
                knowledge_path,
                level=args.level,
                report_mode=args.report,
                waivers_value=args.waivers,
                concentration=args.concentration,
                minor=args.minor,
            )
        except Exception as exc:
            console.print(f"[red]Scanned transcript upload failed:[/] {exc}")
            sys.exit(1)
        finally:
            if output_file:
                _restore_formatter_console(output_file, original_console, args.output)
        return

    try:
        records = load_transcript(args.transcript)
    except Exception as e:
        console.print(f"[red]Error loading transcript:[/] {e}")
        sys.exit(1)

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
    result_payload = None
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
        if args.level == "dist":
            console_ref.rule("[bold blue]Grade Distribution[/]")
            dist = compute_grade_distribution(records)
            print_grade_distribution(dist, args.transcript)

        if run_l1:
            console_ref.rule("[bold blue]Level 1: Credit Tally Engine[/]")
            summary = tally_credits(
                records, program_info, waived_courses=waivers, equivalences=equivalences
            )
            print_credit_tally(summary, args.transcript, program_info.full_name)

        if run_l2:
            console_ref.rule("[bold blue]Level 2: Logic Gate & Waiver Handler[/]")
            snapshots = compute_semester_progression(records, waivers)
            grade_dist = compute_grade_distribution(records)
            print_semester_progression(snapshots, args.transcript, waivers, grade_dist)

        if run_l3:
            console_ref.rule("[bold blue]Level 3: Audit & Deficiency Reporter[/]")
            result = run_audit(
                records,
                program_info,
                waivers,
                equivalences,
                concentration=args.concentration,
                minor=args.minor,
            )
            full = args.report == "full"
            print_audit_report(result, full_report=full)

        result_payload = _build_result_payload(
            records,
            program_info,
            waivers,
            equivalences,
            non_nsu,
            concentration=args.concentration,
            minor=args.minor,
        )

    finally:
        if output_file:
            output_file.close()
            import display.formatter
            display.formatter.console = original_console
            print(f"Report saved to {args.output}")

    _maybe_log_cloud_audit(
        source_transcript_path,
        args.program_name,
        result_payload,
        input_type="csv",
    )


def auth_mode() -> None:
    """Handle auth-only CLI commands."""
    parser = argparse.ArgumentParser(description="GradGate cloud session commands")
    parser.add_argument("--login", action="store_true", help="Sign in with Google via Supabase")
    parser.add_argument("--logout", action="store_true", help="Clear the saved cloud session")
    parser.add_argument(
        "--history",
        nargs="?",
        const="list",
        metavar="SCAN_ID",
        help="List cloud history, or show one scan by id",
    )
    args = parser.parse_args()

    print_banner()

    try:
        if args.login:
            email = sign_in_with_google(console)
            console.print(f"[green]Signed in successfully as {email}.[/]")
            return

        if args.logout:
            sign_out()
            console.print("[green]Cloud session cleared.[/]")
            return

        if args.history:
            if args.history == "list":
                scans = fetch_history()
                if scans:
                    print_history_table(console, scans)
                else:
                    console.print("[dim]No cloud history found for this account yet.[/]")
            else:
                from rich.json import JSON

                detail = fetch_history(args.history)
                console.print(JSON.from_data(detail))
            return
    except Exception as exc:
        console.print(f"[red]Cloud command failed:[/] {exc}")
        sys.exit(1)


def main() -> None:
    auth_flags = {"--login", "--logout", "--history"}
    if any(flag in sys.argv[1:] for flag in auth_flags):
        auth_mode()
        return

    has_positional = any(not a.startswith("-") for a in sys.argv[1:])
    if len(sys.argv) == 1 or (
        not has_positional and "--help" not in sys.argv and "-h" not in sys.argv
    ):
        interactive_menu()
    else:
        cli_mode()


if __name__ == "__main__":
    main()
