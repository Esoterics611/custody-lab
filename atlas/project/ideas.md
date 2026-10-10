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
- **A deleted payment, re-hashed** (2026-10-09). A forger removes a signed payment from the audit log
  and recomputes the chain; the signers' own record of the authorisations they used exposes it
  (`SigningCluster.used_authorisations`).
- **Register an address, with a delay** (2026-10-09). `PolicyEngine.register`: a new withdrawal
  address is approved like the largest payment and payable only after 24 hours; two attacks in the
  panel show both refusals.
- **Inject a fill** (2026-10-09). A man in the middle rewrites a FIX ExecutionReport (LastQty 0.4 to
  1.4, checksum recomputed); the session accepts it, and reconciliation against the exchange's own
  statement refuses it (`trade_session`, `reconcile`).
- **Leave a client out** (2026-10-09). A seventeenth attack in the panel: the omitted client finds no
  proof in the published tree, and a proof from a second tree misses the published, signed root.
- **Set a signer's clock back, and an authorisation countdown** (2026-10-09), vector 4.4 and the
  countdown idea together. The Clocks tab: an authorisation used at once (59.98 s of 60 s left), one
  held back five minutes and refused, one clock set back (still refused), both set back (signed),
  signers on a time authority's signed time refusing it, and a signed time for another nonce
  refused. Each step draws the authorisation's life as a bar. The settlement run's step 7 shows the
  time left. `custody_lab.policy.signed_time` (Roughtime's core, RFC 10049), `TimeService`,
  `custody-lab clocks`, the walkthrough section.

- **Watch the signing protocol** (2026-10-10). Every message between the coordinator and the
  signers through private channels, key generation, signing, refresh and repair, animated round by
  round on the real processes, each split into its fields (the crate's serialization, checked
  against every message's length), with what the coordinator relayed in clear, sealed and as
  authorisations. `SigningCluster(watch=...)`, `custody_lab.demo.protocol`, the dashboard tab,
  `custody-lab protocol`, the walkthrough section, a new cell in chapter 2 and the atlas entry
  `mpc/protocol-messages.md`. A test searches every relayed byte for every signer's share of each
  period and finds none.
- **A live audit-log timeline** (2026-10-10). The policy engine's audit log entry by entry through
  two settlements and two signed snapshots, each entry with its link and its hash, and a switch on a
  forger's copy of it: edit an entry (the chain check stops there), replace its hash as well (the
  check stops at the next link), re-hash every later entry (the chain verifies), then each
  snapshot's anchored head, which exposes the re-hashed copy when the anchored entry is at or after
  the edit; an edit after the last snapshot is exposed by none yet. Every position for every entry
  is computed by the run with the real `verify_chain`. `custody_lab.demo.audit_trail`, the dashboard
  tab, `custody-lab audit`, the walkthrough section, a new section and two cells in chapter 4, and
  vectors 10.1 and 10.2 in the attack-vector analysis.

## Next

None started.

## Open

### From the attack-vector analysis

Each shows an attack that succeeds, then the defence that stops it. Numbers refer to the vectors
in `manual/attack-vectors.md`.

- **Substitute a channel key** (1.4), **read the shares from memory** (1.5, 1.6): not to be built.
  Each would mean writing a tool that extracts key material; they stay as analysis, and chapter 3
  covers the defences (separate machines, keys provisioned out of band).

### Other ideas

- **A second chain.** The teaching two-party ECDSA (`mpc/lindell17`) signing an account-model
  transfer, to show chapter 10's point that each chain's signature rule needs its own threshold
  protocol.
- **A client portal.** One client's view: its balance, its inclusion proof and the custodian's
  signature, all checked in the browser.
- **Replay a day.** Recorded days in `var/day` can be listed and replayed like runs.
- **The time authority on the protocol tab.** Signing with signed time adds a round: each signer's
  nonce out, the time authority's signed time back. Showing it needs the time authority's exchange
  reported to the watch, since the coordinator fetches it outside the signers' pipes.
- **Several days in a row.** The velocity window rolling over, and snapshots compared across days.
