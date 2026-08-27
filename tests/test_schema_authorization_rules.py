"""Domain-neutral matched requirements and authorization blockers."""

from stl_parser import parse
from stl_parser.schema import _parse_schema_text, validate_against_schema

SCHEMA_TEXT = r'''
schema Authorization v1.0 {
    namespace "T"
    anchor source { namespace: required("T") pattern: /Node_[A-Za-z0-9_]+/ }
    anchor target { pattern: /Node_[A-Za-z0-9_]+/ }
    modifier {
        required: [action, outcome]
        optional: [work_id, category, evidence_ref, event_id, priority]
        action: string
        outcome: enum("pass", "pending")
        work_id: string
        category: string
        evidence_ref: string
        event_id: string
        priority: integer
    }
    reference {
        field: evidence_ref
        target: event_id
        required_for: [derive]
        target_actions: [capture, clarify]
        prior: true
    }
    require {
        action: "deliver"
        bindings: [accept]
        outcome: "pass"
        match: work_id
    }
    require {
        action: "capability"
        trigger_field: category
        trigger_values: [external, financial]
        bindings: [grant, gate]
        outcome: "pass"
        match: work_id
    }
    forbid {
        action: authorize
        outcome: pass
        if_action: question
        if_outcomes: [pending]
        if_field: priority
        if_values: [0]
    }
    forbid { action: mutate }
}
'''


def _validate(text):
    return validate_against_schema(parse(text), _parse_schema_text(SCHEMA_TEXT))


def test_requirement_matches_companion_identifier():
    result = _validate(
        '[T:Node_delivery] -> [T:Node_target] '
        '::mod(action="deliver", outcome="pending", work_id="one")\n'
        '[T:Node_acceptance] -> [T:Node_delivery] '
        '::mod(action="accept", outcome="pass", work_id="two")'
    )
    error = next(error for error in result.errors if error.code == "E612")
    assert (error.statement_index, error.field) == (0, "work_id")


def test_requirement_defers_when_matching_identifier_is_missing():
    result = _validate(
        '[T:Node_delivery] -> [T:Node_target] '
        '::mod(action="deliver", outcome="pending")'
    )

    assert not any(error.code == "E612" for error in result.errors)


def test_requirement_accepts_any_configured_binding_action():
    result = _validate(
        '[T:Node_capability] -> [T:Node_target] '
        '::mod(action="capability", outcome="pending", category="external", work_id="cap_1")\n'
        '[T:Node_gate] -> [T:Node_capability] '
        '::mod(action="gate", outcome="pass", work_id="cap_1")'
    )
    assert result.errors == []


def test_nonmatching_trigger_field_does_not_require_binding():
    result = _validate(
        '[T:Node_capability] -> [T:Node_target] '
        '::mod(action="capability", outcome="pending", category="readonly", work_id="cap_1")'
    )
    assert result.errors == []


def test_conflicting_statement_blocks_trigger():
    result = _validate(
        '[T:Node_question] -> [T:Node_target] '
        '::mod(action="question", outcome="pending", priority=0)\n'
        '[T:Node_authorization] -> [T:Node_target] '
        '::mod(action="authorize", outcome="pass")'
    )
    error = next(error for error in result.errors if error.code == "E616")
    assert (error.statement_index, error.field) == (1, "outcome")


def test_directly_forbidden_action_is_rejected():
    result = _validate(
        '[T:Node_original] -> [T:Node_target] ::mod(action="mutate", outcome="pending")'
    )
    error = next(error for error in result.errors if error.code == "E616")
    assert (error.statement_index, error.field) == (0, "action")


def test_reference_rejects_disallowed_target_action():
    result = _validate(
        '[T:Node_observation] -> [T:Node_target] '
        '::mod(action="observe", outcome="pass", event_id="evt_1")\n'
        '[T:Node_requirement] -> [T:Node_target] '
        '::mod(action="derive", outcome="pending", evidence_ref="evt_1")'
    )
    error = next(error for error in result.errors if error.code == "E613")
    assert (error.statement_index, error.field) == (1, "evidence_ref")
