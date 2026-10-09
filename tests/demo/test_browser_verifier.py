"""The dashboard's TypeScript proof check agrees with the Python Merkle-sum tree.

``web/src/reserves.ts`` shares no code with ``custody_lab.reserves.merkle_sum``: it is a second
implementation from the same encoding. These tests feed it, under Node, the proofs the pipeline
publishes and compare the root it recomputes with the Python root.
"""

import json
import shutil
import subprocess
from decimal import Decimal
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from custody_lab.demo.pipeline import LEDGER, published_proof
from custody_lab.reserves.merkle_sum import MerkleSumTree

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not on PATH")
HARNESS = "web/tests/verify-proofs.ts"


def _browser_roots(
    tree: MerkleSumTree, claims: dict[str, str] | None = None
) -> dict[str, dict[str, Any]]:
    document = {
        "proofs": [published_proof(tree.proof(c)) for c in tree.salts],
        "claims": claims or {},
    }
    done = subprocess.run(
        ["node", HARNESS], input=json.dumps(document), capture_output=True, text=True, check=True
    )
    roots: dict[str, dict[str, Any]] = json.loads(done.stdout)
    return roots


def test_every_client_reaches_the_python_root_and_total() -> None:
    tree = MerkleSumTree(LEDGER)

    roots = _browser_roots(tree)

    assert roots.keys() == LEDGER.keys()
    for root in roots.values():
        assert root == {"root": tree.root.hash.hex(), "sats": str(tree.root.sats)}


def test_a_client_claiming_one_satoshi_more_misses_the_root() -> None:
    tree = MerkleSumTree(LEDGER)

    roots = _browser_roots(tree, {"beta-fund": "1.50000001"})

    assert roots["beta-fund"]["root"] != tree.root.hash.hex()
    assert roots["alpha-capital"]["root"] == tree.root.hash.hex()


@settings(max_examples=10, deadline=None)  # each example starts Node
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=12),
        st.integers(0, 21_000_000 * 100_000_000).map(lambda s: Decimal(s) / 100_000_000),
        min_size=1,
        max_size=9,
    )
)
def test_any_ledger_gives_the_same_root_in_both_languages(ledger: dict[str, Decimal]) -> None:
    tree = MerkleSumTree(ledger)

    roots = _browser_roots(tree)

    assert {r["root"] for r in roots.values()} == {tree.root.hash.hex()}
