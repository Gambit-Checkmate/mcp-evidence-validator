"""MCP Evidence Validator - declared-vs-observed evidence for MCP servers.

Validates what an MCP server *declares* against what it *actually does* and
produces a tamper-evident SHA-256 hash-chain ledger for auditors.

Public API:
    fingerprint(value)          -> canonical SHA-256 fingerprint
    Ledger                      -> append-only hash chain with
                                   head() and verify(expected_head)
    validate_batch(declared, observed) -> (findings, summary)
"""

from .fingerprint import canonical_json, fingerprint, fingerprint_matches
from .ledger import GENESIS, UNANCHORED, Ledger
from .validator import validate_batch

__version__ = "0.2.0"
__all__ = [
    "canonical_json",
    "fingerprint",
    "fingerprint_matches",
    "GENESIS",
    "UNANCHORED",
    "Ledger",
    "validate_batch",
    "__version__",
]
