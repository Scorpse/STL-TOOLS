"""STL-K transport conformance tests against the specification checkout."""

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
    path = ROOT / "examples" / "transport" / name
    return validate_against_profiles(
        parse(path.read_text(encoding="utf-8")),
        load_profile(str(PROFILE)),
    )


@pytest.mark.parametrize("name", [
    "conversation-valid.stl",
    "ack-second-transport-valid.stl",
    "retry-valid.stl",
])
def test_valid_transport_conversations(name):
    assert _validate(name).errors == []


@pytest.mark.parametrize(
    ("name", "code", "field", "statement_index"),
    [
        ("unknown-causation-invalid.stl", "E613", "causation_id", 1),
        ("ack-missing-delivered-at-invalid.stl", "E607", "delivered_at", 1),
        ("duplicate-delivery-invalid.stl", "E614", "delivery_id", 1),
        ("supersede-missing-cause-invalid.stl", "E607", "causation_id", 0),
        ("retract-erases-history-invalid.stl", "E603", "history", 1),
    ],
)
def test_invalid_transport_conversations(name, code, field, statement_index):
    result = _validate(name)
    assert any(
        error.code == code
        and error.field == field
        and error.statement_index == statement_index
        for error in result.errors
    ), [(error.code, error.field, error.statement_index, error.message) for error in result.errors]
