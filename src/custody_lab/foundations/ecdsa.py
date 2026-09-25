"""ECDSA (FIPS 186-5, SEC 1) over any ``Curve``.

EDUCATIONAL, NOT PRODUCTION. Variable-time arithmetic, and the nonce is either random or supplied
by the caller so the chapter can show what nonce reuse does. Production code derives the nonce
deterministically (RFC 6979) inside a constant-time library.

Signing works on a message hash ``z`` already reduced to an integer, the same contract as MPC
signing libraries: the caller hashes the transaction; the signer never sees it.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from custody_lab.foundations.ec import SECP256K1, Curve, Point


@dataclass(frozen=True)
class Signature:
    r: int
    s: int


def generate_keypair(curve: Curve = SECP256K1) -> tuple[int, Point]:
    """Return (d, Q) with d uniform in [1, n-1] and Q = d*G."""
    d = 1 + secrets.randbelow(curve.n - 1)
    Q = curve.mul(d, curve.G)
    assert Q is not None
    return d, Q


def hash_to_int(digest: bytes, curve: Curve = SECP256K1) -> int:
    """Leftmost min(bitlen(n), 8*len(digest)) bits of the digest, as an integer (SEC 1, 4.1.3)."""
    z = int.from_bytes(digest, "big")
    excess = 8 * len(digest) - curve.n.bit_length()
    return z >> excess if excess > 0 else z


def sign(d: int, z: int, curve: Curve = SECP256K1, k: int | None = None) -> Signature:
    """Sign the hash integer ``z`` with private key ``d``.

    ``k`` is the per-signature nonce. Leave it ``None`` for a fresh random nonce; pass it only to
    reproduce a worked example. Reusing ``k`` across two messages reveals ``d``.
    The returned ``s`` is normalised to the lower half of [1, n-1] (BIP146 low-S rule).
    """
    while True:
        nonce = k if k is not None else 1 + secrets.randbelow(curve.n - 1)
        R = curve.mul(nonce, curve.G)
        assert R is not None
        r = R.x % curve.n
        s = pow(nonce, -1, curve.n) * (z + r * d) % curve.n
        if r != 0 and s != 0:
            break
        if k is not None:
            raise ValueError("supplied nonce gives r = 0 or s = 0; choose another")
    if s > curve.n // 2:
        s = curve.n - s
    return Signature(r, s)


def verify(Q: Point, z: int, sig: Signature, curve: Curve = SECP256K1) -> bool:
    """Accept iff x(u1*G + u2*Q) mod n == r, with u1 = z/s and u2 = r/s mod n."""
    if not (1 <= sig.r < curve.n and 1 <= sig.s < curve.n):
        return False
    if not curve.is_on_curve(Q):
        return False
    w = pow(sig.s, -1, curve.n)
    X = curve.add(curve.mul(z * w, curve.G), curve.mul(sig.r * w, Q))
    return X is not None and X.x % curve.n == sig.r
