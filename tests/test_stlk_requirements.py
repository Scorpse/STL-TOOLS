"""STL-K requirement-specification conformance tests."""

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
ROOT = Path(SPEC_ROOT_VALUE) / "docs" / "schemas" / "runekiln" if SPEC_ROOT_VALUE else Path(".")
PROFILE = ROOT / "stl-k.stl.profile"


def _validate(name):
    path = ROOT / "examples" / "requirements" / name
    return validate_against_profiles(
        parse(path.read_text(encoding="utf-8")),
        load_profile(str(PROFILE)),
    )


def test_complete_requirement_spec_is_authorizable():
    assert _validate("requirement-spec-valid.stl").errors == []


@pytest.mark.parametrize(
    ("name", "code", "field"),
    [
        ("unresolved-ambiguity-invalid.stl", "E616", "outcome"),
        ("deliverable-without-acceptance-invalid.stl", "E612", "deliverable_id"),
        ("external-without-gate-invalid.stl", "E612", "capability_id"),
        ("derived-without-source-invalid.stl", "E607", "evidence_ref"),
        ("mutate-original-invalid.stl", "E616", "action"),
    ],
)
def test_invalid_requirement_specifications(name, code, field):
    result = _validate(name)
    assert any(error.code == code and error.field == field for error in result.errors), [
        (error.code, error.field, error.statement_index, error.message)
        for error in result.errors
    ]
