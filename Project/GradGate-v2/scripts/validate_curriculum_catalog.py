#!/usr/bin/env python3
"""Validate the canonical curriculum catalog for schema completeness."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CATALOG = REPO / "data" / "curriculum" / "catalog.json"
BLUEPRINTS = REPO / "data" / "curriculum" / "fixture_blueprints.json"
OFFICIAL_MODELS = REPO / "data" / "curriculum" / "official_bucket_models.json"
REQUIRED_BUCKETS = {
    "mandatory_ged",
    "core_math",
    "core_science",
    "core_business",
    "major_core",
    "capstone",
    "internship",
}
REQUIRED_PROGRAM_KEYS = {
    "full_name",
    "alias",
    "degree",
    "total_credits",
    "min_cgpa",
    "waivable",
    "credit_adjustment",
    "buckets",
    "alternative_groups",
    "trails",
    "trail_credits_required",
    "concentrations",
    "concentration_credits_required",
    "concentration_min_cgpa",
    "open_elective_credits",
    "non_credit_labs",
    "minors",
    "prerequisites",
    "credit_prerequisites",
    "bucket_gpa_requirements",
    "provenance",
    "official_structure",
}


def fail(message: str) -> None:
    print(f"[curriculum] {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not CATALOG.exists():
        fail(f"Catalog not found: {CATALOG}")
    if not BLUEPRINTS.exists():
        fail(f"Fixture blueprints not found: {BLUEPRINTS}")
    if not OFFICIAL_MODELS.exists():
        fail(f"Official bucket models not found: {OFFICIAL_MODELS}")

    blob = json.loads(CATALOG.read_text())
    blueprints = json.loads(BLUEPRINTS.read_text())
    official_models = json.loads(OFFICIAL_MODELS.read_text())
    if "programs" not in blob or not isinstance(blob["programs"], dict):
        fail("Catalog must contain a 'programs' object")

    programs = blob["programs"]
    if not programs:
        fail("Catalog contains no programs")

    for alias, program in programs.items():
        missing = REQUIRED_PROGRAM_KEYS - set(program)
        if missing:
            fail(f"{alias} missing keys: {sorted(missing)}")

        buckets = program["buckets"]
        bucket_missing = REQUIRED_BUCKETS - set(buckets)
        if bucket_missing:
            fail(f"{alias} missing buckets: {sorted(bucket_missing)}")

        provenance = program["provenance"]
        for field in ("source_type", "source_url", "source_title", "verified_on", "notes"):
            if field not in provenance:
                fail(f"{alias} provenance missing '{field}'")

        if program["total_credits"] <= 0:
            fail(f"{alias} total_credits must be positive")

        if not isinstance(program["waivable"], list):
            fail(f"{alias} waivable must be a list")

        official_structure = program["official_structure"]
        for field in ("model", "source_granularity", "bucket_requirements", "notes"):
            if field not in official_structure:
                fail(f"{alias} official_structure missing '{field}'")
        if not official_structure["bucket_requirements"]:
            fail(f"{alias} official_structure must include at least one bucket requirement")

    if "program_electives" not in blueprints or "legacy_aliases" not in blueprints:
        fail("Fixture blueprints must define program_electives and legacy_aliases")

    missing_programs = set(programs) - set(blueprints["program_electives"])
    if missing_programs:
        fail(f"Fixture blueprints missing program pools: {sorted(missing_programs)}")

    if set(programs) - set(official_models.get("programs", {})):
        fail("Official bucket models do not cover every program")

    print(f"[curriculum] OK: {len(programs)} programs validated")


if __name__ == "__main__":
    main()
