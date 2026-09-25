from dataclasses import replace

import pytest

from custody_lab.settlement.bitcoin import TxOut, estimated_vsize, parse_transaction
from custody_lab.settlement.transfer import DUST_LIMIT, Utxo, build, check_matches

CUSTODY = b"\x51\x20" + b"\x11" * 32
DEST = b"\x00\x14" + b"\x22" * 20
FEE = estimated_vsize(1, 2) * 2


def utxo(amount: int, vout: int = 0) -> Utxo:
    return Utxo("ab" * 32, vout, amount, CUSTODY)


def test_smallest_sufficient_utxo_is_spent_with_change() -> None:
    stx = build([utxo(10_000_000, 0), utxo(2_000_000, 1), utxo(100, 2)], 1_000_000, DEST, CUSTODY)
    assert stx.tx.inputs[0].vout == 1
    assert [o.amount for o in stx.tx.outputs] == [1_000_000, 2_000_000 - 1_000_000 - FEE]
    check_matches(stx, 1_000_000, DEST, CUSTODY, max_fee=FEE)
    assert parse_transaction(stx.tx.serialize()) == stx.tx


def test_dust_change_goes_to_fee() -> None:
    stx = build([utxo(1_000_000 + FEE + DUST_LIMIT - 1)], 1_000_000, DEST, CUSTODY)
    assert len(stx.tx.outputs) == 1 and stx.fee == FEE + DUST_LIMIT - 1


def test_insufficient_funds() -> None:
    with pytest.raises(ValueError, match="covers"):
        build([utxo(1_000_000)], 1_000_000, DEST, CUSTODY)


def test_check_matches_rejects_wrong_amount_or_address() -> None:
    stx = build([utxo(5_000_000)], 1_000_000, DEST, CUSTODY)
    with pytest.raises(ValueError, match="approved amount"):
        check_matches(stx, 999_999, DEST, CUSTODY, max_fee=FEE)
    with pytest.raises(ValueError, match="outside the instruction"):
        check_matches(stx, 1_000_000, DEST, b"\x51\x20" + b"\x33" * 32, max_fee=FEE)


def test_check_matches_rejects_a_fee_burning_transaction() -> None:
    honest = build([utxo(5_000_000)], 1_000_000, DEST, CUSTODY)
    burned = replace(honest.tx, outputs=(honest.tx.outputs[0], TxOut(1_000, CUSTODY)))
    with pytest.raises(ValueError, match="fee"):
        check_matches(replace(honest, tx=burned), 1_000_000, DEST, CUSTODY, max_fee=10_000)
