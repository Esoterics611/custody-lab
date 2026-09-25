"""Bitcoin transactions for Taproot key-path spends: serialization, BIP341 sighash, BIP86 tweak.

EDUCATIONAL, NOT PRODUCTION. Written from BIP 341 and checked two independent ways:
- against the BIP 341 wallet test vectors;
- by Bitcoin Core deriving the same address and accepting the demo's transactions into blocks.

Production code uses a maintained library (rust-bitcoin, or Bitcoin Core's own wallet).

Amounts inside this module are integer satoshis. ``to_sats`` is the only conversion from the
``Decimal`` BTC amounts used everywhere else.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from custody_lab.foundations.ec import SECP256K1
from custody_lab.foundations.hashing import sha256, tagged_hash
from custody_lab.foundations.schnorr import lift_x

SATS_PER_BTC = Decimal(100_000_000)
SIGHASH_DEFAULT, SIGHASH_ALL, SIGHASH_NONE, SIGHASH_SINGLE = 0x00, 0x01, 0x02, 0x03
SIGHASH_ANYONECANPAY = 0x80


def to_sats(btc: Decimal) -> int:
    """Exact BTC -> satoshi conversion; refuses amounts with sub-satoshi precision."""
    sats = btc * SATS_PER_BTC
    if sats != sats.to_integral_value():
        raise ValueError(f"{btc} BTC is not a whole number of satoshis")
    return int(sats)


def to_btc(sats: int) -> Decimal:
    return Decimal(sats) / SATS_PER_BTC


def compact_size(n: int) -> bytes:
    if n < 0xFD:
        return bytes([n])
    if n <= 0xFFFF:
        return b"\xfd" + n.to_bytes(2, "little")
    if n <= 0xFFFFFFFF:
        return b"\xfe" + n.to_bytes(4, "little")
    return b"\xff" + n.to_bytes(8, "little")


def taproot_tweak(internal_key: bytes, merkle_root: bytes | None = None) -> bytes:
    """BIP341 output key Q = P + H_TapTweak(P || merkle_root) * G, x-only. With no script tree
    (``merkle_root`` None) this is BIP86, the form the demo's custody address uses."""
    P = lift_x(int.from_bytes(internal_key, "big"))
    if P is None:
        raise ValueError("internal key is not a valid x-only point")
    t = int.from_bytes(tagged_hash("TapTweak", internal_key + (merkle_root or b"")), "big")
    if t >= SECP256K1.n:
        raise ValueError("tweak out of range")
    Q = SECP256K1.add(P, SECP256K1.mul(t, SECP256K1.G))
    assert Q is not None
    return Q.x.to_bytes(32, "big")


def p2tr_script(output_key: bytes) -> bytes:
    """scriptPubKey of a Taproot output: OP_1 <32-byte x-only key>."""
    return b"\x51\x20" + output_key


@dataclass(frozen=True)
class TxIn:
    txid: str  # display (big-endian) hex, as RPCs and explorers show it
    vout: int
    sequence: int = 0xFFFFFFFD  # signals replace-by-fee

    def outpoint(self) -> bytes:
        return bytes.fromhex(self.txid)[::-1] + self.vout.to_bytes(4, "little")


@dataclass(frozen=True)
class TxOut:
    amount: int  # satoshis
    script_pubkey: bytes

    def serialize(self) -> bytes:
        return (
            self.amount.to_bytes(8, "little")
            + compact_size(len(self.script_pubkey))
            + self.script_pubkey
        )


@dataclass(frozen=True)
class Transaction:
    inputs: tuple[TxIn, ...]
    outputs: tuple[TxOut, ...]
    version: int = 2
    locktime: int = 0

    def serialize(self, witnesses: Sequence[Sequence[bytes]] | None = None) -> bytes:
        """Legacy serialization, or BIP144 SegWit serialization when ``witnesses`` are given."""
        body = compact_size(len(self.inputs)) + b"".join(
            i.outpoint() + b"\x00" + i.sequence.to_bytes(4, "little") for i in self.inputs
        )
        body += compact_size(len(self.outputs)) + b"".join(o.serialize() for o in self.outputs)
        version = self.version.to_bytes(4, "little")
        locktime = self.locktime.to_bytes(4, "little")
        if witnesses is None:
            return version + body + locktime
        stacks = b"".join(
            compact_size(len(w)) + b"".join(compact_size(len(item)) + item for item in w)
            for w in witnesses
        )
        return version + b"\x00\x01" + body + stacks + locktime

    def txid(self) -> str:
        return sha256(sha256(self.serialize()))[::-1].hex()


def sig_msg(
    tx: Transaction, index: int, spent: Sequence[TxOut], hash_type: int = SIGHASH_DEFAULT
) -> bytes:
    """BIP341 signature message for a key-path spend (no annex), with the 0x00 epoch prefix."""
    output_type = SIGHASH_ALL if hash_type == SIGHASH_DEFAULT else hash_type & 0x03
    anyone_can_pay = bool(hash_type & SIGHASH_ANYONECANPAY)
    msg = bytes([0x00, hash_type])
    msg += tx.version.to_bytes(4, "little") + tx.locktime.to_bytes(4, "little")
    if not anyone_can_pay:
        msg += sha256(b"".join(i.outpoint() for i in tx.inputs))
        msg += sha256(b"".join(o.amount.to_bytes(8, "little") for o in spent))
        msg += sha256(b"".join(compact_size(len(o.script_pubkey)) + o.script_pubkey for o in spent))
        msg += sha256(b"".join(i.sequence.to_bytes(4, "little") for i in tx.inputs))
    if output_type == SIGHASH_ALL:
        msg += sha256(b"".join(o.serialize() for o in tx.outputs))
    msg += b"\x00"  # spend_type: key path, no annex
    if anyone_can_pay:
        this, prev = tx.inputs[index], spent[index]
        msg += this.outpoint() + prev.serialize() + this.sequence.to_bytes(4, "little")
    else:
        msg += index.to_bytes(4, "little")
    if output_type == SIGHASH_SINGLE:
        if index >= len(tx.outputs):
            raise ValueError("SIGHASH_SINGLE without a matching output")
        msg += sha256(tx.outputs[index].serialize())
    return msg


def taproot_sighash(
    tx: Transaction, index: int, spent: Sequence[TxOut], hash_type: int = SIGHASH_DEFAULT
) -> bytes:
    """The 32 bytes a key-path signature commits to: H_TapSighash(sig_msg)."""
    return tagged_hash("TapSighash", sig_msg(tx, index, spent, hash_type))


def estimated_vsize(n_inputs: int, n_outputs: int) -> int:
    """Upper-bound virtual size for key-path inputs and P2TR/P2WPKH outputs."""
    return 11 + 58 * n_inputs + 43 * n_outputs


def _read_compact_size(data: bytes, pos: int) -> tuple[int, int]:
    first = data[pos]
    if first < 0xFD:
        return first, pos + 1
    width = {0xFD: 2, 0xFE: 4, 0xFF: 8}[first]
    return int.from_bytes(data[pos + 1 : pos + 1 + width], "little"), pos + 1 + width


def parse_transaction(raw: bytes) -> Transaction:
    """Parse a legacy-serialized (unsigned, witness-free) transaction."""
    version, pos = int.from_bytes(raw[:4], "little"), 4
    n_in, pos = _read_compact_size(raw, pos)
    inputs = []
    for _ in range(n_in):
        txid, vout = (
            raw[pos : pos + 32][::-1].hex(),
            int.from_bytes(raw[pos + 32 : pos + 36], "little"),
        )
        script_len, pos = _read_compact_size(raw, pos + 36)
        pos += script_len
        inputs.append(TxIn(txid, vout, int.from_bytes(raw[pos : pos + 4], "little")))
        pos += 4
    n_out, pos = _read_compact_size(raw, pos)
    outputs = []
    for _ in range(n_out):
        amount = int.from_bytes(raw[pos : pos + 8], "little")
        script_len, pos = _read_compact_size(raw, pos + 8)
        outputs.append(TxOut(amount, raw[pos : pos + script_len]))
        pos += script_len
    locktime = int.from_bytes(raw[pos : pos + 4], "little")
    if pos + 4 != len(raw):
        raise ValueError("trailing bytes after transaction")
    return Transaction(tuple(inputs), tuple(outputs), version, locktime)
