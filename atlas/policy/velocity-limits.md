# Velocity limits

**In one sentence.** A velocity limit caps the total amount authorised per asset in any rolling
window, such as 15 BTC in any 24 hours, so that a compromise that gets past every other control can
move only a bounded amount before someone notices.

## The problem

Approvals and whitelists can be defeated together: an attacker with two approvers' keys can pay an
approved address repeatedly. Something must bound the loss per unit of time.

## The idea

At any moment the engine adds up every authorisation in the window that ends now, and refuses a new
instruction if that total plus its amount would exceed the limit. "Rolling" matters. With a limit of
15 BTC and authorisations of 10 BTC at 09:00 and 4 BTC at 15:00 on day 1, a 2 BTC request at 08:00 on
day 2 is refused ($14 + 2 = 16$), and the same request at 09:00:01 on day 2 is allowed, because the
10 BTC has left the window. A limit per calendar day would instead allow 14 BTC at 23:59 and another
15 BTC at 00:01, 29 BTC in two minutes.

## Why custody cares

- It bounds loss per unit time when every other control has failed: the custody equivalent of a
  pre-trade credit or notional limit in a FIX gateway.
- It is computed from the audit log, so the limit and the record cannot disagree.

## In the demo

`src/custody_lab/policy/engine.py` (`_velocity_used`, check 5): 20 BTC per 24 hours in the demo's
bitcoin policy. Amounts are `Decimal`; time comes from an injected clock. A Hypothesis test checks
that no generated sequence of instructions ever exceeds the cap in any window.

## In the manual

[Chapter 4](../../manual/chapters/04-policy.md),
"[Rules: tiers, whitelist and a rolling window](../../manual/chapters/04-policy.md#rules-tiers-whitelist-and-a-rolling-window)"
(worked by hand), worked example rows 4 to 7, and Exercise 1.

## Sources

Pre-trade risk control guidance for comparison: SEC Rule 15c3-5 (market access) (**verify
current**).
