"""Regression coverage for named transcript fixtures.

This locks the expected eligibility and headline credit outcomes so
curriculum changes do not silently relabel scenarios.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO / "tests"
KNOWLEDGE = REPO / "data" / "curriculum" / "catalog.json"
MANIFEST = TESTS_DIR / "canonical_fixture_expectations.json"
LEGACY_MAP = TESTS_DIR / "legacy_fixture_map.json"
INVALID_INPUT_FIXTURES = {
    "tc28_invalid_grades.csv",
    "tc39_malformed_columns.csv",
    "tc40_empty_fields.csv",
}


def _load_manifest() -> dict[str, dict[str, object]]:
    return json.loads(MANIFEST.read_text())


def _load_legacy_map() -> dict[str, str]:
    return json.loads(LEGACY_MAP.read_text())


def _run_fixture(
    filename: str,
    program: str,
    waivers: list[str] | None = None,
    concentration: str | None = None,
    minor: str | None = None,
):
    from engine.audit import run_audit
    from engine.program_loader import load_equivalences, load_nsu_course_list, load_program
    from engine.transcript import load_transcript, resolve_retakes, validate_courses
    from engine.waivers import get_waivers

    records = load_transcript(str(TESTS_DIR / filename))
    equivalences = load_equivalences(str(KNOWLEDGE))
    nsu_courses = load_nsu_course_list(str(KNOWLEDGE))

    for code in validate_courses(records, nsu_courses):
        for record in records:
            if record.course_code == code:
                record.grade = "T"
                record.status = "Transfer"

    resolve_retakes(records, equivalences)
    program_info = load_program(str(KNOWLEDGE), program)
    assert program_info is not None, f"Program not found for fixture {filename}"
    active_waivers = get_waivers(
        program_info,
        cli_waivers=",".join(waivers or []),
        interactive=False,
    )
    return run_audit(
        records,
        program_info,
        active_waivers,
        equivalences,
        concentration=concentration,
        minor=minor,
    )


def test_manifest_covers_all_named_fixtures():
    manifest = _load_manifest()
    actual = {
        path.name
        for path in TESTS_DIR.glob("*.csv")
        if not path.name.startswith(("tc", "test_")) and path.name not in INVALID_INPUT_FIXTURES
    }
    assert set(manifest) == actual


@pytest.mark.parametrize("filename,expected", sorted(_load_manifest().items()))
def test_fixture_expectations(filename: str, expected: dict[str, object]):
    audit = _run_fixture(
        filename,
        str(expected["program"]),
        waivers=list(expected.get("waivers", [])),
        concentration=expected.get("concentration"),
        minor=expected.get("minor"),
    )
    assert audit.eligible is expected["eligible"]
    assert audit.credits_completed == pytest.approx(float(expected["credits_completed"]))
    assert audit.credits_required == expected["credits_required"]
    assert audit.reasons == expected["reasons"]


def test_legacy_aliases_resolve_to_canonical_fixtures():
    manifest = _load_manifest()
    aliases = _load_legacy_map()
    assert aliases, "Expected at least one legacy alias during migration"
    for legacy_name, canonical_name in aliases.items():
        assert legacy_name.endswith(".csv")
        assert canonical_name in manifest, f"{legacy_name} -> missing canonical fixture {canonical_name}"
