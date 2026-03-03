"""Waiver handling: CLI arguments and interactive prompts."""

from __future__ import annotations

from typing import List, Optional, Set

from engine.program_loader import ProgramInfo


def get_waivers(program_info: Optional[ProgramInfo],
                cli_waivers: Optional[str] = None,
                interactive: bool = True) -> Set[str]:
    """Determine which courses are waived.

    Args:
        program_info: The program definition (contains waivable courses list).
        cli_waivers: Comma-separated waiver codes from CLI (e.g. "ENG102,MAT112").
        interactive: If True and cli_waivers is None, prompt the user.

    Returns:
        Set of waived course codes.
    """
    if not program_info:
        return set()

    waivable = set(program_info.waivable)
    if not waivable:
        return set()

    if cli_waivers is not None:
        requested = {c.strip().upper() for c in cli_waivers.split(",") if c.strip()}
        return requested & waivable

    if not interactive:
        return set()

    print(f"\nWaivable courses for {program_info.alias}: {', '.join(sorted(waivable))}")
    print("Enter course codes to waive (comma-separated), or press Enter for none:")
    user_input = input("  > ").strip()

    if not user_input:
        return set()

    requested = {c.strip().upper() for c in user_input.split(",") if c.strip()}
    granted = requested & waivable
    rejected = requested - waivable

    if rejected:
        print(f"  Note: {', '.join(sorted(rejected))} cannot be waived for this program.")

    return granted


def compute_adjusted_credits(program_info: ProgramInfo,
                             waivers: Set[str]) -> int:
    """Compute the adjusted total credits required based on waivers."""
    if program_info.credit_adjustment:
        n_waived = len(waivers & set(program_info.waivable))
        total_waivable = len(program_info.waivable)
        if n_waived == total_waivable and "both" in program_info.credit_adjustment:
            return program_info.credit_adjustment["both"]
        elif n_waived == 0 and "none" in program_info.credit_adjustment:
            return program_info.credit_adjustment["none"]
        elif 0 < n_waived < total_waivable and "one" in program_info.credit_adjustment:
            return program_info.credit_adjustment["one"]

    return program_info.total_credits


def waiver_credit_bonus(waivers: Set[str],
                        program_info: Optional[ProgramInfo] = None,
                        transcript_codes: Optional[Set[str]] = None) -> float:
    """Credits for waived courses not already earned in the transcript.

    Only counts courses that are actually waivable for the program,
    and skips any that already appear as passed in the transcript
    (to avoid double-counting with credits_earned).
    """
    effective = set(waivers)
    if program_info and program_info.waivable:
        effective &= set(program_info.waivable)
    if transcript_codes:
        effective -= transcript_codes
    return len(effective) * 3.0
