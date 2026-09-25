"""Elliptic-curve arithmetic over prime fields, short Weierstrass form y^2 = x^3 + ax + b.

EDUCATIONAL, NOT PRODUCTION. Affine coordinates, variable-time double-and-add: the running time
leaks the scalar. Production code uses libsecp256k1 (constant-time, Jacobian coordinates).

Two moduli appear and must not be confused:
- ``p`` is the field prime. Point coordinates live in F_p.
- ``n`` is the group order. Scalars (private keys, nonces) live in Z_n.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    """An affine curve point. The point at infinity is represented by ``None``."""

    x: int
    y: int


@dataclass(frozen=True)
class Curve:
    name: str
    p: int
    a: int
    b: int
    G: Point
    n: int

    def is_on_curve(self, P: Point | None) -> bool:
        if P is None:
            return True
        return (P.y * P.y - (P.x**3 + self.a * P.x + self.b)) % self.p == 0

    def neg(self, P: Point | None) -> Point | None:
        if P is None:
            return None
        return Point(P.x, (-P.y) % self.p)

    def add(self, P: Point | None, Q: Point | None) -> Point | None:
        """Chord-and-tangent addition."""
        if P is None:
            return Q
        if Q is None:
            return P
        if P.x == Q.x and (P.y + Q.y) % self.p == 0:
            return None  # P + (-P) = infinity; also covers doubling a point with y = 0
        if P == Q:
            slope = (3 * P.x * P.x + self.a) * pow(2 * P.y, -1, self.p)  # tangent
        else:
            slope = (Q.y - P.y) * pow(Q.x - P.x, -1, self.p)  # chord
        x = (slope * slope - P.x - Q.x) % self.p
        y = (slope * (P.x - x) - P.y) % self.p
        return Point(x, y)

    def mul(self, k: int, P: Point | None) -> Point | None:
        """Scalar multiplication k*P by double-and-add, least significant bit first."""
        k %= self.n
        result: Point | None = None
        addend = P
        while k:
            if k & 1:
                result = self.add(result, addend)
            addend = self.add(addend, addend)
            k >>= 1
        return result

    def points(self) -> list[Point]:
        """Every affine point, by brute force. Only feasible for toy curves."""
        if self.p > 10_000:
            raise ValueError(f"{self.name}: brute-force enumeration needs a toy curve")
        return [
            Point(x, y)
            for x in range(self.p)
            for y in range(self.p)
            if (y * y - (x**3 + self.a * x + self.b)) % self.p == 0
        ]


SECP256K1 = Curve(
    name="secp256k1",
    p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
    a=0,
    b=7,
    G=Point(
        0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
        0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8,
    ),
    n=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141,
)
"""The Bitcoin curve (SEC 2, section 2.4.1)."""

TOY = Curve(name="toy-43", p=43, a=0, b=7, G=Point(2, 12), n=31)
"""Same equation as secp256k1 over F_43. It has 31 points including infinity, a prime order, so
every point except infinity generates the group. Small enough to check by hand."""


def encode_point(P: Point | None) -> bytes:
    """SEC1 compressed encoding (33 bytes) of a secp256k1 point: 0x02/0x03 parity byte || x."""
    if P is None:
        raise ValueError("the point at infinity has no compressed encoding")
    return bytes([2 + (P.y & 1)]) + P.x.to_bytes(32, "big")


def decode_point(data: bytes) -> Point:
    """Inverse of ``encode_point``. The square root works because p = 3 mod 4."""
    if len(data) != 33 or data[0] not in (2, 3):
        raise ValueError("expected a 33-byte SEC1 compressed point")
    C = SECP256K1
    x = int.from_bytes(data[1:], "big")
    y_sq = (pow(x, 3, C.p) + C.b) % C.p
    y = pow(y_sq, (C.p + 1) // 4, C.p)
    if x >= C.p or y * y % C.p != y_sq:
        raise ValueError("x is not the x-coordinate of a curve point")
    return Point(x, y if (y & 1) == data[0] - 2 else C.p - y)
