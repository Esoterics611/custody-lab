"""The one-input Taproot spend that settles an instruction: select, build, check, finalise.

One settlement spends exactly one custody UTXO, so there is one sighash, one FROST signing
session and one policy authorisation per settlement. Change returns to the custody output key.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from custody_lab.settlement.bitcoin import (
    Transaction,
    TxIn,
    TxOut,
    estimated_vsize,
    taproot_sighash,
)

DUST_LIMIT = 330  # satoshis; smaller change is added to the fee instead


@dataclass(frozen=True)
class Utxo:
    txid: str
    vout: int
    amount: int  # satoshis
    script_pubkey: bytes


@dataclass(frozen=True)
class SettlementTx:
    tx: Transaction
    spent: TxOut
    fee: int

    def sighash(self) -> bytes:
        return taproot_sighash(self.tx, 0, [self.spent])

    def finalize(self, signature: bytes) -> str:
        """Raw transaction hex with the 64-byte key-path signature as the only witness item."""
        if len(signature) != 64:
            raise ValueError("a SIGHASH_DEFAULT key-path signature is 64 bytes")
        return self.tx.serialize(witnesses=[[signature]]).hex()


def build(
    utxos: Sequence[Utxo],
    amount: int,
    destination: bytes,
    change: bytes,
    feerate: int = 2,
) -> SettlementTx:
    """Pay ``amount`` sats to the ``destination`` script from the smallest sufficient UTXO."""
    fee = estimated_vsize(1, 2) * feerate
    candidates = sorted((u for u in utxos if u.amount >= amount + fee), key=lambda u: u.amount)
    if not candidates:
        raise ValueError(f"no single custody UTXO covers {amount} + {fee} sats")
    utxo = candidates[0]
    outputs = [TxOut(amount, destination)]
    change_amount = utxo.amount - amount - fee
    if change_amount >= DUST_LIMIT:
        outputs.append(TxOut(change_amount, change))
    else:
        fee += change_amount
    tx = Transaction((TxIn(utxo.txid, utxo.vout),), tuple(outputs))
    return SettlementTx(tx, TxOut(utxo.amount, utxo.script_pubkey), fee)


def check_matches(
    stx: SettlementTx, amount: int, destination: bytes, change: bytes, max_fee: int
) -> None:
    """Raise unless the transaction:
    - pays exactly ``amount`` to ``destination``;
    - sends everything else back to ``change``;
    - spends at most ``max_fee`` on fees.

    The fee is computed from the input and outputs, not taken from ``stx.fee``. This check ties
    the sighash to the approved instruction.
    """
    to_destination = [o for o in stx.tx.outputs if o.script_pubkey == destination]
    if [o.amount for o in to_destination] != [amount]:
        raise ValueError("transaction does not pay the approved amount to the approved address")
    if any(o.script_pubkey not in (destination, change) for o in stx.tx.outputs):
        raise ValueError("transaction pays an address outside the instruction")
    fee = stx.spent.amount - sum(o.amount for o in stx.tx.outputs)
    if not 0 <= fee <= max_fee:
        raise ValueError(f"fee {fee} sats outside [0, {max_fee}]")
