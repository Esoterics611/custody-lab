# Canton and Kinexys

**Definition.** Two institutional ledgers for tokenised assets and deposits. Canton Network joins
Daml ledgers through a shared ordering service, the Global Synchronizer; each party sees only the
parts of a transaction it is entitled to. Kinexys is J.P. Morgan's blockchain business (Onyx until
November 2024): deposit payments between its institutional clients on a permissioned ledger, and
the JPM Coin (JPMD) deposit token on Base, a public Ethereum layer 2.

**Why custody cares.** Both show institutions choosing privacy and admission control, even when
they settle on public chains. Deposit tokens and tokenised Treasuries on one network make DvP
possible without a cross-chain protocol.

**In the demo.** None; the demo settles on a public-style chain (Bitcoin regtest) without a cash
leg.

**In the manual.** [Chapter 8](../../manual/chapters/08-industry.md), "[Institutional ledgers: Canton and Kinexys](../../manual/chapters/08-industry.md#institutional-ledgers-canton-and-kinexys)".

**Sources.** Broadridge Distributed Ledger Repo on Canton at about USD 280 billion a day
(reported); DTCC and Digital Asset plan to tokenise DTC-custodied Treasuries on Canton, announced
December 2025 (reported); JPMD on Base for institutional clients (reported). All **verify
current**.
