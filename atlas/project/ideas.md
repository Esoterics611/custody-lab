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

## Next

- **Watch the signing protocol.** An animated sequence of the actual messages between the
  coordinator and the signers during key generation, refresh, repair and signing: who sends what to
  whom in each round, with sizes. Needs the cluster to report its messages as events.

## Open

- **What the approver's own device shows.** Chapter 10's Bitget case: approvers sign an
  instruction built by a system they trust. Simulate a compromised instruction builder, and an
  approver device that decodes the destination against the registered-address book on its own, so
  the spoofed instruction is refused before any approval.
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
