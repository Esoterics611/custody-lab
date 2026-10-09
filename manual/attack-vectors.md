# Attack vectors: what can go wrong, and what stops it

## What this document is for

A custody system is judged by the payments it refuses. This document goes through the ways the
demo's design can be attacked, layer by layer, from the moment the key is generated to the
published proof of reserves, and says for each what stops it, where that defence lives in the
code or the tests, and what remains open. It is a companion to the walkthrough's [Attacking the
design](demo-walkthrough.md#attacking-the-design), which runs sixteen of these attacks, and to
[chapter 9](chapters/09-capstone.md#failure-modes), whose failure table sets out the same design
from the defender's side.

Two distinctions run through it. The **design** is the architecture of chapter 9: separate
machines for the signers, the policy engine with its key in a hardware security module, approvers
on devices of their own. The **demo as packaged** runs everything on one computer for
convenience, and some defences of the design do not hold there. Each vector says which of the two
it is about.

Each vector carries one of five statuses:

| Status | Meaning |
|--------|---------|
| Refused, demonstrated | The demo runs the attack and shows the refusal (attack panel, a scenario, or a browser check) |
| Refused, tested | A test makes the attack and asserts the refusal |
| Contained | The attack can succeed, but a limit bounds what it gains |
| Open in the demo | The design stops it; the demo as packaged does not |
| Open | Neither the demo nor the design as written stops it |

Every open vector is also listed under [Future demos](#future-demos) and in
[the ideas list](../atlas/project/ideas.md).

## How to think about an attacker

**The problem.** "Is it secure?" has no answer until it is said against whom. A thief on the
internet, an administrator of one server, an approver who has been bribed and a supplier whose
software is installed everywhere can each do different things, and a defence against one may be
nothing against another.

**The idea in plain words.** An attacker wants one of four things: to move coins it does not own
(a failure of safety, which cannot be undone), to stop coins moving (a failure of liveness, which
costs time), to make the custodian report something false (a failure of the records), or to learn
something secret, such as a share or a client's balance. For each, ask what the attacker must
control, and count the independent parties that must fail before it succeeds. A design is as
strong as that count, taken at its smallest.

The counterpart is a penetration test's scope and a trading firm's control framework: who could
send an order, who could change a limit, who could alter a fill. The comparison stops at
recovery. A wrongly executed trade can be busted and a payment recalled; a confirmed Bitcoin
payment cannot. So custody puts its effort before the signature, and treats every vector that
moves coins as one that must be stopped, not merely detected.

## Two findings about the demo as packaged

Writing this analysis found two places where the demo did not do what its documents said. Both are
now fixed.

**Finding 1, fixed: the coordinator could read the key-generation sub-shares.** In distributed key
generation each signer sends every other signer a sub-share, a point on its secret line, and anyone
who sees all of them can compute every share. Chapter 2 said these travel over private channels,
"which the application around the protocol must provide". The demo provided none: the sub-shares,
and the refresh and repair values, passed through the coordinator in plain form. They are now
sealed from signer to signer (`custody_lab.mpc.channel`: X25519 between the two signers,
HKDF-SHA256, ChaCha20-Poly1305), and a test records everything the coordinator relays and shows it
cannot open any of it (`tests/mpc/test_channel.py`). One trust remains: the signers' channel
public keys pass through the coordinator when the processes start (vector 1.4).

**Finding 2, fixed: one process held the coordinator, the policy engine and the approvers.**
`pipeline.run` and `day.run` created the policy engine's authority key and bob's and carol's
approval keys inside the server process, which is also the coordinator. Chapter 0 states that "a
compromised coordinator can only obtain signatures for transactions that people approved", which is
true of the design, where these are separate parties; in the demo, whoever controlled the server
process could approve and authorise any payment, and the signers would sign it, because their check
is of the authority's signature. The policy engine and each approver's key now run in processes of
their own (`custody_lab.demo.parties`): the authority key is generated inside the policy engine's
process and never leaves it, and the server process receives only authorisations and approvals.
Step 2 of the settlement run lists which process holds which key, and a test checks that the
coordinator's process holds no authority key (`tests/demo/test_parties.py`). All of these processes
still run on one computer (vector 1.5).

## Vectors, layer by layer

### 1. The key and its shares

**1.1 Weak randomness at key generation.** *Attack:* predict the random numbers a signer used, and
compute its share. *Stopped by:* the Rust crate draws from the operating system's generator
(`OsRng` in `rust/custody-frost`); the teaching code uses Python's `secrets`. *Status:* not
demonstrated; it rests on the operating system.

**1.2 A rogue contribution to key generation.** *Attack:* a dishonest signer chooses its
contribution after seeing the others', to bias the key towards one it controls (chapter 2's
rogue-key attack). *Stopped by:* FROST's key generation requires each participant to prove it
knows its own secret, and to commit before seeing the others (chapter 2, Distributed key
generation). *Status:* refused by the crate; not demonstrated separately.

**1.3 Reading the sub-shares in transit.** *Attack:* a coordinator, or anyone on the path between
signers, records the key-generation sub-shares and computes every share. *Stopped by:* sealing
each sub-share to its recipient (Finding 1). *Status:* refused, tested
(`test_the_coordinator_relays_sub_shares_it_cannot_open`).

**1.4 Substituting the channel keys.** *Attack:* the process that starts the signers hands each
signer the coordinator's own channel key in place of its peers', then opens and re-seals every
sub-share in passing. *Stopped by:* in the design, channel keys are provisioned out of band, for
example as attested enclave keys or HSM certificates (chapter 3). *Status:* open in the demo,
where the keys pass through the coordinator at start-up.

**1.5 All shares on one machine.** *Attack:* an administrator of the computer reads the memory of
all three signer processes. *Stopped by:* in the design, separate machines under separate
administration, each share in an HSM or an enclave (chapter 3). *Status:* open in the demo; stated
in the README and in the walkthrough's "What the demo does not protect".

**1.6 Shares left in memory or on disk.** *Attack:* recover a share from a core dump, swap space or
a decommissioned disk. *Stopped by:* in the design, shares that never leave an HSM or an enclave.
The demo's Python processes do not erase their shares from memory. *Status:* open in the demo.

**1.7 Shares stolen one at a time over months.** *Attack:* take one share now and another later;
two shares are the key. *Stopped by:* a refresh between the thefts, after which the two do not
combine. *Status:* refused, demonstrated (Key ceremonies, steps 2 to 5; refusal
`InvalidSignatureShare`). Two shares stolen within one period still sign, which the same ceremony
shows: after such a theft the coins must move to a new key.

**1.8 Destroying shares to freeze the coins.** *Attack:* wipe or ransom two shares, so that no
quorum remains. *Stopped by:* repair while two shares remain (Key ceremonies, steps 7 to 9), and,
in the design, separately held encrypted backups (chapter 2, Backup, recovery and repair).
*Status:* contained: one lost share is repaired; losing two loses the key unless backups exist,
which the demo does not model.

### 2. The signers and the signing protocol

**2.1 One share signs alone.** *Attack:* an insider holding one share signs a payment. *Stopped
by:* the threshold: FROST refuses fewer than two commitments. *Status:* refused, demonstrated
(attack panel, "Sign with one signer"; Key ceremonies, step 2).

**2.2 A reused or predictable nonce.** *Attack:* collect two signatures made with the same nonce
and solve for the share (chapter 1's nonce-reuse lesson). *Stopped by:* fresh nonces from the operating system for every
session, burnt before the authorisation is checked so a refused request cannot reuse them
(`cluster.py`). *Status:* refused by construction; not demonstrated.

**2.3 Many concurrent sessions.** *Attack:* open many signing sessions at once and combine their
replies into a forgery (the ROS attack, chapter 2). *Stopped by:* FROST's binding nonce, which ties
each signer's reply to the full set of commitments. *Status:* refused by the protocol; not
demonstrated.

**2.4 A signer that sends a bad partial signature.** *Attack:* a signer corrupts its reply to
spoil the signature, or to probe the others. *Stopped by:* the coordinator checks each partial
signature against the signer's public share before aggregating, and names the culprit. *Status:*
refused, demonstrated (Key ceremonies, step 5 shows the check naming participant 1).

**2.5 A flaw in the threshold implementation.** *Attack:* exploit a missing check in the code
around the protocol, as BitForge and TSSHOCK did in threshold ECDSA libraries (chapter 10).
*Stopped by:* using a maintained implementation and checking it against an independent verifier:
every demo signature is verified with chapter 1's BIP340 code. FROST has no Paillier step, where
those attacks lived. *Status:* contained. The `frost-secp256k1-tr` crate is outside the scope of
the NCC Group audit of the other ZF FROST crates (README).

**2.6 Signers taken offline.** *Attack:* stop two signers, so that nothing can be paid. *Stopped
by:* nothing, by design: two of three are needed. *Status:* contained: a liveness failure, with no
coins lost (walkthrough, Taking a signer offline). ROAST (chapter 10) keeps a session completing
when some signers stall; the demo does not use it.

### 3. The coordinator

**3.1 Swapping the message after approval.** *Attack:* ask the signers to sign a different
transaction than the one approved. *Stopped by:* each signer checks that the authorisation names
exactly the message it is asked to sign. *Status:* refused, demonstrated (attack panel, "Swap in a
different transaction"; chapter 10's first cell).

**3.2 Replaying an authorisation.** *Attack:* present a used authorisation again. *Stopped by:*
each signer records the identifiers it has used. *Status:* refused, demonstrated (attack panel,
"Replay an authorisation"). See 4.5 for its limit.

**3.3 Refusing to coordinate.** *Attack:* a coordinator that will not relay stops every payment.
*Stopped by:* nothing in the demo; in the design, a second coordinator. *Status:* contained: a
liveness failure.

**3.4 A coordinator that also holds the policy.** *Attack:* control the server process and
authorise anything. *Stopped by:* the policy engine and each approver run in processes of their own,
holding their keys; the coordinator receives only authorisations and approvals (Finding 2).
*Status:* refused, tested (`tests/demo/test_parties.py`).

### 4. The policy engine and its authorisations

**4.1 A forged authorisation.** *Attack:* sign an authorisation with a key of one's own. *Stopped
by:* each signer checks it against the policy authority's two public keys. *Status:* refused,
demonstrated (attack panel, "Sign with an authorisation from an attacker's own authority key").

**4.2 Breaking one of the two signatures.** *Attack:* a future quantum computer computes the
authority's Ed25519 key from its public key. *Stopped by:* every authorisation is also signed with
ML-DSA-65, and the signers require both (chapter 7). *Status:* refused, demonstrated (attack panel,
"Forge an authorisation after breaking Ed25519").

**4.3 Stealing the authority key.** *Attack:* with the authority key, issue authorisations for any
transaction. *Stopped by:* in the design, the key in an HSM and authorisations reconciled against
the audit log (chapter 9's failure table). The signers cannot tell a stolen-key authorisation from
a genuine one. *Status:* open in the design as a single point, covered by the HSM; in the demo
the key is in the policy engine's own process, not in an HSM. Chapter 9's Exercise 4 discusses moving the full
policy check into each signer.

**4.4 An authorisation used late.** *Attack:* hold an approved transaction and send it later, the
pattern of the Drift loss (chapter 10). *Stopped by:* a 60-second lifetime, checked by each
signer. *Status:* refused, demonstrated (attack panel, "Use an authorisation issued five minutes
ago"). Its limit: each signer checks expiry against its own clock, so a signer whose clock has
been set back would accept an expired authorisation. *Open in the demo.*

**4.5 Replaying after a signer restarts.** *Attack:* the used-authorisation record is kept in each
signer's memory; restart a signer and present a used authorisation again within its 60 seconds.
*Stopped by:* the lifetime bounds the window. *Status:* open in the demo: the record is not
persisted.

**4.6 Paying an address that is not on the whitelist.** *Stopped by:* the whitelist, checked before
the approvals, so approvals cannot override it. *Status:* refused, demonstrated (attack panel; the
day's refusal of alpha-capital's unregistered address).

**4.7 Splitting a large payment.** *Attack:* stay under a tier boundary, or drain the account in
many approved payments. *Stopped by:* the velocity limit over a rolling 24 hours. *Status:*
contained, demonstrated (attack panel, "Drain the account"; the day's refusal at 1.50 BTC). The
limit bounds the loss per day; it does not prevent payments under it.

**4.8 Adding an attacker's address to the whitelist.** *Attack:* the whitelist decides where coins
may go, so change it. *Stopped by:* in the design, a registration that is itself an instruction
under approval, with a delay before the new address may be paid. *Status:* open: the demo's
whitelist is fixed in code, and no registration process is modelled.

**4.9 Losing the policy's memory.** *Attack:* the velocity window and the "authorised before"
check read the audit log in the engine's memory; restart the engine and both reset. *Status:* open
in the demo: the log is written to a file at the end of a run and not read back.

### 5. Approvers and what they approve

**5.1 Approving one's own instruction.** *Stopped by:* the four-eyes rule. *Status:* refused,
demonstrated (attack panel).

**5.2 An approval from a key not on the list.** *Stopped by:* the approver list. *Status:* refused,
demonstrated (attack panel).

**5.3 Changing an instruction after its approvals.** *Stopped by:* each approval signs the
instruction's exact contents. *Status:* refused, demonstrated (attack panel, "Raise the amount").

**5.4 One approver's key stolen.** *Stopped by:* the quorum needs a second approver. *Status:*
contained: a payment under the one-approval tier (0.1 BTC) needs only one key.

**5.5 Approving what one cannot see.** *Attack:* approvers sign an instruction built by a system
they trust; compromise that system, and they approve the attacker's payment. This is blind
signing, and it is how the Bybit and Bitget losses passed genuine approvals (chapter 10).
*Stopped by:* each approver's own device decoding the destination and checking it against its
own copy of the client's registered addresses. *Status:* refused, demonstrated (Red team, step 5:
devices that check refuse); open in the settlement run and the day, whose devices sign blind.

**5.6 Approvers colluding.** *Stopped by:* the whitelist and the velocity limit: two dishonest
approvers can only pay registered addresses, within the day's limit. *Status:* contained.

**5.7 A destination that belongs to another client.** *Attack:* the whitelist holds every
client's registered address in one set, so an instruction that sends gamma-treasury's withdrawal
to alpha-capital's registered address passes it. Found while building the red team. *Stopped by:*
binding each destination to its client: the checking approver devices refuse "the destination is
alpha-capital's registered address, not gamma-treasury's". *Status:* refused, demonstrated (Red
team, steps 4 and 5). Reconciliation does not catch it: the books and the chain both fall by the
same amount, so they still agree, and only the destination check sees that the coins went to the
wrong client.

### 6. The transaction

**6.1 Redirecting the change.** *Attack:* build a transaction whose change goes to an attacker.
*Stopped by:* `transfer.check_matches`: the instructed amount to the instructed address, everything
else back to the custody address. *Status:* refused, tested (`tests/settlement/test_transfer.py`).

**6.2 Paying the miner instead.** *Attack:* leave out the change, so the remainder becomes the fee.
*Stopped by:* the fee cap of 10,000 satoshis. *Status:* refused, demonstrated in chapter 5 (a
415,000,000-satoshi fee refused) and tested (`tests/settlement/test_transfer.py`).

**6.3 A signature that does not cover the outputs.** *Attack:* have the signers sign with a
signature mode that leaves outputs uncommitted, so the transaction can be changed after signing.
*Stopped by:* the demo signs with the default mode, which covers every input and output, and
refuses any signature that is not 64 bytes (`SettlementTx.finalize`). *Status:* refused by
construction.

**6.4 Replacing the custodian's own transaction.** The demo's transactions signal that they may be
replaced by a higher fee (`TxIn.sequence`), so the custodian can speed up a stuck payment. Only a
holder of the key can sign a replacement, so this is not a vector for an outsider. *Status:* not
a vector.

### 7. Deposits and the chain

**7.1 A deposit taken back before it confirms.** *Attack:* send a deposit, have it credited, then
replace it with a payment to oneself. *Stopped by:* crediting only confirmed deposits. *Status:*
refused, demonstrated (the day: delta-trading's deposit is replaced and credited nothing).

**7.2 A deposit taken back after it confirms.** *Attack:* on the public network, a block can be
replaced by a longer competing branch, a chain reorganisation, and a confirmed deposit with it.
*Stopped by:* waiting for more confirmations, more for larger amounts. *Status:* refused,
demonstrated (Red team, steps 2 and 3: credited at one confirmation, the deposit is reorganised away
and the books owe 0.50 BTC they do not hold; at three, nothing is credited). The day still credits
at one confirmation on a chain it controls.

**7.3 A look-alike address.** *Attack:* plant an address that starts and ends like a client's in
its history, so that someone copies it (address poisoning). *Stopped by:* withdrawals go only to
registered addresses. *Status:* refused by the whitelist; not demonstrated.

**7.4 A deposit attributed to the wrong client.** *Attack:* claim another client's deposit. The
demo attributes deposits to the single custody address by the transaction id the client reports.
*Stopped by:* in the design, a deposit address per client. *Status:* open in the demo.

### 8. Trading and settlement inputs

**8.1 A false fill.** *Attack:* inject or alter execution reports in the FIX session, so that the
custodian delivers coins it does not owe. The demo's session has no Logon credentials and no TLS.
*Stopped by:* in production, an authenticated and encrypted session, and reconciliation of fills
against the exchange's own statement before settlement. *Status:* open in the demo.

**8.2 The other leg never paid.** *Attack:* the custodian delivers bitcoin and the exchange does not
pay the dollars. *Stopped by:* delivery versus payment (chapter 8). *Status:* open: the demo settles
the bitcoin leg only.

### 9. The proof of reserves

**9.1 A changed figure in a signed snapshot.** *Stopped by:* the signature covers the exact
contents. *Status:* refused, demonstrated (attack panel; the browser's signature check with
"Lower the liabilities by 1 BTC"; the walkthrough's `var/altered.json`).

**9.2 A snapshot signed by a key that holds nothing.** *Stopped by:* the client reads the key out
of the custody address it deposited to and compares. *Status:* refused, demonstrated (the
signature card's "key inside it" check).

**9.3 A client counted for less.** *Stopped by:* the client recomputes its path from the balance it
expects. *Status:* refused, demonstrated (attack panel; the balance check's "+1 satoshi").

**9.4 A negative balance hidden in the tree.** *Attack:* add a negative leaf to lower the total.
*Stopped by:* the verifier rejects any negative sibling sum (`merkle_sum.verify`). *Status:* refused,
tested.

**9.5 A client left out.** *Attack:* omit a client from the tree. *Stopped by:* only that client,
when it asks for its proof and gets none. *Status:* open: a client that never checks is never
missed (chapter 0, What a proof of reserves does not show).

**9.6 Borrowed coins.** *Attack:* borrow coins for the moment of the snapshot and return them after.
*Status:* open: a snapshot shows one moment. Frequent, unannounced snapshots narrow the window.

**9.7 A liability created without coins.** *Attack:* a bug or a fraud credits a client with nothing
behind it, as at Liquid (chapter 10). *Stopped by:* reconciling the books with the chain after every
movement. *Status:* refused, demonstrated (the day's books panel; chapter 10's reserve-ratio cell).

### 10. The records

**10.1 Editing an audit entry.** *Stopped by:* the hash chain. *Status:* refused, demonstrated
(attack panel, "Edit an amount in the audit log").

**10.2 Cutting entries off the end.** *Stopped by:* the snapshot records the log's head. *Status:*
refused at the next snapshot; entries made after the last snapshot can be cut or rewritten
undetected until the next one. *Contained.*

**10.3 Editing a run's event file.** The dashboard's replay shows whatever `events.jsonl` says, and
the file is not signed. *Status:* open; it is a display record, not the system of record.

### 11. Software and suppliers

**11.1 A malicious or vulnerable dependency.** *Attack:* a library the demo installs is replaced or
has a flaw. *Stopped by:* pinned versions in
`uv.lock`, `Cargo.lock` and `web/package-lock.json`; libraries chosen for their audits, recorded in
the build plan; `npm audit --omit=dev` reports nothing in what ships. *Status:* contained. No build
is reproducible or attested.

### 12. The demo's own surfaces

**12.1 Anyone who can reach the server.** The dashboard's API has no authentication: whoever
reaches it can start runs and read their results. It listens on 127.0.0.1 only. *Status:* open in
the demo; a production interface authenticates every caller.

**12.2 Reading files through the replay.** *Attack:* ask the server to replay a path outside the
runs directory. *Stopped by:* a run is looked up only by the name of an existing directory under
`var/demo`. *Status:* refused, tested (`tests/demo/test_front_ends.py`).

### 13. Physical access and side channels

**13.1 Timing and power analysis.** *Attack:* measure how long signing takes, or the power it
draws, to learn the secret. The teaching implementations are variable-time and labelled so;
the demo signs with the Rust crate. *Status:* open in the demo, which makes no constant-time claim.

**13.2 Extracting keys from an enclave.** *Attack:* a memory-bus interposer such as TEE.fail
extracts keys from Intel TDX and AMD SEV-SNP with physical access (chapter 10). *Status:* not a
vector for the demo, which uses no enclave; a vector for designs that do (chapter 3).

### 14. Time

**14.1 A quantum computer.** *Attack:* compute the custody key from the public key, which a Taproot
key-path output puts on the chain. *Stopped by:* nothing in the demo's on-chain signature, which is
classical. The authorisations are hybrid. *Status:* open; BIP 360 proposes outputs without the key
path (chapter 10), and chapter 7 sets out the migration.

## Summary

This table summarises the statuses above.

| Status | Vectors |
|--------|---------|
| Refused, demonstrated | 1.7, 2.1, 2.4, 3.1, 3.2, 4.1, 4.2, 4.4, 4.6, 5.1, 5.2, 5.3, 5.5, 5.7, 6.2, 7.1, 7.2, 9.1, 9.2, 9.3, 9.7, 10.1 |
| Refused, tested or by construction | 1.2, 1.3, 2.2, 2.3, 3.4, 6.1, 6.3, 7.3, 9.4, 12.2 |
| Contained | 1.8, 2.5, 2.6, 3.3, 4.7, 5.4, 5.6, 10.2, 11.1 |
| Open in the demo | 1.4, 1.5, 1.6, 4.3, 4.4 (signer clock), 4.5, 4.9, 7.4, 8.1, 12.1, 13.1 |
| Open | 4.8, 8.2, 9.5, 9.6, 10.3, 14.1 |

## Future demos

Each open vector can be shown as an attack that succeeds, then a defence that stops it.

1. **Substitute a channel key** (1.4): a coordinator that swaps the keys at start-up reads the
   sub-shares; pinned, provisioned keys stop it.
2. **Read the shares from memory** (1.5, 1.6): an administrator of one machine reads all three
   signer processes, which is why chapter 3 separates them.
3. **Set a signer's clock back** (4.4): an expired authorisation accepted; a monotonic or attested
   time source refuses it.
4. **Restart a signer and replay** (4.5): a used authorisation accepted after a restart; a persisted
   record refuses it.
5. **Register an attacker's address** (4.8): an unprotected whitelist change, then registration as
   an approved instruction with a delay.
6. **Inject a fill** (8.1): a false execution report in an unauthenticated session changes the
   settlement; reconciliation against the exchange's statement catches it.
7. **Borrow for the snapshot** (9.6): a custodian borrows coins for one snapshot; an unannounced
   second snapshot shows the gap.
8. **Leave a client out** (9.5): the omitted client asks for its proof and finds none.
9. **Rewrite the log between snapshots** (10.2): entries after the last anchor rewritten unnoticed
   until the next snapshot.

## Recap

1. Count the independent parties that must fail before coins move; that count, at its smallest, is
   the design's strength.
2. Most vectors that move coins are refused by a check the demo demonstrates: the threshold, the
   signers' own check of the authorisation, its lifetime and single use, the whitelist, the
   transaction check, and the books reconciled with the chain.
3. Two findings came out of this analysis, both fixed: the key-generation sub-shares travelled in
   clear through the coordinator (now sealed to their recipient), and the coordinator, the policy
   engine and the approvers ran in one process (now each in its own).
4. What remains open is mostly what the demo leaves out on purpose (separate machines, a public
   chain, authenticated sessions) and what no proof of reserves can show (omitted clients,
   borrowed coins). Each has a future demo.
