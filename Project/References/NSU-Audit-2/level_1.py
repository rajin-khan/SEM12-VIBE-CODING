#!/usr/bin/env python3
"""
Level 1 — Credit Tallying Report
Calculates attempted and earned credits from a transcript CSV.

Usage:
    python level_1.py <transcript.csv>
"""

import sys
import os
from engine.credit_engine import process_transcript

# ─── Color helpers ───────────────────────────────────────
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
    GREEN = Fore.GREEN
    RED = Fore.RED
    YELLOW = Fore.YELLOW
    CYAN = Fore.CYAN
    BOLD = Style.BRIGHT
    RESET = Style.RESET_ALL
except ImportError:
    GREEN = RED = YELLOW = CYAN = BOLD = RESET = ""

def header_bar(title, width=50):
    return f"\n{'=' * width}\n  {title}\n{'=' * width}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python level_1.py <transcript.csv>")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        sys.exit(1)

    # Level 1 Processing
    records, attempted, earned = process_transcript(filepath)

    # Report
    print(header_bar("LEVEL 1 — CREDIT TALLY REPORT"))
    print(f"  Transcript File  : {os.path.basename(filepath)}")
    print(f"  Credits Attempted: {BOLD}{attempted}{RESET}")
    print(f"  Credits Earned   : {BOLD}{GREEN}{earned}{RESET}")

    print(f"\n{'CODE':<10} {'COURSE NAME':<30} {'CR':<4} {'GRADE':<10} {'STATUS'}")
    print("-" * 75)
    for r in records:
        status_color = GREEN if r.status in ("BEST", "WAIVED") else ""
        if r.status == "RETAKE-IGNORED": status_color = Style.DIM
        elif r.status == "FAILED": status_color = RED
        elif r.status == "WITHDRAWN": status_color = YELLOW

        print(f"{r.course_code:<10} {r.course_name[:28]:<30} {r.credits:<4} {r.grade:<10} {status_color}{r.status}{RESET}")
    print("-" * 75)
    print(f"  Total Credits Earned: {BOLD}{GREEN}{earned}{RESET}")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
