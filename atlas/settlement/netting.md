# Netting

**In one sentence.** Netting adds up a settlement cycle's fills into one obligation per asset, so
only the net amount moves.

## The problem

Over a cycle a client trades many times in both directions. Settling each fill separately would mean
one on-chain payment per fill, each with its own policy decision, signature, fee and confirmation
wait.

## The idea

For fills with side $\sigma = +1$ (buy) or $-1$ (sell), quantity $q$ and price $p$, the change in
the client's base asset (bitcoin) is $\sum \sigma q$ and the change in its quote asset (dollars) is
$-\sum \sigma q p$. A negative base means the client delivers base to the exchange.

The demo's four fills: sell 0.40 at 64,000, buy 0.15 at 63,950.50, sell 0.35 at 64,010 and sell 0.25
at 64,020. The bitcoin legs add to $-0.40 + 0.15 - 0.35 - 0.25 = -0.85$, so the client delivers
0.85 BTC. The dollar legs add to $25{,}600 - 9{,}592.575 + 22{,}403.50 + 16{,}005 = 54{,}415.925$,
which the exchange owes the client and which the demo never settles (chapter 8).

## Why custody cares

- Many fills become one on-chain transfer: one policy decision, one signature and one fee.
- The cycle length trades unsettled exposure against on-chain cost: shorter cycles mean less
  exposure and more transactions.
- Netting the bitcoin side alone leaves settlement risk on the dollar side unless both legs are
  joined (delivery versus payment, chapter 8).

## In the demo

`src/custody_lab/settlement/netting.py` (`net`, `NetPosition`), with `Decimal` throughout. A
Hypothesis test checks that the net base equals buys minus sells.

## In the manual

[Chapter 5](../../manual/chapters/05-settlement.md),
"[Many fills, one delivery](../../manual/chapters/05-settlement.md#many-fills-one-delivery)" (worked
by hand), "[Netting](../../manual/chapters/05-settlement.md#netting)" and the worked example.

## Sources

CPMI-IOSCO, *Principles for Financial Market Infrastructures* (2012), Principle 8 (settlement
finality) and the discussion of netting.
