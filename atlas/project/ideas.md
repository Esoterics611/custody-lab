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
- **Chapter 10, custody in practice** (2026-10-09). Custodians' key arrangements, what each large
  asset asks of a custodian, the large 2025 and 2026 losses that passed through genuine approvals,
  broken threshold ECDSA implementations, and what is being standardised. Every fact re-read at
  its source; the research notes, with 122 sources, are in `atlas/project/research/`.
- **Key ceremonies** (2026-10-09). Share refresh and share repair bound from `frost-core` 3.0.0;
  a share stolen before a refresh fails to combine with one stolen after it, two shares of one
  period still sign, and a lost share is rebuilt by two helpers. The dashboard tab,
  `custody-lab ceremonies`, the walkthrough section.
- **Private channels and a split server** (2026-10-09), both from the attack-vector analysis.
  Key-generation sub-shares are sealed signer to signer; the policy engine and each approver run in
  processes of their own, so the coordinator holds none of their keys.
- **Red team** (2026-10-09). A deposit reorganised away after one confirmation leaves the books 0.50
  BTC short, and nothing is credited under a three-confirmation rule; a withdrawal sent to another
  client's registered address passes blind approver devices and is refused by checking ones (a new
  vector, 5.7: the global whitelist does not bind a destination to its client).
- **Borrow for the snapshot** (2026-10-09). The red team hides its 0.50 BTC hole with a loan for a
  scheduled snapshot (ratio 1.00000) and an unannounced snapshot after repayment shows 0.66667.
  "Restart a signer and replay" was dropped: an authorisation names one exact transaction, so a
  replayed signature gains nothing (attack-vectors.md, 4.5).
- **Register an address, with a delay** (2026-10-09). `PolicyEngine.register`: a new withdrawal
  address is approved like the largest payment and payable only after 24 hours; two attacks in the
  panel show both refusals.
- **Inject a fill** (2026-10-09). A man in the middle rewrites a FIX ExecutionReport (LastQty 0.4 to
  1.4, checksum recomputed); the session accepts it, and reconciliation against the exchange's own
  statement refuses it (`trade_session`, `reconcile`).
- **Leave a client out** (2026-10-09). A seventeenth attack in the panel: the omitted client finds no
  proof in the published tree, and a proof from a second tree misses the published, signed root.

## Next

- **Watch the signing protocol.** An animated sequence of the actual messages between the
  coordinator and the signers during key generation, refresh, repair and signing: who sends what to
  whom in each round, with sizes. Needs the cluster to report its messages as events.

## Open

### From the attack-vector analysis

Each shows an attack that succeeds, then the defence that stops it. Numbers refer to the vectors
in `manual/attack-vectors.md`.

- **Substitute a channel key** (1.4). A coordinator that swaps the signers' channel keys at start-up
  reads the sub-shares; keys pinned at provisioning stop it.
- **Read the shares from memory** (1.5, 1.6). An administrator of the one machine reads all three
  signer processes: why chapter 3 puts shares on separate machines.
- **Set a signer's clock back** (4.4). An expired authorisation accepted; a trusted time source
  refuses it.
- **Rewrite the log between snapshots** (10.2). Entries after the last anchored head rewritten
  unnoticed until the next snapshot.

### Other ideas

- **A second chain.** The teaching two-party ECDSA (`mpc/lindell17`) signing an account-model
  transfer, to show chapter 10's point that each chain's signature rule needs its own threshold
  protocol.
- **An authorisation countdown.** Show each authorisation's 60-second life on the dashboard, and a
  signing that starts too late being refused (chapter 10, Drift).
- **A client portal.** One client's view: its balance, its inclusion proof and the custodian's
  signature, all checked in the browser.
- **A live audit-log timeline**, with a switch that edits one entry and shows where the hash chain
  breaks.
- **Replay a day.** Recorded days in `var/day` can be listed and replayed like runs.
- **Several days in a row.** The velocity window rolling over, and snapshots compared across days.
