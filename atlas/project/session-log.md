# Session log

Newest first.

## 2026-10-10: Watching the protocol: every message through the coordinator, field by field

The owner asked to continue with the next idea, to make it a showcase, and to update the course and
documents to match. The ideas list's next item was watching the signing protocol.

**Cluster.** `SigningCluster(watch=...)` calls the watch with each round's requests as they are
sent and again with the replies. Without a watch nothing changes.

**Protocol demo** (`custody_lab.demo.protocol`, `custody-lab protocol`, `POST /api/protocol`,
`GET /api/protocol/steps` and `/api/protocol/ceremonies`). A fresh 2-of-3 cluster plays private
channels, key generation, signing, refresh, repair, and signing with the repaired share: sixteen
rounds and two aggregations. Each round's event lists every message both ways: hop, what it
carries, origin, destination, kind (instruction, clear, sealed, authorisation), bytes, fields and a
SHA-256 fingerprint. The fields follow the crate's serialization, read in the `frost-core` 3.0.0
and `frost-secp256k1-tr` 3.0.0 sources (observed): a 5-byte header holding version 0 and the CRC-32
of `FROST-secp256k1-SHA256-TR-v1` (`230f8ab3`, recomputed here), 32-byte scalars, 33-byte points,
and proofs as a length byte, an x-only R and z. A refresh's round-1 package drops the commitment to
its zero constant term (`keys/refresh.rs`). Every message's fields are checked against its length
as it passes.

Measured (observed): round-1 package 137 B, refresh round-1 package 104 B, sealed sub-share 65 B
(nonce 12, ciphertext 37, tag 16), public key package 236 B, nonce commitments 71 B, signing
package 245 B, authorisation 7,047 B (ML-DSA-65 signature in hex 6,618 B), signature share 32 B,
delta and sigma 60 B. One run: 113 messages; 6,305 B clear, 2,280 B sealed, 28,188 B of
authorisations.

Dropped: a coordinator-side sweep that tried every 32-byte window of the relayed bytes as a share
against the verifying shares. OpenSSL took 18.3 s for 20,000 windows (observed), too slow for a
demo step. It is replaced by a direct test.

**Dashboard.** A **Watch the protocol** tab: an SVG stage with the coordinator and three signers;
each round's requests and replies travel the spokes as packets coloured by kind (sealed ones
padlocked, stacked when a hop carries several), signers turn amber while they work and dim when not
involved, and each shows its share's period and verifying share. The round card explains the
round, lists its messages, and splits the chosen one into its fields as a bar. A panel counts the
bytes the coordinator has relayed, by kind; a timeline groups the rounds by ceremony. Play, pause,
previous, next and four speeds; reduced motion honoured.

**Course and documents.**
- Walkthrough: a section, "Watching the protocol", written to the writing standard: the problem,
  the idea with a FIX message log as the counterpart, the six ceremonies with the measured sizes,
  and what breaks: chapter 2's toy sub-shares in clear give the key 9 to a coordinator that only
  records them; the channel keys' trust and their lack of forward secrecy. Intro, tab count,
  troubleshooting row, recap item.
- Chapter 2: a cell that runs key generation and signing under a watch and prints each round's
  bytes by kind, with a sentence on each printed line; re-rendered (30 pages).
- Glossary: public key package, round-1 package, serialization, signature share, signing package,
  sub-share, verifying share.
- Atlas: `mpc/protocol-messages.md` (the formats and sizes); `frost.md` and `dkg.md` point at the
  tab; `proactive-refresh.md` and `backup-recovery.md` corrected, since both said refresh and repair
  were not on the signing path, which the key ceremonies have used since 2026-10-09.
- Attack vectors: 1.3 is now refused and demonstrated; 1.4 names rounds 1 and 2.
- README: it said the dashboard had three tabs (it had seven; now eight); the new command.
- CLAUDE.md: layout, commands, module status, and a Proposed decision on the watch.

**Verified.** Full suite: 287 passed (64 s; one starlette deprecation warning, present before this
change). `ruff check`, `ruff format --check src tests`, `mypy` strict (84 files), `oxlint` and `npm
--prefix web run build` clean; `tests/test_docs_links.py` passes. New tests:
`tests/demo/test_protocol.py` (fields add up, sealed messages delivered unchanged, round-1 packages
forwarded unchanged, refresh and repair, signatures, a format change stops the run),
`test_no_share_of_any_period_passes_through_the_coordinator` (each share read from its key package
and checked against OpenSSL's share times G, then searched for in every relayed byte: none found),
and the CLI and stream test. Dashboard driven headless (Playwright 1.63.0, headless shell 1243, the
three libraries unpacked into the scratchpad) at 1280 and 390 px and in dark mode; rounds 1, 4, 7, 8
and 13 inspected in screenshots; no console messages; no horizontal scroll. Three defects found that
way and fixed: the padlock's body took the packet's colour (CSS specificity), a dimmed signer's
spoke showed through its box, and at phone width the round list sat above the stage.

**Open.** The time authority's round is not on the tab (ideas list). At 390 px the stage's labels
render at about 9 to 10 px.

### Deliverables

- The dashboard has a new tab that animates every message between the coordinator and the signers
  through key generation, signing, refresh and repair, on the real signing processes.
- Each message is split into its fields byte by byte, following the FROST library's own format,
  and that format is checked against every message as it passes.
- The tab shows that the coordinator reads only public values and authorisations: every value that
  could reveal a share travels sealed, and a new test searches every relayed byte for every share
  and finds none.
- Measured: the post-quantum signatures on authorisations are about three quarters of all traffic
  through the coordinator; the threshold protocol's own messages are tens to hundreds of bytes.
- The walkthrough, chapter 2, the glossary, the atlas and the attack-vector analysis now teach the
  protocol's messages, and two stale atlas entries and the README's tab list were corrected.

## 2026-10-09: Clocks: an authorisation's life against signers' clocks, and signed time

Logged on 2026-10-10: the session that made these two commits (`e2cde5c`, `4b9a4f4`) did not log
them. Vector 4.4 and the countdown idea, done together.

**Signed time.** `custody_lab.policy.signed_time` is the core of Roughtime (RFC 10049): the signer
draws a 32-byte nonce, the time authority signs the time together with it (Ed25519), and the signer
accepts the time only if the signature verifies and the nonce is its own. `SigningCluster` takes an
optional time source: its public key is given to every signer at start, the coordinator fetches a
signed time for each signer's nonce and relays it, and the signer never reads its own clock.
`set_clock(i, offset)` is the educational attack. `TimeService` runs the time authority's key in a
process of its own.

**Clocks demo** (`custody_lab.demo.clocks`, the Clocks tab, `custody-lab clocks`). Seven steps
with no chain: an authorisation used at once, one held back five minutes and refused, one clock set
back (still refused), both set back (signed), signers on signed time refusing it, and a signed time
for another nonce refused. Each step draws the authorisation's life as a bar; the settlement run's
step 7 shows the time left. A new vector, 4.10 (a lying time authority), is open in the demo.
Walkthrough section, glossary entries, ideas list.

**Verified (2026-10-10).** `custody-lab clocks`: "59.98 s of 60 s, once signed"; the held-back
authorisation refused by both signers; with signer 1's clock set back, refused by signer 3 only;
with both set back, signed; on signed time, refused by both; a signed time for another nonce
refused by both; `signed: ["in_time","both_clocks"]`. `tests/demo/test_clocks.py` and the cluster's
clock tests pass in the 2026-10-10 suite. The session that made the commits recorded no
verification.

### Deliverables

- Signers can take the time from a time authority's signed answer instead of their own machines'
  clocks, so setting a clock back no longer revives an expired authorisation.
- A Clocks tab shows an authorisation refused after its 60 seconds, accepted again once both
  signers' clocks are set back, and refused by signers on signed time.
- A recorded signed time cannot be replayed: each answer is bound to a fresh number the signer drew.

## 2026-10-09: Five more vectors demonstrated: borrowed coins, a forged fill, address registration, a re-hashed log, an omitted client

Continuing down the attack-vector analysis's future demos.

**Red team** (now four attacks, nine steps). *Borrowed coins* (9.6): the hole the reorganised deposit
leaves is hidden from a scheduled snapshot by 0.50 BTC borrowed from the exchange (reserve ratio
1.00000, signed; the books panel agrees while the loan is held); after repayment an unannounced
snapshot shows 0.66667. *A forged fill* (8.1): `trading.fix.trade_session` can run a session
through an educational man in the middle; rewriting LastQty from 0.4 to 1.4 passes the session,
because simplefix recomputes BodyLength and CheckSum (observed); `reconcile()` against the
exchange's own statement refuses it ("E0001: qty 1.4 in the session, 0.4 in the exchange's
statement").

**Address registration** (4.8). `PolicyEngine.register`: an `AddressRegistration` approved like the
largest payment, recorded in the audit log, payable only after 24 hours; hashed under its own key,
so payment approvals never count for it.

**Attack panel**, now twenty attacks: an omitted client (9.5), registration with one approval, payment
to a just-registered address, and a signed payment deleted from the audit log and re-hashed (10.2),
caught by the signers' own record (`SigningCluster.used_authorisations`).

**Reassessed.** Vector 4.5, replay after signers restart: an authorisation names one exact sighash,
so a replayed signature can only complete the same transaction with the same txid; no gain, demo
dropped. Two future demos that would mean writing tools to extract key material (substituting a
channel key, reading shares from memory) stay as analysis only.

**Verified.** Full suite: 263 passed. `ruff`, `mypy` strict, `oxlint` clean. `custody-lab attacks`:
20 of 20 refused.

**Open.** One planned future demo (a signer's clock set back, 4.4) and the other ideas in
`atlas/project/ideas.md`.

### Deliverables

- The red team now also shows a custodian hiding a shortfall with coins borrowed for a scheduled
  proof of reserves, exposed by an unannounced one.
- A forged FIX execution report that passes every session check is caught by reconciling against the
  exchange's own record of what it executed.
- New withdrawal addresses now need the approvals of the largest payment and a 24-hour wait before
  anything can be paid to them.
- The attack panel grew to twenty attacks, including a deleted payment hidden by re-hashing the
  audit log and caught by the signers' own records.

## 2026-10-09: Attack-vector analysis; private channels; a split server; a red team

The owner asked for a thorough analysis of attack vectors, added to the future-demos list and the
documentation.

**Analysis.** `manual/attack-vectors.md`: fourteen layers, each vector with what stops it, where it
is shown or tested, and a status (refused and demonstrated, refused and tested, contained, open in
the demo, open). Linked from the README, the manual's contents page and the walkthrough. Two
findings, both now fixed:
- *Sub-shares in clear.* Chapter 2 said the coordinator "learns nothing secret from the messages it
  relays", but the demo relayed every DKG sub-share, refresh package and repair value in clear. They
  are now sealed signer to signer (`custody_lab.mpc.channel`: static X25519, HKDF-SHA256 bound to
  both identifiers and the step, ChaCha20-Poly1305). A recording coordinator cannot open any of them
  (test). The channel keys still pass through the coordinator at start-up; stated where the claim is
  made (cluster.py, chapter 2 re-rendered, the dashboard).
- *One process for coordinator, policy and approvers.* Chapter 0 said a compromised coordinator "can
  only obtain signatures for transactions that people approved"; in the demo the server process
  also held the authority key and both approvers' keys. `custody_lab.demo.parties` runs the policy
  engine and each approver's key in processes of their own; a test checks that this engine's
  authority key is not in the coordinator's process. Chapter 0 re-rendered to say what the split
  does and does not protect.

**Red team** (`custody_lab.demo.redteam`, dashboard tab, `custody-lab redteam`). A deposit credited
at one confirmation is reorganised away on regtest (`invalidateblock`, observed: the deposit drops
to 0 confirmations and the double spend has 2); the books owe 1.50 BTC against 1.00 held; at three
confirmations nothing is credited. A new vector, 5.7: the global whitelist does not bind a
destination to its client, so a withdrawal sent to another client's registered address passes blind
approver devices, and the books still agree with the chain; devices with their own address book
refuse it.

**Verified.** Full suite: 255 passed. `ruff`, `mypy` strict, `oxlint` clean. Red team and key
ceremonies tabs driven headless at 1280 and 390 px, no console messages, no horizontal scroll.

**Open.** Nine future demos remain in the analysis and in `atlas/project/ideas.md`.

### Deliverables

- An attack-vector analysis now covers the whole design layer by layer, with the status of every
  vector and the evidence for it.
- The analysis found two gaps between the demo and its own documents; both are fixed: secret
  key-generation messages are now encrypted end to end, and the policy engine and approvers run apart
  from the coordinator.
- A new red-team demo shows two attacks succeeding against weak rules and failing against the
  defences: a deposit taken back by a reorganised chain, and a withdrawal sent to the wrong
  client's address.
- The red team uncovered a further weakness, a whitelist that does not tie an address to its
  client, and shows the approver-device check that closes it.

## 2026-10-09: A day at the custodian, the client's signature check, chapter 10, key ceremonies

The owner asked for work to continue autonomously, keeping a running list of ideas
(`atlas/project/ideas.md`), adding transactions and complexity with first-principles explanations,
and covering what leading custodians and current research do.

**A day at the custodian** (`custody_lab.demo.day`, dashboard tab, `custody-lab day`). Four clients
deposit from wallets of their own; delta-trading replaces its deposit before it confirms (a full
replace-by-fee double spend, observed on regtest to evict the deposit) and is credited nothing;
alpha-capital and beta-fund trade in their own FIX sessions (`trade()` now takes the client's
SenderCompID); netting across clients sends 0.75 BTC on chain and settles beta-fund's 0.45 BTC in the
books; the settlement spends gamma-treasury's deposit coin; signer 3 goes down at noon; withdrawals
at both tiers; three refusals by the ledger, the whitelist and the velocity limit. The books equal the
chain after every step (3.0999907 BTC at the end). The velocity refusal now reads "1.50 BTC per 24
hours".

**The client checks the custodian's signature in the browser.** `web/src/snapshot.ts` rebuilds the
snapshot's signed message and verifies the BIP340 signature with `@noble/curves` 2.4.0 (audits
reported by its README); `web/src/address.ts` decodes the custody address with `@scure/base` 2.4.0
and compares its key with the signing key. Oracles: all 19 BIP340 vectors, Python-signed snapshots
(altered copies fail), and Bitcoin Core's `rawtr()` addresses.

**Chapter 10, custody in practice.** A research agent produced notes with 122 sources
(`atlas/project/research/custody-landscape-2026.md`). Every fact the chapter states was re-read at its
source in this session: Anchorage, Fireblocks and Coinbase's 10-K on key arrangements; the FBI notice
and reports on Bybit, Drift, Bitget and Liquid; BitForge and TSSHOCK; BIP 445, 360 and 361; NIST IR
8214C; TEE.fail; Circle's USDC terms; CoinGecko's ranking (observed 09:27 UTC). Bybit's reported
`delegatecall` mechanism was not confirmed at the source read and is not stated. The research agent
reported that one of its requests sent the owner's email address in a User-Agent header; the notes
contain no personal data (checked).

**Key ceremonies.** `custody-frost` binds `frost-core` 3.0.0's refresh (`refresh_dkg_*`) and
repairable threshold scheme (`repair_share_part1` to `part3`). `SigningCluster` gains `refresh`,
`wipe`, `repair` and an educational `export_share`. `custody_lab.demo.ceremonies` shows one stolen
share failing alone, two shares of one period signing (a refresh does not undo that), shares from
before and after a refresh refused by FROST, and a lost share rebuilt by two helpers.

**Dashboard.** Two new tabs (the day, key ceremonies); every tab stays mounted; the replay picker no
longer widens a phone-width page; the CLI prints a failed run's error whole without a traceback.

**Verified.** Full suite before the ceremonies: 234 passed; added since: browser snapshot and address
oracles, four cluster tests, three ceremony tests, front-end tests, all passing. `ruff check`, `ruff
format --check src tests`, `mypy` strict and `oxlint` clean. Every new tab driven headless at 1280
and 390 px with no console messages and no horizontal scroll. Chapter 10 renders (14 pages); chapter
9 re-rendered for its next link (only that line changed).

**Open.** See `atlas/project/ideas.md`. The three browser libraries are still not installed
system-wide. `npm audit` reports one finding in build tooling (`source-map-js` under vite), none in
what ships.

### Deliverables

- A second demo scenario plays a custodian's whole day, with deposits, a double-spend attempt,
  two clients trading, withdrawals and three refusals, and checks after every step that the books
  match the coins on the chain.
- Each client can now check in the browser that the custodian signed the published proof of
  reserves, with the key that holds the coins, using audited code independent of the custodian's.
- A new chapter on custody in practice compares the demo with how leading custodians protect keys,
  explains what each large asset needs, and shows that the largest recent losses passed through
  genuine approvals, each fact re-read at its source.
- The demo now refreshes and repairs key shares live: a share stolen before a refresh is shown to be
  useless with one stolen after it, and a lost share is rebuilt without anyone revealing their own.
- The dashboard gained two tabs and works on a phone in every state tested.

## 2026-10-09: Operator QA pass over the rebuilt dashboard

The owner asked for work to continue until the demo is very good. Another session had already
delivered the previous entry's open items and added offline signers, the attack panel, the
browser balance check and replay (the entry below). This session took that state through as an
operator: every tab and mode driven headless at 1280 and 390 px and in dark mode, every
walkthrough section read against the screenshots, and every walkthrough command run as written.

**Found and fixed.**
- At 390 px the page was 547 px wide from the first load. The `.replay` row kept its default
  `min-width: auto`, so the longest recorded run's name (423 px) set the page width. It now has
  `min-width: 0`; the page measured 390 px on load, after a run, with the FIX transcript open,
  after replaying a failed run, and on the balance and attack tabs.
- `custody-lab run --offline 1 --offline 3`, which the walkthrough presents as the expected way to
  see a liveness failure, cut the step 7 error at the terminal width ("FROST re...") and then
  printed an 80-line traceback (103 lines in all). The error line is now printed whole, followed
  by one line naming the run's `events.jsonl`, and the command exits 1. The server still logs
  tracebacks of failed dashboard runs. The test runs at 40 columns and fails on the old code.
- The balance check showed `Error: not an amount: abc`; it now shows `not an amount: abc`.
- The walkthrough's command-line sentence now describes the exit; two paragraphs left ragged by
  edits were rewrapped (a word diff shows whitespace changes only).
- `tests/policy/test_authorisation.py` formatted (the previous entry's open item).

**Checked, no change needed.**
- With all three signers stopped, the FROST crate raises `ValueError('IncorrectNumberOfShares')`,
  which `pipeline.run` turns into "0 of 3 signers online and 2 are required".
- Each attack's refusal comes from the component named: `tests/demo/test_attacks.py` pins the
  text of all sixteen.
- The copy button put the full 64-character value on the clipboard and showed "copied".
- A recording made before events carried `at_ms` replays all nine steps without durations, as the
  walkthrough says.
- From the Windows side, `curl.exe` (through WSL interop) fetched `/api/steps` at 127.0.0.1 and the
  page at localhost with status 200 (observed): a Windows browser on this machine reaches the
  server inside WSL2. This closes the open item carried by both previous entries.

**Verified.** `uv run pytest`: 226 passed. `ruff check`, `ruff format --check src tests`, `mypy`
(strict) and `oxlint` clean; `npm --prefix web run build` succeeded. The walkthrough's
after-the-run commands, run as written against a new settled run, printed every Expect block.
`tests/test_docs_links.py` passes. No console messages in any headless session.

**Open.**
- The three browser libraries are still not installed system-wide; the scratchpad copy lasts one
  session.
- `ruff format --check` with no path also reports Python blocks inside the generated
  `manual/chapters/*.md`, which Quarto writes and which are not edited by hand.
- Step 6's `spends` prints "5 BTC" where step 3 prints "5.00 BTC".
- The six-stage strip shows a partly finished stage as pending: Bitcoin turns amber at step 1,
  back to white until step 3, and stays white from step 4 to step 7.
- `var/demo/` holds the QA runs of both sessions, failed ones included; they fill the replay list.

### Deliverables

- The dashboard was taken through as an operator would use it, on a desktop screen, a phone screen
  and in dark mode, and every statement in the operator's walkthrough was checked against it.
- The dashboard no longer scrolls sideways on a phone once runs have been recorded.
- A failed run on the command line now ends with its error in full and a pointer to the run's
  record, instead of a long technical trace.
- The demo was confirmed reachable from a Windows browser while it runs inside WSL2 on this
  machine.
- The full test suite of 226 tests passes, and every check command in the walkthrough produces
  the output the walkthrough promises.

## 2026-10-09: Offline signers, attack panel, browser balance check, replay

The owner asked for more in the demo, to make it more useful and better to look at, and to keep
building. Five features were added, each with tests, and the dashboard was rebuilt around them.

**Offline signers.**
- `SigningCluster.stop(i)` ends one signer's process. `pipeline.run` takes `offline`: those
  signers' processes stop at the start of step 7, and the coordinator asks signers 1 and 3 while
  both run, otherwise whichever are running (`_asked`). The default run is unchanged, so signer 2
  stays online and unasked as chapter 0 says.
- The first version took the signers to ask (`signers`) and stopped the rest, which stopped
  signer 2 in the default run. It was replaced within the session (commit c842f1c).
- With one signer left, the FROST crate refuses with `IncorrectNumberOfCommitments` (observed);
  step 7 fails with "1 of 3 signers online and 2 are required" and nothing is broadcast.
- `POST /api/runs` takes `{"offline": [...]}` and answers 422 for an identifier outside 1 to 3,
  before creating a run directory; `custody-lab run --offline N`.

**Attack panel.** `custody_lab.demo.attacks` sets up the policy, approvers and a 2-of-3 cluster
without a chain and tries sixteen attacks: seven on the policy engine, six on the signers
(including an authorisation with a valid Ed25519 signature and a forged ML-DSA-65 one), three on
the published records. Each reports the refusing component's own message; one that succeeds is
reported as accepted, which a test proves by breaking `PolicyEngine._decide`. `POST /api/attacks`
streams them through the same worker-thread helper as runs; `custody-lab attacks` prints them and
exits 1 if any got through.

**Browser balance check.** The reserves step publishes each client's inclusion proof.
`web/src/reserves.ts` recomputes the path on WebCrypto SHA-256 and bigint satoshis, sharing no code
with `merkle_sum.py`. `tests/demo/test_browser_verifier.py` runs it under Node on Python-built
proofs, including Hypothesis ledgers. That test found `str(Decimal)` publishing one satoshi as
`1E-8`, which the TypeScript side refuses; balances are now published in fixed point.

**Dashboard.** Three tabs (settlement run, attacks, balance check), a six-stage strip above them, a
progress bar, per-step durations, a summary once settled, a switch per signer, signer roles through
step 9 (the snapshot signature, open since 2026-10-09), shortened hashes with a copy button, and
tables that scroll in their own box (the 390 px word breaks, open since 2026-10-09). `App.tsx` was
split into six modules.

**Durations.** Browser timing showed steps 3 to 9 as "0.0 s". Measured on the server: step 1
5.04 s, step 2 150 ms in that run, steps 3 to 9 between 0 and 41 ms, signing 30 ms. Events that
arrive in one network read cannot be told apart in the browser, so each event now carries `at_ms`
from the server's monotonic clock.

**Replay.** `GET /api/runs` lists the 20 newest recorded runs with how each ended and which signers
were offline; `GET /api/runs/<run>` returns one run's events, by directory name only. The dashboard
replays them, shortening pauses over 700 ms.

**Other.** Step 6 shows what the transaction spends and pays. The missing-`bitcoind` error points at
the README's prerequisites (open since 2026-10-09). `cluster.py` was formatted. The walkthrough
gained four sections (taking a signer offline, checking a client's balance, attacking the design,
replaying a recorded run), and its screen descriptions, troubleshooting, summary table and recap
were updated; the glossary gained **Replay**; README and CLAUDE.md describe the new commands.

**Verified.**
- `uv run pytest`: 226 passed (38 s), including the regtest runs with signer 1 offline and with
  signers 1 and 3 offline. `ruff check` and `mypy` (strict) clean; `oxlint` clean;
  `npm --prefix web run build` succeeded; `tests/test_docs_links.py` passes.
- `custody-lab attacks`: 16 of 16 refused in 0.2 s, each reason read.
- The built dashboard was driven headless (Playwright 1.63.0, headless shell 1243, the three
  libraries again unpacked into the scratchpad): a full run, the balance check with +1 satoshi, the
  attacks, a run with signer 1 offline, a run with signers 1 and 3 offline, replays of a failed and
  a settled run, phone width (390 px) on all three tabs with no horizontal scroll, and dark mode.
  No console messages. Screenshots were inspected.

**Decided.** Three Proposed entries in the CLAUDE.md decisions log: offline signers and how the
coordinator chooses; the attack panel reports rather than raises; the TypeScript verifier as the
tree's cross-language oracle.

**Open.**
- The three browser libraries are still not installed system-wide.
- `ruff format --check` reports `tests/policy/test_authorisation.py`, untouched this session.
- The policy engine's velocity refusal prints the window as `1 day, 0:00:00`; the walkthrough
  explains it rather than the engine changing its message.
- The copy button was not clicked in the headless run; the clipboard was not checked.
- Not checked: the Windows browser reaching the server inside WSL2.

### Deliverables

- The demo can now take any signer offline before signing: with one signer down the payment still
  settles, and with two down it stops safely at the signing step with no coins moved.
- A new attack panel runs sixteen attacks against the demo's real code, from a forged
  approval to a quantum-style forgery and a doctored reserves report, and shows each one refused by
  the right component in its own words.
- Each client can now check its own balance against the published proof of reserves directly in
  the browser, with code independent of the custodian's, and sees the check fail when its balance
  is off by one satoshi.
- The dashboard was redesigned around three tabs, with a live view of where the settlement is,
  real timings per step, a summary once settled, and a layout that works on a phone and in dark
  mode.
- Recorded runs can be replayed on the dashboard without a Bitcoin node, so the demo can be shown
  on any machine and a failed run can be looked at again.
- The operator's walkthrough gained four sections explaining these features from first principles,
  and the full test suite (226 tests) passes.

## 2026-10-09: Dashboard checked in a browser; operator walkthrough

The owner asked to see the dashboard in a browser for the first time, check its nine steps and
key-shares panel against chapter 0, fix what was wrong, and write a step-by-step walkthrough of a
complete run for an operator.

**Browser.**
- The owner's `sudo apt install -y libnspr4 libnss3 libasound2t64` had not taken effect: `dpkg -l`
  listed none of the three packages and `/var/log/apt/history.log` had no entry for them. sudo
  cannot read a password from the `!` prompt, so the install was not repeated.
- Playwright's cached headless shell (`chromium_headless_shell-1243`) ran on the three Ubuntu
  packages unpacked with `apt-get download` and `dpkg -x` into the session's scratchpad, through
  `LD_LIBRARY_PATH`. The driver was Playwright for Python 1.63.0 from the uv cache (its
  `browsers.json` names headless-shell revision 1243), run with
  `uv run --no-project --with playwright==1.63.0`; nothing was added to the project.

**Checked against chapter 0.** Every number matched: height 101, 5.00 BTC funded, 4 fills and 12
FIX messages, 0.85 BTC and 54,415.925 USD, "1 of 2 required approvals", signers 1 and 3, one
confirmation, a 310-satoshi fee, liabilities and assets 4.1499969 BTC, reserve ratio 1. The three
signer process ids differed from the server's. Four mismatches were found and fixed:
- Step 6 listed "fee cap" as a policy check and left out "not authorised before". The fee cap is
  `check_matches` in the settlement code. The step now shows the transaction check (matches
  instruction, fee, fee cap) apart from the engine's seven checks in the engine's order, and is
  titled as chapter 0 titles it, "Build the transaction and apply the policy". Chapter 6 prints
  the step titles and was re-rendered; its Markdown changed in that one line.
- Step 5 showed `base -0.85` and `quote 54415.925`; it now shows "client delivers 0.85 BTC" and
  "client receives 54,415.925 USD". Every BTC, USD and satoshi amount in the step details carries
  its unit.
- The key-shares panel read "Key generation has not run" while step 2 was running; it now names
  the step's state.
- The snapshot path was shown under the home directory; it is now relative to the working
  directory.

**Found while writing the troubleshooting rows.** Without `bitcoind` on `PATH`, `RegtestNode` raised
before the `try` that reports failures: the run emitted no event, the dashboard kept nine pending
steps with no error, and no `events.jsonl` was written. The node is now created and started inside
the `try`, so step 1 fails with the error shown. A new test reproduces the missing `bitcoind`; it
failed on the old code and passes on the new.

**Walkthrough.** `manual/demo-walkthrough.md`: starting the server, each step's problem, what
happens, what is on the screen and where its trading-infrastructure counterpart stops holding;
checks on the run's files afterwards; troubleshooting; a summary table; a recap. Linked from the
README, the manual's contents page and CLAUDE.md.

**Verified.**
- `uv run pytest tests/demo`: 8 passed. `ruff check` and `mypy` (strict) clean; `oxlint` clean;
  `npm --prefix web run build` succeeded.
- The rebuilt dashboard was driven headless through a full run: nine steps done in 6.8 s, no
  console messages, no horizontal page scroll at 390 px wide. Screenshots of every step, the
  expanded FIX transcript and the failure without `bitcoind` were inspected.
- Every command in the walkthrough's after-the-run section was run as written against a real run
  and printed its Expect block, including the altered snapshot failing both checks. The busy-port
  error, `{"detail":"Not Found"}` from a server started outside the repository root, and the
  missing-`bitcoind` failure were each reproduced. `tests/test_docs_links.py` passes.

**Open.**
- The three libraries are still not installed system-wide; the scratchpad copy lasts one session.
- At 390 px the step 4 fills table breaks words inside its cells ("se ll", "0. 4").
- The key-shares panel does not mark the second signature, over the snapshot, in step 9.
- The missing-`bitcoind` error points at "CLAUDE.md, Toolchain"; the README's prerequisites table
  is the page a reader installing Bitcoin Core would use.
- `ruff format --check` reports `src/custody_lab/mpc/cluster.py`, which this session did not touch.
- Not checked: the Windows browser reaching the server inside WSL2.

### Deliverables

- The dashboard was viewed in a browser for the first time, and a full run was checked against the
  manual's walkthrough of the demo: every figure matched.
- The dashboard now labels every amount with its unit and lists the policy engine's checks exactly
  as the engine runs them, with the transaction's own check shown separately.
- A missing Bitcoin Core installation now shows as a clear failure on the first step instead of a
  run that silently does nothing.
- A new operator's walkthrough takes a reader through one complete run, explaining what each value
  on the screen means and why a custodian needs it, without the mathematics.
- The walkthrough shows how to check a run independently from its files, including a
  proof-of-reserves snapshot whose signature stops verifying when one figure in it is changed.

## 2026-10-08: Chapters, atlas and glossary rewritten to the writing standard

The owner asked for the rest of the rewrite after chapter 0 (2026-10-08). Each chapter keeps its
verified facts, cells and citations; what changes is the explanation around them. Headings that the
glossary and atlas link to are kept where the content stays.

**Chapter 1, Foundations.**
- Changed: "What this chapter is for" replaces the learning objectives and the intuition section,
  whose terms came before their explanations. New first-principles sections: why multiplication on
  a clock is not one-way (the key recovered by one division, in a cell); hash functions, with what
  each of the three attacks would break, moved ahead of the Fiat-Shamir transform that uses them;
  a toy Schnorr signature with a real SHA-256 challenge, worked by hand ($e = 18$, $s = 12$) with
  the altered message rejected. The Lagrange weights are derived on the clock from chapter 0's
  1.5 and $-0.5$. The x-only and low-S rules, previously stated without reason, are explained in
  the formal treatment from the cycle's mirror. ECDSA verification is derived. A Recap closes the
  chapter.
- Verified: renders to 27 pages (from 20), exit 0; no page ends on a heading; no printed line over
  80 characters; the two new table pages were rasterised and inspected. Every point quoted on the
  walk was computed: the draft gave $5G = (29, 12)$, which is $25G$; it is $(12, 12)$, now asserted
  in a cell. The BIP340 vector count (19) was read from the test's CSV.
- Glossary: five rows added (Elliptic curve, Point addition, Prover, Verifier, Tagged hash); four
  re-pointed to the sections that now teach them. One atlas link re-pointed from the removed
  "Intuition" section.

**Chapter 2, MPC custody.**
- Changed: "What this chapter is for" states the problem chapter 1 left (the machine that rebuilds
  the key), explains multisig before comparing it with MPC, and keeps the three-questions table as
  a summary. Each first-principles section now opens with the problem it solves. The rogue-key
  attack is explained before the cell that runs it, where the draft pointed forward to the formal
  treatment. Lindell 2017 is explained step by step, including why the decrypted value is
  $k_2^{-1}(z + r x_1 x_2)$. FROST's symbols are each named. Two new worked examples by hand: a
  distributed key generation whose three lines ($3 + x$, $2 + 5x$, $4 - x$) sum to the chapter's
  sharing $9 + 5x$, with Feldman checks; and a proactive refresh that gives new shares 25, 10 and
  26, where old share 1 with new share 3 recovers 8 instead of 9. A Recap closes the chapter.
- Verified: renders to 29 pages (from 22), exit 0; no page ends on a heading; no printed line over
  80 characters; the DKG table page was rasterised and inspected. The DKG and refresh numbers were
  found by search so that no sub-share or commitment is zero, and both are asserted in cells.
- Two statements were narrowed rather than carried: FROST's $H_1$ to $H_5$ are SHA-256 with a
  context string each (not "tags"), and BitForge is described by its missing-modulus-proof
  weakness without detail beyond that.
- Glossary: six rows added (Multisig, Hiding nonce, Binding nonce, Rogue-key attack, Private
  channel, Publicly verifiable encryption); Signing quorum and one atlas link re-pointed from the
  removed "Intuition" section.

**Chapter 3, Key storage.**
- Changed: "What this chapter is for" names the three attackers that motivate the chapter (an
  administrator on a signing host, a backup thief, people with physical access). A new section,
  "Symmetric encryption in brief", explains AES, authenticated encryption and its tag, key
  derivation and key encapsulation, which the draft used without explanation; the draft also
  assumed chapter 7 for ML-KEM. Each first-principles section opens with its problem. Hypervisor,
  microcode, memory encryption and Nitro's PCRs are explained where they appear. The production
  placement of each demo part is argued in prose before its table, and the release pattern's third
  check (report data) is explained as a relay attack. A Recap closes the chapter.
- Verified: renders to 20 pages (from 16), exit 0; no page ends on a heading; no printed line over
  80 characters; the new section's page was rasterised and inspected. A suspected missing chapter
  link turned out to be present (checked in the Markdown and with `pymupdf`).
- Glossary: six rows added (Symmetric encryption, Authenticated encryption, Key derivation
  function, Hypervisor, Microcode, Memory encryption); Enclave, HSM and TEE re-pointed from the
  removed "Intuition" section. The bold-term check now skips code, where `2**128` had been read
  as bold markers.

**Chapter 4, Policy and authorisation.**
- Changed: the draft had no first-principles section; it now has six (default deny; tiers,
  whitelist and a rolling window, with a velocity decision worked by hand and the calendar-day gap
  it closes; signed four-eyes approvals; canonical encoding, with a cell showing two digests of one
  instruction becoming one; the authorisation and the four signer checks; a hash chain built by
  hand, edited, and truncated). "What this chapter is for" names the losses the policy engine
  exists for. The nine-row worked example is explained in prose before its table, and each cell's
  output is described.
- Verified: renders to 20 pages (from 12), exit 0; no page ends on a heading. The new check for
  printed lines over 80 characters found one carried over from the draft (the nine results on one
  line); they now print one per line. The description of the first four audit entries was
  corrected against the rendered output: the fourth is the second instruction's approved
  evaluation.
- Glossary: four rows added (Amount tier, Digest, Authority key, Head); Default-deny, Four-eyes
  and one atlas link re-pointed from the removed "Intuition" section.

**Chapter 5, Trading to settlement.**
- Changed: two new first-principles sections, "Settling against an exchange" (pre-funding and
  off-exchange settlement, from the draft's intuition) and "Many fills, one delivery" (netting worked
  by hand). The Taproot tweak's purpose (no hidden script path) and the tweaked private key are
  explained; the sighash's per-field hashes are named; FIX tags are glossed in the FIX leg. Each
  cell's output is described: the transaction-model cell, the FIX transcript and the regtest run.
  The draft cited "the house rules of engagement (`fix-client/ROE.md`)", a file in another, private
  repository that no reader of this public project can open; the chapter now states the dialect
  directly.
- Verified: renders to 18 pages (from 15), exit 0, settling a real transaction on regtest; no page
  ends on a heading. Every description of output was checked against the rendered Markdown: both
  Logons carry `1137=9`, the transcript ends with a Logout each way (added after the check), the
  refused transaction's fee is 415,000,000 sats, and the custody address holds 4.1499969 BTC after
  settlement.
- Glossary: four rows added (Off-exchange settlement, Pre-funding, Input and output, SegWit); one
  atlas link re-pointed from the removed "Intuition" section.

**Chapter 6, Proof of reserves.**
- Changed: "What this chapter is for" replaces the intuition section. "Hash trees" builds a
  four-item tree and an inclusion proof in a cell before sums are introduced; "Adding sums" walks
  beta-fund's proof by hand next to the figure. The total-only attack, salts and proof of control
  each open with the problem they address. Pedersen commitments are explained (why hiding, why
  binding, why they add), and why hidden values need range proofs. Each cell's output is described.
- Verified: renders to 16 pages (from 13), exit 0, running the whole demo during the build; no page
  ends on a heading. The demo printed all nine steps done, liabilities and assets 4.1499969 BTC and
  a reserve ratio of 1.00000, as the text states.
- Glossary: two rows added (Assets and liabilities, Statement); Proof of reserves re-pointed from
  the removed "Intuition" section.

**Chapter 7, Post-quantum cryptography.**
- Changed: "What this chapter is for" explains what a quantum computer is and keeps the two clocks
  (signatures fail on the day, encryption retroactively). "What a quantum computer breaks" separates
  Shor (broken) from Grover (weakened) before its table. A new by-hand example with two chains of
  length 4 shows the Winternitz advance attack and the checksum that stops it, before the FIPS 205
  WOTS+ cell. LWE is explained in school terms (elimination, and why errors defeat it). The migration
  order is argued from the two clocks. Each cell's output is described. A duration claim for a
  future quantum computer ("hours or days") was replaced by how the work scales, which is what the
  sources support.
- Verified: renders to 21 pages (from 18), exit 0; no page ends on a heading; the backup sizes
  (1,088 + 12 + 48 bytes) and both half-forged token refusals in the text match the rendered output.
- Glossary: two rows added (Quantum computer, Checksum); Harvest now decrypt later and Shor's
  algorithm re-pointed from the removed "Intuition" section.

**Chapter 8, Industry and regulation.**
- Changed: "What this chapter is for" states the chapter's central idea (ownership moving from a
  register to keys) and where the demo connects. A new first-principles section, "Registers and
  tokens". Jargon is explained where it appears: money market fund, margin, repo, layer 2, transfer
  agent, primary dealers, ERC-20 and ERC-1155, omnibus address. The DvP cell's two trades are
  explained before it runs. The regulatory statements (the MiCA Article 75 table, the US rules, the
  SOC definitions) and every dated fact are kept as they were, not reworded; the new paragraphs
  around them say what each points to for a key-holding system, framed as the chapter's reading.
- Verified: renders to 17 pages (from 14), exit 0; no page ends on a heading; the DvP balances, the
  two legs and the fee walkthrough's equal assets and liabilities in the text match the rendered
  output. One sentence that carried no fact was cut before rendering.
- Glossary: six rows added (Register, Margin, Repo, Layer 2, Omnibus address, Transfer agent);
  Token and Tokenisation re-pointed from the removed "Intuition" section.

**Chapter 9, Capstone.**
- Changed: "What this chapter is for" and a new first-principles section: how a design review runs,
  and safety against liveness, with a worked example of why a threshold of independent sites raises
  availability (99 to 99.97 percent for 2-of-3) and lowers the chance of compromise (1 in 100 to
  about 3 in 10,000) at once, and why shared administration erases both. The architecture figure is
  explained in prose; the failure table opens with how to read it, and RBF, CPFP and reorganisation
  are defined before the table instead of after it. The worked example's numbers are each
  explained. A Recap closes the chapter. The question-and-answer structure is kept.
- Verified: renders to 17 pages (from 14), exit 0; no page ends on a heading; the probability table
  printed by the new cell matches the text (0.999702 and 2.98e-04 for 2-of-3).
- Glossary: Safety and Liveness re-pointed to the section that now defines them.

All ten chapters now follow the writing standard. Every rewrite was rendered to both formats, and
`tests/test_docs_links.py` passes after each.

**Atlas and glossary.**
- Changed: all 43 concept entries rewritten to one seven-part format (in one sentence, the problem,
  the idea with the manual's worked numbers, why custody cares, in the demo, in the manual,
  sources), replacing the bullet summaries; every file and function reference and every source is
  kept. The regulatory statements in the MiCA, qualified-custodian and SOC entries are kept as
  written. The FIX entry's pointer to a rules-of-engagement file in another, private repository is
  replaced by the dialect itself. The glossary is rebuilt from a one-sentence table into an
  alphabetical list: 216 terms, each defined in two to four sentences, with its existing links. The
  atlas index describes the new entry format.
- Verified: `tests/test_docs_links.py` passes after each area; the glossary generator stopped on any
  term without a new definition and on any definition without a term (none either way); `ruff`
  clean.
- After the push, GitHub's rendered HTML for the glossary and chapters 2 and 9 shows the formulas
  marked up for maths display, the links, chapter 9's figure and the warning boxes.

**Open.** The owner's review of the rewritten manual. Unchanged from earlier entries: the dashboard
in a browser (headless Chromium here needs `libnspr4`, `libnss3` and `libasound2t64`), ML-KEM
decapsulation vectors, and four Proposed decisions in `CLAUDE.md`.

### Deliverables

- Every chapter of the manual now teaches from first principles: each idea starts from the problem
  it solves, is explained in plain words, is worked by hand with small numbers, and is then run in
  code that checks those numbers when the manual is built.
- New worked examples show, among others, a key generated by three machines without any of them
  knowing it, a share refresh that makes stolen old shares useless, a Winternitz forgery stopped by
  its checksum, and why a 2-of-3 signing cluster is both more available and harder to compromise
  than a single key.
- Every chapter now opens with what it is for and closes with a recap, and every term it introduces
  is in the glossary.
- All 43 atlas entries are rewritten as self-contained explanations with the manual's worked numbers
  and links to the sections that teach them.
- The glossary defines 216 terms in two to four sentences each, alphabetically, with links into the
  manual.
- A test now fails if any link in the repository's Markdown points to a missing page or section, so
  later edits cannot silently break the manual's cross-references.

## 2026-10-08: Open-source licence, links between chapters, the manual on GitHub, README

**Changed.**
- Licence (owner's choice): MIT OR Apache-2.0, copyright Esoterics611. `LICENSE-MIT` and
  `LICENSE-APACHE` are GitHub's standard texts (`gh api /licenses/mit`, `/licenses/apache-2.0`)
  with only the MIT year and holder filled in. The licence is declared in `pyproject.toml`
  (`license`, `license-files`), both Rust `Cargo.toml` files and `web/package.json`.
- `manual/links.py`, a Pandoc JSON filter in standard-library Python, registered in
  `manual/_quarto.yml`. It rewrites links to sibling `.qmd` sources to `.pdf` or `.md`, links
  every "chapter N" and "Module N" in running text, adds previous and next lines at the top and
  bottom of each chapter, and in Markdown output puts an `<a id>` before every heading. It is
  in mypy's file list.
- `manual/_quarto.yml` builds a second format, GitHub Markdown, beside each source
  (`manual/chapters/NN-slug.md`, figures in `NN-slug_files/`). All ten chapters are rendered and
  the Markdown is committed; PDFs stay uncommitted.
- `scripts/render-manual.sh` renders every chapter, or the ones named, in both formats.
- `manual/README.md`, the contents page; `README.md` rewritten: the problem, one run in nine steps
  with links to chapters, reading order, prerequisites and commands with expected output, what is
  real and what is a toy, how it is tested, layout, records, licence.
- `atlas/glossary.md`: every "Taught in" pointer is a link to its section. Each atlas entry's "In
  the manual" line links its chapter and each quoted section, and each module heading in
  `atlas/index.md` links its chapter (one-off script, not kept).
- Chapter 0 links the glossary and atlas.
- `CLAUDE.md`: layout, commands, two Accepted decisions.

**Verified.**
- Quarto passes a JSON filter the format (`latex` for PDF, `commonmark` for GitHub Markdown) and
  the input file in `QUARTO_DOCUMENT_FILE` (observed in a scratch project before the filter was
  written).
- `scripts/render-manual.sh`: all ten chapters render in both formats (exit 0).
- Chapter 0's PDF holds 35 links to sibling chapter PDFs (`pymupdf`); its Markdown has 45 heading
  anchors and 34 chapter links.
- A link check over every Markdown file in the repository: 682 relative links, none pointing at a
  missing file or anchor.
- No generated Markdown contains a local path or a personal name (`grep` for `/home/`, `/tmp/`,
  and the account and owner names).
- The built wheel carries `License-Expression: MIT OR Apache-2.0` and both licence files;
  `cargo metadata` reads the licence for both crates.
- `mypy` (strict) and `ruff` are clean on the filter.
- After the push, GitHub's rendered HTML (`gh api .../contents/<file>`, `Accept:
  application/vnd.github.html`): chapter 0 has 71 formulas marked up for maths display, its
  figure, 34 relative chapter links and its heading anchors; the README and chapter 1 show their
  warning boxes. GitHub's licence detection reports Apache-2.0 only, reading one of the two files.

**Found (observed).** Two atlas entries cited headings by shortened names that no longer
matched: `mpc/cggmp.md` ("Production ECDSA libraries") and `settlement/bitcoin-regtest-taproot.md`
("What a key-path signature signs"). Both now name and link the full headings.

**Open.**
- Whether every formula displays correctly on GitHub needs a look in a browser; the HTML only
  shows that GitHub marks each one up for its maths display.
- `pyproject.toml` still names the owner as author, while the licence and history use
  Esoterics611.
- Each chapter rewrite changes headings, so the glossary and atlas links need re-pointing with it.
- Unchanged: the owner's read of chapter 0, the dashboard in a browser, ML-KEM decapsulation
  vectors, three Proposed decisions.

### Deliverables

- The project is open source under MIT OR Apache-2.0, the same licences as the Rust libraries it
  builds on.
- The whole manual reads on GitHub: every chapter is published as a page with its code output
  and figures, and readers can click from chapter to chapter.
- Every mention of another chapter, in the PDFs and on GitHub, is a link, and each chapter ends
  with previous and next links.
- The glossary and the atlas link each term and concept to the section of the manual that
  teaches it.
- The README explains what the project demonstrates and where to start reading, and gives
  commands to install and run it with the expected output.

## 2026-10-08: Writing standard; chapter 0 rewritten as the pilot

**Changed.**
- The owner read the manual and could not follow it. Reading chapter 0, chapter 1 and the atlas
  found five causes: terms used before they were explained (chapter 0's first table used DKG,
  threshold signing, Merkle sum trees and sighash), one sentence where a paragraph was needed,
  facts given without their reason, tables carrying the explanation, and glossary definitions
  built from other undefined terms.
- `CLAUDE.md`: a writing standard for the manual, atlas and glossary. Each concept is taught as
  problem, plain idea with a trading-infrastructure counterpart, worked example, code, failure
  and recap. One Accepted decision.
- `manual/chapters/00-orientation.qmd` rewritten to the standard, from 1,861 to about 10,100 words
  (prose, tables and code). New: Bitcoin in five ideas (ledger, keys, signatures, hash functions,
  transactions and blocks); secret sharing as a line through points with a figure; threshold
  signing worked by hand ($s = k + e d$ on shares 10, 13 and 16, combined to 39 by Lagrange
  weights); nonce reuse solved as two equations; DKG as three lines summed; policy, approvals and
  the authorisation; a compromise table for the two quorums; proof of reserves with the demo's
  tree worked by hand; the nine steps in the pipeline's own order and names. Eleven code cells
  compute the chapter's numbers from `custody_lab` and the `cryptography` library.
- `manual/chapter-template.qmd`: opens with "What this chapter is for", gives the per-concept
  order in First principles, and closes with a Recap.
- `atlas/glossary.md`: ten terms chapter 0 now defines (Custodian, Digital signature, Ledger,
  Node, Partial signature, Policy engine, Quorum, Secret sharing, Threshold signing, Transaction);
  182 in total.

**Verified.**
- Chapter 0 renders to 31 pages (exit 0); no page ends on a heading (`pypdf`). Every cell's
  printed output was read in the PDF: the threshold pairs all combine to 39, the nonce-reuse cell
  recovers 7, netting gives 0.85 BTC and 54,415.925 USD, the fee is 155 vB x 2 = 310 satoshis, and
  liabilities and assets after settlement are both 4.1499969 BTC. The figure and three table
  pages were rasterised (`pymupdf`) and inspected.
- Every bold term in chapter 0 is in the glossary, apart from paragraph labels.
- The template renders (exit 0).
- Facts re-derived from the code, not carried over: policy tiers and checks
  (`policy/engine.py`), the 60-second authorisation lifetime, the four signer checks and nonce
  burning (`mpc/cluster.py`), the leaf layout and alphabetical leaf order (`reserves/merkle_sum.py`),
  the three-way address check (`demo/pipeline.py`, `settlement/chain.py`), and that each run
  starts its own regtest node.

**Found (observed).** Quarto (`project: type: default`) leaves links to other `.qmd` files
unchanged in both PDF and GitHub Markdown output. A standard-library Python JSON filter, tested in
a scratch project, rewrites them to `.pdf` and `.md`; Quarto passes it `latex` and `commonmark`
as the format. Section links still fail in Markdown output, which drops heading ids.

**Open.**
- The owner reads chapter 0 before chapters 1 to 9, the atlas and the glossary are rewritten.
- Links between chapters and a full README, both requested; plan pending.
- The dashboard in a browser; ML-KEM decapsulation vectors; three Proposed decisions.

### Deliverables

- The manual has a written standard for explanation: every concept starts from the problem it
  solves, is explained in plain words, and is worked through by hand before any code.
- The orientation chapter is rewritten to that standard and now teaches Bitcoin, keys,
  signatures, key splitting, threshold signing, approvals and proof of reserves from nothing,
  with every number computed by code at build time.
- The chapter shows by hand, with numbers under 100, how two of three machines produce the
  signature of a key that none of them holds.
- The glossary gains ten basic terms the manual previously used without defining.

## 2026-10-08: Build plan brought current; figures are matplotlib, Mermaid dropped

**Changed.**
- `atlas/project/build-plan.md`: M6 and M7 are marked done on 2026-09-25 with what each delivers.
  The M7 row names RustCrypto `slh-dsa` instead of calling the SLH-DSA choice open. The M0 and
  `quarto-cli` rows no longer list Mermaid as a blocker.
- `manual/chapter-template.qmd`: the Mermaid block is replaced by a matplotlib figure cell, which
  is what every chapter already uses.
- `CLAUDE.md`: Toolchain status is done; the note under Commands says figures are matplotlib and
  why Mermaid is not used; the Quarto rationale no longer counts Mermaid; one Proposed decision.

**Verified.**
- No `{mermaid}` block exists in `manual/chapters/*.qmd` (`grep`).
- The template renders to a 4-page PDF (exit 0), the figure caption on page 2. The figure cell was
  rendered to PNG and inspected; the first version clipped the boxes at the bottom edge, fixed
  with `set_ylim`.

**Open.**
- The dashboard has not been viewed in a browser. Playwright's cached Chromium
  (`~/.cache/ms-playwright/chromium_headless_shell-1243`) does not start on this host:
  `libnspr4.so` is missing.
- ML-KEM decapsulation vectors; the three Proposed decisions.

### Deliverables

- The build plan records all ten modules as done, including proof of reserves and post-quantum,
  with the libraries actually chosen.
- The chapter template draws its example diagram with matplotlib, so a new chapter renders to PDF
  on this host without a browser installed.
- The Mermaid-in-PDF blocker is closed: no chapter uses Mermaid, and the template no longer does.

## 2026-09-27: Fees charged to the client; no house coins at the custody address

**Changed.**
- `demo/pipeline.py`: `HOUSE_BUFFER` is removed. The custody address is funded with the clients'
  5.00 BTC only, and the settlement's network fee is debited from the settled client's balance
  with the delivered amount. The docstring states why (MiCA Article 75(7)).
- `tests/demo/test_pipeline.py`: the reserve ratio must now equal 1, and the snapshot's assets
  must equal its liabilities.
- Chapter 5: funding and the worked arithmetic move from 5.01 to 5.00 BTC (change 414,999,690
  sats); one sentence names who pays the fee.
- Chapter 6: alpha-capital's balance after settlement is 1.1499969 BTC in the figure, the table,
  the text, the cells and Solution 2; the reserve ratio is exactly 1.
- Chapter 8: the ¶7 row and the walkthrough ("Fees without house coins") describe the new
  behaviour. Exercise 4 now asks for the alternative, a house address spent as a second input.
- Chapter 9: the restart row applies once shares persist. In the demo a restart loses the share
  with the used-token set, so no persistence was added. The production list no longer names
  segregated house funds.
- `atlas/industry/mica.md`, `atlas/capstone/system-design.md`, `CLAUDE.md` (status, one
  Proposed decision).

**Verified.**
- `pytest`: 202 passed; `ruff` and `mypy` clean.
- `custody-lab run` on regtest: funding 5.00 BTC, fee 310 sats, liabilities and assets both
  4.1499969 BTC, reserve ratio 1.00000.
- Chapters 5, 6, 8 and 9 re-render (15, 13, 14 and 14 pages); none ends a page on a heading. The
  printed outputs match the text: chapter 5's custody output of 4.1499969 BTC after settlement,
  chapter 6's ratio of 1.00000, chapter 8's equal assets and liabilities. Chapter 6's tree figure
  was rendered to PNG and inspected with the longer labels.

**Decided.** The two-input design from the previous session's prompt was not built. It needs a
multi-input transaction builder, a second key and a second authorisation, all to keep round
client balances. Charging the fee to the client closes the ¶7 gap with a four-line change, and it
matches common custody practice. Recorded as Proposed in `CLAUDE.md` for the owner.

**Open.** Unchanged from the capstone entry: ML-KEM decapsulation vectors, Mermaid in PDF, the
dashboard in a browser, and the Proposed Merkle-sum oracle decision.

### Deliverables

- The demo no longer keeps the custodian's own coins at the client custody address: each
  settlement's network fee is charged to the client being settled.
- After every settlement batch the custody address now holds exactly what clients are owed, and
  the proof of reserves shows a ratio of exactly 1.
- The manual's figures, worked examples and exercises in chapters 5, 6, 8 and 9 match the new
  behaviour, and every one of them was regenerated by running the code.
- The capstone's failure table now states that the signer-restart replay risk applies only once
  shares survive a restart, which they do not in the demo.

## 2026-09-27: Module 9, capstone

**Changed.**
- Wrote `manual/chapters/09-capstone.qmd` as a design review in question-and-answer form:
  - the brief, the assumptions, and the safety and liveness requirements;
  - a production architecture figure, drawn with matplotlib because Mermaid in PDF is still
    blocked;
  - the eight-step settlement walk, and a table of what each component holds and what its
    compromise gives an attacker;
  - deep dives: threshold signing vs multisig, FROST vs threshold ECDSA, the signer's checks,
    two quorums, hot, warm and cold, the key lifecycle, what clients get, quantum risk;
  - fourteen failure modes with class, detection and response, and seven trade-offs with their
    cost;
  - a numbers cell computed from the libraries, and a walkthrough on the real signing cluster.
- `atlas/capstone/system-design.md`, linked from the index; 9 glossary terms (171 in total).
- Updated chapter 0's reading order, `CLAUDE.md` module status and the build plan. Every module
  in the build plan is now done.

**Verified.**
- Chapter 9 renders to 13 pages; page endings read with `pypdf`, none on a heading. The figure was
  rendered to PNG and inspected before it went into the chapter.
- The numbers cell printed: 155 vB and 310 sats for a one-input settlement (the fee chapter 6's
  demo paid), 58 vB per further key-path input, a 1,984-byte authority key, a 7,047-byte
  serialised token, and 20 siblings for a million clients.
- The walkthrough ran the real cluster: signers {1, 3} and {2, 3} each produced a valid 64-byte
  signature under one group key; the first token replayed to {1, 2} was refused by signer 1.
- Every glossary pointer names a heading in its chapter. Chapter 0 re-renders.

**Found (observed in `mpc/cluster.py`).** Each signer keeps its used-authorisation set in process
memory. A restart empties it, and in a cluster with $n \ge 2t$ two disjoint signer sets can each
honour one token. Both are bounded by the token's expiry and by its naming one exact message; the
chapter lists them as failure modes, and Exercise 3 works the second. The code is unchanged.

**Open.**
- ML-KEM decapsulation vectors remain unchecked. Checking them needs a second implementation that
  loads expanded decapsulation keys, such as RustCrypto `ml-kem` bound through `custody-pq`.
- Mermaid in PDF still needs `unzip` on this host.
- The dashboard has not been viewed in a browser.

### Deliverables

- Chapter 9 presents the whole custody system as a design review: the brief, the architecture,
  the reasoning behind each major choice, and what each choice costs.
- A diagram shows where every key lives in a production deployment, with shares at three
  independent sites and one of them offline.
- A table of fourteen failure modes gives, for each, whether money or only availability is at
  risk, how it is detected, and the response.
- The chapter's figures (transaction sizes, fees, token and proof sizes) are computed from the
  project's own code when the manual is built, not quoted.
- Running the real signing processes, the chapter shows that any two of the three signers can
  sign for the same key, and that a reused approval token is refused.

## 2026-09-27: Module 8, industry and regulation

**Changed.**
- Wrote `manual/chapters/08-industry.qmd`:
  - First principles: four forms of money on a ledger, DvP with an atomic-settlement model cell,
    settlement finality, public and permissioned ledgers;
  - Formal treatment: tokenised funds and collateral, Canton and Kinexys, Agorá and mBridge, MiCA
    Article 75 paragraph by paragraph, US qualified-custodian rules and recent changes, SOC
    reports, and Israel (public sector, companies, researchers);
  - worked example: the demo against MiCA Article 75;
  - walkthrough: the demo's two settlement legs (0.85 BTC on chain, USD 54,415.925 never settled)
    and the custodian's fee buffer commingled with client coins at the custody address.
- Six atlas entries under `atlas/industry/`, linked from the index; 21 glossary terms (162 in
  total).
- Updated chapter 0's reading order, `CLAUDE.md` module status and the build plan.

**Verified.**
- Chapter 8 renders to 13 pages; every cell ran and printed the values the text states. Page
  endings read with `pypdf`: none ends on a heading. Chapter 0 re-renders.
- Every glossary pointer names a heading in its chapter.
- Primary sources read: the BIS Agorá press release of 27 May 2026 (eight central banks, the
  Bank of Canada having joined the original seven; atomic multi-currency settlement in a
  prototype; real-value testing next; no production timeline); MiCA Article 75 text.
- Reported by secondary sources and marked **verify current** in the chapter: tokenised Treasury
  products about USD 15 billion; CFTC tokenised-collateral guidance; Canton and Broadridge DLR
  volumes; the DTCC Canton plan; Kinexys volumes and JPMD on Base; mBridge membership; the MiCA
  transition ending 1 July 2026; the SEC safeguarding withdrawal, SAB 122 and the state trust
  company no-action letter; GENIUS Act timing; the CLARITY Act cloture vote failing on
  15 September 2026; the digital shekel timeline; Sela and Icebreaker; Project Eden; the Israeli
  acquisitions; researcher affiliations.

**Decided.** Single-fund figures (BUIDL) are left out: two sources a month apart gave USD 2.8
billion and USD 5 billion. The chapter cites the market aggregate only.

**Open.**
- The demo breaches MiCA Article 75(7) by design: its fee buffer shares the custody address with
  client coins. The chapter describes the fix (Exercise 4); the pipeline is unchanged.

### Deliverables

- Chapter 8 explains the four kinds of money now issued as tokens: bank deposits, stablecoins,
  money market fund shares and central bank money. It sets out what the holder of each actually
  owns.
- It describes the institutional networks (Canton, Kinexys) and the central bank projects
  (Agorá, mBridge) as of September 2026, with every fact that can change marked for re-checking.
- It sets out the EU's custody duties under MiCA and the US qualified-custodian rules, and maps
  each duty onto the demo's controls.
- It shows, with the demo's own code, that the demo settles only the bitcoin side of a trade and
  keeps the custodian's own coins at the client address. Both are gaps a regulated custodian
  would have to close.
- It maps Israel's part in the field: the Bank of Israel's digital shekel and experiments, Project
  Eden, the MPC custody companies founded in Israel, and the Israeli researchers whose protocols
  the demo teaches.

## 2026-09-27: Module 3, key storage

**Changed.**
- Wrote `manual/chapters/03-key-storage.qmd`, a chapter with no module:
  - First principles: three questions for any key store, key wrapping, tamper response and the
    FIPS 140-3 levels, remote attestation, sealing, side channels;
  - Formal treatment: HSMs (PKCS#11, key ceremonies), TEEs (SGX, SEV-SNP and TDX, Nitro
    Enclaves, interposer attacks), MPC as a storage choice, combinations, a comparison table;
  - worked example: where each part of the demo would live in production;
  - walkthrough: a key share released over ML-KEM only to an enclave whose report carries the
    reviewed measurement and binds the requester's public key.
- Three atlas entries under `atlas/storage/`, linked from the index. 26 glossary terms (141 in
  total); the chapter 6 "Attestation" row now points to "Remote attestation", and the Txid row's
  second pointer gained its missing "5 FP" prefix.
- Updated chapter 0 (reading order, what is real), `CLAUDE.md` module status and the build plan.

**Verified.**
- Chapter 3 renders to 16 pages. Every cell ran; the key-wrapping cell reproduces the RFC 3394
  section 4.1 vector, and the release cell refuses a patched build and a substituted public key.
  Page endings read with a throwaway `pypdf`: none ends on a heading.
- Chapter 0 re-renders.
- Every glossary pointer names a heading in its chapter (a scratchpad script over all chapters).
- Facts checked by web search, each marked in the chapter:
  - FIPS 140-2 certificates moved to the historical list on 21 September 2026 (reported);
  - AWS CloudHSM `hsm2m.medium` and Azure Managed HSM at FIPS 140-3 Level 3 (reported);
  - Nitro Enclaves isolation, PCR0 and PCR8, KMS condition keys (**observed** in AWS
    documentation);
  - SGX deprecated on client processors from 11th-generation Core, continued on Xeon (reported);
  - WireTap, Battering RAM, TEE.fail and DDRop (September 2026, ACM CCS 2026), with Intel's and
    AMD's statements that interposer attacks are out of scope (reported);
  - PKCS#11 3.2 approved as an OASIS Standard in 2026, with ML-KEM, ML-DSA and SLH-DSA
    (reported);
  - SP 800-186 allows secp256k1 for blockchain-related applications (reported);
  - NIST IR 8214C threshold call taking submissions, no standard yet (reported);
  - Fireblocks: MPC-CMP shares and policy engine in SGX across clouds (reported by Fireblocks).

**Open.**
- Vendor-specific claims about programmable HSMs and BIP340 support are left general and marked
  **verify current**; no vendor documentation was read.

### Deliverables

- Chapter 3 compares the three places a custody key can live: a hardware security module, a
  processor enclave, and shares spread across machines.
- For each option, the chapter states where the key exists, who can make it sign, what an
  outsider can verify, and which attacks it does not stop.
- It covers the memory-bus attacks on processor enclaves published between late 2025 and
  September 2026, which the chip makers place outside their protection.
- A worked example places every key in the demo where a production deployment would keep it.
- A model walkthrough hands a key share only to a machine that proves, by attestation, that it
  runs the reviewed signer code.

## 2026-09-27: Demo front ends

**Changed.**
- `demo/cli.py` is the `custody-lab` command (`[project.scripts]`):
  - `run` runs the demo once and prints each step, its details (cut to the terminal width) and
    the summary;
  - `serve` starts uvicorn on the server app.
- `demo/server.py`:
  - `POST /api/runs` runs `pipeline.run` on a worker thread in a fresh `var/demo/<run>/` and
    streams its events in the response as NDJSON;
  - `GET /api/steps` lists the steps;
  - `web/dist` is served at `/` when it has been built;
  - there is no limit on concurrent runs.
- `demo/pipeline.py`:
  - `new_workdir` names each run directory by its UTC start time;
  - a step that raises is reported as a `failed` event, which also lands in `events.jsonl`,
    before the exception propagates.
- `web/`: the Vite starter is replaced by the dashboard:
  - a Run button and nine step rows with status and details;
  - fills and signers as tables, and the FIX transcript collapsed;
  - a key-shares panel mapping each share to its process ID and marking the two signers;
  - light and dark themes, and a dev proxy from `/api` to port 8000.

  The starter assets are removed and `web/README.md` is rewritten.
- Tests:
  - `tests/demo/test_front_ends.py` (5 tests) drives the CLI and the server against stand-ins
    for `pipeline.run`. They share one file because mypy rejects a second `conftest.py` in a test
    tree without `__init__.py`;
  - `test_pipeline.py` adds a regtest test in which the FIX step raises.
- Updated `CLAUDE.md` (layout, commands, module status, one Accepted decision), the build plan's
  demo slice row, and chapter 0 (how to run the demo, where the code is).

**Verified.**
- `pytest`: 202 passed, up from 196. `ruff` and `mypy` are clean (60 files).
- `npm --prefix web run build` (tsc and vite) and `oxlint` pass.
- One real run through `custody-lab serve`:
  - `POST /api/runs` streamed running and done for all nine steps;
  - shares 1 to 3 were held by three processes, and signers 1 and 3 signed;
  - the settlement had one confirmation, and the reserve ratio was 1.00241;
  - the run directory holds `events.jsonl`, `audit.jsonl` and `reserves/`;
  - `/` served the built dashboard.
- Two real runs posted at the same time both completed all nine steps, each with its own signer
  processes, settlement transaction and run directory.
- Chapter 0 renders to 7 pages. Page endings were read with a throwaway `pypdf` (this host has no
  rasteriser); none ends on a heading.

**Decided (owner).** Runs stream as NDJSON in the `POST /api/runs` response, not as server-sent
events.

**Open.**
- The dashboard has not been viewed in a browser: this host has no headless browser. Only the
  type check, the bundle and the served HTML were checked.
- Starlette 1.7.0 warns that its test client's use of `httpx` is deprecated in favour of `httpx2`
  (**observed** in the pytest warnings). Not acted on.
- Chapters 3, 8 and 9. ML-KEM decapsulation vectors. Mermaid in PDF still needs `unzip`.

### Deliverables

- The demo runs from one command, `custody-lab run`, which prints each step of the custody flow as
  it happens.
- A browser dashboard starts a run and shows all nine steps live, from the FIX trading session to
  the proof-of-reserves snapshot. It shows which operating-system process holds each key share
  and which two signed.
- `custody-lab serve` serves the dashboard and its API from one process. Each run gets its own
  private Bitcoin chain and signer processes; two runs at once both settled.
- A step that fails is reported by name on the dashboard, in the command-line output and in the
  run's event log.
- 202 tests pass. A manual run through the server settled a transaction on the private chain with
  one confirmation.

## 2026-09-25: Module 7, post-quantum

**Changed.**
- `rust/custody-pq`: a PyO3 binding to RustCrypto `slh-dsa` 0.1.0 covering all 12 FIPS 205
  parameter sets. It exposes key generation (random and from seeds), and sign and verify in both
  the internal form and the context form. It is a uv workspace member and a runtime dependency.
  `signature` is pinned to `=2.3.0-pre.4`, because cargo otherwise picks pre.7, which does not
  compile with this `slh-dsa`.
- `src/custody_lab/pq/wots.py` (EDUCATIONAL) implements the FIPS 205 pieces for
  SLH-DSA-SHA2-128f:
  - address (ADRS) and its compressed form;
  - SHA-256 tweakable hashes and hash chains;
  - WOTS+ key generation, signing and public-key recovery, with the checksum;
  - XMSS nodes, signing and root recovery;
  - the SLH-DSA public root.
- Hybrid authorisation tokens (`policy/authorisation.py`):
  - `AuthorityKey` holds an Ed25519 key and an ML-DSA-65 key;
  - every token carries both signatures, the ML-DSA one with context
    `custody-lab/authorisation`;
  - `check` requires both;
  - `PolicyEngine`, the pipeline, every test and the chapter 2, 4 and 5 cells use it.

  Chapter 4's authorisation section is updated to match.
- `tests/pq/vectors/acvp-subset.json` holds 46 NIST ACVP vectors from `usnistgov/ACVP-Server`
  commit `a7f283c`, with the SHA-256 of each source file and the selection rule. New tests:
  - `tests/pq/test_pq_vectors.py`: ML-DSA key generation and verification, ML-KEM key generation,
    SLH-DSA key generation for all 12 parameter sets, verification, deterministic signing, and
    hedged signing;
  - `tests/pq/test_wots.py`: the public root against 10 NIST cases and against RustCrypto on
    fresh seeds, XMSS round trips, and the checksum defeating a chain advance;
  - `tests/policy/test_authorisation.py`: a token with only one valid signature is rejected.
- Wrote `manual/chapters/07-post-quantum.qmd`:
  - First principles: what a quantum computer breaks, Lamport with a forgery after reuse,
    Winternitz chains and the checksum, XMSS and SLH-DSA, one-bit LWE;
  - Formal treatment: ML-KEM, ML-DSA (Fiat-Shamir with aborts), SLH-DSA, a size table, the hybrid
    token;
  - threshold post-quantum signatures, migration design, and walkthroughs for the libraries, an
    ML-KEM share backup and the hybrid token.
- Six atlas entries under `atlas/pq/` and 19 glossary terms (115 in total). Also updated:
  - the orientation chapter (reading order, what is real);
  - `CLAUDE.md` (layout, toolchain, module status, three Accepted decisions);
  - the build plan's SLH-DSA row.

**Verified.**
- `pytest`: 196 passed, up from 134. `ruff` and `mypy` are clean (57 files).
- Teaching WOTS+/XMSS reproduces PK.root for all 10 NIST SLH-DSA-SHA2-128f keyGen cases on the
  first run, and matches RustCrypto on fresh seeds.
- RustCrypto `slh-dsa` matches NIST on the following (**observed**):
  - key generation, 21 cases over all 12 parameter sets;
  - verification, 2 pass and 1 fail as expected;
  - a deterministic signature, byte for byte.
- `cryptography` ML-DSA matches NIST key generation for 44, 65 and 87, and verification including
  2 rejected cases. ML-KEM-768 and -1024 match NIST key generation.
- All chapters render. Chapters 2, 4, 5 and 6 were re-rendered with hybrid tokens, and chapter 6
  runs the full demo with them. Chapter 7 renders to 18 pages. No page in any chapter ends on a
  heading.
- Every glossary section pointer resolves.
- Citations checked by web search:
  - Threshold Raccoon (EUROCRYPT 2024, ePrint 2024/184);
  - Trilithium (ePrint 2025/675) and Quorus (ePrint 2025/1163);
  - BIP 360 Pay-to-Merkle-Root, merged 2026, and BIP 361 (reported by news sites; **verify
    current**);
  - NIST IR 8547 draft dates, 2030 and 2035 (**verify current**).

**Decided (owner).** RustCrypto `slh-dsa` via PyO3; Lamport as an illustration only; hybrid
authorisation tokens.

**Open.**
- ML-KEM decapsulation vectors are not checked: `cryptography` loads ML-KEM private keys only from
  seeds, and those vectors give expanded keys.
- Approvals, proof of control and settlements remain classical.
- Chapters 3, 8 and 9.

### Deliverables

- The custody signers now require every policy authorisation to carry both an Ed25519 and an
  ML-DSA-65 signature. A forger would have to break both a classical and a post-quantum scheme.
- SLH-DSA, ML-DSA and ML-KEM are in the project and checked against NIST's official ACVP test
  vectors. SLH-DSA comes from a Rust library bound the same way as the FROST signer.
- A from-scratch WOTS+ and XMSS implementation reproduces NIST's SLH-DSA public keys exactly, as
  the teaching version of hash-based signatures.
- Chapter 7 covers the following, with every example executed at build time:
  - what a quantum computer breaks;
  - how hash-based and lattice signatures work from first principles;
  - why they resist threshold signing;
  - the order in which a custodian should migrate.

## 2026-09-25: Module 7 library survey

**Changed.** Updated the library status table in `atlas/project/build-plan.md` with the
post-quantum survey. No code changed.

**Verified.**
- `cryptography` 50.0.1 (OpenSSL 4.0.2) exposes ML-DSA-44/65/87 and ML-KEM-768/1024 with
  seed-based key generation. ML-DSA-65 and ML-KEM-768 round trips ran here with FIPS 203/204
  sizes.
- It has no SLH-DSA module.
- PyPI `slh-dsa` 0.2.5 imports as `slhdsa` with all 12 parameter sets.
- `pqcrypto` 1.0.0 still ships empty algorithm packages here.
- NIST ACVP vectors exist for all three standards. The SLH-DSA keyGen file gives seeds and the
  expected public key.

**Open.** SLH-DSA library choice, and whether Lamport is a module or a chapter illustration.
Whether the demo moves its authorisation tokens to hybrid Ed25519 + ML-DSA. All three wait on
the owner.

## 2026-09-25: Module 6, proof of reserves; first commit

**Changed.**
- First commit, `489194e`: everything up to the previous entry. Rendered PDFs are now ignored
  (`manual/.gitignore`).
- Reviewed the uncommitted Module 6 code from 2026-09-24 before changing it:
  - `reserves/merkle_sum.py` hashes both children's sums into each parent and rejects negative
    sibling sums;
  - `reserves/snapshot.py` signs a tagged hash of the canonical statement;
  - `PolicyEngine.authorise_attestation` issues a token for that message without approvals.

  No defects found. No source file changed.
- Tests added, 9 in total:
  - `tests/reserves/test_merkle_sum.py`: the root against an independent hashlib derivation;
    Hypothesis over arbitrary ledgers; altered balance, salt, id and negative sibling; the Hu,
    Zhang and Guo total-only attack, passing a total-only tree and failing this one;
  - `tests/reserves/test_snapshot.py`: the published file verifies with the standard library and a
    BIP340 verifier; an attestation token signs its attestation and is refused for a sighash;
  - `tests/demo/test_pipeline.py` (regtest): all nine steps complete, the snapshot signature
    verifies, and the snapshot's audit head is in the exported log.
- Wrote `manual/chapters/06-reserves.qmd`:
  - First principles: hash trees, sum trees, the total-only attack, salts and leaks, proof of
    control with domain separation, and what a proof of reserves does not show;
  - Formal treatment: the leaf and node layout, verification, the snapshot, and a zero-knowledge
    section without code (Pedersen commitments, range proofs, Provisions, DAPOL+);
  - the worked example on the demo's ledger, and a code walkthrough that runs the whole demo and
    verifies the published snapshot from the file.
- Added four atlas entries under `atlas/reserves/` and 14 glossary terms (96 in total). Also
  updated:
  - the orientation chapter (chapter 6 in the reading order);
  - the audit-trail atlas entry (the head is now anchored);
  - `CLAUDE.md` module status and layout, and one **Proposed** decision on the Merkle-sum test
    oracle.

**Verified.**
- `pytest`: 134 passed, up from 125. `ruff` and `mypy` are clean (54 files).
- The pipeline, run from a file, completed all nine steps:
  - 0.85 BTC settled with one confirmation and a 310-sat fee;
  - liabilities 4.15 BTC, assets 4.1599969 BTC, reserve ratio 1.00241;
  - all inclusion proofs and the proof-of-control signature verify.

  Run from stdin, it failed when the signer processes started. Inferred, not confirmed: `spawn`
  re-imports `__main__`, which stdin cannot provide.
- Chapter 6 renders to 13 pages and runs the full demo on regtest during the build. Its pages were
  rasterised and inspected; no page in chapters 0 or 6 ends on a heading.
- Every chapter section cited in the glossary exists.
- Citations checked by web search:
  - Hu, Zhang and Guo, *Computers & Security* 2019, ePrint 2018/1139 (reported);
  - Dagher et al., CCS 2015;
  - Ji and Chalkias, CCS 2021;
  - Chalkias, Chatzigiannis and Ji, ePrint 2022/043.

  The `dapol` Rust crate is reported by the same search (GitHub, docs.rs) and was not built.

**Decided.**
- Chapter 6 covers zero-knowledge proofs of liabilities as a section with no code, as the build
  plan says.
- The Merkle-sum test oracle is recorded as Proposed in `CLAUDE.md`.

**Open.**
- The pipeline has no CLI or dashboard entry point; the docstring describes both.
- The Mazars pause and exchange zk-SNARK proofs in chapter 6 are marked **verify current**.
- The remaining modules: key storage (chapter 3), post-quantum (Module 7), industry (Module 8)
  and the capstone.

### Deliverables

- The repository has its first commit, with rendered PDFs excluded.
- Proof of reserves works end to end. After each settlement the demo publishes the following,
  and a third party can verify the file with the standard library and a BIP340 verifier:
  - a Merkle-sum commitment to client liabilities;
  - the custody key's on-chain balance;
  - a 2-of-3 FROST proof-of-control signature;
  - the anchored policy audit head.
- New tests show that the liabilities tree resists the published attack on total-only sum trees,
  and that an attestation authorisation cannot be used to sign a transaction.
- Chapter 6 teaches the topic from first principles and runs the whole demo during its build.
  Four atlas entries and 14 glossary terms cover the topic.

## 2026-09-25: First principles in chapters 2 and 5, glossary, depth rule

**Changed.**
- Chapter 2 has a new "First principles" section with seven subsections:
  - MPC, parties, rounds, the coordinator, broadcast and private channels;
  - three ways to split a key: Shamir, additive, multiplicative;
  - adversary models: corrupted, semi-honest and malicious parties, static and mobile
    adversaries, abort and identifiable abort, UC security;
  - commitments: hiding, binding, hash and point commitments, Feldman commitments on the toy
    curve;
  - zero-knowledge proofs, with chapter 1's forgery as the reason a transcript reveals nothing;
  - Paillier's homomorphism on a toy key with $N = 35$;
  - concurrent sessions: the ROS attack and FROST's binding factor.
- Five new cells in chapter 2. `dkg.check_round1` rejects a rogue-key commitment, and every toy
  number is asserted. Other chapter 2 changes:
  - "MPC" is expanded at first use and safe primes are defined;
  - Exercises 6 (classify semi-honest and malicious actions) and 7 (Feldman binding) are added,
    with an asserted solution for 7;
  - Paillier 1999, Feldman 1987, Drijvers et al. 2019 and Benhamouda et al. 2021 are added to
    further reading.
- Chapter 5 has a new "First principles" section with four subsections:
  - UTXOs against an account ledger: inputs, outputs, outpoint, txid, change, fee, satoshis,
    dust;
  - locking scripts and witnesses: Taproot key and script paths, addresses, SegWit;
  - what the sighash covers, plus locktime and sequence;
  - mempool, blocks, proof of work, confirmation, regtest and coinbase maturity.

  One offline cell builds the worked example's transaction, shows `check_matches` refusing the
  transaction with its change output removed (fee 416,000,000 sats), and shows that one satoshi
  more to the payee changes the sighash.
- Chapter 4: "canonical" is defined at the start of "Canonical encoding". Its other terms map onto
  pre-trade risk checks and are defined where used, so it has no First principles section.
- `atlas/glossary.md` has 82 terms, each with one sentence and the chapter section that teaches
  it. It is linked from `atlas/index.md` and the orientation chapter.
- `manual/chapter-template.qmd` has a "First principles" section.
- `CLAUDE.md` changes:
  - new rule "Assume no cryptography background";
  - a decision-log row (accepted by the owner this session);
  - the glossary added to the layout table;
  - chapter page counts updated.

**Verified.**
- All five chapters render: orientation 7 pages, chapter 1 20, chapter 2 22, chapter 4 12,
  chapter 5 15. Chapter 5 still confirms a regtest transaction during the build.
- New cell output appears in the PDFs:
  - "rejected: participant 3: bad proof of knowledge";
  - "no change output: fee 416000000 sats outside [0, 10000]".
- A text scan of all five PDFs finds no page whose last line is a heading.
- Chapter 2's and chapter 5's new pages were rasterised and inspected.
- A script confirmed that every chapter section title cited in the glossary exists.
- `pytest`, `ruff` and `mypy` were not run; no source file changed.

**Found and fixed.**
- Chapter 2's split table hyphenated "Multiplicative". Widened the column.
- The first wording of the depth rule required a First principles section in every chapter, which
  chapter 4 does not need. The rule now requires the section where a chapter introduces
  cryptography or chain mechanics.

**Open.**
- The uncommitted, untested `demo/pipeline.py` and `reserves/` work noted in the previous entry is
  unchanged. `CLAUDE.md` still lists Module 6 as a skeleton.
- The atlas entries' Definition lines still use compressed wording; the glossary covers the terms.
- Nothing is committed.

### Deliverables

- Chapter 2 now teaches, before its formal treatment:
  - what a multi-party protocol is;
  - the attacker models its security claims rest on;
  - commitments, zero-knowledge proofs and homomorphic encryption;
  - why many concurrent signing sessions are an attack surface.
- Chapter 5 now explains Bitcoin's transaction model from the ground up: coins as outputs, change
  and fee, locking scripts and witnesses, the sighash, and confirmation.
- A new glossary defines 82 terms in one sentence each and points to the section that teaches
  each one.
- The manual's standing rule now assumes no cryptography background. The chapter template carries
  a First principles section for future chapters.
- All five chapters render with every new example asserted by executed code.

## 2026-09-25: Orientation chapter, first principles in chapter 1

**Changed.**
- Added `manual/chapters/00-orientation.qmd`, with no code cells. It covers:
  - the demo's nine steps in plain words, each with the idea it rests on and the chapter that
    teaches it;
  - the two quorums;
  - trading-infrastructure counterparts and where each analogy breaks;
  - terms with a different meaning here (nonce, share, commitment, settlement);
  - which components are real and which are toys;
  - reading order.
- Chapter 1 has a new "First principles" section before the formal treatment. It starts from
  school algebra:
  - modular arithmetic and inverses;
  - the four group rules;
  - the cycle of multiples of $G$: generator, order, scalar, and the two moduli;
  - double-and-add and the discrete logarithm;
  - Schnorr identification: what the nonce hides, why the commitment comes first, key recovery
    from a reused nonce, a forgery when the challenge is known in advance, then Fiat-Shamir;
  - Shamir sharing as a line through points.
- Six new cells assert every number in that prose. The learning objectives are reworked.
  Exercise 6 (forge with a known challenge) has an asserted solution. Schnorr 1991 and
  Fiat-Shamir 1986 are added to further reading.
- `manual/_quarto.yml`:
  - the `Highlighting` redefinition is guarded, so a chapter without code blocks renders;
  - section and subsection headings reserve 16 and 9 lines, so no heading is left at a page foot
    above a table.

**Verified.**
- All five chapters render:
  - orientation, 7 pages;
  - chapter 1, 20 pages (was 12);
  - chapter 2, 15 pages;
  - chapter 4, 12 pages;
  - chapter 5, 11 pages, and it still settles a regtest transaction during the build.
- Chapter 1's new cells check:
  - the group rules on all 31 elements of the toy curve;
  - the 31-step cycle, by repeated addition;
  - key recovery from a reused nonce;
  - the forged commitment $(21, 18)$.
- Orientation and chapter 1 pages were rasterised and inspected. A text scan of all five PDFs
  finds no page whose last line is a heading.
- `pytest`, `ruff` and `mypy` were not run; no source file changed.

**Found and fixed.**
- The orientation chapter failed to render. The shared header redefines `Highlighting`, which
  pandoc defines only in a document with a code block.
- Orientation table columns were sized by header length. Widths are now set in the separator
  rows.
- Headings were stranded at the page foot above a long table. The first subsection threshold
  exceeded what a section check leaves after its own heading, which recreated the fault below
  a section heading. Thresholds of 16 and 9 lines avoid it.

**Observed, not changed.**
- The following were modified at 20:40-20:41 on 2026-09-24, after the previous log entry:
  - `src/custody_lab/demo/pipeline.py`;
  - `src/custody_lab/reserves/`;
  - `policy/engine.py`, which gained `authorise_attestation` and now imports
    `reserves.snapshot`.

  They have no tests and no log entry. The pipeline imports.
- Mermaid is still blocked. `unzip` is absent, and Quarto's `chrome-headless-shell` directory is
  empty.
- Nothing in the repository is committed; `master` has no commits.

**Open.**
- Plan items 3 to 6 wait for review of chapter 1's depth and tone:
  - chapter 2 background (adversary models, commitments, zero-knowledge proofs, homomorphic
    encryption, concurrent sessions);
  - chapter 5's Bitcoin transaction model;
  - `atlas/glossary.md`;
  - the template section and the `CLAUDE.md` depth rule.

### Deliverables

- A new orientation chapter traces one settlement through the demo in plain words. For each step
  it names the idea the step rests on and the chapter that teaches it.
- Chapter 1 now teaches its vocabulary from school algebra before any notation: modular
  arithmetic, groups, generator and order, the discrete logarithm, what a signature's nonce and
  commitment do, and Shamir sharing as a line through points.
- Every number in the new material is computed on the toy curve and asserted by code that runs
  when the chapter renders.
- All five chapters render under the shared configuration, which now handles chapters without
  code and keeps headings with the tables that follow them.

## 2026-09-24: Module 5, trading to settlement

**Changed.**
- `src/custody_lab/trading/fix.py`: FIX 5.0 SP2 on FIXT.1.1. `8=FIXT.1.1`; Logon
  `98=0 108=30 1137=9`; NewOrderSingle; fills with 150=F 39=2 32/31 14 151 75 60 and no AvgPx;
  MsgSeqNum checked. The toy exchange fills at the limit price. `trade()` also works from inside a
  running event loop.
- `src/custody_lab/settlement/`:
  - `netting.py`: `Decimal` netting.
  - `bitcoin.py`: BIP86 tweak, BIP341 `sig_msg`/`taproot_sighash` for all hash types, BIP144
    serialization, parser, exact BTC-to-sats conversion.
  - `transfer.py`: one-input spend, smallest sufficient UTXO, dust to fee. `check_matches`
    checks exact payment, change only to custody, and a fee cap computed from input minus
    outputs.
  - `regtest.py`: a private `bitcoind` on free ports, readiness via `bitcoin-cli -rpcwait`, and
    JSON-RPC with `Decimal` amounts.
  - `chain.py`: descriptor-derived address, `validateaddress`, `scantxoutset rawtr(...)`.
- `rust/custody-frost`: `taproot_output_key`; `sign`/`aggregate` take `taproot=True`
  (`sign_with_tweak`/`aggregate_with_tweak`). `SigningCluster.sign(..., taproot=True)` and
  `taproot_output_key()` pass them through.
- Added a `regtest` pytest marker and a mypy override for `simplefix`.
- Wrote chapter 5, which settles a real transaction on a throwaway node when rendered, and four
  atlas entries under `atlas/settlement/`.

**Verified.**
- `pytest` 125 passed, including `test_frost_signed_taproot_spend_is_mined`. `ruff` and `mypy`
  are clean.
- All BIP 341 wallet vectors pass: 7 tweaks including script-tree roots, and `sigMsg`/`sigHash`
  for 7 hash types. The expected signatures are reproduced byte for byte by chapter 1's BIP340
  signer with zero aux randomness.
- The custody output key is computed identically by the Rust crate, `bitcoin.taproot_tweak`, and
  Bitcoin Core's `tr()` descriptor.
- Chapter 5's render confirmed a spend with 1 confirmation and 4.1599969 BTC of custody change.
  The FIX transcript and settlement pages were rasterised and inspected.

**Found and fixed.**
- `check_matches` initially had no fee cap, so a transaction paying the approved amount to the
  approved address could burn the rest as fee. The cap is added and tested.
- `trade()` failed inside a running event loop (caught by the chapter render).
- 14 Markdown lists across chapters 2, 4 and 5 lacked the blank line pandoc requires and
  rendered as run-on paragraphs. All are fixed and checked in the PDF text.

**Decided.**
- **FIX 5.0 SP2, never 4.4** (owner, mid-session). Conventions come from
  `~/code/fix-client/ROE.md`, read only; the fix-gateway and fix-client repos agree.
- Taproot transactions are written from BIP 341, not taken from a library. The oracles are the
  BIP vectors and Bitcoin Core acceptance.

**Open.**
- Signer-side transaction decoding (PSBT).
- Multi-UTXO settlements.
- Fee estimation from the mempool.

### Deliverables

- Fills from a FIX 5.0 SP2 session (FIXT.1.1, DefaultApplVerID 9) are netted per settlement cycle
  into one instruction per asset.
- Each instruction becomes a Taproot key-path spend that is checked against it (exact payment,
  change, fee cap), authorised by the policy engine, signed 2-of-3 by separate FROST processes,
  and mined by Bitcoin Core.
- The transaction and sighash code passes every BIP 341 wallet test vector, and three independent
  implementations agree on the custody address.
- Chapter 5 renders to an 11-page PDF that settles a real regtest transaction during the build.

## 2026-09-24: Module 4, policy and authorisation

**Changed.**
- Wrote `src/custody_lab/policy/`:
  - `model.py`: canonical JSON, `SettlementInstruction`, and Ed25519 `Approval`.
  - `audit.py`: hash-chained `AuditLog` and `verify_chain`.
  - `authorisation.py`: a signed token binding id, instruction digest, exact message and expiry.
  - `engine.py`: a default-deny `PolicyEngine` with seven ordered checks. Velocity and "authorised
    before" are read from the audit log.
- Signers now enforce authorisations:
  - `SigningCluster(threshold, count, authority)` and `sign(message, signers, token)`.
  - Each signer burns its nonces, then verifies the token's signature and expiry, that it matches
    the FROST signing package's message (new binding `signing_package_message`), and that it has
    not been used before.
- `cryptography` moved from the `dev` group to runtime dependencies.
- Added `manual/_quarto.yml` with the shared PDF settings. Code lines now wrap (`fvextra`), and
  chapter front matter keeps only title, subtitle and date.
- Updated chapter 2's cluster cell for the gate, and wrote chapter 4 and five atlas entries under
  `atlas/policy/`.

**Verified.**
- `pytest` 92 passed, `ruff` clean, `mypy` clean (37 files).
- Hypothesis checks two properties: authorised volume never exceeds the velocity cap in any
  24-hour window, and unknown assets are always denied.
- Cluster tests confirm signers refuse forged, expired, message-substituted and replayed tokens.
- Chapters 1, 2 and 4 re-render under the shared config (12, 14 and 12 pages). Chapter 2's and 4's
  signing pages were rasterised with `pypdfium2` and inspected.

**Found and fixed.**
- `SigningCluster._request` raised on the first signer error without reading the other replies.
  The unread reply was then taken as the answer to the next request. It was caught by
  `test_signers_refuse_forged_expired_and_replayed_tokens`, which received the previous test's
  error. All replies are now drained before raising.
- Page inspection showed code lines of 81-88 characters and long outputs clipped at the margin.
  The 88-character check was wrong: the code area is about 80 characters. Code now wraps; cell
  output does not, so printed lines stay under 80 characters.

**Decided.**
- The engine's only state is the audit log.
- Until Module 5 the caller supplies the sighash with the instruction and the engine takes the
  binding on trust. The chapter says so.

**Open.**
- Policy governance (who changes rules and whitelists) is not implemented.
- The audit log is in memory.
- The anchoring of the audit head is planned for Module 6.
- Taproot tweak binding and transaction library for Module 5.
- Rendered PDFs are neither committed nor ignored.

### Deliverables

- A default-deny policy engine decides every settlement instruction through seven ordered checks:
  asset, amount, tier quorum, whitelist, rolling velocity limit, duplicate authorisation, and
  four-eyes approvals signed with Ed25519.
- Every decision is written to a hash-chained audit log that detects edited, deleted and
  reordered entries, and the engine reads its velocity state back from that log.
- The MPC signers now refuse to produce a share without the policy engine's signed
  authorisation. They check it against the exact message in the FROST signing package and reject
  forged, expired, substituted and replayed tokens.
- A coordinator bug that could pair one signer's error with the next request was found by the new
  tests and fixed.
- Chapter 4 renders to a 12-page PDF with a nine-step worked example asserted in code, and all
  chapters now share one PDF configuration that wraps long code lines.

## 2026-09-24: Module 2, MPC custody

**Changed.**
- Teaching code in `src/custody_lab/mpc/`, all EDUCATIONAL, NOT PRODUCTION:
  - `paillier.py`: Miller-Rabin primes, encryption, homomorphic add and scalar multiply.
  - `lindell17.py`: two-party ECDSA, semi-honest core, zero-knowledge proofs omitted and listed.
  - `frost.py`: RFC 9591 FROST(secp256k1, SHA-256).
  - `dkg.py`: Pedersen DKG with Feldman checks and proof of knowledge; zero-sharing refresh.
- Added `encode_point`/`decode_point` (SEC1) to `foundations/ec.py`, and `expand_message_xmd` and
  `hash_to_field` (RFC 9380) to `foundations/hashing.py`.
- Demo signing path:
  - `rust/custody-frost/src/lib.rs` binds ZF `frost-secp256k1-tr` 3.0.0: `dkg_part1..3`,
    `commit`, `signing_package`, `sign`, `aggregate`, `group_public_key`. It is stateless, bytes
    in and out.
  - `src/custody_lab/mpc/cluster.py` (`SigningCluster`) runs one spawned process per share.
    Nonces are single-use and erased on use.
- Tests in `tests/mpc/`. The RFC 9591 vectors are stored at
  `tests/mpc/vectors/frost-secp256k1-sha256.json` (sha256 `5bda3e29…`, from `cfrg/draft-irtf-cfrg-frost`
  `poc/`).
- Wrote chapter 2 (`manual/chapters/02-mpc-custody.qmd`) and eight atlas entries under
  `atlas/mpc/`.

**Verified.**
- Module 1: `pytest` 42 passed, `ruff` and `mypy` clean, before any Module 2 change.
- After Module 2: `pytest` 68 passed, `ruff` clean, `mypy` clean (29 files). Two issues found by
  the first lint run were fixed.
- The educational FROST matches every RFC 9591 intermediate value: shares, nonces, commitments,
  binding-factor inputs, binding factors, signature shares and the final signature.
- The ZF crate's 2-of-3 signatures from three separate processes verify with
  `custody_lab.foundations.schnorr.verify` for all three signer pairs; a single signer is refused.
- Lindell 2017 signatures (2048-bit Paillier) verify with `cryptography`.
- Chapter 2 renders to 13 pages with all six cells executed.

**Decided.**
- The Rust binding passes serialized bytes rather than holding Python objects. Each signer
  process owns its secrets, and the coordinator relays only public packages.
- The cggmp21 listing is abridged from docs.rs 0.6.3 and not compiled.
- Backup and repair are covered as prose, pointing at cb-mpc PVE and ZF `repairable`.

**Open.**
- Taproot tweak (`sign_with_tweak`, `aggregate_with_tweak`) is not yet bound; Module 5 needs it
  for BIP86 key-path spends.
- The Taproot transaction library.
- Rendered PDFs are neither committed nor ignored.
- Mermaid is still blocked on `unzip`.

### Deliverables

- The demo's signing path works end to end. Three separate processes run distributed key
  generation and 2-of-3 FROST signing through the Zcash Foundation crate. The resulting BIP340
  signatures verify with an independent implementation.
- Teaching implementations of Paillier, two-party ECDSA (Lindell 2017), FROST and distributed key
  generation with proactive refresh are in place, each checked against an external oracle.
- The educational FROST reproduces every intermediate value of the RFC 9591 secp256k1 test
  vector.
- Chapter 2 renders to a 13-page PDF covering threshold signing, CGGMP, FROST, DKG, refresh and
  backup, with a hand-checkable threshold signature worked on the toy curve.
- Eight MPC atlas entries are drafted, and the full suite (68 tests), ruff and mypy pass.

## 2026-09-24: Module 1, Foundations

**Changed.**
- Wrote `src/custody_lab/foundations/`, all EDUCATIONAL, NOT PRODUCTION:
  - `ec.py`: the `Curve` group law, `SECP256K1`, and a toy curve y^2 = x^3 + 7 over F_43 with n = 31.
  - `hashing.py`: SHA-256 and BIP340 tagged hashes.
  - `ecdsa.py`: sign and verify, with low-S.
  - `schnorr.py`: BIP340.
  - `shamir.py`: split, Lagrange coefficients, reconstruct.
- Wrote tests in `tests/foundations/`. Oracles are `cryptography` 50.0.1 for ECDSA and public
  keys, and all 19 official BIP340 test vectors
  (`tests/foundations/vectors/bip340-test-vectors.csv`, sha256 `34c9d1d9…`). Shamir uses Hypothesis
  property tests plus an exhaustive secrecy check on Z_31.
- Wrote `manual/chapters/01-foundations.qmd`, with hand-computed toy examples asserted in code, and
  six atlas entries under `atlas/foundations/`.
- Added `cryptography` to the `dev` group and `matplotlib` to the `docs` group.
- Removed the second-person line from the chapter template's objectives.

**Verified.**
- Chapter 1 rendered to a 12-page PDF with all 12 code cells executed. The PDF text contains each
  cell's output.
- secp256k1 constants were checked against independent sources: p equals 2^256 - 2^32 - 977; G
  equals `cryptography`'s generator; n*G is infinity; n passes a Fermat check.
- Twenty random ECDSA sign/verify round trips passed, and BIP340 vector 0 reproduced (ad-hoc run).
- The figure was exported to PNG and inspected.
- `pytest`, `ruff` and `mypy` were not run.

**Found and fixed.** The first chapter render failed: the secp256k1 group order had a dropped hex
digit (63 digits, not prime). The render's executed cells caught it before any test run.
`test_n_times_generator_is_infinity` covers it.

**Decided.**
- Chapter 1 uses a matplotlib figure instead of Mermaid, because headless Chrome is still blocked
  on `unzip`.
- EdDSA is covered by `cryptography`'s Ed25519, with no from-scratch version.

**Open.**
- Run the test suite.
- Whether rendered chapter PDFs are committed. `manual/chapters/01-foundations.pdf` is currently
  untracked and not ignored.

### Deliverables

- Module 1 teaching code implements secp256k1 arithmetic, ECDSA, BIP340 Schnorr and Shamir secret
  sharing in readable Python, labelled EDUCATIONAL, NOT PRODUCTION.
- Its test suite checks the code against independent oracles: the `cryptography` library and the
  19 official BIP340 test vectors.
- Chapter 1 renders to a 12-page PDF whose worked examples are computed by hand and asserted by
  executed code. Every listing in it ran at build time.
- The chapter build caught a wrong secp256k1 constant before the tests were run, the failure the
  executed-manual design was chosen to catch.
- Six atlas entries cover finite fields, elliptic curves, hash functions, ECDSA, Schnorr/BIP340
  and EdDSA, and Shamir sharing.

## 2026-09-24: Module 0, toolchain

**Changed.**
- Added a `docs` dependency group (quarto-cli, ipykernel, nbclient, pyyaml). It and `dev` are
  installed by default.
- Added the Rust extension `rust/custody-frost` (PyO3 0.29, maturin, `frost-secp256k1-tr` 3.0.0).
  It is a uv workspace member and a dependency of `custody-lab`. Added `tests/test_custody_frost.py`.
- Added `scripts/regtest.sh` and `scripts/bitcoin-regtest.conf`; node data goes in `var/regtest`.
- Scaffolded `web/` from Vite 9.2.1's `react-ts` template.
- Installed, per user, with no sudo:
  - TinyTeX in `~/.TinyTeX`.
  - Rust 1.98.1 via rustup. rustup added `. "$HOME/.cargo/env"` to `~/.profile` and `~/.bashrc`.
  - Bitcoin Core 31.1 in `~/.local/opt`, symlinked into `~/.local/bin`.

**Verified.**
- `quarto check jupyter` passed.
- A copy of the chapter template, with the Mermaid block removed, rendered to a 3-page PDF with
  lualatex. Its code cell ran in `.venv/bin/python` and imported `custody_lab`.
- `uv sync` built the extension, and `custody_frost.ciphersuite_id()` returned
  `FROST-secp256k1-SHA256-TR-v1`.
- `bitcoind` 31.1 SHA256 matched `SHA256SUMS`. The regtest node started, mined 101 blocks to a
  bech32m address (wallet balance 50.00000000) and stopped.
- `npm run build` in `web/` succeeded.
- `pytest`, `ruff` and `mypy` were not run.

**Decided.** React for the dashboard, the Rust extension as a runtime dependency, and the `docs`
group on by default. All three are logged as Proposed in `CLAUDE.md`.

**Open.**
- Mermaid in PDF: `quarto install chrome-headless-shell` fails with
  `Failed to spawn 'unzip': entity not found`. Fix: `sudo apt install -y unzip`, then rerun it.
- The GPG signature on Bitcoin Core's `SHA256SUMS` was not checked.

### Deliverables

- The manual toolchain works: Quarto 1.10.18 with TinyTeX renders the chapter template to PDF,
  executing its Python cells in the project environment.
- The demo's threshold-signing library, ZF `frost-secp256k1-tr` 3.0.0, compiles into a PyO3
  extension that `uv sync` builds and Python imports.
- A local Bitcoin Core 31.1 regtest node starts, mines to a Taproot address and stops through
  `scripts/regtest.sh`.
- The TypeScript dashboard scaffold (Vite, React) builds.
- Mermaid diagrams in PDF remain blocked on the missing `unzip` system package.

## 2026-09-24: project setup, threshold-signing feasibility

**Changed.**
- Created the uv project (`custody-lab`, Python 3.12) with a package skeleton of seven empty
  subpackages and one import smoke test. The dev group holds pytest, hypothesis, ruff and mypy.
- Wrote `CLAUDE.md`, `atlas/index.md`, `atlas/project/build-plan.md`,
  `atlas/project/threshold-signing-feasibility.md` and `manual/chapter-template.qmd`.

**Verified.**
- `uv sync` resolved 16 packages.
- cb-mpc was cloned and its README, `Makefile`, `CMakeLists.txt`, C API headers, theory PDFs and
  Cure53 report were read.
- `cryptography` 50.0.1 signed and verified with ML-DSA-65 on this host.
- PyPI and crates.io metadata were read for each candidate library.
- `pytest`, `ruff` and `mypy` were not run.

**Decided.** The owner limited the project to Python, TypeScript and Rust, at showcase depth. The
cb-mpc build was stopped for that reason before it started. On review, the owner accepted every
proposed decision in the `CLAUDE.md` log. The demo signs with FROST (`frost-secp256k1-tr`, 2-of-3)
on Bitcoin regtest.

**Open.**
- The Taproot transaction library.
- The SLH-DSA library.
- Quarto, Rust and `bitcoind` are not installed.

### Deliverables

- `CLAUDE.md` defines the project's purpose, conventions, architecture, toolchain, module status
  and a dated decisions log.
- The repository is a uv-managed Python 3.12 package, with one subpackage per demo module and a
  strict lint, type and test configuration.
- `atlas/index.md` indexes 42 planned knowledge-base entries across the nine curriculum areas and
  defines the entry format.
- `atlas/project/build-plan.md` sequences the modules into a thin end-to-end slice followed by
  deepening, estimated at about 24.5 working days.
- `manual/chapter-template.qmd` fixes the eight-section chapter structure and executes code cells
  at render time.
- `atlas/project/threshold-signing-feasibility.md` records that cb-mpc implements Lindell 2017,
  HLNR 2018 and Lindell 2024 Schnorr in C++ with no Python binding. It recommends from-scratch
  Python for teaching and the Zcash Foundation FROST crate (Rust) for the demo.
