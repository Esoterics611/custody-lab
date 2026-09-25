import csv
from pathlib import Path

import pytest

from custody_lab.foundations import schnorr

# BIP 340 test vectors (BIP 340 is BSD-2-Clause), fetched 2026-09-24 from
# https://github.com/bitcoin/bips/blob/master/bip-0340/test-vectors.csv
# sha256 34c9d1d9c3a88d524bc80778540dc43f8306ec249a7485293063c376db851c2d
with open(Path(__file__).parent / "vectors" / "bip340-test-vectors.csv", newline="") as f:
    VECTORS = list(csv.DictReader(f))


@pytest.mark.parametrize("v", VECTORS, ids=[f"vector-{v['index']}" for v in VECTORS])
def test_bip340_vector(v: dict[str, str]) -> None:
    pubkey = bytes.fromhex(v["public key"])
    msg = bytes.fromhex(v["message"])
    sig = bytes.fromhex(v["signature"])
    if v["secret key"]:
        seckey = bytes.fromhex(v["secret key"])
        assert schnorr.pubkey_gen(seckey) == pubkey
        assert schnorr.sign(msg, seckey, bytes.fromhex(v["aux_rand"])) == sig
    assert schnorr.verify(msg, pubkey, sig) == (v["verification result"] == "TRUE")
