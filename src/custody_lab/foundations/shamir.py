"""Shamir secret sharing over Z_q (Shamir 1979).

EDUCATIONAL, NOT PRODUCTION. The secret is the constant term of a random polynomial of degree
t-1, and share i is the polynomial evaluated at x = i. Any t shares determine the polynomial and
therefore the secret; t-1 shares are consistent with every possible secret.

The default modulus is the secp256k1 group order, so a shared secret can be a private key. That
is where Module 2 starts: threshold signing uses the same Lagrange coefficients, but never
reconstructs the key in one place.
"""

from __future__ import annotations

import secrets
from collections.abc import Sequence
from dataclasses import dataclass

from custody_lab.foundations.ec import SECP256K1


@dataclass(frozen=True)
class Share:
    x: int
    y: int


def evaluate(coefficients: Sequence[int], x: int, modulus: int) -> int:
    """Evaluate c0 + c1*x + c2*x^2 + ... mod ``modulus`` by Horner's rule."""
    result = 0
    for c in reversed(coefficients):
        result = (result * x + c) % modulus
    return result


def split(
    secret: int,
    threshold: int,
    count: int,
    modulus: int = SECP256K1.n,
    coefficients: Sequence[int] | None = None,
) -> list[Share]:
    """Split ``secret`` into ``count`` shares, any ``threshold`` of which reconstruct it.

    ``coefficients`` (c1 .. c_{t-1}) are random unless given; pass them only to reproduce a
    worked example.
    """
    if not 1 <= threshold <= count:
        raise ValueError("need 1 <= threshold <= count")
    if count >= modulus:
        raise ValueError("share x-coordinates 1..count must be distinct and non-zero mod modulus")
    if not 0 <= secret < modulus:
        raise ValueError("secret must be in [0, modulus)")
    if coefficients is None:
        coefficients = [secrets.randbelow(modulus) for _ in range(threshold - 1)]
    elif len(coefficients) != threshold - 1:
        raise ValueError(f"need {threshold - 1} coefficients for threshold {threshold}")
    poly = [secret, *coefficients]
    return [Share(x, evaluate(poly, x, modulus)) for x in range(1, count + 1)]


def lagrange_coefficient(i: int, xs: Sequence[int], modulus: int, at: int = 0) -> int:
    """lambda_i = prod over j != i of (at - x_j) / (x_i - x_j) mod ``modulus``."""
    num, den = 1, 1
    for j in xs:
        if j != i:
            num = num * (at - j) % modulus
            den = den * (i - j) % modulus
    return num * pow(den, -1, modulus) % modulus


def reconstruct(shares: Sequence[Share], modulus: int = SECP256K1.n) -> int:
    """Interpolate the polynomial at x = 0. Correct only with at least ``threshold`` shares."""
    xs = [s.x for s in shares]
    if len(set(xs)) != len(xs):
        raise ValueError("share x-coordinates must be distinct")
    return sum(s.y * lagrange_coefficient(s.x, xs, modulus) for s in shares) % modulus
