"""Net a settlement cycle's fills into one obligation per asset.

In the off-exchange (ClearLoop-style) model the client's assets stay with its custodian while it
trades. The exchange extends trading credit against the custodied balance, and at the end of each
settlement cycle only the **net** position moves. Ten fills become one on-chain transfer in one
direction.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from custody_lab.trading.fix import Fill


@dataclass(frozen=True)
class NetPosition:
    base_asset: str
    quote_asset: str
    base: Decimal  # positive: the exchange owes the client; negative: the client owes the exchange
    quote: Decimal
    fills: int

    @property
    def client_delivers_base(self) -> bool:
        return self.base < 0


def net(fills: Sequence[Fill]) -> NetPosition:
    """Sum signed quantities: a buy adds base and spends quote; a sell does the reverse."""
    if not fills:
        raise ValueError("nothing to net")
    symbols = {f.symbol for f in fills}
    if len(symbols) != 1:
        raise ValueError(f"one symbol per netting set, got {sorted(symbols)}")
    base_asset, quote_asset = symbols.pop().split("-")
    base, quote = Decimal(0), Decimal(0)
    for f in fills:
        sign = 1 if f.side == "buy" else -1
        base += sign * f.qty
        quote -= sign * f.qty * f.price
    return NetPosition(base_asset, quote_asset, base, quote, len(fills))
