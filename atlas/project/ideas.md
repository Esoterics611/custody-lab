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

## Next

- **The client checks the custodian's signature in the browser.** The balance check proves that a
  balance is inside the published root, but not that the custodian signed that root. Verifying the
  snapshot's BIP340 proof-of-control signature in TypeScript, with an audited library
  (`@noble/curves` 2.4.0, published 2026-08-27), closes the client's own check. Oracle: the BIP340
  test vectors and snapshots made by the Python code, run under Node as
  `tests/demo/test_browser_verifier.py` does for the tree.
- **Course material from the industry research.** How leading custodians secure keys today, the
  top assets and the signature schemes they need, the research frontier, and recent incidents with
  their custody lessons. Sources and evidence classes from the research report; time-sensitive
  facts marked verify current.

## Open

- **The key is the one holding the coins.** Decode the custody address (bech32m) in the browser
  and show that the snapshot's signing key is the key inside it, so a client checks the proof of
  control against the address it deposited to, not against a key the custodian names.
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
