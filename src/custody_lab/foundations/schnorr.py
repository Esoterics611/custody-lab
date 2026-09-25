"""BIP340 Schnorr signatures over secp256k1, following the BIP's reference algorithm.

EDUCATIONAL, NOT PRODUCTION. Variable-time arithmetic. Production code uses libsecp256k1's
``schnorrsig`` module.

BIP340 differences from textbook Schnorr, each there for Bitcoin:
- Public keys and R are x-only (32 bytes). Of the two points with that x, the one with even y is
  meant, so the signer negates its key or nonce when needed.
- Every hash is a tagged hash, so a nonce hash can never be confused with a challenge hash.
- The nonce is derived from the key, the message and ``aux_rand``. It stays safe if the
  randomness is bad, and it resists side channels when the randomness is good.
"""

from __future__ import annotations

from custody_lab.foundations.ec import SECP256K1, Point
from custody_lab.foundations.hashing import tagged_hash

_C = SECP256K1


def _int(b: bytes) -> int:
    return int.from_bytes(b, "big")


def _bytes32(i: int) -> bytes:
    return i.to_bytes(32, "big")


def _has_even_y(P: Point) -> bool:
    return P.y % 2 == 0


def _mul_g(k: int) -> Point:
    P = _C.mul(k, _C.G)
    assert P is not None
    return P


def lift_x(x: int) -> Point | None:
    """The curve point with this x and an even y, or None if x is not on the curve."""
    if x >= _C.p:
        return None
    y_sq = (pow(x, 3, _C.p) + 7) % _C.p
    y = pow(y_sq, (_C.p + 1) // 4, _C.p)  # square root; valid because p = 3 mod 4
    if pow(y, 2, _C.p) != y_sq:
        return None
    return Point(x, y if y % 2 == 0 else _C.p - y)


def pubkey_gen(seckey: bytes) -> bytes:
    """The 32-byte x-only public key for a 32-byte secret key."""
    d0 = _int(seckey)
    if not 1 <= d0 <= _C.n - 1:
        raise ValueError("secret key must be an integer in [1, n-1]")
    return _bytes32(_mul_g(d0).x)


def sign(msg: bytes, seckey: bytes, aux_rand: bytes) -> bytes:
    """Return the 64-byte signature R.x || s."""
    d0 = _int(seckey)
    if not 1 <= d0 <= _C.n - 1:
        raise ValueError("secret key must be an integer in [1, n-1]")
    if len(aux_rand) != 32:
        raise ValueError("aux_rand must be 32 bytes")
    P = _mul_g(d0)
    d = d0 if _has_even_y(P) else _C.n - d0
    t = bytes(a ^ b for a, b in zip(_bytes32(d), tagged_hash("BIP0340/aux", aux_rand), strict=True))
    k0 = _int(tagged_hash("BIP0340/nonce", t + _bytes32(P.x) + msg)) % _C.n
    if k0 == 0:
        raise RuntimeError("nonce is zero (probability negligible)")
    R = _mul_g(k0)
    k = k0 if _has_even_y(R) else _C.n - k0
    e = _int(tagged_hash("BIP0340/challenge", _bytes32(R.x) + _bytes32(P.x) + msg)) % _C.n
    sig = _bytes32(R.x) + _bytes32((k + e * d) % _C.n)
    if not verify(msg, _bytes32(P.x), sig):
        raise RuntimeError("produced an invalid signature")
    return sig


def verify(msg: bytes, pubkey: bytes, sig: bytes) -> bool:
    """Accept iff s*G - e*P has even y and x-coordinate r."""
    if len(pubkey) != 32:
        raise ValueError("public key must be 32 bytes")
    if len(sig) != 64:
        raise ValueError("signature must be 64 bytes")
    P = lift_x(_int(pubkey))
    r, s = _int(sig[:32]), _int(sig[32:])
    if P is None or r >= _C.p or s >= _C.n:
        return False
    e = _int(tagged_hash("BIP0340/challenge", sig[:32] + pubkey + msg)) % _C.n
    R = _C.add(_C.mul(s, _C.G), _C.mul(_C.n - e, P))
    return R is not None and _has_even_y(R) and R.x == r
