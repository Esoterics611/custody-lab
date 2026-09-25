"""Paillier encryption (Paillier 1999): additively homomorphic public-key encryption.

EDUCATIONAL, NOT PRODUCTION. No side-channel protection, and key generation does not prove the
modulus is well formed (production two-party ECDSA requires that proof).

The property two-party ECDSA needs: given ciphertexts, anyone can compute
``Enc(a) * Enc(b) = Enc(a + b)`` and ``Enc(a) ** k = Enc(k * a)`` (mod N^2) without the private key.
"""

from __future__ import annotations

import math
import secrets
from dataclasses import dataclass


def is_probable_prime(n: int, rounds: int = 40) -> bool:
    """Miller-Rabin with random bases; error probability at most 4^-rounds."""
    if n < 2:
        return False
    for small in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % small == 0:
            return n == small
    d, r = n - 1, 0
    while d % 2 == 0:
        d, r = d // 2, r + 1
    for _ in range(rounds):
        x = pow(2 + secrets.randbelow(n - 3), d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def generate_prime(bits: int) -> int:
    while True:
        candidate = secrets.randbits(bits) | (1 << (bits - 1)) | 1  # full length, odd
        if is_probable_prime(candidate):
            return candidate


@dataclass(frozen=True)
class PublicKey:
    n: int

    @property
    def n2(self) -> int:
        return self.n * self.n

    def encrypt(self, m: int, r: int | None = None) -> int:
        """Enc(m) = (1 + N)^m * r^N mod N^2, with (1 + N)^m = 1 + mN mod N^2."""
        if not 0 <= m < self.n:
            raise ValueError("plaintext must be in [0, N)")
        if r is None:
            r = 1 + secrets.randbelow(self.n - 1)
        return (1 + m * self.n) * pow(r, self.n, self.n2) % self.n2

    def add(self, c1: int, c2: int) -> int:
        """Enc(a) (+) Enc(b) = Enc(a + b mod N)."""
        return c1 * c2 % self.n2

    def mul(self, c: int, k: int) -> int:
        """k (x) Enc(a) = Enc(k * a mod N)."""
        return pow(c, k, self.n2)


@dataclass(frozen=True)
class PrivateKey:
    public: PublicKey
    lam: int
    mu: int

    def decrypt(self, c: int) -> int:
        """m = L(c^lambda mod N^2) * mu mod N, with L(u) = (u - 1) / N."""
        n = self.public.n
        return (pow(c, self.lam, self.public.n2) - 1) // n * self.mu % n


def generate_keypair(bits: int = 2048) -> PrivateKey:
    """An N of ``bits`` bits from two primes of half that length. 2048 bits takes a few seconds."""
    while True:
        p, q = generate_prime(bits // 2), generate_prime(bits // 2)
        n = p * q
        if p != q and n.bit_length() == bits and math.gcd(n, (p - 1) * (q - 1)) == 1:
            break
    lam = math.lcm(p - 1, q - 1)
    return PrivateKey(PublicKey(n), lam, pow(lam, -1, n))
