import asyncio
from decimal import Decimal

import simplefix

from custody_lab.trading.fix import Order, reconcile, trade, trade_session

ORDERS = [
    Order("C1", "BTC-USD", "sell", Decimal("0.4"), Decimal("64000")),
    Order("C2", "BTC-USD", "buy", Decimal("0.15"), Decimal("63950.5")),
    Order("C3", "BTC-USD", "sell", Decimal("0.35"), Decimal("64010")),
]


def test_every_order_is_filled_at_its_limit() -> None:
    fills, _ = trade(ORDERS)
    assert [(f.cl_ord_id, f.side, f.qty, f.price) for f in fills] == [
        (o.cl_ord_id, o.side, o.qty, o.price) for o in ORDERS
    ]
    assert len({f.exec_id for f in fills}) == 3


def test_transcript_is_a_well_formed_fix_session() -> None:
    _, transcript = trade(ORDERS)
    types = [m.split("|35=")[1].split("|")[0] for m in transcript]
    assert types == ["A", "A", "D", "8", "D", "8", "D", "8", "5", "5"]
    client = [m for m in transcript if "|49=CUSTODY-CLIENT|" in m]
    assert [int(m.split("|34=")[1].split("|")[0]) for m in client] == [1, 2, 3, 4, 5]
    assert all(m.startswith("8=FIXT.1.1|9=") and "|10=" in m for m in transcript)
    assert all("|1137=9|" in m for m in transcript if "|35=A|" in m)  # DefaultApplVerID FIX50SP2
    assert not any("|6=" in m for m in transcript)  # no AvgPx


def test_trade_works_from_inside_an_event_loop() -> None:
    async def caller() -> int:
        fills, _ = trade(ORDERS[:1])
        return len(fills)

    assert asyncio.run(caller()) == 1


def _inflate_first_fill(msg: simplefix.FixMessage) -> simplefix.FixMessage | None:
    """A man in the middle: the first ExecutionReport's LastQty and CumQty become 1.4."""
    if msg.get(35) != b"8" or msg.get(17) != b"E0001":
        return None
    for tag in (32, 14):
        msg.remove(tag)
        msg.append_pair(tag, "1.4")
    return msg


def test_an_honest_session_reconciles_with_the_exchange_statement() -> None:
    result = trade_session(ORDERS)

    assert result.rewritten == []
    assert reconcile(result.fills, result.statement) == []


def test_a_rewritten_fill_passes_the_session_and_fails_reconciliation() -> None:
    result = trade_session(ORDERS, rewrite=_inflate_first_fill)

    # the session accepted it: sequence numbers, BodyLength and CheckSum all hold
    assert result.fills[0].qty == Decimal("1.4") and len(result.rewritten) == 1
    assert reconcile(result.fills, result.statement) == [
        "E0001: qty 1.4 in the session, 0.4 in the exchange's statement"
    ]
