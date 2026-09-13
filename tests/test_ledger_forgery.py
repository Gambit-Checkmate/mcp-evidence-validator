"""Forgery tests: three edits that a self-describing chain cannot detect.

Each test builds a ledger the way the CLI does, applies one edit, and asserts
that the edit is detected only when verify is given the head recorded before
the edit. The bare chain walk is asserted too, so the tests document exactly
how much the chain proves on its own.
"""

import json

from mcp_evidence_validator import UNANCHORED, Ledger

DECLARED = {
    "server": "fictional-weather",
    "tools": [{"name": "get_forecast", "permissions": ["read:weather"]}],
}
OBSERVED = {"invocations": [{"tool": "get_forecast", "arguments": {"city": "Perth"}}]}
REPORT = {
    "summary": {"findings": 1},
    "findings": [{"check": "scope_violation", "severity": "high"}],
}


def build() -> Ledger:
    led = Ledger()
    led.append("declaration", DECLARED)
    led.append("observation_batch", OBSERVED)
    led.append("report", REPORT)
    return led


def test_full_rewrite_forgery_defeats_the_bare_chain():
    led = build()
    head = led.head()

    forged = Ledger()
    for position, block in enumerate(led):
        record = block["record"]
        if position == 0:
            record = json.loads(
                json.dumps(record).replace("read:weather", "ADMIN_WRITE:*")
            )
        forged.append(block["type"], record)

    assert forged.verify(UNANCHORED) == []
    problems = forged.verify(head)
    assert problems, "a replayed chain must not verify against the recorded head"
    assert "head mismatch" in problems[0]


def test_tail_truncation_removes_the_findings():
    led = build()
    head = led.head()

    truncated = Ledger()
    for block in list(led)[:-1]:
        truncated.append(block["type"], block["record"])

    assert len(truncated) == 2
    assert truncated.verify(UNANCHORED) == []
    assert truncated.verify(head), "a shortened ledger must not verify against the head"


def test_published_prev_hash_and_index_are_checked():
    led = build()
    head = led.head()
    for block in led:
        block["prev_hash"] = "sha256:" + "f" * 64
        block["index"] = 999

    problems = led.verify(head)
    assert any("prev_hash field says" in problem for problem in problems)
    assert any("index field says" in problem for problem in problems)


def test_intact_ledger_verifies_against_its_head():
    led = build()
    assert led.verify(led.head()) == []


def test_head_of_empty_ledger_is_genesis():
    from mcp_evidence_validator import GENESIS

    assert Ledger().head() == GENESIS
