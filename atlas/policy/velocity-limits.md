# Velocity limits

**Definition.** A cap on the total authorised per asset over a rolling window (here 15 BTC per
24 hours). An instruction is denied if the amount already authorised in the window plus its own
amount exceeds the cap.

**Why custody cares.**
- It bounds loss per unit time when every other control has failed, the custody equivalent of a
  pre-trade credit or notional limit.
- It is computed from the audit log, so the limit and the record cannot disagree.

**In the demo.** `src/custody_lab/policy/engine.py` (`_velocity_used`, check 5). Amounts are
`Decimal`; time comes from an injected clock. A Hypothesis test checks that no generated sequence
of instructions ever exceeds the cap in any window.

**In the manual.** Chapter 4, worked example rows 4 to 7; Exercise 1.

**Sources.** Pre-trade risk control guidance for comparison: SEC Rule 15c3-5 (market access)
(**verify current**).
