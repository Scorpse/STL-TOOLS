"""STL-K runner-profile conformance tests."""

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
RUNNERS = ROOT / "runners"


def _validate(profile_name: str, fixture_name: str):
    return validate_against_profiles(
        parse((RUNNERS / "examples" / fixture_name).read_text(encoding="utf-8")),
        load_profile(str(RUNNERS / f"{profile_name}.stl.profile")),
    )


@pytest.mark.parametrize(
    ("profile_name", "fixture_name"),
    [
        ("cli-runner", "cli-runner-valid.stl"),
        ("api-agent", "api-agent-valid.stl"),
        ("hosted-agent", "hosted-agent-valid.stl"),
        ("cloud-environment", "cloud-environment-valid.stl"),
    ],
)
def test_runner_profile_composes_with_stlk(profile_name, fixture_name):
    assert _validate(profile_name, fixture_name).errors == []


@pytest.mark.parametrize(
    ("profile_name", "fixture_name", "code", "field"),
    [
        ("cli-runner", "missing-runner-id-invalid.stl", "E607", "runner_id"),
        ("cli-runner", "cli-missing-executable-invalid.stl", "E607", "executable"),
        ("api-agent", "unsupported-control-invalid.stl", "E603", "control_operation"),
        ("hosted-agent", "raw-credential-invalid.stl", "E617", "api_key"),
        ("cloud-environment", "cloud-missing-cleanup-owner-invalid.stl", "E607", "cleanup_owner"),
        ("cli-runner", "wrong-runner-kind-invalid.stl", "E603", "runner_kind"),
        ("api-agent", "unadvertised-capability-grant-invalid.stl", "E612", "capability_id"),
    ],
)
def test_invalid_runner_contract_is_rejected(profile_name, fixture_name, code, field):
    result = _validate(profile_name, fixture_name)
    assert any(error.code == code and error.field == field for error in result.errors), [
        (error.code, error.field, error.statement_index, error.message)
        for error in result.errors
    ]
