# Netting

**Definition.** Sum the signed quantities of a cycle's fills:
- base: $\Delta = \sum \sigma q$;
- quote: $-\sum \sigma q p$.

Only the net moves. A negative base means the client delivers base to the exchange.

**Why custody cares.**
- Ten fills become one on-chain transfer, which means one policy decision, one signature and one
  fee.
- The cycle length trades unsettled exposure against on-chain cost.

**In the demo.** `src/custody_lab/settlement/netting.py` (`net`, `NetPosition`), with `Decimal`
throughout. A Hypothesis test checks that the net base equals buys minus sells.

**In the manual.** Chapter 5, "Netting" and the worked example (four fills netting to −0.85 BTC).

**Sources.** CPMI-IOSCO, *Principles for Financial Market Infrastructures* (2012), Principle 8
(settlement finality) and the discussion of netting.
