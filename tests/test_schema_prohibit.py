"""Generic prohibited-modifier schema rules."""

from stl_parser import parse
from stl_parser.schema import load_schema, validate_against_schema

SCHEMA = """
schema Safe v1.0 {
    anchor source { namespace: required("T") }
    modifier { optional: [connection_ref] connection_ref: string }
    prohibit { fields: [password, api_key, token, credential] }
}
"""


def test_prohibited_modifier_is_rejected_precisely():
    result = validate_against_schema(
        parse('[T:Runner_one] -> [T:Pool_main] ::mod(api_key="raw-secret")'),
        load_schema(SCHEMA),
    )

    assert [(error.code, error.field, error.statement_index) for error in result.errors] == [
        ("E617", "api_key", 0),
    ]


def test_opaque_reference_remains_valid():
    result = validate_against_schema(
        parse('[T:Runner_one] -> [T:Pool_main] ::mod(connection_ref="vault-ref:runner-one")'),
        load_schema(SCHEMA),
    )

    assert result.errors == []
