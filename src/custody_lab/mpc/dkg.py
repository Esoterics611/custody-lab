"""Distributed key generation (Pedersen DKG with Feldman commitments) and proactive refresh.

EDUCATIONAL, NOT PRODUCTION. All participants run in one process here, and private channels and
broadcast are assumed.

DKG: every participant deals a Shamir sharing of its own random secret a_i0. Each participant's
final share is the sum of the sub-shares it received. The group key is sum(a_i0) * G, a secret
nobody ever held.
- **Feldman commitments** (a_ik * G) let each receiver check its sub-share without learning the
  polynomial.
- **Proof of knowledge** of a_i0 stops a participant from choosing its contribution after seeing
  the others' (the rogue-key attack).

Refresh: every participant deals a sharing of **zero**. Adding the sub-shares changes every share,
leaves the group key unchanged, and makes old shares useless in combination with new ones.
"""

from __future__ import annotations

import secrets
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from custody_lab.foundations.ec import SECP256K1, Point, encode_point
from custody_lab.foundations.hashing import tagged_hash
from custody_lab.foundations.shamir import evaluate

C = SECP256K1
POK_TAG = "custody-lab/dkg-proof-of-knowledge"


@dataclass(frozen=True)
class Round1Package:
    """Broadcast by participant ``identifier``."""

    identifier: int
    commitments: tuple[Point | None, ...]  # a_ik * G for k = 0..t-1; a_i0 * G is None on refresh
    proof: tuple[Point, int] | None  # Schnorr proof of knowledge of a_i0 (DKG only)


def _pok_challenge(identifier: int, A: Point, R: Point) -> int:
    data = identifier.to_bytes(2, "big") + encode_point(A) + encode_point(R)
    return int.from_bytes(tagged_hash(POK_TAG, data), "big") % C.n


def _expected_share_point(commitments: Sequence[Point | None], x: int) -> Point | None:
    """sum_k C_k * x^k: the public image f(x)*G of the dealer's polynomial at x."""
    total: Point | None = None
    for k, Ck in enumerate(commitments):
        total = C.add(total, C.mul(pow(x, k, C.n), Ck))
    return total


class Dealer:
    """One participant's contribution: a random polynomial of degree t-1."""

    def __init__(self, identifier: int, threshold: int, refresh: bool = False) -> None:
        self.identifier = identifier
        first = 0 if refresh else 1 + secrets.randbelow(C.n - 1)
        self._coefficients = [first] + [secrets.randbelow(C.n) for _ in range(threshold - 1)]
        self._refresh = refresh

    def round1(self) -> Round1Package:
        commitments = tuple(C.mul(a, C.G) for a in self._coefficients)
        proof = None
        if not self._refresh:
            A = commitments[0]
            k = 1 + secrets.randbelow(C.n - 1)
            R = C.mul(k, C.G)
            assert A is not None and R is not None
            proof = (R, (k + self._coefficients[0] * _pok_challenge(self.identifier, A, R)) % C.n)
        return Round1Package(self.identifier, commitments, proof)

    def share_for(self, x: int) -> int:
        """Round 2, sent privately to participant x: f_i(x)."""
        return evaluate(self._coefficients, x, C.n)


def check_round1(pkg: Round1Package, refresh: bool = False) -> None:
    A = pkg.commitments[0]
    if refresh:
        if A is not None:
            raise ValueError(f"participant {pkg.identifier}: refresh must share zero")
        return
    if A is None or pkg.proof is None:
        raise ValueError(f"participant {pkg.identifier}: missing commitment or proof")
    R, mu = pkg.proof
    c = _pok_challenge(pkg.identifier, A, R)
    if C.mul(mu, C.G) != C.add(R, C.mul(c, A)):
        raise ValueError(f"participant {pkg.identifier}: bad proof of knowledge")


def combine(
    me: int, packages: Mapping[int, Round1Package], received: Mapping[int, int]
) -> tuple[int, Point | None]:
    """Verify every sub-share against its dealer's commitments; return (my share, sum of a_i0*G).

    The second value is the group public key after a DKG, and the identity (None) after a
    refresh.
    """
    share, group_key = 0, None
    for i, pkg in packages.items():
        if C.mul(received[i], C.G) != _expected_share_point(pkg.commitments, me):
            raise ValueError(f"sub-share from participant {i} does not match its commitments")
        share = (share + received[i]) % C.n
        group_key = C.add(group_key, pkg.commitments[0])
    return share, group_key


def run(threshold: int, count: int) -> tuple[dict[int, int], Point]:
    """Simulate a full DKG among participants 1..count; return their shares and the group key."""
    dealers = {i: Dealer(i, threshold) for i in range(1, count + 1)}
    packages = {i: d.round1() for i, d in dealers.items()}
    for pkg in packages.values():
        check_round1(pkg)
    shares, keys = {}, set()
    for me in dealers:
        share, group_key = combine(me, packages, {i: d.share_for(me) for i, d in dealers.items()})
        shares[me] = share
        keys.add(group_key)
    (group_key,) = keys  # every participant computed the same key
    assert group_key is not None
    return shares, group_key


def refresh(shares: Mapping[int, int], threshold: int) -> dict[int, int]:
    """Proactive refresh: every holder deals a sharing of zero and adds what it receives."""
    dealers = {i: Dealer(i, threshold, refresh=True) for i in shares}
    packages = {i: d.round1() for i, d in dealers.items()}
    for pkg in packages.values():
        check_round1(pkg, refresh=True)
    new_shares = {}
    for me, old in shares.items():
        delta, identity = combine(me, packages, {i: d.share_for(me) for i, d in dealers.items()})
        assert identity is None
        new_shares[me] = (old + delta) % C.n
    return new_shares
