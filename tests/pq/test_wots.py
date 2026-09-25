"""Teaching WOTS+ and XMSS (FIPS 205, SLH-DSA-SHA2-128f).

Oracles: the NIST ACVP SLH-DSA keyGen vectors (the top-layer XMSS root is PK.root), and RustCrypto
``slh-dsa`` through ``custody_pq`` on fresh seeds. Hypothesis checks sign-and-recover round trips
and the checksum's defence against advancing a chain.
"""

import json
import secrets
from pathlib import Path
from typing import Any

import custody_pq
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from custody_lab.pq import wots

KEYGEN: list[dict[str, Any]] = [
    t
    for t in json.loads((Path(__file__).parent / "vectors" / "acvp-subset.json").read_text())[
        "slh_dsa_keygen"
    ]
    if t["parameterSet"] == "SLH-DSA-SHA2-128f"
]
digests = st.binary(min_size=wots.N, max_size=wots.N)


@pytest.mark.parametrize("t", KEYGEN, ids=lambda t: str(t["tcId"]))
def test_public_root_matches_nist(t: dict[str, Any]) -> None:
    sk_seed, pk_seed = bytes.fromhex(t["skSeed"]), bytes.fromhex(t["pkSeed"])
    assert pk_seed + wots.keygen_root(sk_seed, pk_seed) == bytes.fromhex(t["pk"])


def test_public_root_matches_rustcrypto_on_fresh_seeds() -> None:
    sk_seed, sk_prf, pk_seed = (secrets.token_bytes(wots.N) for _ in range(3))
    _, pk = custody_pq.keygen_internal("SLH-DSA-SHA2-128f", sk_seed, sk_prf, pk_seed)
    assert pk == pk_seed + wots.keygen_root(sk_seed, pk_seed)


def test_checksum_digit_count() -> None:
    assert (wots.LEN1, wots.LEN2, wots.LEN) == (32, 3, 35)
    assert len(wots.digits_with_checksum(bytes(wots.N))) == wots.LEN


@settings(max_examples=10, deadline=None)
@given(digests, st.integers(min_value=0, max_value=2**wots.H_PRIME - 1))
def test_xmss_signature_recovers_the_root(message: bytes, leaf: int) -> None:
    sk_seed, pk_seed = secrets.token_bytes(wots.N), secrets.token_bytes(wots.N)
    root = wots.keygen_root(sk_seed, pk_seed)
    top = wots.top_layer_address
    signature = wots.xmss_sign(message, sk_seed, leaf, pk_seed, top())
    assert wots.xmss_root_from_signature(signature, message, pk_seed, top()) == root
    other = bytes([message[0] ^ 1]) + message[1:]
    assert wots.xmss_root_from_signature(signature, other, pk_seed, top()) != root


@settings(max_examples=20, deadline=None)
@given(digests.filter(lambda m: wots.base_2b(m, wots.LG_W, 1)[0] < wots.W - 1))
def test_advancing_a_message_chain_does_not_forge(message: bytes) -> None:
    """Hash the first chain one step further: that signs a digest whose first digit is one
    higher. The checksum of that digest is one lower, which would need a chain run backwards."""
    sk_seed, pk_seed = secrets.token_bytes(wots.N), secrets.token_bytes(wots.N)
    adrs = wots.top_layer_address()
    adrs.set_type_and_clear(wots.WOTS_HASH)
    public_key = wots.wots_public_key(sk_seed, pk_seed, adrs.copy())
    signature = wots.wots_sign(message, sk_seed, pk_seed, adrs.copy())

    forged_message = bytes([message[0] + 16]) + message[1:]  # first 4-bit digit plus one
    step = adrs.copy()
    step.set_chain(0)
    digit = wots.digits_with_checksum(message)[0]
    forged = [wots.chain(signature[0], digit, 1, pk_seed, step), *signature[1:]]
    recovered = wots.wots_public_key_from_signature(forged, forged_message, pk_seed, adrs.copy())
    assert recovered != public_key
    genuine = wots.wots_public_key_from_signature(signature, message, pk_seed, adrs.copy())
    assert genuine == public_key
