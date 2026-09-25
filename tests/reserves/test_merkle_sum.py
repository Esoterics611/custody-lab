"""Merkle-sum tree tests.

No published test vectors exist for this construction. The oracles are:
- an independent derivation of the root from the documented byte layout, using hashlib only;
- the Hu, Zhang and Guo (2019) attack on sum trees that hash only the parent total, which must
  fail against this tree;
- Hypothesis properties over arbitrary ledgers.
"""

import hashlib
from dataclasses import replace
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from custody_lab.reserves.merkle_sum import MerkleSumTree, Node, leaf, parent, verify
from custody_lab.settlement.bitcoin import to_btc

LEDGER = {
    "alpha-capital": Decimal("1.15"),
    "beta-fund": Decimal("1.50"),
    "gamma-treasury": Decimal("1.00"),
    "delta-trading": Decimal("0.50"),
}


def _tagged(tag: str, data: bytes) -> bytes:
    prefix = hashlib.sha256(tag.encode()).digest()
    return hashlib.sha256(prefix + prefix + data).digest()


def _u64(n: int) -> bytes:
    return n.to_bytes(8, "big")


def test_root_matches_an_independent_derivation() -> None:
    tree = MerkleSumTree(LEDGER)
    level = []
    for client in sorted(LEDGER):
        sats = int(LEDGER[client] * 100_000_000)
        data = tree.salts[client] + client.encode() + b"\x00" + _u64(sats)
        level.append((_tagged("custody-lab/por-leaf", data), sats))
    while len(level) > 1:
        level = [
            (_tagged("custody-lab/por-node", lh + _u64(ls) + rh + _u64(rs)), ls + rs)
            for (lh, ls), (rh, rs) in zip(level[::2], level[1::2], strict=True)
        ]
    assert tree.root == Node(*level[0])
    assert tree.root.total == Decimal("4.15")


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=12),
        st.integers(min_value=0, max_value=2_100_000_000_000_000),
        min_size=1,
        max_size=20,
    )
)
def test_every_client_verifies_and_the_root_carries_the_total(sats: dict[str, int]) -> None:
    tree = MerkleSumTree({client: to_btc(amount) for client, amount in sats.items()})
    assert tree.root.sats == sum(sats.values())
    assert all(verify(tree.proof(client), tree.root) for client in sats)


def test_a_changed_balance_salt_or_client_id_fails() -> None:
    tree = MerkleSumTree(LEDGER)
    proof = tree.proof("beta-fund")
    assert verify(proof, tree.root)
    assert not verify(replace(proof, balance=proof.balance - Decimal("0.00000001")), tree.root)
    assert not verify(replace(proof, salt=bytes(32)), tree.root)
    assert not verify(replace(proof, client_id="beta-funds"), tree.root)


def test_a_negative_sibling_sum_is_rejected() -> None:
    tree = MerkleSumTree(LEDGER)
    proof = tree.proof("beta-fund")
    first = proof.path[0]
    negative = replace(first, sibling=Node(first.sibling.hash, -1))
    assert not verify(replace(proof, path=(negative, *proof.path[1:])), tree.root)


def test_negative_liabilities_are_refused() -> None:
    with pytest.raises(ValueError, match="negative"):
        MerkleSumTree({"alpha-capital": Decimal("-0.1")})


def _total_only_parent(left: Node, right: Node) -> Node:
    """The parent of the original Merkle-sum proposal: it hashes the total, not each child's sum."""
    total = left.sats + right.sats
    return Node(_tagged("custody-lab/por-node", _u64(total) + left.hash + right.hash), total)


def test_understated_total_passes_a_total_only_tree_but_fails_this_one() -> None:
    """Hu, Zhang and Guo (2019): publish max(a, b) instead of a + b, and show each client a
    sibling sum that makes its own path add up to the published total."""
    alice = leaf("alice", Decimal("1"), bytes(32))
    bob = leaf("bob", Decimal("3"), bytes(32))
    claimed = max(alice.sats, bob.sats)  # 3 BTC published; 4 BTC owed

    root = Node(_tagged("custody-lab/por-node", _u64(claimed) + alice.hash + bob.hash), claimed)
    assert _total_only_parent(alice, Node(bob.hash, claimed - alice.sats)) == root
    assert _total_only_parent(Node(alice.hash, claimed - bob.sats), bob) == root

    for_alice = parent(alice, Node(bob.hash, claimed - alice.sats))
    for_bob = parent(Node(alice.hash, claimed - bob.sats), bob)
    assert for_alice.sats == for_bob.sats == claimed
    assert for_alice.hash != for_bob.hash  # no single root satisfies both clients
    assert parent(alice, bob).sats == alice.sats + bob.sats
