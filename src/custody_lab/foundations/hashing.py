"""Hash helpers: SHA-256 and BIP340 tagged hashes.

Tagged hashing prefixes the input with SHA256(tag) twice, so a hash computed for one purpose (a
nonce) can never collide with a hash computed for another (a challenge), even on equal input.
"""

from __future__ import annotations

import hashlib


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def tagged_hash(tag: str, data: bytes) -> bytes:
    """BIP340 tagged hash: SHA256(SHA256(tag) || SHA256(tag) || data)."""
    tag_digest = sha256(tag.encode())
    return sha256(tag_digest + tag_digest + data)


def expand_message_xmd(msg: bytes, dst: bytes, length: int) -> bytes:
    """RFC 9380 section 5.3.1 with SHA-256: stretch ``msg`` to ``length`` uniform bytes."""
    ell = -(-length // 32)
    if ell > 255 or length > 65535 or len(dst) > 255:
        raise ValueError("expand_message_xmd: input out of range")
    dst_prime = dst + bytes([len(dst)])
    b0 = sha256(bytes(64) + msg + length.to_bytes(2, "big") + b"\x00" + dst_prime)
    blocks = [sha256(b0 + b"\x01" + dst_prime)]
    for i in range(2, ell + 1):
        mixed = bytes(a ^ b for a, b in zip(b0, blocks[-1], strict=True))
        blocks.append(sha256(mixed + bytes([i]) + dst_prime))
    return b"".join(blocks)[:length]


def hash_to_field(msg: bytes, dst: bytes, modulus: int) -> int:
    """RFC 9380 hash_to_field with count = 1 and L = 48 bytes (128-bit security), reduced mod
    ``modulus``. Used by FROST(secp256k1, SHA-256) for H1, H2 and H3."""
    return int.from_bytes(expand_message_xmd(msg, dst, 48), "big") % modulus
