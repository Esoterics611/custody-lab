# MiCA

**In one sentence.** MiCA, the EU's Markets in Crypto-Assets Regulation (Regulation (EU)
2023/1114), licenses crypto-asset service providers (CASPs) and makes custody and administration of
crypto-assets for clients a licensed service, with the duties set out in its Article 75.

## The problem

A custodian serving EU clients needs a licence, and its key-holding system has to support duties
that go beyond keeping keys safe: records, statements, prompt return of assets, and the separation of
clients' holdings from the provider's own.

## The idea

Stablecoin titles applied from 30 June 2024, the rest from 30 December 2024; the transition for
existing providers ended by 1 July 2026 at the latest. Article 75 makes custody a licensed service:

- ¶2 a register of positions per client, every movement evidenced;
- ¶3 a custody policy against fraud, cyber threats and negligence;
- ¶5 statements at least quarterly; ¶6 prompt return of assets;
- ¶7 client holdings segregated from the provider's own, legally and operationally;
- ¶8 liability for loss attributable to the provider, capped at market value at the time of loss;
- ¶9 sub-custody only with authorised CASPs.

DORA (Regulation (EU) 2022/2554), applying from 17 January 2025, adds ICT risk management.

For a key-holding system the paragraphs point to engineering work: a ledger that records every
movement, not only balances (¶2); the controls of chapters 2 to 4 (¶3); a withdrawal path that works
promptly, including when signers fail (¶6); keeping the provider's own coins away from the clients'
addresses (¶7); and an audit log that can attribute an incident (¶8).

## Why custody cares

It sets the duties a regulated EU custodian's system must support, and chapter 8 maps each one onto
the demo, gap by gap.

## In the demo

Chapter 8's worked example maps each paragraph to the demo. For ¶7 the demo charges each
settlement's network fee to the client being settled, so the custody address holds client coins only
and assets equal liabilities after every batch. Clients still share one omnibus address, so
segregation between clients lives in the ledger, not on chain.

## In the manual

[Chapter 8](../../manual/chapters/08-industry.md),
"[Regulation in the EU: MiCA](../../manual/chapters/08-industry.md#regulation-in-the-eu-mica)",
"[Worked example](../../manual/chapters/08-industry.md#worked-example)",
"[Fees without house coins](../../manual/chapters/08-industry.md#fees-without-house-coins)".

## Sources

Regulation (EU) 2023/1114, Articles 70, 75, 143 (Article 75 text **observed**); **verify current**
for enforcement after the transition.
