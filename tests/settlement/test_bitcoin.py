import json
from decimal import Decimal
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from custody_lab.foundations import schnorr
from custody_lab.settlement import bitcoin

# BIP 341 wallet test vectors (BIP 341 is BSD-3-Clause), fetched 2026-09-24 from
# https://github.com/bitcoin/bips/blob/master/bip-0341/wallet-test-vectors.json
# sha256 403e19fb81dd1f31e745699216308f61fb403774b2aafa87b631b8f7c042d37f
V = json.loads((Path(__file__).parent / "vectors" / "bip341-wallet-test-vectors.json").read_text())
KEY_PATH = V["keyPathSpending"][0]
TX = bitcoin.parse_transaction(bytes.fromhex(KEY_PATH["given"]["rawUnsignedTx"]))
SPENT = [
    bitcoin.TxOut(u["amountSats"], bytes.fromhex(u["scriptPubKey"]))
    for u in KEY_PATH["given"]["utxosSpent"]
]


def _root(value: str | None) -> bytes | None:
    return bytes.fromhex(value) if value else None


@pytest.mark.parametrize("v", V["scriptPubKey"], ids=lambda v: v["expected"]["bip350Address"][:12])
def test_output_key_tweak(v: dict) -> None:  # type: ignore[type-arg]
    key = bytes.fromhex(v["given"]["internalPubkey"])
    tweaked = bitcoin.taproot_tweak(key, _root(v["intermediary"]["merkleRoot"]))
    assert tweaked.hex() == v["intermediary"]["tweakedPubkey"]
    assert bitcoin.p2tr_script(tweaked).hex() == v["expected"]["scriptPubKey"]


def test_parse_and_serialize_round_trip() -> None:
    assert TX.serialize().hex() == KEY_PATH["given"]["rawUnsignedTx"]


@pytest.mark.parametrize(
    "v", KEY_PATH["inputSpending"], ids=lambda v: f"hash_type={v['given']['hashType']:#04x}"
)
def test_sighash_and_signature(v: dict) -> None:  # type: ignore[type-arg]
    g, im = v["given"], v["intermediary"]
    assert bitcoin.sig_msg(TX, g["txinIndex"], SPENT, g["hashType"]).hex() == im["sigMsg"]
    sighash = bitcoin.taproot_sighash(TX, g["txinIndex"], SPENT, g["hashType"])
    assert sighash.hex() == im["sigHash"]
    # The vector signatures are BIP340 with all-zero aux randomness; chapter 1's signer matches.
    signature = schnorr.sign(sighash, bytes.fromhex(im["tweakedPrivkey"]), bytes(32))
    assert signature == bytes.fromhex(v["expected"]["witness"][0])[:64]


@given(st.integers(min_value=0, max_value=21_000_000 * 100_000_000))
def test_sats_round_trip(sats: int) -> None:
    assert bitcoin.to_sats(bitcoin.to_btc(sats)) == sats


def test_sub_satoshi_amount_is_refused() -> None:
    with pytest.raises(ValueError, match="whole number"):
        bitcoin.to_sats(Decimal("0.000000001"))


@pytest.mark.parametrize(
    "n, encoded", [(0, "00"), (252, "fc"), (253, "fdfd00"), (70000, "fe70110100")]
)
def test_compact_size(n: int, encoded: str) -> None:
    assert bitcoin.compact_size(n).hex() == encoded
