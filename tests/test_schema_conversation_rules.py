"""Domain-neutral cross-statement conversation rules."""

from stl_parser import parse
from stl_parser.schema import _parse_schema_text, validate_against_schema

SCHEMA_TEXT = r'''
schema Conversation v1.0 {
    namespace "T"
    anchor source { namespace: required("T") pattern: /Event_[A-Za-z0-9_]+/ }
    anchor target { pattern: /Event_[A-Za-z0-9_]+/ }
    modifier {
        required: [action, event_id, delivery_id]
        optional: [causation_id, delivered_at]
        action: enum("send", "ack", "retry")
        event_id: string
        delivery_id: string
        causation_id: string
        delivered_at: datetime
    }
    conditional { when: action values: [ack] required: [causation_id, delivered_at] }
    reference { field: causation_id target: event_id required_for: [ack, retry] prior: true }
    unique { field: delivery_id }
    unique { field: event_id except_actions: [ack, retry] }
    same { field: event_id reference: causation_id target: event_id actions: [ack, retry] }
}
'''


def _validate(text):
    return validate_against_schema(parse(text), _parse_schema_text(SCHEMA_TEXT))


def test_reference_resolves_to_prior_statement():
    result = _validate(
        '[T:Event_source] -> [T:Event_target] '
        '::mod(action="send", event_id="evt_1", delivery_id="del_1")\n'
        '[T:Event_ack] -> [T:Event_source] '
        '::mod(action="ack", event_id="evt_1", delivery_id="del_2", '
        'causation_id="evt_1", delivered_at="2026-08-27T12:01:00Z")'
    )
    assert result.errors == []


def test_unknown_reference_names_field_and_statement():
    result = _validate(
        '[T:Event_ack] -> [T:Event_source] '
        '::mod(action="ack", event_id="evt_1", delivery_id="del_1", '
        'causation_id="missing", delivered_at="2026-08-27T12:01:00Z")'
    )
    error = next(error for error in result.errors if error.code == "E613")
    assert (error.statement_index, error.field) == (0, "causation_id")


def test_conditional_required_field_uses_required_field_diagnostic():
    result = _validate(
        '[T:Event_source] -> [T:Event_target] '
        '::mod(action="send", event_id="evt_1", delivery_id="del_1")\n'
        '[T:Event_ack] -> [T:Event_source] '
        '::mod(action="ack", event_id="evt_1", delivery_id="del_2", causation_id="evt_1")'
    )
    error = next(error for error in result.errors if error.field == "delivered_at")
    assert (error.code, error.statement_index) == ("E607", 1)


def test_unique_field_rejects_second_occurrence():
    result = _validate(
        '[T:Event_one] -> [T:Event_target] '
        '::mod(action="send", event_id="evt_1", delivery_id="duplicate")\n'
        '[T:Event_two] -> [T:Event_target] '
        '::mod(action="send", event_id="evt_2", delivery_id="duplicate")'
    )
    error = next(error for error in result.errors if error.code == "E614")
    assert (error.statement_index, error.field) == (1, "delivery_id")


def test_unique_field_exceptions_allow_retry_but_not_duplicate_creation():
    retry = _validate(
        '[T:Event_one] -> [T:Event_target] '
        '::mod(action="send", event_id="evt_1", delivery_id="del_1")\n'
        '[T:Event_retry] -> [T:Event_one] '
        '::mod(action="retry", event_id="evt_1", delivery_id="del_2", causation_id="evt_1")'
    )
    duplicate = _validate(
        '[T:Event_one] -> [T:Event_target] '
        '::mod(action="send", event_id="evt_1", delivery_id="del_1")\n'
        '[T:Event_two] -> [T:Event_target] '
        '::mod(action="send", event_id="evt_1", delivery_id="del_2")'
    )
    assert retry.errors == []
    assert any(error.code == "E614" and error.field == "event_id" for error in duplicate.errors)


def test_same_rule_rejects_changed_logical_event_on_retry():
    result = _validate(
        '[T:Event_one] -> [T:Event_target] '
        '::mod(action="send", event_id="evt_1", delivery_id="del_1")\n'
        '[T:Event_retry] -> [T:Event_one] '
        '::mod(action="retry", event_id="evt_2", delivery_id="del_2", causation_id="evt_1")'
    )
    error = next(error for error in result.errors if error.code == "E615")
    assert (error.statement_index, error.field) == (1, "event_id")
