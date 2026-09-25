import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from custody_lab.foundations import schnorr
from custody_lab.mpc.cluster import SigningCluster
from custody_lab.policy import authorisation
from custody_lab.settlement import bitcoin, chain, transfer
from custody_lab.settlement.regtest import RegtestNode

pytestmark = [
    pytest.mark.regtest,
    pytest.mark.skipif(shutil.which("bitcoind") is None, reason="bitcoind not on PATH"),
]


def test_frost_signed_taproot_spend_is_mined(tmp_path: Path) -> None:
    authority = authorisation.AuthorityKey.generate()
    with (
        RegtestNode(tmp_path / "node") as rpc,
        SigningCluster(2, 3, authority.public_bytes()) as cluster,
    ):
        internal_key = cluster.dkg()
        output_key = cluster.taproot_output_key()
        assert output_key == bitcoin.taproot_tweak(internal_key)  # Rust crate == Python
        address = chain.custody_address(rpc, internal_key)
        assert chain.script_pubkey(rpc, address) == bitcoin.p2tr_script(output_key)  # == Core

        rpc.call("createwallet", "miner")
        miner = rpc.wallet("miner")
        mine_to = miner.call("getnewaddress")
        rpc.call("generatetoaddress", 101, mine_to)
        miner.call("sendtoaddress", address, "1.0")
        rpc.call("generatetoaddress", 1, mine_to)

        destination = chain.script_pubkey(rpc, miner.call("getnewaddress", "", "bech32"))
        change = bitcoin.p2tr_script(output_key)
        stx = transfer.build(chain.custody_utxos(rpc, output_key), 25_000_000, destination, change)
        transfer.check_matches(stx, 25_000_000, destination, change, max_fee=10_000)
        expires = datetime.now(UTC) + timedelta(minutes=1)
        token = authorisation.issue(authority, b"\x00" * 32, stx.sighash(), expires).to_bytes()

        signature = cluster.sign(stx.sighash(), [1, 3], token, taproot=True)
        assert schnorr.verify(stx.sighash(), output_key, signature)
        txid = rpc.call("sendrawtransaction", stx.finalize(signature))
        assert txid == stx.tx.txid()
        rpc.call("generatetoaddress", 1, mine_to)
        assert rpc.call("getrawtransaction", txid, True)["confirmations"] == 1
        remaining = chain.custody_utxos(rpc, output_key)
        assert [u.amount for u in remaining] == [100_000_000 - 25_000_000 - stx.fee]
