"""WOTS+ one-time signatures and the XMSS Merkle tree, as FIPS 205 defines them for SLH-DSA.

EDUCATIONAL, NOT PRODUCTION. Parameters are fixed to SLH-DSA-SHA2-128f. The code covers the
two layers SLH-DSA is built from, not the whole scheme (no FORS, no hypertree, no message
hashing):

- **WOTS+** signs one n-byte digest with a single key. Each digit of the digest (and of a
  checksum) is a position along a hash chain. The signer reveals the chain values at those
  positions. The verifier hashes each one onward to the chain's end, and the ends hash to the
  public key.
- **XMSS** is a Merkle tree over 2^h' WOTS+ public keys. Its root is the long-term public key,
  and each signature carries one WOTS+ signature plus the authentication path to the root.

``keygen_root`` computes SLH-DSA's public root, the XMSS root of the top layer. It is checked
against the NIST ACVP SLH-DSA keyGen vectors and against RustCrypto ``slh-dsa`` (``custody_pq``).
Production code uses a FIPS 205 library.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

N = 16  # hash output bytes
H_PRIME = 3  # height of each XMSS tree
D = 22  # layers in the SLH-DSA hypertree; the public root is the XMSS root of layer d - 1
LG_W = 4
W = 2**LG_W  # chain length: 16 values, positions 0..15
LEN1 = 8 * N // LG_W  # 32 message digits
LEN2 = 3  # checksum digits: floor(log2(LEN1 * (W - 1)) / LG_W) + 1
LEN = LEN1 + LEN2

WOTS_HASH, WOTS_PK, TREE, WOTS_PRF = 0, 1, 2, 5  # FIPS 205 address types used here


class Address:
    """The 32-byte FIPS 205 address (ADRS) that makes every hash call in the scheme distinct."""

    def __init__(self) -> None:
        self.data = bytearray(32)

    def copy(self) -> Address:
        other = Address()
        other.data[:] = self.data
        return other

    def _set(self, start: int, end: int, value: int) -> None:
        self.data[start:end] = value.to_bytes(end - start, "big")

    def set_layer(self, layer: int) -> None:
        self._set(0, 4, layer)

    def set_type_and_clear(self, kind: int) -> None:
        self._set(16, 20, kind)
        self._set(20, 32, 0)

    def set_keypair(self, i: int) -> None:
        self._set(20, 24, i)

    def keypair(self) -> int:
        return int.from_bytes(self.data[20:24], "big")

    def set_chain(self, i: int) -> None:  # also the tree height in a TREE address
        self._set(24, 28, i)

    def set_hash(self, i: int) -> None:  # also the tree index in a TREE address
        self._set(28, 32, i)

    def tree_index(self) -> int:
        return int.from_bytes(self.data[28:32], "big")

    def compressed(self) -> bytes:
        """ADRS^c, the 22-byte form hashed by the SHA2 parameter sets (FIPS 205 section 11.2)."""
        d = self.data
        return bytes(d[3:4] + d[8:16] + d[19:20] + d[20:32])


def _sha2(pk_seed: bytes, adrs: Address, message: bytes) -> bytes:
    """PRF, F, H and T_l for security category 1: truncated SHA-256 over a padded seed block."""
    block = pk_seed + bytes(64 - N) + adrs.compressed()
    return hashlib.sha256(block + message).digest()[:N]


def chain(x: bytes, start: int, steps: int, pk_seed: bytes, adrs: Address) -> bytes:
    """Hash ``x`` forward ``steps`` times from position ``start`` of one chain."""
    for j in range(start, start + steps):
        adrs.set_hash(j)
        x = _sha2(pk_seed, adrs, x)
    return x


def base_2b(data: bytes, b: int, out_len: int) -> list[int]:
    """Split ``data`` into ``out_len`` b-bit digits, most significant first."""
    digits, total, bits, pos = [], 0, 0, 0
    for _ in range(out_len):
        while bits < b:
            total = (total << 8) | data[pos]
            pos, bits = pos + 1, bits + 8
        bits -= b
        digits.append((total >> bits) & (2**b - 1))
    return digits


def digits_with_checksum(message: bytes) -> list[int]:
    """The LEN chain positions a WOTS+ signature reveals for an n-byte ``message``.

    The checksum grows when a message digit shrinks. Hash chains only run forward, so anyone
    who advances a message digit would have to move a checksum digit backwards.
    """
    digits = base_2b(message, LG_W, LEN1)
    checksum = sum(W - 1 - d for d in digits) << ((8 - (LEN2 * LG_W) % 8) % 8)
    return digits + base_2b(checksum.to_bytes((LEN2 * LG_W + 7) // 8, "big"), LG_W, LEN2)


def _chain_start(sk_seed: bytes, pk_seed: bytes, adrs: Address, i: int) -> bytes:
    """The secret value at position 0 of chain ``i``: PRF(PK.seed, SK.seed, ADRS)."""
    sk_adrs = adrs.copy()
    sk_adrs.set_type_and_clear(WOTS_PRF)
    sk_adrs.set_keypair(adrs.keypair())
    sk_adrs.set_chain(i)
    return _sha2(pk_seed, sk_adrs, sk_seed)


def _compress(values: list[bytes], pk_seed: bytes, adrs: Address) -> bytes:
    """T_len: hash the LEN chain ends into one WOTS+ public key."""
    pk_adrs = adrs.copy()
    pk_adrs.set_type_and_clear(WOTS_PK)
    pk_adrs.set_keypair(adrs.keypair())
    return _sha2(pk_seed, pk_adrs, b"".join(values))


def wots_public_key(sk_seed: bytes, pk_seed: bytes, adrs: Address) -> bytes:
    ends = []
    for i in range(LEN):
        start = _chain_start(sk_seed, pk_seed, adrs, i)
        adrs.set_chain(i)
        ends.append(chain(start, 0, W - 1, pk_seed, adrs))
    return _compress(ends, pk_seed, adrs)


def wots_sign(message: bytes, sk_seed: bytes, pk_seed: bytes, adrs: Address) -> list[bytes]:
    signature = []
    for i, digit in enumerate(digits_with_checksum(message)):
        start = _chain_start(sk_seed, pk_seed, adrs, i)
        adrs.set_chain(i)
        signature.append(chain(start, 0, digit, pk_seed, adrs))
    return signature


def wots_public_key_from_signature(
    signature: list[bytes], message: bytes, pk_seed: bytes, adrs: Address
) -> bytes:
    ends = []
    for i, digit in enumerate(digits_with_checksum(message)):
        adrs.set_chain(i)
        ends.append(chain(signature[i], digit, W - 1 - digit, pk_seed, adrs))
    return _compress(ends, pk_seed, adrs)


def xmss_node(sk_seed: bytes, i: int, z: int, pk_seed: bytes, adrs: Address) -> bytes:
    """Node ``i`` at height ``z`` of the XMSS tree; height 0 holds the WOTS+ public keys."""
    if z == 0:
        adrs.set_type_and_clear(WOTS_HASH)
        adrs.set_keypair(i)
        return wots_public_key(sk_seed, pk_seed, adrs)
    left = xmss_node(sk_seed, 2 * i, z - 1, pk_seed, adrs)
    right = xmss_node(sk_seed, 2 * i + 1, z - 1, pk_seed, adrs)
    adrs.set_type_and_clear(TREE)
    adrs.set_chain(z)
    adrs.set_hash(i)
    return _sha2(pk_seed, adrs, left + right)


@dataclass(frozen=True)
class XmssSignature:
    leaf: int
    wots: list[bytes]
    auth_path: list[bytes]  # the sibling at each height, leaf to root


def xmss_sign(
    message: bytes, sk_seed: bytes, leaf: int, pk_seed: bytes, adrs: Address
) -> XmssSignature:
    auth_path = [xmss_node(sk_seed, (leaf >> j) ^ 1, j, pk_seed, adrs) for j in range(H_PRIME)]
    adrs.set_type_and_clear(WOTS_HASH)
    adrs.set_keypair(leaf)
    return XmssSignature(leaf, wots_sign(message, sk_seed, pk_seed, adrs), auth_path)


def xmss_root_from_signature(
    signature: XmssSignature, message: bytes, pk_seed: bytes, adrs: Address
) -> bytes:
    """Recompute the tree root: the WOTS+ public key, then one hash per authentication step."""
    adrs.set_type_and_clear(WOTS_HASH)
    adrs.set_keypair(signature.leaf)
    node = wots_public_key_from_signature(signature.wots, message, pk_seed, adrs)
    adrs.set_type_and_clear(TREE)
    adrs.set_hash(signature.leaf)
    for height, sibling in enumerate(signature.auth_path, start=1):
        adrs.set_chain(height)
        index = adrs.tree_index()
        if (signature.leaf >> (height - 1)) & 1 == 0:
            adrs.set_hash(index // 2)
            node = _sha2(pk_seed, adrs, node + sibling)
        else:
            adrs.set_hash((index - 1) // 2)
            node = _sha2(pk_seed, adrs, sibling + node)
    return node


def top_layer_address() -> Address:
    adrs = Address()
    adrs.set_layer(D - 1)
    return adrs


def keygen_root(sk_seed: bytes, pk_seed: bytes) -> bytes:
    """PK.root of SLH-DSA-SHA2-128f: the XMSS root of the hypertree's top layer."""
    return xmss_node(sk_seed, 0, H_PRIME, pk_seed, top_layer_address())
