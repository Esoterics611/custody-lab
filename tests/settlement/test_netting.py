from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from custody_lab.settlement.netting import net
from custody_lab.trading.fix import Fill


def fill(side: str, qty: str, price: str = "60000") -> Fill:
    return Fill("E1", "C1", "BTC-USD", side, Decimal(qty), Decimal(price))


def test_net_sell_means_client_delivers_base() -> None:
    position = net([fill("sell", "0.4"), fill("buy", "0.15"), fill("sell", "0.35", "60100")])
    assert position.base == Decimal("-0.6")
    assert (
        position.quote == Decimal("0.4") * 60000 - Decimal("0.15") * 60000 + Decimal("0.35") * 60100
    )
    assert position.client_delivers_base and position.fills == 3


def test_mixed_symbols_are_refused() -> None:
    other = Fill("E2", "C2", "ETH-USD", "buy", Decimal(1), Decimal(3000))
    with pytest.raises(ValueError, match="one symbol"):
        net([fill("buy", "1"), other])


@given(
    st.lists(
        st.tuples(st.sampled_from(["buy", "sell"]), st.decimals("0.00000001", "5", places=8)),
        min_size=1,
        max_size=20,
    )
)
def test_net_base_is_buys_minus_sells(trades: list[tuple[str, Decimal]]) -> None:
    fills = [fill(side, str(qty)) for side, qty in trades]
    buys = sum((q for s, q in trades if s == "buy"), Decimal(0))
    sells = sum((q for s, q in trades if s == "sell"), Decimal(0))
    assert net(fills).base == buys - sells
