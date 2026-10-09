# Ideas for the demo and the course

A running list of what would make the demo show more, and the course teach more. Each entry says
what it would show and what it depends on. Newest decisions in the session log.

Status: **done** (merged, tested), **next** (being built), **open** (not started).

## Done

- **A day at the custodian** (2026-10-09). Deposits from clients' own wallets, a double spend by
  replacement before confirmation (credited nothing), two clients trading in their own FIX
  sessions, netting across clients (internalised settlement), coin selection across clients'
  coins, a signer taken down at noon, withdrawals at both approval tiers, and three refusals by
  three layers (ledger, whitelist, velocity). The ledger is reconciled with the chain after every
  step. `custody_lab.demo.day`, the dashboard tab, `custody-lab day`, the walkthrough section.
- **The client checks the custodian's signature in the browser** (2026-10-09). The snapshot's
  BIP340 signature, rebuilt and verified with `@noble/curves`; oracles: the 19 BIP340 vectors and
  Python-signed snapshots.
- **The key is the one holding the coins** (2026-10-09). The custody address decoded in the
  browser with `@scure/base`, and its key compared with the key that signed; oracle: Bitcoin Core.

## Next

- **Chapter 10 from the industry research** (draft in `atlas/project/research/10-practice-draft.qmd`;
  notes and 122 sources in `research/custody-landscape-2026.md`). Before moving the draft to
  `manual/chapters/10-practice.qmd` and rendering: drop the unverified Circle quote; Solana expiry
  is about a minute and a half; say "the large losses examined here", not "the largest"; define
  slashing, destination tag and durable nonce before the table, unbolded in it; remove `[:70]` in
  the `approved-but-wrong` cell and describe its output by heading; add glossary entries (account
  model, blind signing, destination tag, durable nonce, freeze function, MuSig2, ROAST, slashing);
  re-render chapter 9 for its next link. Facts were re-read at source on 2026-10-09 except Circle.
- **Share refresh and repair in the demo.** `frost-core` 3.0.0 has `refresh_dkg_*` and
  `repair_share_part1..3` (observed in its source); bind them in `rust/custody-frost`.
- **Course material from the industry research.** How leading custodians secure keys today, the
  top assets and the signature schemes they need, the research frontier, and recent incidents with
  their custody lessons. Sources and evidence classes from the research report; time-sensitive
  facts marked verify current.

## Open

- **Watch the signing protocol.** An animated sequence of the actual messages between the
  coordinator and the signers during key generation and signing: round-one commitments, round-two
  partial signatures, aggregation, each with its size. Needs the cluster to report its messages as
  events.
- **A stolen share becomes worthless.** Refresh the shares (same key, same address) and show that
  an old share combined with a new one cannot sign. Depends on what the ZF FROST crate exposes for
  refresh; verify before designing.
- **Repair a lost share.** Wipe one signer's share and rebuild it with the help of two others,
  without either revealing its own. Depends on the crate's repairable-share support; verify first.
- **A client portal.** One client's view: its balance, its inclusion proof and the custodian's
  signature, all checked in the browser.
- **A live audit-log timeline**, with a switch that edits one entry and shows where the hash chain
  breaks.
- **Replay a day.** Recorded days in `var/day` can be listed and replayed like runs.
- **Several days in a row.** The velocity window rolling over, and snapshots compared across days.
