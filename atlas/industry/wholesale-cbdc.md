# Wholesale CBDC: Agorá and mBridge

**In one sentence.** Wholesale central bank digital currency is central bank money in token form,
held only by banks and used to settle interbank and cross-border payments; Project Agorá and mBridge
are the two largest experiments.

## The problem

Cross-border payments pass through chains of correspondent banks, each leg settling separately, with
settlement risk between legs (the risk named after Herstatt). Settling both currencies, or an asset
and its cash, on one ledger removes the gap.

## The idea

- **Project Agorá** puts tokenised central bank reserves and tokenised commercial bank deposits on one
  programmable platform, each central bank keeping control of its own money. A prototype settles
  cross-border, multi-currency payments atomically: both legs in one transaction, valid or invalid
  together.
- **mBridge** is a shared ledger on which participating central banks issue wholesale CBDC for
  cross-border payments.

## Why custody cares

Wholesale CBDC is the safest cash leg for delivery versus payment. The securities leg is still a key
held by a custodian (chapters 2 and 3).

## In the demo

None. Chapter 8's DvP cell models atomic settlement on one ledger.

## In the manual

[Chapter 8](../../manual/chapters/08-industry.md),
"[Delivery versus payment](../../manual/chapters/08-industry.md#delivery-versus-payment)",
"[Wholesale central bank money: Agorá and mBridge](../../manual/chapters/08-industry.md#wholesale-central-bank-money-agorá-and-mbridge)";
the Bank of Israel's retail experiments (Sela, Icebreaker) under
"[Israel](../../manual/chapters/08-industry.md#israel)".

## Sources

BIS press release, 27 May 2026: the BIS, eight central banks and more than 40 private institutions;
atomic multi-currency settlement shown in a prototype; real-value testing next; no production timeline
(**observed**). mBridge: minimum viable product 2024; BIS Innovation Hub left October 2024; members
China, Hong Kong, Thailand, UAE; Saudi central bank withdrawn; Macao joined 2026 (reported; **verify
current**).
