"""Chain queries the settlement layer needs, answered by Bitcoin Core over RPC.

Bitcoin Core derives the custody address from the FROST group key independently of this code. The
demo cross-checks it against ``bitcoin.taproot_tweak`` and against the Rust crate's tweaked key.
"""

from __future__ import annotations

from custody_lab.settlement.bitcoin import to_sats
from custody_lab.settlement.regtest import BitcoinRPC
from custody_lab.settlement.transfer import Utxo


def custody_address(rpc: BitcoinRPC, internal_key: bytes) -> str:
    """BIP86 address for an x-only internal key, via the descriptor ``tr(KEY)``."""
    descriptor = rpc.call("getdescriptorinfo", f"tr({internal_key.hex()})")["descriptor"]
    address: str = rpc.call("deriveaddresses", descriptor)[0]
    return address


def script_pubkey(rpc: BitcoinRPC, address: str) -> bytes:
    return bytes.fromhex(rpc.call("validateaddress", address)["scriptPubKey"])


def custody_utxos(rpc: BitcoinRPC, output_key: bytes) -> list[Utxo]:
    """Unspent outputs paying the Taproot output key, from the UTXO set (no wallet needed)."""
    result = rpc.call("scantxoutset", "start", [f"rawtr({output_key.hex()})"])
    return [
        Utxo(u["txid"], u["vout"], to_sats(u["amount"]), bytes.fromhex(u["scriptPubKey"]))
        for u in result["unspents"]
    ]
