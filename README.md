# MCP Evidence Validator

[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/14122/badge)](https://www.bestpractices.dev/projects/14122)
[![OpenSSF Baseline](https://www.bestpractices.dev/projects/14122/baseline)](https://www.bestpractices.dev/projects/14122)

Validate what an MCP server *declares* against what it *actually does*, and produce a tamper-evident evidence record you can hand to an auditor.

**Status:** v0.2 (installable)  ·  **License:** Apache-2.0  ·  **Language:** Python 3.10+ (stdlib only, zero dependencies)

---

## Why

Model Context Protocol (MCP) is the industry standard for connecting AI agents to tools and data. It is now governed by the Agentic AI Foundation (AAIF) under the Linux Foundation, with 97M+ monthly SDK downloads and 10,000+ active public servers.

But the protocol leaves the *evidence* problem open:

- A server declares tool schemas and permissions, but nothing verifies those declarations against observed runtime behaviour.
- An annotation can be accurate at declaration time and silently stale minutes later, when the contract it was bound to mutates underneath it.
- MCP has already seen the first malicious server (Sept 2025), CVE-2025-6514 (CVSS 9.6, RCE), and a hosting-platform breach affecting 3,000+ downstream applications.

The **declared-vs-observed gap** is the measurement finding that matters. This validator is a reference implementation for closing it.

## What it does

1. **Captures declarations** - the tool schemas, permissions, and annotations an MCP server publishes.
2. **Observes reality** - the tool invocations, argument shapes, and contract hashes seen at runtime.
3. **Checks the gap** - declared annotation still bound? Contract mutated since declaration? Privilege use inside declared scope?
4. **Produces a tamper-evident ledger** - every check result is committed to a SHA-256 hash chain. Changing any earlier record invalidates every record after it.

## Install

```bash
pip install mcp-evidence-validator      # from PyPI once published
# or from source:
git clone https://github.com/narko4u/mcp-evidence-validator.git
cd mcp-evidence-validator
pip install .
```

No dependencies — Python 3.10+ standard library only.

## Quickstart

After installing from source above, run these commands from the repository
root so the bundled fictional example files are available:

```bash
# Compare a declared manifest against observed runtime records
mcp-ev-validate validate --declared examples/fictional-server-declared.json --observed examples/fictional-server-observed.json --out evidence.json

# Audit a ledger later: prove no record was altered
mcp-ev-validate verify --ledger evidence.json
```

The `validate` command prints a JSON report. Its `summary` contains:

```json
{
  "declared_tools": 2,
  "observations": 3,
  "findings": 2,
  "checks": [
    "bound_unmutated",
    "contract_mutated",
    "scope_violation"
  ]
}
```

The report's `findings` array describes the deliberately undeclared
`admin_token` argument in observation 2 and the changed contract in
observation 3. Validation exits **0** when the report is produced, even when
it contains findings; inspect the report to assess the observed behaviour.

The same command writes `evidence.json` in the current directory, linking
the declaration, observation batch, and report into a SHA-256 hash chain.
The `verify` command checks that chain and, for this example, exits **0**
with:

```text
ledger intact: 3 blocks, chain verified
block types: {"declaration": 1, "observation_batch": 1, "report": 1}
```

An intact ledger proves the recorded evidence has not changed, not that the
observations are free of findings. You can also replace `mcp-ev-validate`
with `python -m mcp_evidence_validator` in either command above.

## Concepts

| Term | Meaning |
|------|---------|
| Declaration | What a server publishes: tool name, description, input schema, permission scope |
| Contract | A canonical, hashable form of a declaration (canonical JSON → SHA-256) |
| Annotation | A statement binding a declaration to a contract (e.g. "this tool is scoped to read-only") |
| Observation | A runtime fact: invocation record, argument values, contract hash at call time |
| Finding | A measurable gap between declaration and observation |
| Ledger | An append-only SHA-256 hash chain over every captured record |

## Check types

- **Bound, contract unmutated** - healthy baseline: annotation still matches the contract it was declared against.
- **Bound, contract since mutated** - finding: the annotation was accurate at declaration time but is stale because the contract moved underneath it. Pairs with a review-scheduling gate.
- **Observed outside declared scope** - finding: runtime behaviour exceeds what the declaration permits (arguments, tools, or permissions not present in the declaration).

## Roadmap

- [x] Installable package (v0.2, `mcp-ev-validate` CLI, `verify` subcommand)
- [x] Test suite + CI (Python 3.10–3.12)
- [ ] **A2A agent-card validation (v0.3)** — validate A2A agent cards
      (`.well-known/agent-card.json`) against observed agent behaviour:
      declared capabilities vs runtime delegation, auth requirements honoured,
      signed-card identity checks. A2A is an AAIF-hosted project (joined
      Aug 2026); this extends the declared-vs-observed evidence ladder to the
      agent-to-agent boundary. Directly addresses the open A2A identity
      verification gap (a2aproject/A2A issue #1672).
- [ ] MCP client integration (intercept tool-call records via a lightweight proxy)
- [ ] Automated review-scheduling gate (re-validate annotations on contract change)
- [ ] Report renderers (HTML, PDF)
- [ ] Policy pack support (declare what "acceptable" means per environment)

## Project status

This is the public face of an evidence-engineering programme. The core ideas are exercised in production-grade systems elsewhere in the organisation; this repository is the open, reference implementation. It contains no proprietary code and no real client data. All examples are fictional.

## Security

See [SECURITY.md](SECURITY.md) for the vulnerability reporting policy. Security issues are handled privately — do not open a public issue.

## Verifying releases

Releases are signed with **sigstore keyless signing** (GitHub Actions
workload identity). Each release contains:

- `SHA256SUMS` — hashes of every release asset
- `SHA256SUMS.sig` — the cosign signature over `SHA256SUMS`
- `SHA256SUMS.pem` — the ephemeral signing certificate

To verify a release (requires the [cosign CLI](https://docs.sigstore.dev/cosign/installation/)):

```sh
cosign verify-blob \
  --cert SHA256SUMS.pem \
  --signature SHA256SUMS.sig \
  --certificate-identity "https://github.com/narko4u/mcp-evidence-validator/.github/workflows/release.yml@refs/tags/v0.2.1" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  SHA256SUMS
```

The expected signer identity is the repository's `release.yml` workflow
running under the release tag (GitHub Actions OIDC, issuer
`https://token.actions.githubusercontent.com`). After the signature
verifies, check the asset hashes:

```sh
sha256sum -c SHA256SUMS
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Contributions welcome under the Apache-2.0 licence; please follow the Code of Conduct.
