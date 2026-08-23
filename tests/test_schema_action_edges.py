"""Action-keyed edge rules (edge{ source/action/target })."""
from pathlib import Path
import pytest
from stl_parser import parse
from stl_parser.schema import load_schema, validate_against_schema, _parse_schema_text

FIX = Path(__file__).parent / "fixtures" / "action_edges.stl.schema"


@pytest.fixture
def schema():
    return load_schema(str(FIX))


def _v(text, schema):
    return validate_against_schema(parse(text), schema)


def test_edge_rules_parse_action_keyed(schema):
    assert len(schema.edge_rules) == 2
    assert schema.edge_rules[0].actions == ["gate"]
    assert schema.edge_rules[0].relations == []


def test_allowed_action_edges(schema):
    ok = ('[Review:Gate_Pre] -> [Review:Branch_x] ::mod(action="gate", outcome="pass")\n'
          '[Review:Verifier_C] -> [Review:Revision_y] ::mod(action="verify", outcome="pass")')
    r = _v(ok, schema)
    assert r.is_valid, [e.message for e in r.errors]


def test_wrong_target_rejected(schema):
    r = _v('[Review:Gate_Pre] -> [Review:WorkItem_z] ::mod(action="gate")', schema)
    assert not r.is_valid and any(e.code == "E611" for e in r.errors)


def test_wrong_action_for_source_rejected(schema):
    # Verifier cannot 'gate'; Gate source rule doesn't match Verifier source.
    r = _v('[Review:Verifier_C] -> [Review:Revision_y] ::mod(action="gate")', schema)
    assert not r.is_valid and any(e.code == "E611" for e in r.errors)


def test_error_names_action_field(schema):
    r = _v('[Review:Gate_Pre] -> [Review:WorkItem_z] ::mod(action="gate")', schema)
    e = next(e for e in r.errors if e.code == "E611")
    assert e.field == "action" and "action=gate" in e.message


def test_edge_needs_exactly_one_key():
    both = ('schema X v1 { namespace "X" anchor source { pattern: /A_[a-z]+/ } '
            'anchor target { pattern: /B_[a-z]+/ } modifier { required: [action] } '
            'edge { source: [A] relation: [r] action: [a] target: [B] } }')
    with pytest.raises(Exception):
        _parse_schema_text(both)
    neither = ('schema X v1 { namespace "X" anchor source { pattern: /A_[a-z]+/ } '
               'anchor target { pattern: /B_[a-z]+/ } modifier { required: [action] } '
               'edge { source: [A] target: [B] } }')
    with pytest.raises(Exception):
        _parse_schema_text(neither)
