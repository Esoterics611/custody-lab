# Operating the demo: a walkthrough

## What this walkthrough is for

This walkthrough takes one complete run of the demo through the browser dashboard, as its
operator sees it: what to start, what to press, what appears at each of the nine steps, what
each value on the screen means, and how to check the results independently once the run is over.
It explains each idea from first principles at the level needed to run and present the demo,
without the mathematics. [Chapter 0](chapters/00-orientation.md) follows the same run with the
arithmetic written out, and the later chapters give the full mechanism.

The reader is assumed to know trading infrastructure: FIX sessions, signed exchange API requests,
maker-checker approval, clearing and netting. Where one of those has a counterpart in the demo,
the walkthrough names it and says where the comparison stops holding.

Terms printed in **bold** are defined where they appear and in [the glossary](../atlas/glossary.md).

One run takes about seven seconds. The checks in the last sections use only the files a run
leaves behind, so they can be done at any time afterwards.

## Why a custodian needs any of this

Bitcoin has no account operator. Coins are locked to an **address**, the address is derived from
a **public key**, and spending the coins requires a **digital signature** made with the matching
**private key**. The network checks the signature and nothing else: it does not know who made
it, and once a payment has been accepted into the chain, the shared record of every payment,
nobody can recall it. There is no chargeback, no cancelled trade and no corrected ledger entry.
Whoever can produce the signature controls the coins.

The nearest counterpart is an exchange API key. A firm trading through a signed REST API holds
one private key, and whoever has a copy of that key file can send requests as the firm. The
comparison stops at recovery: an exchange can cancel a fraudulent order or freeze an account,
and on Bitcoin a confirmed payment stays where it went.

A custodian holding bitcoin for clients therefore has to control two things: who is able to
produce a signature, and which payments a signature may be used for. The demo shows one complete
answer in three parts:

- **The key is never in one place.** It is created as three shares in three separate processes,
  and any two of them sign together without the key ever being rebuilt.
- **People decide, machines sign.** A policy engine refuses every payment it has not been
  configured to allow, requires approvals that people sign with their own keys, and issues a
  signed permission naming one exact transaction. Each signing process checks that permission
  itself.
- **The custodian proves what it holds.** After the payment it publishes what it owes its
  clients, the coins it holds, and a signature showing that it controls those coins.

Several steps rely on one more idea. A **hash function** turns any amount of data into a short
fixed-length value, often called a fingerprint. The same data always gives the same fingerprint,
changing a single byte gives a completely different one, and the data cannot be worked out from
the fingerprint. Transaction identifiers, the value the signers sign and the links in the audit
log are all fingerprints in this demo.

## What the demo does not protect

The demo shows the protocol, not the protection around it. All three signing processes run on
one computer, and an administrator of that computer can read all three shares. In production each
share would sit on a separate machine under separate administration, inside a hardware security
module or a secure enclave; [chapter 3](chapters/03-key-storage.md) explains where each key would
live. The coins are on a private test network and have no value, and the exchange is a toy that
fills every order in full at its limit price. The dashboard carries the banner
EDUCATIONAL, NOT PRODUCTION for these reasons.

## Before the first run

The demo needs four tools. uv creates the Python environment, Rust compiles the project's two
extensions when uv installs them, Bitcoin Core runs the private chain, and Node.js builds the
dashboard. Installation is described in [the README's prerequisites](../README.md#prerequisites).
The commands below check that each is present:

| Tool | Command | Expect (the versions this walkthrough was checked with) |
|------|---------|----------------------------------------------------------|
| uv | `uv --version` | `uv 0.12.3` |
| Rust | `cargo --version` | a version line; any stable release |
| Bitcoin Core | `bitcoind -version` | `Bitcoin Core daemon version v31.1.0` |
| Node.js | `node --version` | `v24.19.0` |

Build the environment and the dashboard once, from the repository root (terminal 1):

```bash
uv sync
npm --prefix web ci
npm --prefix web run build
```

**Expect:** `uv sync` finishes without an error. The last command ends with a line starting
`✓ built in`. The server serves the dashboard as it was last built, so the build is repeated after
any change under `web/src`.

## Starting the dashboard

The walkthrough uses two terminals, both in the repository root. Terminal 1 runs the server;
terminal 2 is for checks.

**Terminal 1:**

```bash
uv run custody-lab serve
```

**Expect:**

```
INFO:     Started server process [759810]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

The number in `Started server process` will differ; note it. This server process is also the
**coordinator**: the program that passes messages between the signing processes and adds up
their results. It holds no share of the key. Step 2 compares its number with theirs.

The server must be started from the repository root, because it finds the built dashboard
(`web/dist`) and writes each run's files (`var/demo/`) relative to the directory it starts in.

**Terminal 2:**

```bash
curl -s http://127.0.0.1:8000/api/steps
```

**Expect:** one line of JSON listing the nine steps, beginning
`{"chain":"Start a private Bitcoin Core regtest chain",`.

Open <http://127.0.0.1:8000> in a browser. With the repository under WSL2, use the Windows
browser at the same address; if the page does not load there while the `curl` check works, see
[Troubleshooting](#troubleshooting).

**The page before a run.** The header holds the title, a one-line summary, the red banner and a
blue **Run the demo** button. On the left are the nine numbered steps, each marked PENDING. On the
right, the **Key shares** panel reads "Key generation has not run." followed by the sentence about
the coordinator.

## The cast

The run has a fixed cast, the same as in [chapter 0](chapters/00-orientation.md#the-cast):

- four clients hold bitcoin with the custodian: alpha-capital 2.00 BTC, beta-fund 1.50,
  gamma-treasury 1.00 and delta-trading 0.50, a total of 5.00 BTC;
- alpha-capital trades on the toy exchange;
- ops-desk, an operations user, raises the payment instruction;
- bob and carol approve it;
- signers 1, 2 and 3 each hold one share of the custody key, each in its own process; any two
  can sign, and signers 1 and 3 do;
- the coordinator is the server process from terminal 1.

## Running the demo

Press **Run the demo**. The button greys out and reads "Running" until the run ends. Each step
turns from PENDING to RUNNING, with an amber bar on its left, and then to DONE, with a green bar,
and its results appear under its title. Terminal 1 logs `"POST /api/runs HTTP/1.1" 200 OK` as the
run starts.

Each press starts a new run with its own private chain, its own three signing processes and its
own directory under `var/demo/`, named by the time it started in UTC, for example
`var/demo/20261008T210826Z-gai2i96y/`. Closing the browser during a run does not stop it: the run
finishes and its files stay in that directory.

### Step 1: Start a private Bitcoin Core regtest chain

**The problem.** Settling a payment needs a Bitcoin network. The public network moves real coins,
and it adds new payments to the chain about every ten minutes, at times nobody chooses. A demo
needs a network where coins cost nothing and time moves on command.

**What happens.** The demo starts Bitcoin Core, the standard Bitcoin software, in **regtest** mode:
a private Bitcoin network that exists only inside this run. It checks transactions and signatures by
the same rules as the public network, but it produces a **block**, the batch of transactions added
to the chain at one time, whenever asked, and its coins have no value. The node keeps its data
inside the run's directory and the data is deleted when the run ends, so every run starts from an
empty chain, and the chain cannot be queried after the run.

The demo creates a wallet for the exchange and mines 101 blocks into it. Every block pays a
reward to whoever produced it, and Bitcoin's rule is that a reward cannot be spent until 100 more
blocks have been built on top of it. After 101 blocks the first reward can be spent, so the
exchange has coins to fund the demo with. The step also creates the exchange's settlement
address: the address where the exchange receives coins, and the only destination the policy in
step 6 allows.

The counterpart is a test venue that only one firm connects to and whose clock that firm
controls. The comparison stops at time: on the public network nobody controls when a block
arrives, which matters for step 8.

**On the screen.** `height 101` is the number of blocks on the chain. `exchange address` starts
`bcrt1q`. The `bcrt1` prefix marks a regtest address; an address on the public network starts
`bc1`. The letter after the `1` is the address's version: `q` is version 0, the format a wallet
uses for a single ordinary key. The custody address in step 2 starts `bcrt1p`: version 1,
**Taproot**.

**If it fails.** Without Bitcoin Core on the server's `PATH`, step 1 turns red and shows
`error RuntimeError: bitcoind not found on PATH (see CLAUDE.md, Toolchain)`, and terminal 1 prints
`demo run in var/demo/... failed` followed by the traceback.

### Step 2: Distributed key generation: 2-of-3, one process per share

**The problem.** Whoever holds the private key controls the coins. A key kept whole in one file
can be taken by one administrator, one stolen backup or one piece of malware, and coins sent away
with it cannot be recalled. Keeping copies for safety only adds places to steal it from.

**What happens.** The demo starts three signing processes, each a fresh program that inherits
nothing from the server's memory. Together they run **distributed key generation (DKG)**: each
process picks random numbers of its own, they exchange values derived from those numbers through
the coordinator, and each process ends up holding one **share** of a key. The key those shares
belong to is never calculated anywhere: not while it is generated, not afterwards, and not when
signing in step 7. Any two of the three shares are enough to sign and one is not, which makes it
a 2-of-3 key: a **threshold** of two out of three. The processes publish the key's public half,
the group key, which anyone may see.

The counterpart is dual control: two officers who each know half of a vault combination. The
comparison stops at use. To open the vault, the two halves are put together. Here the shares are
never put together; step 7 shows how two of them still produce a signature.

The custody address, where the clients' coins will be held, is derived from the group key by
Bitcoin's Taproot rules. Those rules first adjust the group key by a fixed formula, a **tweak**,
into an output key; the tweak commits the address to having no other way of being spent. The
demo derives the address in three independent ways: in the Rust FROST library, in this project's
own Python code written from the Bitcoin specification, and in Bitcoin Core. It stops if they
disagree. A wrong address is worse than a failed run, because coins sent to it would be locked to
a key nobody holds, permanently.

**On the screen.**

- `signers`: a table of share number and process id (`pid`), three different numbers.
- `threshold 2 of 3`.
- `group key`: the public key the shares belong to, 64 hexadecimal characters (32 bytes).
- `output key`: the group key after the tweak.
- `address`: the custody address, starting `bcrt1p`.
- `implementations agree yes`: the three derivations matched.

The **Key shares** panel now lists Signer 1, Signer 2 and Signer 3, each with its process number
and "holds share N of 3", and ends with "Threshold 2 of 3."

**Check it.** Compare the three process numbers with the number terminal 1 printed at start-up.
They are different: the shares live in three other processes, and the server, which is the
coordinator, holds none. The signing processes exit when the run ends; their numbers stay in the
run's `events.jsonl`.

### Step 3: Fund the custody address

**The problem.** The custodian's books say it owes its four clients 5.00 BTC. The books by
themselves prove nothing: the coins have to be at the address the key controls.

**What happens.** The exchange's wallet sends 5.00 BTC, the total of the four client balances, to
the custody address, and one block is mined to confirm it. In a real deployment each client
deposits its own coins; the demo funds the address in one payment to keep the run short.

From here on there are two records, and they must agree. The **ledger** is the custodian's own
books: how much it owes each client. The chain records only that the custody address holds
5.00 BTC and knows nothing about whose coins they are. The counterpart is an omnibus account at
a bank or depository, with the firm's own sub-ledger saying which client owns what. The
comparison stops at correction: there is no bank or depository behind the chain that can reverse
a wrong payment out of the account.

Bitcoin does not keep a balance per address. It keeps individual coins, each of a fixed amount,
called **UTXOs** (unspent transaction outputs), and a UTXO is always spent whole, the way a
banknote is handed over whole and change comes back. After this step the custody address holds
exactly one coin, of 5.00 BTC. Step 6 depends on this.

**On the screen.** `txid` is the funding transaction's identifier, a fingerprint of its contents.
`amount 5.00 BTC`. `ledger` lists alpha-capital 2.00, beta-fund 1.50, gamma-treasury 1.00 and
delta-trading 0.50 BTC, which add up to the amount.

### Step 4: FIX 5.0 SP2 trading session with the exchange

**The problem.** A custodian pays out because something created an obligation; here it is
trading. Under **off-exchange settlement**, the client's coins stay with its custodian while it
trades, the exchange lets it trade against them, and at the end of each settlement cycle only the
net obligation moves. [Chapter 5](chapters/05-settlement.md#settling-against-an-exchange)
explains why institutions prefer this to moving coins onto the exchange first. The trades in this
step therefore become a payment the custodian has to make, in steps 5 to 8.

**What happens.** alpha-capital connects to the toy exchange over FIX 5.0 SP2 on the FIXT.1.1
session layer: `8=FIXT.1.1`, with `1137=9` on the Logon. After the Logon exchange it sends four
NewOrderSingle messages, and the exchange answers each with an ExecutionReport for a full fill at
the limit price. Both sides then log out. The session is minimal: no heartbeats, resend requests
or gap fills, and the exchange fills every order. A production session would also carry partial
fills, rejects and cancels.

**On the screen.** `client alpha-capital`. `fills` has one row per ExecutionReport: exec id E0001 to
E0004, ClOrdID C1 to C4, symbol BTC-USD, side, quantity and price. Quantities and prices appear
without trailing zeros: 0.4 is the order's 0.40. `fix messages 12`. Pressing **12 FIX messages**
under `transcript` opens the raw messages, both directions in the order they were sent, with the SOH
delimiter shown as `|`; the box scrolls sideways.

**Check it.** In the transcript, the first two messages are `35=A` (Logon) and carry `1137=9`;
then come four `35=D` (NewOrderSingle), each followed by its `35=8` (ExecutionReport); the last
two are `35=5` (Logout). That is 2 + 4 + 4 + 2 = 12.

### Step 5: Net the settlement cycle into one instruction

**The problem.** Settling each fill separately would put four payments on chain: four fees,
four rounds of approval, four signatures, and four chances for one of them to go wrong.

**What happens.** The four fills are combined into one obligation, the way a clearing house nets
a day's trades into one delivery per participant. This is **netting**, and the counterpart holds
exactly, except on the cash side described below.

On the bitcoin side, alpha-capital sold 0.40 + 0.35 + 0.25 = 1.00 BTC and bought 0.15 BTC, so it
delivers 1.00 − 0.15 = 0.85 BTC.

On the dollar side, the sales bring in 0.40 × 64,000 = 25,600.00, 0.35 × 64,010 = 22,403.50 and
0.25 × 64,020 = 16,005.00, a total of 64,008.50 USD. The purchase costs
0.15 × 63,950.50 = 9,592.575 USD. Net, alpha-capital receives 64,008.50 − 9,592.575 =
54,415.925 USD.

The result is a settlement instruction named `settle-cycle-1`: deliver 0.85 BTC to the exchange's
settlement address, raised by ops-desk. The name appears in the policy audit log rather than on
the screen.

The demo settles the bitcoin side only; the 54,415.925 USD is never paid. In a real settlement
the two sides must move together, or one party carries the risk that the other never pays. That
is **DvP** (delivery versus payment), explained in
[chapter 8](chapters/08-industry.md#delivery-versus-payment).

**On the screen.** `fills 4`, `client delivers 0.85 BTC`, `client receives 54,415.925 USD`, and
`instruction`: asset BTC, amount 0.85, to the exchange address.

**Check it.** The instruction's `to` is the exchange address from step 1, character for
character.

### Step 6: Build the transaction and apply the policy

**The problem.** The signing processes will sign whatever they are given, so something has to
decide whether a payment should happen at all, and that decision has to be tied to one exact
transaction. An approval of "0.85 BTC to the exchange" that could be attached to a different
transaction would let an insider, or anyone who had taken over the server, send 4.15 BTC
somewhere else under the same approval.

**What happens, part 1: the transaction.** The settlement code builds the payment before anyone
approves it, because the approval will name the exact transaction. The transaction spends the
custody address's one coin of 5.00 BTC and creates two new coins: 0.85 BTC to the exchange, and
the **change**, the remainder, back to the custody address. Amounts on chain are whole numbers of
**satoshis**, and 1 BTC is 100,000,000 satoshis. The difference between what a transaction spends
and what it creates is the **fee**, which goes to whoever mines the block. It is set by the
transaction's size: 155 virtual bytes at 2 satoshis per virtual byte, 310 satoshis. The change
is therefore 5.00 − 0.85 − 0.0000031 = 4.1499969 BTC. The fee is charged to alpha-capital in
step 9, so that the custody address keeps holding client coins only.

The code then checks the transaction against the instruction: it pays exactly 0.85 BTC to exactly
the instructed address, everything else goes back to the custody address, and the fee is no more
than a cap of 10,000 satoshis. The fee cap matters because a transaction does not state its fee
anywhere: the fee is whatever is left over. A transaction that paid 0.85 BTC to the exchange and
left out the change coin would hand the other 4.15 BTC to the miner as a fee of 415,000,000
satoshis. [Chapter 5](chapters/05-settlement.md#what-the-signature-covers-the-sighash) builds
that transaction and shows the check refusing it.

Finally the code computes the transaction's **sighash**: the fingerprint the signature will be made
over. It covers the coin the transaction spends, with its amount, and the coins it creates. The
counterpart is a signed exchange API request, where the client signs a digest of the method, path,
body and timestamp, and the exchange rejects the request if any byte differs. The same holds here: a
signature over this sighash is valid for this transaction and no other.

**What happens, part 2: the policy.** The **policy engine** decides whether the instruction is
allowed. It is **default-deny**: anything its configuration does not explicitly allow is refused.
It runs its checks in a fixed order, and the first failure decides:

1. asset: BTC has a policy;
2. amount: a positive number;
3. tier: the amount decides how many approvals are needed (up to 0.1 BTC one, up to 10 BTC two,
   above 10 BTC refused outright), so 0.85 BTC needs two;
4. whitelist: the destination is on the **whitelist**, which holds only the exchange's address;
5. velocity: the **velocity limit** of 20 BTC authorised in any 24 hours still holds;
6. not authorised before: the same instruction cannot be authorised twice;
7. approvals: enough valid approvals from different people, none of them from the person who
   raised the instruction.

An approval here is not a click on a button. bob and carol each hold a private key of their own,
and approving means signing the instruction's exact contents with it; the engine checks each
signature against that approver's public key. ops-desk raised the instruction and cannot approve
it, which is the **four-eyes** rule. The counterpart is maker-checker, and it holds; the
difference is that an approval is bound to the instruction's exact contents, so changing the
amount or the address afterwards invalidates it.

With bob's approval alone the engine answers PENDING, "1 of 2 required approvals": not refused,
waiting for more. With bob's and carol's it answers APPROVED and issues an **authorisation**: a
permission naming the sighash, signed by the policy engine's own key, valid for 60 seconds, and
usable once. It is signed twice, with Ed25519 and with ML-DSA-65, a signature scheme designed to
withstand a future quantum computer ([chapter 7](chapters/07-post-quantum.md)), and a signer
requires both. Every decision is written to the policy audit log, a **hash chain** in which each
entry carries the fingerprint of the entry before it. An edited entry, or one removed from the
middle, breaks the chain; entries cut off the end leave no break, which step 9 deals with.

**On the screen.**

- `matches instruction yes`: the transaction passed the check against the instruction.
- `fee 310 sats` and `fee cap 10,000 sats`.
- `sighash`: 64 hexadecimal characters.
- `initiator ops-desk`.
- `policy checks`: the seven checks above, in order.
- `with one approval pending: 1 of 2 required approvals`.
- `approved by bob, carol`.
- `authorisation id`: the identifier the signers record so the authorisation cannot be used
  again.

### Step 7: Threshold signature from 2 of 3 signer processes

**The problem.** The authorisation is only worth something if the machines holding the shares
enforce it. The coordinator relays every message between the signers, so if the coordinator
alone checked permissions, whoever took over the coordinator could have anything signed.

**What happens.** The coordinator sends the sighash and the authorisation to signers 1 and 3. Each
checks the authorisation itself: both of its signatures are the policy engine's, it has not
expired, it names exactly the sighash being signed, and it has not been used before. Only then
does the signer take part.

Signing uses **FROST**, a threshold signing protocol, in two rounds. In the first, each signer
commits to a random number it will use once, its **nonce**. In the second, each sends a
**partial signature** computed from its own share. The coordinator adds the partial signatures
into one signature, and the demo checks it against the custody key with a verifier written
separately in this project. Signer 2 takes no part, and no process holds or calculates the whole
key at any point.

The counterpart is a safe-deposit box with two locks and two keyholders, each turning their own
key. The comparison stops at the result: the chain receives one ordinary 64-byte signature,
indistinguishable from one made with a single key, and cannot tell that two parties made it.

Two of three is a deliberate choice. One signer can be offline, broken or lost and the coins can
still move; one signer that is compromised cannot move them alone.

**On the screen.** `signers 1, 3`; `signature`, 128 hexadecimal characters (64 bytes);
`verified yes`. In the **Key shares** panel, Signer 1 and Signer 3 are marked "signed" and
Signer 2 "not asked".

### Step 8: Broadcast and confirm on chain

**The problem.** A signed transaction moves nothing until the network accepts it into a block.

**What happens.** The demo sends the transaction to Bitcoin Core, which checks it against every
rule, including the signature, and accepts it. One block is mined on top, which gives the
transaction one **confirmation**. The exchange now holds 0.85 BTC, and the custody address holds
one coin of 4.1499969 BTC.

The network never declares a payment final. Each further block makes the payment harder to
reverse, and each institution chooses how many confirmations it treats as final for a given
amount. On regtest the block arrives on command; on the public network a block arrives about
every ten minutes. The counterpart is **settlement finality** at a depository, which is a defined
legal moment; on Bitcoin it is a matter of how many blocks have been built on top
([chapter 8](chapters/08-industry.md#settlement-finality)).

**On the screen.** `txid`: the settlement transaction's identifier. It is not the sighash from
step 6: the txid names the transaction for everyone, and the sighash is the fingerprint the
signers signed. `block`: the fingerprint of the block that contains it. `confirmations 1`.
`fee 310 sats`.

### Step 9: Proof-of-reserves snapshot with proof of control

**The problem.** Clients cannot see the custodian's books or its keys. A custodian could owe more
than it holds, or point at coins it does not control, and the clients would find out only when
their withdrawals failed.

**What happens.** The ledger is updated: alpha-capital's 2.00 BTC falls by the 0.85 BTC
delivered and the 310-satoshi fee, to 1.1499969 BTC. The four balances now total 4.1499969 BTC.
That total is the custodian's **liabilities**: what it owes.

The liabilities are published as a **Merkle sum tree**. Each client's balance is a leaf. Leaves are
paired, and each pair gets a parent carrying a fingerprint that covers both children, their sums
included, and the sum of both; parents are paired the same way, up to a single top node, the
**Merkle root**, which carries the total. The root is published. Each client receives an **inclusion
proof**: the few values needed to recompute the root from its own leaf, which shows that its own
balance was counted in the published total. Changing any client's balance, or leaving a client out,
changes the root.

The assets are read from the chain: the coins at the custody address, one coin of 4.1499969 BTC.
The **reserve ratio**, assets divided by liabilities, is exactly 1.

The custodian also has to show that it can move those coins, not just point at an address. This
is **proof of control**: signers 1 and 3 sign the snapshot with the custody key, under a separate
kind of authorisation that permits signing a snapshot and nothing else, so it cannot be turned
into a payment. The snapshot also records the audit log's latest fingerprint, its **head**. A log
with entries cut off the end, or rewritten from the start, would no longer lead to the published
head.

The counterpart is a client-money reconciliation signed off by an auditor. The comparison stops at
who can check it: each client can check its own inclusion, and anyone can check the signature,
without relying on the auditor. A proof of reserves also has limits: it does not show debts the
custodian owes elsewhere, it cannot show that a client who never checks its proof was included, and
it cannot show that the coins were not borrowed for the moment of the snapshot ([chapter
0](chapters/00-orientation.md#what-a-proof-of-reserves-does-not-show)).

**On the screen.** `liabilities 4.1499969 BTC`, `assets 4.1499969 BTC`, `reserve ratio 1.00000`,
`root`, `inclusion proofs verify yes`, `proof of control yes`, `audit head`, and `snapshot`, the
file's path: `var/demo/<run>/reserves/snapshot-103.json`. The 103 is the block height at the
snapshot: the 101 blocks of step 1, the funding block of step 3 and the settlement block of
step 8. The **Key shares** panel keeps showing signers 1 and 3 as "signed" from step 7; it does
not mark this second signature separately.

The button returns to **Run the demo** when the run is over.

## After the run: checking the files

Each run leaves three files in its directory, and they can be checked without the dashboard or
the server. Run the commands below in terminal 2, from the repository root.

**Find the run.** Directory names start with the UTC start time, so the last one listed is the
newest:

```bash
RUN=$(ls -d var/demo/*/ | tail -1); echo "$RUN"; ls -R "$RUN"
```

**Expect:** the run's directory, holding `audit.jsonl`, `events.jsonl` and
`reserves/snapshot-103.json`.

**The event log.** `events.jsonl` holds every event the dashboard displayed, one JSON object per
line: a running and a done event for each step.

```bash
wc -l < "$RUN/events.jsonl"
```

**Expect:** `18`.

**The audit log.** `audit.jsonl` is the policy engine's hash chain. The command below prints each
entry and checks that it names the fingerprint of the entry before it (the first names 64 zeros),
then finds which entry the snapshot's audit head points to:

```bash
uv run python - "$RUN" <<'EOF'
import json, sys
from pathlib import Path

run = Path(sys.argv[1])
entries = [json.loads(line) for line in (run / "audit.jsonl").read_text().splitlines()]
previous = "0" * 64
for e in entries:
    print(e["seq"], e["event"], e["payload"].get("reason", ""), "| linked:", e["prev_hash"] == previous)
    previous = e["hash"]
head = json.loads(next((run / "reserves").glob("snapshot-*.json")).read_text())["audit_head"]
print("snapshot audit head is entry", [e["hash"] for e in entries].index(head))
EOF
```

**Expect:**

```
0 evaluated 1 of 2 required approvals | linked: True
1 evaluated 2 of 2 required approvals | linked: True
2 authorised  | linked: True
3 attestation_authorised  | linked: True
snapshot audit head is entry 2
```

Entry 0 is the PENDING decision with bob's approval alone, entry 1 the APPROVED decision, entry 2
the authorisation for the settlement, and entry 3 the authorisation to sign the snapshot. The
snapshot points to entry 2 because its contents were fixed before the snapshot's own
authorisation was issued. This check follows the links only;
[chapter 4](chapters/04-policy.md#a-log-that-shows-its-own-edits) also recomputes each
fingerprint and shows an edited entry being caught.

**The snapshot.** The command below checks the snapshot file the way an outside reader would. It
recomputes, from the file's contents, the message the signers signed, and checks the signature
against the custody key named in the file. The signature check uses this project's BIP340
verifier, which is tested against Bitcoin's published test vectors.

```bash
cat > var/check_snapshot.py <<'EOF'
import hashlib, json, sys
from custody_lab.foundations import schnorr

document = json.load(open(sys.argv[1]))
attestation = document.pop("attestation")
document.pop("reserve_ratio")
statement = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
tag = hashlib.sha256(attestation["tag"].encode()).digest()
message = hashlib.sha256(tag + tag + statement).digest()
print("message matches the file:", message.hex() == attestation["message"])
key = bytes.fromhex(document["custody_output_key"])
signature = bytes.fromhex(attestation["bip340_signature"])
print("signature verifies:", schnorr.verify(message, key, signature))
EOF
uv run python var/check_snapshot.py "$RUN"reserves/snapshot-103.json
```

**Expect:**

```
message matches the file: True
signature verifies: True
```

**What a change does.** Make a copy of the snapshot with the liabilities lowered by 1 BTC, as a
custodian hiding a debt might, and check the copy:

```bash
sed 's/"liabilities": "4.1499969"/"liabilities": "3.1499969"/' "$RUN"reserves/snapshot-103.json > var/altered.json
uv run python var/check_snapshot.py var/altered.json
```

**Expect:**

```
message matches the file: False
signature verifies: False
```

The signature covers the snapshot's exact contents. Changing one digit gives a different message,
and the signers' signature does not verify for it. Producing a valid signature for the altered
snapshot would take two of the three shares and a fresh authorisation from the policy engine.

## Running it again

Each press of **Run the demo** starts from nothing: a new chain, a new key, a new custody address
and three new signing processes. Some values therefore change on every run and others never do.

- **The same on every run:** height 101; 5.00 BTC funded; 4 fills and 12 FIX messages;
  0.85 BTC delivered and 54,415.925 USD received; the fee of 310 satoshis; "1 of 2 required
  approvals" with one approval; signers 1 and 3; one confirmation; liabilities and assets of
  4.1499969 BTC; a reserve ratio of 1.00000; `snapshot-103.json`. A different value here means
  the code has changed.
- **Different on every run:** process numbers, keys, addresses, transaction ids, the sighash, the
  signature, the authorisation id, the Merkle root, the audit head and the run directory.

The same run can be watched in the terminal instead of the browser with `uv run custody-lab run`,
which prints each step and its details and writes the same files. To stop the server, press
Ctrl+C in terminal 1.

## Troubleshooting

| Symptom | Check | Fix |
|---------|-------|-----|
| The browser shows `{"detail":"Not Found"}` at <http://127.0.0.1:8000> | Was the server started from the repository root, after `npm --prefix web run build`? | Stop it with Ctrl+C, change to the repository root, build, start it again |
| Terminal 1 prints `ERROR: [Errno 98] error while attempting to bind on address ('127.0.0.1', 8000): address already in use` | `ss -ltnp \| grep :8000` shows what holds the port | Stop the other server, or start this one with `uv run custody-lab serve --port 8001` and open that port |
| Step 1 turns red: `RuntimeError: bitcoind not found on PATH` | `which bitcoind` in terminal 1 | Install Bitcoin Core 31.1 (see the README), then restart the server from a shell where `which bitcoind` finds it |
| A red line under the header: "The demo server is not reachable" | The page cannot reach the server's API: was it opened from `npm --prefix web run dev` with no `custody-lab serve` running? | Start the server in terminal 1 |
| `curl` in terminal 2 works, but the Windows browser does not load the page | WSL's forwarding of `localhost` to Windows | Check the WSL networking settings, or open the page in a browser inside WSL |
| Any other step turns red | The `error` line under the step, the traceback in terminal 1, and the run's `events.jsonl` | The error names the failed check; the chapter for that step explains it |

## The nine steps at a glance

This table summarises what each step has already explained, as a list of what to look for.

| Step | Expect on the screen | Chapter |
|------|----------------------|---------|
| 1. Chain | height 101; exchange address `bcrt1q…` | [5](chapters/05-settlement.md) |
| 2. Keys | three process numbers, none of them the server's; threshold 2 of 3; implementations agree yes; custody address `bcrt1p…` | [2](chapters/02-mpc-custody.md) |
| 3. Fund | amount 5.00 BTC; ledger of 2.00, 1.50, 1.00 and 0.50 BTC | [5](chapters/05-settlement.md) |
| 4. Trade | four fills; 12 FIX messages, Logon carrying `1137=9` | [5](chapters/05-settlement.md) |
| 5. Net | client delivers 0.85 BTC, receives 54,415.925 USD; instruction to the step 1 address | [5](chapters/05-settlement.md) |
| 6. Policy | matches instruction yes; fee 310 sats under a 10,000 cap; one approval PENDING; bob and carol approve | [4](chapters/04-policy.md) |
| 7. Sign | signers 1 and 3 signed, signer 2 not asked; verified yes | [2](chapters/02-mpc-custody.md) |
| 8. Broadcast | confirmations 1; fee 310 sats | [5](chapters/05-settlement.md) |
| 9. Reserves | liabilities and assets 4.1499969 BTC; reserve ratio 1.00000; proofs and proof of control yes | [6](chapters/06-reserves.md) |

## Recap

1. On Bitcoin, whoever can produce the signature controls the coins, and a confirmed payment
   cannot be recalled. Custody is the control of who can sign, and what.
2. The custody key exists only as three shares in three processes. Any two sign together without
   rebuilding it, and the coordinator holds none (steps 2 and 7).
3. The payment starts as trades and is netted into one instruction (steps 4 and 5).
4. The transaction is built first, checked against the instruction and fingerprinted. People
   approve by signing, the policy engine issues an authorisation naming that fingerprint, and
   each signer checks the authorisation itself (steps 6 and 7).
5. The chain receives one ordinary signature and confirms the payment (step 8).
6. The snapshot publishes liabilities, assets and a signature proving control, and fixes the
   audit history; its file can be checked by anyone, and a changed figure fails the check
   (step 9 and the checks after the run).

[Chapter 0](chapters/00-orientation.md) follows the same run with the arithmetic of each step,
and the [contents page](README.md) lists the chapters that explain each mechanism in full.
