"""Two-party ECDSA after Lindell (CRYPTO 2017), semi-honest core.

EDUCATIONAL, NOT PRODUCTION. The zero-knowledge proofs that make the protocol secure against a
cheating party are omitted:
- proofs of knowledge of x1, x2, k1 and k2 (with a commitment from P1 first);
- a proof that N is a valid Paillier modulus;
- a proof that ``c_key`` encrypts the discrete log of Q1.

Without them a malicious party can bias the key or extract the other's share. This module shows
the arithmetic that makes two-party ECDSA work; ``cb-mpc`` (C++) is the audited implementation
of the full protocol.

Key sharing is multiplicative, as in the paper: Q = x1 * x2 * G. Neither party ever holds x1*x2.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from custody_lab.foundations.ec import SECP256K1, Point
from custody_lab.foundations.ecdsa import Signature, verify
from custody_lab.mpc import paillier

C = SECP256K1
q = C.n


def _random_scalar() -> int:
    return 1 + secrets.randbelow(q - 1)


def _mul_g(k: int) -> Point:
    P = C.mul(k, C.G)
    assert P is not None
    return P


@dataclass(frozen=True)
class KeyGenMessage1:
    """P1 -> P2 at key generation."""

    Q1: Point
    paillier_public: paillier.PublicKey
    c_key: int  # Enc_P1(x1)


@dataclass(frozen=True)
class SignMessage:
    """P2 -> P1 at signing: P2's nonce point and the encrypted partial signature."""

    R2: Point
    c3: int


class Party1:
    """Holds x1 and the Paillier private key. Receives the final signature."""

    def __init__(self, paillier_bits: int = 2048) -> None:
        self._x1 = _random_scalar()
        self._paillier = paillier.generate_keypair(paillier_bits)
        self.Q: Point | None = None

    def keygen_message(self) -> KeyGenMessage1:
        pk = self._paillier.public
        return KeyGenMessage1(_mul_g(self._x1), pk, pk.encrypt(self._x1))

    def keygen_finish(self, Q2: Point) -> Point:
        Q = C.mul(self._x1, Q2)
        assert Q is not None
        self.Q = Q
        return Q

    def sign_commit(self) -> Point:
        """Round 1: choose k1, send R1 = k1*G."""
        self._k1 = _random_scalar()
        return _mul_g(self._k1)

    def sign_finish(self, z: int, msg: SignMessage) -> Signature:
        """Round 3: decrypt P2's partial signature and remove k1."""
        assert self.Q is not None
        R = C.mul(self._k1, msg.R2)
        assert R is not None
        r = R.x % q
        s_prime = self._paillier.decrypt(msg.c3) % q
        s = pow(self._k1, -1, q) * s_prime % q
        sig = Signature(r, min(s, q - s))  # low-S
        if not verify(self.Q, z, sig):
            raise RuntimeError("P2 sent a bad partial signature")
        return sig


class Party2:
    """Holds x2 and P1's encrypted share c_key. Never sees x1, k1 or the Paillier private key."""

    def __init__(self) -> None:
        self._x2 = _random_scalar()
        self.Q: Point | None = None

    def keygen(self, msg: KeyGenMessage1) -> Point:
        """Store P1's public material; return Q2 = x2*G for P1."""
        self._pk, self._c_key = msg.paillier_public, msg.c_key
        Q = C.mul(self._x2, msg.Q1)
        assert Q is not None
        self.Q = Q
        return _mul_g(self._x2)

    def sign(self, z: int, R1: Point) -> SignMessage:
        """Round 2: c3 = Enc(rho*q + k2^-1 * z) (+) (k2^-1 * r * x2) (x) Enc(x1).

        Decrypted mod q this is k2^-1 * (z + r * x1 * x2). The random rho*q term hides the
        plaintext's size from P1 without changing its value mod q.
        """
        k2 = _random_scalar()
        R = C.mul(k2, R1)
        assert R is not None
        r = R.x % q
        k2_inv = pow(k2, -1, q)
        rho = secrets.randbelow(q * q)
        c1 = self._pk.encrypt(rho * q + k2_inv * z % q)
        c2 = self._pk.mul(self._c_key, k2_inv * r * self._x2 % q)
        return SignMessage(_mul_g(k2), self._pk.add(c1, c2))
