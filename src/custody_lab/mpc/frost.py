"""FROST threshold Schnorr signatures, RFC 9591 ciphersuite FROST(secp256k1, SHA-256).

EDUCATIONAL, NOT PRODUCTION. Checked against the RFC's test vectors. Two limits:
- This ciphersuite is not BIP340. Its signatures are 65 bytes (compressed R || z) and do not
  spend Taproot outputs.
- The demo therefore signs with the Zcash Foundation crate's ``frost-secp256k1-tr`` variant, via
  ``custody_frost``.

Protocol shape (t-of-n, coordinator-based):
1. Round 1: each signer draws two nonces (hiding d, binding e) and publishes D = dG, E = eG.
2. The coordinator fixes the message and the commitment list.
3. Round 2: each signer derives per-signer binding factors rho_i from everything public, and
   returns z_i = d_i + e_i * rho_i + lambda_i * s_i * c.
4. The coordinator sums the z_i.

The binding factor ties each nonce to this exact message and signer set, which defeats the
nonce-manipulation attack on the naive two-party Schnorr of chapter 1.
"""

from __future__ import annotations

import secrets
from collections.abc import Sequence
from dataclasses import dataclass

from custody_lab.foundations.ec import SECP256K1, Point, encode_point
from custody_lab.foundations.hashing import hash_to_field, sha256
from custody_lab.foundations.shamir import lagrange_coefficient

C = SECP256K1
CONTEXT = b"FROST-secp256k1-SHA256-v1"


def _scalar(i: int) -> bytes:
    return i.to_bytes(32, "big")


def H1(m: bytes) -> int:
    return hash_to_field(m, CONTEXT + b"rho", C.n)


def H2(m: bytes) -> int:
    return hash_to_field(m, CONTEXT + b"chal", C.n)


def H3(m: bytes) -> int:
    return hash_to_field(m, CONTEXT + b"nonce", C.n)


def H4(m: bytes) -> bytes:
    return sha256(CONTEXT + b"msg" + m)


def H5(m: bytes) -> bytes:
    return sha256(CONTEXT + b"com" + m)


@dataclass(frozen=True)
class Nonces:
    hiding: int
    binding: int


@dataclass(frozen=True)
class Commitment:
    identifier: int
    hiding: Point
    binding: Point


def nonce_generate(secret: int, random_bytes: bytes | None = None) -> int:
    """H3(random || secret): stays unpredictable even if the random bytes are weak."""
    if random_bytes is None:
        random_bytes = secrets.token_bytes(32)
    return H3(random_bytes + _scalar(secret))


def commit(
    identifier: int,
    signing_share: int,
    hiding_randomness: bytes | None = None,
    binding_randomness: bytes | None = None,
) -> tuple[Nonces, Commitment]:
    """Round 1. The randomness arguments exist only to reproduce test vectors."""
    nonces = Nonces(
        nonce_generate(signing_share, hiding_randomness),
        nonce_generate(signing_share, binding_randomness),
    )
    D, E = C.mul(nonces.hiding, C.G), C.mul(nonces.binding, C.G)
    assert D is not None and E is not None
    return nonces, Commitment(identifier, D, E)


def binding_factor_input(
    group_public_key: Point, commitments: Sequence[Commitment], msg: bytes, identifier: int
) -> bytes:
    encoded = b"".join(
        _scalar(c.identifier) + encode_point(c.hiding) + encode_point(c.binding)
        for c in sorted(commitments, key=lambda c: c.identifier)
    )
    prefix = encode_point(group_public_key) + H4(msg) + H5(encoded)
    return prefix + _scalar(identifier)


def binding_factors(
    group_public_key: Point, commitments: Sequence[Commitment], msg: bytes
) -> dict[int, int]:
    return {
        c.identifier: H1(binding_factor_input(group_public_key, commitments, msg, c.identifier))
        for c in commitments
    }


def group_commitment(commitments: Sequence[Commitment], rho: dict[int, int]) -> Point:
    R: Point | None = None
    for c in commitments:
        R = C.add(R, C.add(c.hiding, C.mul(rho[c.identifier], c.binding)))
    if R is None:
        raise ValueError("group commitment is the identity")
    return R


def challenge(R: Point, group_public_key: Point, msg: bytes) -> int:
    return H2(encode_point(R) + encode_point(group_public_key) + msg)


def sign(
    identifier: int,
    signing_share: int,
    nonces: Nonces,
    group_public_key: Point,
    commitments: Sequence[Commitment],
    msg: bytes,
) -> int:
    """Round 2: this signer's share z_i."""
    rho = binding_factors(group_public_key, commitments, msg)
    R = group_commitment(commitments, rho)
    lam = lagrange_coefficient(identifier, [c.identifier for c in commitments], C.n)
    c = challenge(R, group_public_key, msg)
    return (nonces.hiding + nonces.binding * rho[identifier] + lam * signing_share * c) % C.n


def aggregate(
    group_public_key: Point, commitments: Sequence[Commitment], msg: bytes, shares: Sequence[int]
) -> tuple[Point, int]:
    """Coordinator: the signature is (R, sum of z_i)."""
    R = group_commitment(commitments, binding_factors(group_public_key, commitments, msg))
    return R, sum(shares) % C.n


def verify(group_public_key: Point, msg: bytes, signature: tuple[Point, int]) -> bool:
    """Plain Schnorr verification: z*G == R + c*PK."""
    R, z = signature
    c = challenge(R, group_public_key, msg)
    return C.mul(z, C.G) == C.add(R, C.mul(c, group_public_key))


def encode_signature(signature: tuple[Point, int]) -> bytes:
    R, z = signature
    return encode_point(R) + _scalar(z)
