"""Merkle-sum tree over client liabilities, with per-client inclusion proofs.

EDUCATIONAL, NOT PRODUCTION. Each leaf commits to one client's balance under a per-client salt.
Each parent commits to **both** children's hashes **and both children's sums**, and carries their
total. The root therefore commits to the total liabilities.

A client given its salt and proof recomputes the path to the published root. That checks two
things:
- its balance is included;
- no sibling on its path carries a negative sum.

Committing to both child sums closes the flaw in the first Merkle-sum proposal, where only the
total was hashed, so a custodian could shift value between siblings and hide a shortfall.

Balances are ``Decimal`` BTC at the interface; hashing uses exact integer satoshis.
"""

from __future__ import annotations

import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from custody_lab.foundations.hashing import tagged_hash
from custody_lab.settlement.bitcoin import to_btc, to_sats

LEAF_TAG, NODE_TAG = "custody-lab/por-leaf", "custody-lab/por-node"


@dataclass(frozen=True)
class Node:
    hash: bytes
    sats: int

    @property
    def total(self) -> Decimal:
        return to_btc(self.sats)


@dataclass(frozen=True)
class ProofStep:
    sibling: Node
    sibling_is_left: bool


@dataclass(frozen=True)
class InclusionProof:
    client_id: str
    balance: Decimal
    salt: bytes
    path: tuple[ProofStep, ...]


def _sats_bytes(sats: int) -> bytes:
    if sats < 0:
        raise ValueError("negative sum")
    return sats.to_bytes(8, "big")


def leaf(client_id: str, balance: Decimal, salt: bytes) -> Node:
    sats = to_sats(balance)
    data = salt + client_id.encode() + b"\x00" + _sats_bytes(sats)
    return Node(tagged_hash(LEAF_TAG, data), sats)


def parent(left: Node, right: Node) -> Node:
    data = left.hash + _sats_bytes(left.sats) + right.hash + _sats_bytes(right.sats)
    return Node(tagged_hash(NODE_TAG, data), left.sats + right.sats)


class MerkleSumTree:
    def __init__(self, balances: Mapping[str, Decimal]) -> None:
        if any(b < 0 for b in balances.values()):
            raise ValueError("liabilities cannot be negative")
        self.salts = {c: secrets.token_bytes(32) for c in balances}
        self._clients = sorted(balances)
        leaves = [leaf(c, balances[c], self.salts[c]) for c in self._clients]
        while len(leaves) & (len(leaves) - 1) or not leaves:  # pad to a power of two
            leaves.append(Node(secrets.token_bytes(32), 0))  # zero-balance filler
        self._levels = [leaves]
        while len(self._levels[-1]) > 1:
            level = self._levels[-1]
            self._levels.append([parent(level[i], level[i + 1]) for i in range(0, len(level), 2)])
        self._balances = dict(balances)

    @property
    def root(self) -> Node:
        return self._levels[-1][0]

    def proof(self, client_id: str) -> InclusionProof:
        index = self._clients.index(client_id)
        path = []
        for level in self._levels[:-1]:
            sibling = index ^ 1
            path.append(ProofStep(level[sibling], sibling_is_left=sibling < index))
            index //= 2
        return InclusionProof(
            client_id, self._balances[client_id], self.salts[client_id], tuple(path)
        )


def verify(proof: InclusionProof, root: Node) -> bool:
    """Recompute the root from the client's own leaf; reject negative sibling sums."""
    node = leaf(proof.client_id, proof.balance, proof.salt)
    for step in proof.path:
        if step.sibling.sats < 0:
            return False
        node = parent(step.sibling, node) if step.sibling_is_left else parent(node, step.sibling)
    return node == root
