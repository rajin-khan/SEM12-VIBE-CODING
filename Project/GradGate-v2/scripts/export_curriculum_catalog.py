#!/usr/bin/env python3
"""Export the current curriculum knowledge into a structured catalog.

This is a migration tool: the generated JSON becomes the canonical runtime
curriculum source, while `program_knowledge.md` remains a legacy compatibility
input during the transition window.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "cli"))

from engine.program_loader import load_all_programs, load_equivalences, load_nsu_course_list

KNOWLEDGE = REPO / "data" / "program_knowledge.md"
SOURCES = REPO / "data" / "program_sources.json"
OFFICIAL_MODELS = REPO / "data" / "curriculum" / "official_bucket_models.json"
OUT = REPO / "data" / "curriculum" / "catalog.json"


def _course_payload(course) -> dict[str, object]:
    return {
        "code": course.code,
        "name": course.name,
        "credits": course.credits,
        "is_non_credit_lab": course.is_non_credit_lab,
    }


def _program_payload(
    info,
    sources: dict[str, object],
    official_models: dict[str, object],
    verified_on: str | None,
) -> dict[str, object]:
    payload = {
        "full_name": info.full_name,
        "alias": info.alias,
        "degree": info.degree,
        "total_credits": info.total_credits,
        "min_cgpa": info.min_cgpa,
        "waivable": info.waivable,
        "credit_adjustment": info.credit_adjustment,
        "buckets": {
            "mandatory_ged": [_course_payload(course) for course in info.mandatory_ged],
            "core_math": [_course_payload(course) for course in info.core_math],
            "core_science": [_course_payload(course) for course in info.core_science],
            "core_business": [_course_payload(course) for course in info.core_business],
            "major_core": [_course_payload(course) for course in info.major_core],
            "capstone": [_course_payload(course) for course in info.capstone],
            "internship": [_course_payload(course) for course in info.internship],
        },
        "alternative_groups": [
            {"options": group.options, "credits": group.credits}
            for group in info.alternative_groups
        ],
        "trails": [{"name": trail.name, "courses": trail.courses} for trail in info.trails],
        "trail_credits_required": info.trail_credits_required,
        "concentrations": [
            {"name": concentration.name, "alias": concentration.alias, "courses": concentration.courses}
            for concentration in info.concentrations
        ],
        "concentration_credits_required": info.concentration_credits_required,
        "concentration_min_cgpa": info.concentration_min_cgpa,
        "open_elective_credits": info.open_elective_credits,
        "non_credit_labs": info.non_credit_labs,
        "minors": [
            {
                "name": minor.name,
                "total_credits": minor.total_credits,
                "required_courses": minor.required_courses,
                "elective_courses": minor.elective_courses,
                "elective_pick_count": minor.elective_pick_count,
                "prerequisites": sorted(minor.prerequisites),
            }
            for minor in info.minors
        ],
        "prerequisites": info.prerequisites,
        "credit_prerequisites": info.credit_prerequisites,
        "bucket_gpa_requirements": {},
        "provenance": {
            "source_type": sources.get(info.alias, {}).get("source_type", "program_page"),
            "verified_on": verified_on,
            **sources.get(info.alias, {}),
        },
        "official_structure": official_models.get(info.alias, {}),
    }

    if info.alias == "BBA":
        payload["bucket_gpa_requirements"] = {
            "core_business": 2.0,
            "major_core": 2.0,
        }

    return payload


def main() -> None:
    programs = load_all_programs(str(KNOWLEDGE))
    sources_blob = json.loads(SOURCES.read_text())
    official_models_blob = json.loads(OFFICIAL_MODELS.read_text())
    verified_on = sources_blob.get("verified_on")
    sources = sources_blob.get("programs", {})
    official_models = official_models_blob.get("programs", {})
    payload = {
        "metadata": {
            "source_model": "handbook_migration_v1",
            "verified_on": verified_on,
            "notes": (
                "Structured curriculum catalog used as the canonical runtime source during the "
                "handbook migration. The JSON catalog is the active runtime input; the markdown "
                "knowledge file remains only as a temporary migration reference."
            ),
        },
        "nsu_course_list": sorted(load_nsu_course_list(str(KNOWLEDGE))),
        "equivalences": sorted(
            [sorted(group) for group in {frozenset(group) for group in load_equivalences(str(KNOWLEDGE)).values()}]
        ),
        "programs": {
            alias: _program_payload(info, sources, official_models, verified_on)
            for alias, info in sorted(programs.items())
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
