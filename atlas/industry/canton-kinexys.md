# Canton and Kinexys

**In one sentence.** Canton Network and J.P. Morgan's Kinexys are institutional ledgers for
tokenised assets and deposits, built to give participants privacy and admission control.

## The problem

Banks and market infrastructures want the benefits of a shared ledger (settlement at any hour, asset
and cash on one ledger) without publishing their positions to everyone or admitting anyone as a
participant.

## The idea

- **Canton Network** joins ledgers running Digital Asset's Daml smart-contract language through a
  shared ordering service, the Global Synchronizer; each party sees only the parts of a transaction it
  is entitled to. Its largest application is Broadridge's Distributed Ledger Repo, for **repo**:
  short-term loans in which one party sells securities and agrees to buy them back, usually the next
  day.
- **Kinexys** is J.P. Morgan's blockchain business (Onyx until November 2024). It moves deposits
  between its institutional clients on a permissioned ledger, and issues the JPM Coin (JPMD) deposit
  token on Base, a public Ethereum **layer 2**: a chain that processes transactions on its own and
  periodically records its state on Ethereum.

## Why custody cares

Both show institutions choosing privacy and admission control, even when they settle on public
chains. Deposit tokens and tokenised Treasuries on one network make delivery versus payment possible
without a cross-chain protocol.

## In the demo

None; the demo settles on a public-style chain (Bitcoin regtest) without a cash leg.

## In the manual

[Chapter 8](../../manual/chapters/08-industry.md),
"[Institutional ledgers: Canton and Kinexys](../../manual/chapters/08-industry.md#institutional-ledgers-canton-and-kinexys)".

## Sources

Broadridge Distributed Ledger Repo on Canton at about USD 280 billion a day (reported); DTCC and
Digital Asset plan to tokenise DTC-custodied Treasuries on Canton, announced December 2025 (reported);
JPMD on Base for institutional clients (reported). All **verify current**.
