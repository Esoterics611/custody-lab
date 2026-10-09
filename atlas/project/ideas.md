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
- **Restart a signer and replay** (4.5). A used authorisation accepted after a restart within its
  60 seconds; a persisted record refuses it.
- **Register an attacker's address** (4.8). An unprotected whitelist change, then registration as
  an approved instruction with a delay before first payment.
- **Spoof the instruction** (5.5; chapter 10's Bitget case). A compromised instruction builder fools
  approvers who sign blind; an approver device that decodes the destination against registered
  addresses refuses.
- **Reorganise the chain** (7.2). On regtest, invalidate the block holding a credited deposit and
  double-spend it; a confirmation threshold by amount refuses to credit too early.
- **Inject a fill** (8.1). A false execution report in the unauthenticated FIX session changes the
  settlement; reconciliation against the exchange's statement catches it.
- **Borrow for the snapshot** (9.6). Coins borrowed for one snapshot; an unannounced second snapshot
  shows the gap.
- **Leave a client out** (9.5). The omitted client asks for its proof and finds none.
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
