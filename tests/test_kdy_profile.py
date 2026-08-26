"""Cross-repository conformance tests for the versioned KDY profile."""

import os
from pathlib import Path

import pytest

from stl_parser import parse
from stl_parser.schema import load_profile, validate_against_profiles

SPEC_ROOT_VALUE = os.environ.get("STL_SPEC_ROOT")
pytestmark = pytest.mark.skipif(
    not SPEC_ROOT_VALUE,
    reason="set STL_SPEC_ROOT to run specification conformance tests",
)
SPEC_ROOT = Path(SPEC_ROOT_VALUE) if SPEC_ROOT_VALUE else Path(".")
SCHEMA_ROOT = SPEC_ROOT / "docs" / "schemas"
KDY_ROOT = SCHEMA_ROOT / "kdy"


def _validate(path: Path, profile_path: Path = KDY_ROOT / "kdy.stl.profile"):
    return validate_against_profiles(
        parse(path.read_text(encoding="utf-8")),
        load_profile(str(profile_path)),
    )


def test_kdy_profile_accepts_complete_four_lane_envelope():
    result = _validate(KDY_ROOT / "examples" / "envelope-valid.stl")
    assert result.errors == []


def test_kdy_profile_rejects_missing_event_identity_precisely():
    result = _validate(KDY_ROOT / "examples" / "envelope-invalid.stl")
    event_errors = [error for error in result.errors if error.field == "event_id"]
    assert [(error.code, error.message) for error in event_errors] == [
        ("E607", "Statement 0: missing required modifier 'event_id'")
    ]


@pytest.mark.parametrize(
    ("old", "new", "field"),
    [
        ("confidence=0.95", "confidence=0.9", "confidence"),
        ('visibility="procedural"', 'visibility="private"', "visibility"),
        ('sensitivity="internal"', 'sensitivity="restricted"', "sensitivity"),
        ('profile_version="kdy-0.1"', 'profile_version="kdy-0.2"', "profile_version"),
    ],
)
def test_kdy_profile_rejects_noncanonical_envelope_values(old, new, field):
    text = (KDY_ROOT / "examples" / "envelope-valid.stl").read_text(encoding="utf-8")
    result = validate_against_profiles(
        parse(text.replace(old, new, 1)),
        load_profile(str(KDY_ROOT / "kdy.stl.profile")),
    )
    assert any(error.code == "E603" and error.field == field for error in result.errors)


@pytest.mark.parametrize("fixture_name", [
    "agent-coord-example.stl",
    "agent-build-example.stl",
    "agent-review-example.stl",
    "agent-assess-example.stl",
])
def test_original_agent_profile_remains_independently_valid(fixture_name):
    result = _validate(
        SCHEMA_ROOT / "examples" / fixture_name,
        SCHEMA_ROOT / "agent.stl.profile",
    )
    assert result.errors == []
