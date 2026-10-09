"""The dashboard's Taproot address decoder agrees with Bitcoin Core.

``web/src/address.ts`` decodes the output key from a bech32m address with ``@scure/base``. Bitcoin
Core is the oracle: it derives the address of a known key (the ``rawtr`` descriptor puts the key
in the address unchanged), and the browser code must decode the same key back.
"""

import json
import secrets
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from custody_lab.foundations import schnorr
from custody_lab.settlement.regtest import RegtestNode

pytestmark = [
    pytest.mark.regtest,
    pytest.mark.skipif(
        shutil.which("node") is None or shutil.which("bitcoind") is None,
        reason="needs node and bitcoind on PATH",
    ),
]
HARNESS = "web/tests/decode-address.ts"


def _decode(addresses: list[str]) -> list[dict[str, Any]]:
    done = subprocess.run(
        ["node", HARNESS], input=json.dumps(addresses), capture_output=True, text=True, check=True
    )
    decoded: list[dict[str, Any]] = json.loads(done.stdout)
    return decoded


def test_the_key_core_puts_in_an_address_is_the_key_the_browser_reads(tmp_path: Path) -> None:
    keys = [schnorr.pubkey_gen(secrets.token_bytes(32)).hex() for _ in range(8)]
    with RegtestNode(tmp_path / "node") as rpc:

        def address(key: str) -> str:
            descriptor = rpc.call("getdescriptorinfo", f"rawtr({key})")["descriptor"]
            derived: str = rpc.call("deriveaddresses", descriptor)[0]
            return derived

        addresses = [address(k) for k in keys]
        rpc.call("createwallet", "w")
        segwit_v0 = rpc.wallet("w").call("getnewaddress", "", "bech32")

    last = addresses[0][-1]
    mistyped = addresses[0][:-1] + ("q" if last != "q" else "p")  # one character changed
    decoded = _decode(addresses + [segwit_v0, mistyped])

    assert decoded[: len(keys)] == [{"prefix": "bcrt", "key": k} for k in keys]
    assert "error" in decoded[-2]  # version 0: bech32, not a Taproot address
    assert "error" in decoded[-1]  # one character changed: the checksum fails
