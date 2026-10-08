# Off-exchange settlement

**In one sentence.** In off-exchange settlement the client's assets stay with its custodian while
it trades, the exchange sees a balance backed by assets the custodian locks for it, and only the net
obligation moves at the end of each cycle.

## The problem

In the usual crypto-exchange arrangement the client pre-funds the exchange: it moves coins into the
exchange's wallets before trading. If the exchange fails, the client is an unsecured creditor with
no particular claim on the coins it deposited. The collapse of FTX in November 2022 made that
concrete for many institutions.

## The idea

- The client's assets stay at its custodian, in an account locked for trading.
- The exchange shows the client a mirrored trading balance backed by those locked assets.
- At the end of each cycle only the net obligation moves, in one direction; exchanges may also post
  collateral with the custodian.

The client's exposure to the exchange is then bounded by one cycle's unsettled net position, not by
its whole account. What the arrangement does not protect: anything the exchange owes beyond its
posted collateral, fiat held at the exchange, and positions opened since the last settlement.

## Why custody cares

- It is a product custodians sell: Copper's ClearLoop (launched 2022) and comparable networks
  (**verify current**).
- The settlement cycle length becomes a risk dial: shorter cycles mean less exposure and more
  on-chain fees.

## In the demo

The settlement half: fills are netted per cycle and only the net BTC moves on chain. The
mirrored-balance and collateral mechanics are described, not built.

## In the manual

[Chapter 5](../../manual/chapters/05-settlement.md),
"[Settling against an exchange](../../manual/chapters/05-settlement.md#settling-against-an-exchange)",
"[How this shows up in production](../../manual/chapters/05-settlement.md#how-this-shows-up-in-production)",
and Exercise 5.

## Sources

Copper, *ClearLoop* product documentation (**verify current**).
