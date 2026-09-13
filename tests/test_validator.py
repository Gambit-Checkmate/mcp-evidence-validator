"""Validator end-to-end tests (declared vs observed)."""

import json

from mcp_evidence_validator import validate_batch
from mcp_evidence_validator.cli import main

DECLARED = {
    "server": "fictional-weather",
    "declared_at": "2026-08-01T00:00:00Z",
    "tools": [
        {
            "name": "get_forecast",
            "description": "Return forecast for a city",
            "input_schema": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "days": {"type": "integer", "minimum": 1, "maximum": 7},
                },
                "required": ["city"],
            },
            "permissions": ["read:weather"],
        }
    ],
    "annotations": [
        {
            "tool": "get_forecast",
            "statement": "read-only forecast access",
            "bound_contract": None,  # filled below via helper
        }
    ],
}


def with_bound_annotation(contract: str) -> dict:
    d = json.loads(json.dumps(DECLARED))
    d["annotations"][0]["bound_contract"] = contract
    return d


def make_observed(entries) -> dict:
    return {"server": "fictional-weather", "observations": entries}


def test_clean_batch_no_findings():
    from mcp_evidence_validator.validator import build_contract

    decl = with_bound_annotation(build_contract(DECLARED["tools"][0]))
    obs = make_observed(
        [
            {
                "index": 1,
                "observed_at": "2026-08-02T12:00:00Z",
                "tool": "get_forecast",
                "args": {"city": "Townsville", "days": 3},
                "contract_hash": build_contract(DECLARED["tools"][0]),
            }
        ]
    )
    findings, summary = validate_batch(decl, obs)
    assert findings == []
    assert summary["declared_tools"] == 1
    assert summary["observations"] == 1


def test_unknown_tool_finding():
    obs = make_observed(
        [
            {
                "index": 1,
                "observed_at": "2026-08-02T12:00:00Z",
                "tool": "delete_everything",
                "args": {},
            }
        ]
    )
    findings, _ = validate_batch(DECLARED, obs)
    assert findings[0]["check"] == "unknown_tool"
    assert findings[0]["severity"] == "high"


def test_scope_violation_finding():
    obs = make_observed(
        [
            {
                "index": 2,
                "observed_at": "2026-08-02T12:05:00Z",
                "tool": "get_forecast",
                "args": {"city": "Townsville", "admin_token": "redacted"},
            }
        ]
    )
    findings, _ = validate_batch(DECLARED, obs)
    assert any(f["check"] == "scope_violation" for f in findings)


def test_contract_mutated_finding():
    obs = make_observed(
        [
            {
                "index": 3,
                "observed_at": "2026-08-02T12:10:00Z",
                "tool": "get_forecast",
                "args": {"city": "Townsville"},
                "contract_hash": "sha256:" + "1" * 64,
            }
        ]
    )
    findings, _ = validate_batch(DECLARED, obs)
    assert any(f["check"] == "contract_mutated" for f in findings)


def test_cli_validate_and_verify(tmp_path):
    declared = tmp_path / "declared.json"
    observed = tmp_path / "observed.json"
    out = tmp_path / "evidence.json"
    declared.write_text(json.dumps(DECLARED))
    observed.write_text(json.dumps(make_observed([])))

    rc = main(
        ["validate", "--declared", str(declared), "--observed", str(observed), "--out", str(out)]
    )
    assert rc == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["ledger"] == "mcp-evidence-validator"

    head = json.loads(out.read_text())["blocks"][-1]["hash"]
    rc = main(["verify", "--ledger", str(out), "--expected-head", head])
    assert rc == 0


def test_cli_verify_detects_tamper(tmp_path):
    from mcp_evidence_validator.cli import load_json

    declared = tmp_path / "declared.json"
    observed = tmp_path / "observed.json"
    out = tmp_path / "evidence.json"
    declared.write_text(json.dumps(DECLARED))
    observed.write_text(json.dumps(make_observed([])))
    main(["validate", "--declared", str(declared), "--observed", str(observed), "--out", str(out)])

    head = load_json(str(out))["blocks"][-1]["hash"]
    data = load_json(str(out))
    data["blocks"][0]["record"]["server"] = "tampered"
    out.write_text(json.dumps(data))

    rc = main(["verify", "--ledger", str(out), "--expected-head", head])
    assert rc != 0


def test_cli_version():
    try:
        rc = main(["--version"])
        assert rc in (0, 2)  # argparse exits via SystemExit(0) normally
    except SystemExit as exc:
        assert exc.code == 0
