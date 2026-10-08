"""422 with an envelope and 422 without one must not collapse into 'the agent is down'."""
from orchestration.clients import classify_http


def test_prep_style_422_is_an_output():
    body = {"stage": "prep", "evidence": {"status": "pending"}, "status": "pending"}
    kind, payload = classify_http(422, body)
    assert kind == "output" and payload is body


def test_bare_422_is_a_schema_refusal_not_a_dead_process():
    kind, _ = classify_http(422, {"detail": ["stage must be 'receiving'"]})
    assert kind == "schema_refusal"


def test_404_stays_a_refusal_and_500_stays_unavailable():
    assert classify_http(404, {"detail": "unknown tenant"})[0] == "rejected"
    assert classify_http(503, "down")[0] == "unavailable"


def test_200_pending_is_an_output():
    body = {"stage": "returns", "status": "pending", "evidence": {"status": "pending"}}
    assert classify_http(200, body)[0] == "output"
