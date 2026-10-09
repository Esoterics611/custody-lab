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

The dashboard has four more tabs, explained after the run. [A day at the
custodian](#a-day-at-the-custodian) runs a busier day: deposits, a double spend, two clients
trading, netting across them, withdrawals and three refusals, with the books compared to the chain
after every step. [Key ceremonies](#key-ceremonies) shows a share stolen before a refresh failing to
combine with one stolen after it, and a lost share rebuilt. [Attacking the
design](#attacking-the-design) tries sixteen attacks against the demo's own code and shows which
component refuses each. [Checking a client's balance](#checking-a-clients-balance) lets each client
recompute its own place in the published snapshot. [Taking a signer
offline](#taking-a-signer-offline) runs the demo with signers missing, and [Replaying a recorded
run](#replaying-a-recorded-run) shows a past run again without a Bitcoin node.

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

**The page before a run.** The header holds the title, a one-line summary and the red banner.
Under it, a row of six boxes traces a settlement's path through the design: Exchange, Netting,
Policy, Signers, Bitcoin and Reserves. During a run each box turns amber while one of its steps is
running and green once all of them are done. Below the row are three tabs, and the page opens on
**Settlement run**. That tab has a blue **Run the demo** button beside a progress bar reading
"0 of 9 steps", and under them the nine numbered steps, each marked PENDING. On the right, the
**Key shares** panel shows Signer 1, Signer 2 and Signer 3, each "not started" and each with a
switch set to "online", followed by two notes: any 2 of 3 sign, and the coordinator holds no
share. Leave the switches on for the first run; [Taking a signer
offline](#taking-a-signer-offline) explains them. Once a run has been recorded, a list under the
button offers past runs for replay.

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

Each finished step shows on the right how long it took, as measured by the server. Step 1 takes
about five seconds, almost all of it Bitcoin Core starting. Step 2 takes under half a second and
every later step under a tenth of a second; the threshold signature in step 7 takes about 30
milliseconds. The custody steps are fast because they are a handful of calculations and messages
between processes on one computer, and the chain answers at once because regtest produces blocks on
command.

Long values, such as keys, fingerprints, signatures and addresses, are shown by their first ten
and last eight characters. Hovering over one shows the whole value, and **copy** beside it copies
the whole value.

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
`error RuntimeError: bitcoind not found on PATH (see README.md, Prerequisites)`, and terminal 1 prints
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

In the **Key shares** panel, each signer now reads "holds its share" and shows its process
number, for example "process 780714, share 1 of 3".

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

- `spends`: "5 BTC, output 0 of" (or "output 1 of") a transaction id. The id is the funding
  transaction's from step 3, and the output number is where the exchange's wallet placed the
  custody payment in it, which the wallet chooses at random.
- `pays`: a table of the two new coins, `exchange 0.85 BTC` and `custody (change) 4.1499969 BTC`.
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

**On the screen.** `signers 1, 3`; `offline none`; `signature`, 128 hexadecimal characters
(64 bytes); `verified yes`. In the **Key shares** panel, Signer 1 and Signer 3 read "signing the
payment" and then "signed the payment", with a green background, and Signer 2 reads "online, not
asked".

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
step 8. In the **Key shares** panel, signers 1 and 3 read "signing the snapshot" and then "signed
payment and snapshot". Under the step's details, **4 inclusion proofs published: check one in this
browser** opens the balance check described in [Checking a client's
balance](#checking-a-clients-balance).

When the run is over, the button returns to **Run the demo**, all six boxes in the top row are
green, and a green box above the steps sums up the run: the amount paid to the exchange, the
signers, the settlement's transaction id and the reserve ratio, with a button to the balance check.

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

**Expect:** `18`. Each event also carries `at_ms`, the milliseconds since the run started, which
the dashboard uses for each step's duration and for replays.

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

- **The same on every run:** height 101; 5.00 BTC funded; 4 fills and 12 FIX messages; 0.85 BTC
  delivered and 54,415.925 USD received; the fee of 310 satoshis; "1 of 2 required approvals" with
  one approval; signers 1 and 3 while all three are online; one confirmation; liabilities and assets
  of 4.1499969 BTC; a reserve ratio of 1.00000; `snapshot-103.json`. A different value here means
  the code has changed.
- **Different on every run:** process numbers, keys, addresses, transaction ids, the output
  number in step 6's `spends`, the sighash, the signature, the authorisation id, the Merkle root,
  the audit head, the run directory, and each step's duration by a few milliseconds.

The same run can be watched in the terminal instead of the browser with `uv run custody-lab run`,
which prints each step and its details and writes the same files. To stop the server, press
Ctrl+C in terminal 1.

## A day at the custodian

The settlement run follows one payment. A custodian's day holds many: clients deposit and
withdraw, several clients trade, payments go out at different sizes, a machine is taken down for
maintenance, and some requests must be refused. The **A day at the custodian** tab runs such a
day on the same private chain, with the same policy engine and the same 2-of-3 signing processes,
and adds four ideas the single payment cannot show: a deposit that never arrives, netting across
clients, choosing which coin to spend, and refusals by three different layers. Press **Run the
day**; the day takes about seven seconds, and `uv run custody-lab day` runs it in the terminal.

### Two records that must agree

**The problem.** The custodian keeps two records of the same money. The **ledger** says how much
it owes each client. The chain says which coins sit at the custody address. Neither can be
trusted alone: the ledger is the custodian's own entry, which a bug or a fraud can change, and
the chain knows nothing about clients. If the two drift apart, either the custodian owes more
than it holds, or it holds coins it cannot account for.

**The idea.** After every event the custodian compares the two totals. This is
**reconciliation**: the ledger's total, summed over every client, must equal the total of the
coins at the custody address, to the satoshi. The counterpart is a bank's daily reconciliation of
its own books against its account statement at another bank (a nostro reconciliation), and it
holds; the difference is that here the statement is the public chain, which the custodian cannot
edit and anyone can read.

**On the screen.** The **Books and chain** panel beside the steps shows, after each step that can
move coins, the ledger (one row per client), the coins at the custody address (each with where it
came from) and one line comparing the totals: green with "=" when they agree, red with "≠" when
they do not. Rows and coins that changed in the last step are marked. Seven steps report the
books, and every one of them reconciles; the day's test fails if any does not.

### Deposits: credit only what has confirmed

**The problem.** A client sends coins to the custody address. The custodian sees the payment
within a second, in the **mempool**, the pool of transactions waiting to be put in a block. If it
credits the client then, the client can trade or withdraw against coins that have not arrived.
Until a payment is in a block, the payer can still send the same coins somewhere else.

**The idea.** A coin can be spent only once, and the chain records which spend happened first.
A payment waiting in the mempool has not happened yet: its sender can broadcast a second
transaction spending the same coins with a higher fee, and nodes then drop the first one. This is
**RBF**, replace-by-fee, and used against a payee it is a **double spend**: the same coins promised
twice, delivered once. The defence is to credit a deposit only once it is in a block. Each
further block makes the payment harder to undo, and on the public network a custodian waits for
several before crediting; the demo, on a chain it controls, credits at one.

The counterpart is a cheque. A bank gives provisional credit for a cheque and makes it final only
when the cheque clears; a cheque that bounces is returned and the credit reversed. The comparison
stops at the reversal. If the custodian credited a deposit that was then replaced, there would be
no one to return it from: the coins went back to the sender, the ledger would owe the client
0.50 BTC that the custody address never received, and reconciliation would fail.

**Worked example.** Each client starts with 3.00 BTC in a wallet of its own (step 1). In step 3
all four send their deposits: alpha-capital 2.00 BTC, beta-fund 1.50, gamma-treasury 1.00 and
delta-trading 0.50. All four are seen in the mempool and none is credited. delta-trading then
broadcasts a second transaction spending the same coins as its deposit, paying them back to its
own wallet with a fee of 0.001 BTC, higher than its deposit's. Bitcoin Core accepts the
replacement and drops the deposit (observed: the replaced transaction is no longer known to the
node at all). One block is mined. Three deposits have one confirmation and are credited; the
fourth does not exist any more, and delta-trading is credited nothing. The books read 4.50 BTC,
and the custody address holds three coins: 2.00 + 1.50 + 1.00 = 4.50 BTC.

**On the screen.** `seen unconfirmed: 4 deposits in the mempool, none credited yet`; a table of
the four deposits with each status ("credited at 1 confirmation", or for delta-trading "replaced
before it confirmed: not credited"); `replacement` naming the transaction that paid delta-trading
back; and the credit rule. In the day's transaction log, delta-trading's deposit is marked red.

**A simplification.** The demo has one custody address, so it learns whose deposit is whose from
the transaction id the client reports. A real custodian gives each client a deposit address of
its own, derived from the custody key, so that the chain itself says whose a deposit is.

### Netting across clients

**The problem.** Two of the custodian's clients trade with the same exchange on the same day:
alpha-capital sells, beta-fund buys. Settled separately, alpha-capital's coins leave the custody
address for the exchange, and the exchange sends coins back to the same address for beta-fund:
two on-chain payments, two fees and two rounds of signing, where part of the movement cancels out.

**The idea.** The custodian nets twice. First each client's own fills, as in the settlement run.
Then, acting for all its clients towards the one exchange, it nets their positions against each
other: only the difference moves on chain, and the rest moves between clients in its ledger. That
second step is **internalised settlement**. The counterpart is a settlement agent netting its
clients' deliveries towards one clearing house, and it holds. It stops at what the client owns
in between: until the ledger entry is made, beta-fund's coins are only a claim on the custodian,
which is why MiCA requires a custodian to keep a register of positions for each client, with
every movement recorded ([chapter 8](chapters/08-industry.md#regulation-in-the-eu-mica)).

**Worked example.** In step 4 each client trades in its own FIX session, logged on under its own
SenderCompID, `ALPHA-CAPITAL` or `BETA-FUND`:

| Client | Order | Side | Quantity (BTC) | Price (USD) |
|--------|-------|------|----------------|-------------|
| alpha-capital | A1 | Sell | 0.80 | 64,000 |
| alpha-capital | A2 | Sell | 0.40 | 64,050 |
| beta-fund | B1 | Buy | 0.45 | 63,980 |

Per client (step 5): alpha-capital delivers 0.80 + 0.40 = 1.20 BTC and receives
0.80 × 64,000 + 0.40 × 64,050 = 51,200 + 25,620 = 76,820.00 USD. beta-fund receives 0.45 BTC
and pays 0.45 × 63,980 = 28,791.00 USD.

Across clients: the custodian delivers 1.20 − 0.45 = 0.75 BTC to the exchange on chain and
receives 76,820.00 − 28,791.00 = 48,029.00 USD. The other 0.45 BTC moves from alpha-capital to
beta-fund in the custodian's books only. The settlement instruction `settle-day-1` is for
0.75 BTC.

### Which coin to spend

**The problem.** The custody address now holds three coins, deposited by three different
clients. The settlement of 0.75 BTC is alpha-capital's obligation. Must it spend alpha-capital's
coin?

**The idea.** No. Coins at one address are interchangeable: the chain does not know whose they
are, and the ledger does. Which coin to spend is a separate decision, **coin selection**, made on
cost. Every coin a transaction spends needs its own signature, so one coin means one signing
session, one authorisation and the smallest transaction. The demo picks the smallest single coin
that covers the payment and its fee, which keeps the larger coins for larger payments; if no
single coin is large enough, it refuses rather than spend several. The difference comes back to
the custody address as change, and the fee is charged to the client the payment is for.

**Worked example.** Step 6 pays 0.75 BTC plus a 310-satoshi fee. The coins are 2.00, 1.50 and
1.00 BTC; the smallest that covers 0.7500031 BTC is the 1.00 BTC coin, which gamma-treasury
deposited. The transaction pays 0.75 BTC to the exchange and returns 1.00 − 0.75 − 0.0000031 =
0.2499969 BTC to the custody address. bob and carol approve, signers 1 and 3 sign, and one block
confirms it. In the books, alpha-capital's 2.00 BTC falls by the 1.20 BTC it sold and the fee, to
0.7999969 BTC; beta-fund's rises by the 0.45 BTC it bought, to 1.95 BTC; gamma-treasury still
has 1.00 BTC, although its coin was spent. Ledger and coins both total 3.7499969 BTC.

**On the screen.** `coin spent: 1.00 BTC, deposit from gamma-treasury`, `pays 0.75 BTC`,
`change 0.2499969 BTC`, `fee 310 sats`, `fee charged to: alpha-capital, the delivering client`.
In the books panel, gamma-treasury's coin disappears and a new coin appears: "change from
settle-day-1".

### A signer goes down

At noon (step 7) signer 3's process is stopped, as for maintenance. Its share cannot be used until
it returns. The custody key is 2-of-3, so for the rest of the day the coordinator asks signers 1
and 2, and every later signature, including the end-of-day snapshot's, is theirs. This is
[Taking a signer offline](#taking-a-signer-offline) inside an ordinary day: nothing a client sees
changes.

### Withdrawals and approval tiers

**The problem.** A withdrawal sends coins out of custody for good. It must go only where the
client has said in advance it may go, and the effort spent approving it should match what is at
stake: two people for a large payment, one for a small one.

**The idea.** Each client registers its withdrawal address with the custodian before the day
(step 1 shows the four registered addresses), and the registered addresses are the policy's
whitelist, beside the exchange's. A request names an amount; the policy's tiers set the number of
approvals: up to 0.1 BTC one, up to 10 BTC two.

**Worked example.** In step 8 gamma-treasury withdraws 0.60 BTC, tier two: bob and carol approve.
Coin selection skips the 0.2499969 BTC change coin, which is too small, and spends beta-fund's
1.50 BTC deposit; 0.8999969 BTC returns as change. gamma-treasury's balance falls by the
withdrawal and its fee to 1.00 − 0.60 − 0.0000031 = 0.3999969 BTC. In step 9 beta-fund withdraws
0.05 BTC, tier one: bob's approval alone is enough. The smallest sufficient coin is now the
0.2499969 BTC change, which leaves 0.1999938 BTC; beta-fund's balance becomes
1.95 − 0.05 − 0.0000031 = 1.8999969 BTC. Both are signed by signers 1 and 2. After each, ledger
and coins agree: 3.1499938 BTC, then 3.0999907 BTC.

### Three refusals, three layers

**The problem.** Most of what protects client coins is a payment that does not happen. Each rule
belongs to a particular layer, and a refusal should come from the layer that owns the rule.

**The idea.** Three requests in step 10, each stopped by a different layer:

1. **The ledger.** delta-trading asks to withdraw 0.20 BTC. Its deposit never arrived, so it is
   owed nothing: "delta-trading holds 0.00 BTC". The request is refused before any transaction is
   built and before the policy engine sees it, because whether a client has the money is a
   question for the books.
2. **The whitelist.** alpha-capital asks for 0.30 BTC to an address it never registered. Both
   approvers sign, and the policy engine still refuses: "denied: destination … is not
   whitelisted". An approval cannot add an address; registering one is a separate act, done in
   advance. A custodian can also hold a newly registered address back for a set period before it
   may be paid, so that a registration made by an attacker can be noticed first.
3. **The velocity limit.** alpha-capital retries the same 0.30 BTC to its registered address. The
   day's limit is 1.50 BTC, and 0.75 + 0.60 + 0.05 = 1.40 BTC has already been authorised;
   1.40 + 0.30 = 1.70 BTC is over it: "denied: velocity limit 1.50 BTC per 24 hours; 1.40 BTC
   already authorised". The limit bounds what can leave in a day even if every approver were
   compromised; the request can be made again tomorrow, or raised with more scrutiny.

No transaction is built or signed for any of the three, so nothing reaches the chain, and the
books still equal the coins. The two refusals by the policy engine are in its audit log; the
ledger's refusal is the custodian's own record.

### The end of the day

Step 11 publishes the proof of reserves, as step 9 of the settlement run does. The ledger reads
alpha-capital 0.7999969, beta-fund 1.8999969, gamma-treasury 0.3999969 and delta-trading 0.00 BTC:
liabilities of 3.0999907 BTC. The custody address holds three coins: alpha-capital's 2.00 BTC
deposit, never spent, and the two changes, 0.8999969 and 0.1999938 BTC: assets of
2.00 + 0.8999969 + 0.1999938 = 3.0999907 BTC. The reserve ratio is 1, and signers 1 and 2 sign
the snapshot. The audit log holds nine entries: an evaluation and an authorisation for each of the
three payments, the two refused evaluations, and the snapshot's authorisation. The snapshot is
`var/day/<run>/reserves/snapshot-106.json`: block 106 is the 102nd block of step 1 plus one block
each for the deposits, the settlement and the two withdrawals.

**What the day shows.** Every movement of client money is either on the chain or in the ledger,
and the two are compared after each one. A deposit counts when it confirms, not when it is seen.
Netting can keep a client's purchase off the chain entirely, which makes the ledger the only
record of it. Coins at one address are interchangeable, so the ledger, not the coin, says whose
they are. And each refusal comes from the layer that owns the rule: the books for balances, the
policy for destinations and limits.

## Key ceremonies

**The problem.** A 2-of-3 key protects the coins as long as nobody holds two shares. Over the
years a custody key is in use, shares are exposed: a server is breached, a backup tape goes
missing, an administrator leaves. A thief who takes one share in January and another in June
holds two shares, and two shares are the key. Shares are also lost: a disk fails, a site burns
down. Two such losses and the coins are frozen for good. Replacing the key each time means moving
every coin to a new address, with fees, new deposit instructions for every client, and a window in
which both keys matter. Custodians need a way to renew shares, and to rebuild one, without
changing the key.

**The idea in plain words.** Two ceremonies do it.

A **refresh** gives every signer a new share of the same key. The signers run a key generation
whose secret is zero and add the result to their shares. Adding zero leaves the key, and so the
custody address, unchanged; but every share moves to a new line, and a share from before the
refresh no longer combines with one from after it. Time is cut into periods, and a thief must now
collect two shares within one period. Chapter 2 works this by hand: on its toy curve the shares
14, 19 and 24 become 25, 10 and 26, new shares 1 and 3 still give the key 9, and old share 1 with
new share 3 gives 8 ([chapter 2, Proactive refresh on the toy
curve](chapters/02-mpc-custody.md#proactive-refresh-on-the-toy-curve)).

A **share repair** rebuilds a lost share from two of the others. Each helper splits a value derived
from its own share into random-looking pieces, one per helper, and sends them out; each helper adds
up the pieces it receives and passes only that sum to the signer being repaired, who adds the sums
into its share. No helper's share, and no single piece or sum, reveals a share.

The counterpart is a bank changing the combination of a vault held under dual control: the vault
and its contents stay where they are, each officer gets a new half, and an old half written down
somewhere becomes useless. The comparison stops at what an old half was worth: an old combination
never opens the new lock, but two shares stolen within the same period are the key itself, before
and after any refresh. A refresh limits how long a thief has to collect shares; it does not undo a
theft of two. After that, the coins must move to a new key.

**Worked example.** Press **Run the ceremonies** on the **Key ceremonies** tab. The nine steps run
on the same signing processes as the settlement run, with no chain, in under a second;
`uv run custody-lab ceremonies` runs them in the terminal.

1. *Generate the key.* As step 2 of the settlement run: three processes, one share each.
2. *A thief copies signer 1's share.* The demo copies the share out of signer 1's process, as a
   thief who copied its storage would hold it. Alone it cannot sign: FROST refuses with
   `IncorrectNumberOfCommitments`.
3. *A second share from the same period.* Had the thief also copied signer 3's share now, the two
   would sign: `signature valid yes`. This is the case a refresh cannot help.
4. *Refresh.* All three signers run the refresh. `group key unchanged yes` and `output key
   unchanged yes`: the custody address is the same. The public key package, which records each
   signer's public share, changes; its fingerprint is shown before and after.
5. *Old and new do not combine.* The thief now copies signer 3's new share and tries to sign with
   it and signer 1's old one. FROST checks each partial signature against the signer's public
   share and refuses: "the share from participant 1 does not fit". Checked against the old public
   key package instead, it is participant 3's share that does not fit: the two shares belong to
   different periods either way.
6. *The new shares sign* under the same output key.
7. *Signer 2 loses its share.* Asked to sign, signer 2 answers "no key share: it was lost and has
   not been repaired".
8. *Signers 1 and 3 rebuild it.* Each sends signer 2 one sum and nothing else. The public key
   package is unchanged: the rebuilt share is the same share signer 2 had.
9. *Signer 2 signs again*, with signer 3, under the same output key.

The **Who holds what** panel beside the steps shows each signer's share by period, 1 before the
refresh and 2 after, signer 2's share lost and then rebuilt, and what the thief holds: signer 1's
period-1 share and signer 3's period-2 share, with the verdict that it cannot sign.

**What breaks without it.** Without refresh, every share ever exposed stays dangerous for the life
of the key, and a patient thief needs only to wait. Without repair, each lost share brings the
custodian one step closer to frozen coins, and the only cure is a full move to a new key. Both
ceremonies need the signers to be online together, refresh all three of them, which is why a
custodian schedules them like any other change, with the same approvals.

## Taking a signer offline

**The problem.** A 2-of-3 key exists so that the coins can still move when one signer cannot take
part: its machine has failed, its site is cut off, or it has been taken out of service because it
may be compromised. A design that claims this should show it working, and should show what happens
when too many signers are gone.

**The idea.** The coordinator does not need particular signers, only enough of them. It asks
signers 1 and 3 while both are running, and otherwise asks whichever signers are still running.
With fewer than two running, no signature can form: the run stops at step 7 and the coins stay
where they are. That is a **liveness** failure: the payment is delayed, nothing is lost, and it can
be made once a signer is back. The opposite, a payment made that should not have been, is a
**safety** failure, and cannot be undone.

The counterpart is a bank mandate with three authorised signatories, any two of whom must sign a
payment: one on leave does not stop payments, and two on leave do. The comparison stops at what
the signatories check. Here each signer checks the policy engine's authorisation before it takes
part, so the signers still running cannot sign anything the policy engine has not approved, however
urgent the payment.

**The switches.** Each card in the **Key shares** panel has a switch. A signer switched off keeps
its share through key generation, because a share has to exist before its holder can lose it, and
at the start of step 7 the server stops that signer's process, as a power failure would. The
switches apply to the next run, stay where they are set, and are locked while a run is going. The
note under the cards counts the signers that will be online and turns red when fewer than two
will be.

**Worked example: one signer offline.** Switch off Signer 1. Its card reads "stops before step 7".
Press **Run the demo**. Steps 1 to 6 run as before. At step 7, Signer 1's card changes to
"offline: process stopped", and the coordinator asks signers 2 and 3. Step 7 shows `signers 2, 3`
and `offline 1`, and the run settles exactly as before: 0.85 BTC to the exchange, a 310-satoshi
fee, liabilities and assets of 4.1499969 BTC. Signers 2 and 3 end as "signed payment and
snapshot".

Nothing on the chain shows the difference. The signature from signers 2 and 3 verifies under the
same custody key as one from signers 1 and 3, because both pairs hold shares of the same key.

**Worked example: two signers offline.** Switch off Signer 3 as well. The note turns red: "with 1
online, step 7 fails and no coins move." Press **Run the demo**. At step 7 the coordinator can ask
only signer 2. Signer 2 checks the authorisation, which is valid, and then the FROST library
refuses to sign: in the first round of signing each participant sends a commitment, and one
commitment is fewer than the key's threshold of two. Step 7 turns red with:

```
RuntimeError: 1 of 3 signers online and 2 are required; FROST refused: signer 2:
ValueError('IncorrectNumberOfCommitments')
```

Steps 8 and 9 stay PENDING. Nothing was broadcast, so the coins never left the custody address.
Signer 2 reads "could not sign alone", and the Signers box in the top row is red.

The same runs work from the command line: `uv run custody-lab run --offline 1` settles with
signers 2 and 3, and `uv run custody-lab run --offline 1 --offline 3` stops at step 7: it prints
the error above in full, names the run's `events.jsonl`, and exits with status 1.

**What it shows.** One signer down changes nothing a client would notice; two down stops payments
and loses nothing. The threshold sets that balance: with 3 of 3, one signer down would stop
payments, and with 1 of 3, one compromised signer could move the coins alone.
[Chapter 9](chapters/09-capstone.md#safety-and-liveness) works out how likely each failure is for
each choice.

## Checking a client's balance

**The problem.** Step 9 publishes a total and a root, and no client can see the other clients'
balances. A custodian short of coins could count one client for less than it is owed, so that the
published total matches the coins it holds. Only that client knows its true balance, so only that
client can catch it, and it has to be able to check without relying on the custodian's software.

**The idea.** Each client receives its own inclusion proof: its balance, its salt, and for each
level of the tree the fingerprint and sum of the node beside its path. Starting from the balance it
believes it is owed, the client recomputes its leaf's fingerprint, combines it with the first
sibling to get their parent, combines that with the next sibling, and so on to the top. If the
result equals the published root, the published total counts this client at exactly that balance.
A balance different by one satoshi gives a different leaf fingerprint, and every fingerprint above
it changes with it. The **salt**, random bytes hashed into the leaf, stops anyone who sees a proof
from working out other clients' balances by guessing.

The **Check a client's balance** tab does this calculation in the browser, in
`web/src/reserves.ts`, using the browser's own SHA-256. It is a second implementation, written
from the tree's published encoding: it shares no code with the Python that built the tree, and a
test runs it on proofs the Python code produces and compares the roots. A client checking with
software it did not get from the custodian is the point of the check. The page holds all four
proofs because it plays each client in turn; a real client receives only its own.

The counterpart is an auditor's balance confirmation, in which the auditor writes to a client to
confirm the balance in the books. The comparison stops at who does the checking: here the client
checks the published figure itself, and needs neither the auditor nor the custodian.

**Worked example.** After a run, press the button in the green summary, or the link under step 9.
alpha-capital is selected, and the balance field holds 1.1499969, its balance after the
settlement. The tree orders the clients alphabetically, alpha-capital, beta-fund, delta-trading,
gamma-treasury, and pairs them in that order, so alpha-capital's path has two levels below the
root:

- **Leaf**: alpha-capital's salt, name and 1.1499969 BTC, hashed. It is combined with the
  right-hand sibling, beta-fund's leaf, holding 1.5 BTC.
- **Level 1**: the two leaves with their sums, hashed: a total of 1.1499969 + 1.5 = 2.6499969 BTC.
  It is combined with the right-hand sibling holding delta-trading and gamma-treasury,
  0.5 + 1 = 1.5 BTC.
- **Root**: 2.6499969 + 1.5 = 4.1499969 BTC, the liabilities step 9 published.

The verdict below the path is green: "Included. The recomputed root equals the published root, so
the snapshot commits to alpha-capital holding 1.1499969 BTC, within total liabilities of
4.1499969 BTC (published: 4.1499969 BTC)." The published root at the foot of the page is step 9's
`root`.

Now choose beta-fund and press **+1 satoshi**. The field reads 1.50000001, the root's total reads
4.14999691 BTC, one satoshi more than was published, and the verdict turns red: "Not included.
With 1.50000001 BTC the path reaches a different root, so the published snapshot does not commit
to that balance." Changing one satoshi in the leaf changed every fingerprint above it. **Reset**
puts back the proof's own balance.

**The second check: who signed the root.** A balance found inside a root proves nothing unless
the custodian is bound to that root. A custodian could publish one root to a client who checks
and another to everyone else, or change the figures after publishing them. The snapshot closes
this: it names the root, the liabilities and assets, the block it was taken at and the latest
audit-log fingerprint, and two of the three signers sign it with the custody key, the same key
that holds the coins.

The card **Check the custodian's signature**, under the balance check, rebuilds the signed
message from the snapshot's own fields, in the same order and encoding as the server, and checks
the signature with **BIP340**, Bitcoin's signature rule, using `@noble/curves`, an audited
TypeScript library that shares no code with the server's verifier. With the published figures the
verdict is green: the recomputed message equals the published one, and the signature verifies
over it. **Lower the liabilities by 1 BTC** changes one figure on the page, as a custodian hiding
a debt would: the recomputed message changes, the signature no longer verifies, and the verdict
turns red. This is the after-the-run check on `var/altered.json`, done in the browser.

One more question remains: is the key that signed the snapshot the key that holds the coins? A
custodian could sign with a key that controls nothing. A Taproot address is that key written in
bech32m, the address format of BIP 350, so the client can read the key out of the address it
deposited to without asking the custodian. The card shows the custody address from step 2, the
key decoded from it in the browser (with `@scure/base`), and whether it is the key that signed;
the verdict is green only when it is. Bitcoin Core is the oracle for the decoder: it derives
addresses from known keys, and the browser code must read the same keys back
(`tests/demo/test_browser_address.py`).

The counterpart is an auditor's signed opinion on the reconciliation: it is worth something
because the figures cannot be changed afterwards without the signature failing. The comparison
stops at who can check it: anyone with the snapshot can verify this signature, with any BIP340
implementation, without trusting the custodian's software. The browser library is checked against
Bitcoin's 19 published BIP340 test vectors and against snapshots signed by the Python code
(`tests/demo/test_browser_snapshot.py`).

**What breaks without it.** The attack "Publish a liabilities tree with a client's balance cut by
0.5 BTC", in the next section, is this check catching a custodian: the published tree counts
alpha-capital for 0.5 BTC less, and alpha-capital's recomputation from its true balance misses the
published root. A client that never checks leaves that undetected, which is one of the limits
listed under step 9.

## Attacking the design

**The problem.** A custody design is defined as much by what it refuses as by what it does. A run
that settles shows that the approved path works. It does not show that a thief, a careless insider
or a compromised server is stopped: each refusal has to be tried.

**The idea.** The **Attack the design** tab sets up the demo's policy engine, approvers and a
2-of-3 signing cluster, without a chain, and tries sixteen attacks against the real code. Each
row names the component that stopped the attack and quotes that component's own refusal. An
attack that got through would be marked ACCEPTED in red and the summary would say a defence is
broken; a test breaks the policy engine on purpose to prove the panel shows it. The attacks need
no Bitcoin node and take about a fifth of a second. `uv run custody-lab attacks` runs them in the
terminal and exits with an error if any is accepted.

Where an attack needs a transaction, a 32-byte fingerprint of the instruction stands in for its
sighash. The signers check only that the authorisation names the exact message they are asked to
sign, and a sighash is a 32-byte message like any other. The snapshot in the last group carries
block height 0 for the same reason.

A **replay** is the presentation, a second time, of a message or permission that was valid once,
to get its effect again. Several attacks below are replays in some form.

The counterpart is a penetration test's list of findings turned round: every row is an attack and
the expected result is a refusal. The comparison stops at scope. These are attacks on the design's
own rules, run inside one computer; they say nothing about the machines, networks and people around
it, which [chapter 3](chapters/03-key-storage.md) and [chapter 9](chapters/09-capstone.md) cover.

**Policy engine** ([chapter 4](chapters/04-policy.md)). The engine runs its seven checks in order,
and the first failure decides.

- *Pay an address that is not on the whitelist*: "denied: destination attacker-address is not
  whitelisted". Two valid approvals do not help, because the whitelist is checked before the
  approvals.
- *Pay 0.85 BTC with one approval where the tier needs two*: "pending: 1 of 2 required approvals".
- *Approve an instruction its own initiator raised*: bob raises the instruction and approves it,
  and carol approves it. Under the four-eyes rule only carol's approval counts: "1 of 2".
- *Approve with a key that is not on the approver list*: mallory signs a correct approval with a
  key the policy does not list, so it does not count: "1 of 2".
- *Raise the amount from 0.85 to 8.5 BTC after both approvals*: each approval signs the
  instruction's exact contents, so after the change neither matches: "0 of 2".
- *Submit an authorised instruction a second time*: "instruction already authorised". The engine
  finds the earlier authorisation in its own audit log.
- *Drain the account in 9.5 BTC payments, each fully approved*: each payment is within the tier
  that two approvals allow, but a third would bring the day's total to 28.5 BTC, over the 20 BTC
  velocity limit: "velocity limit 20 BTC per 24 hours; 19.0 BTC already authorised".

**Signers** ([chapters 2](chapters/02-mpc-custody.md) and [4](chapters/04-policy.md)). Each
signer process checks the authorisation itself, and each refusal is shown on its own line.

- *Sign with an authorisation from an attacker's own authority key*: the attacker writes an
  authorisation for a payment to its own address and signs it with a key it generated: "not signed
  by the policy authority (Ed25519)".
- *Forge an authorisation after breaking Ed25519, as a quantum computer could*: the attacker is
  given the policy engine's real Ed25519 key, as a large quantum computer could compute it from
  the public key, but not its ML-DSA-65 key. The Ed25519 signature is now valid and the ML-DSA-65
  one is not: "not signed by the policy authority (ML-DSA-65)". This is why each authorisation
  carries both signatures ([chapter 7](chapters/07-post-quantum.md)).
- *Replay an authorisation that has already been used*: the authorisation is used once, for its
  own payment, and then presented again. Each signer kept its identifier: "authorisation already
  used".
- *Swap in a different transaction after approval*: the authorisation names one sighash, and the
  coordinator asks the signers to sign another: "signing package message differs from the
  authorised message".
- *Use an authorisation issued five minutes ago*: an authorisation is valid for 60 seconds:
  "expired at" followed by the time it expired.
- *Sign with one signer, as an insider holding one share would*: a valid authorisation, presented
  to signer 2 alone: "IncorrectNumberOfCommitments", as in [Taking a signer
  offline](#taking-a-signer-offline).

**Published records** ([chapters 4](chapters/04-policy.md) and [6](chapters/06-reserves.md)).

- *Lower the liabilities in a signed reserves snapshot*: the signature covers the snapshot's exact
  contents and does not verify over the altered copy. This is the check on `var/altered.json`
  after the run, done in code.
- *Publish a liabilities tree with a client's balance cut by 0.5 BTC*: alpha-capital recomputes
  the root from its own 1.1499969 BTC and misses it, as in [Checking a client's
  balance](#checking-a-clients-balance).
- *Edit an amount in the audit log*: the edited entry's fingerprint no longer matches its
  contents: "entry 1: content does not match its hash".

The [attack-vector analysis](attack-vectors.md) goes further: every vector it found, layer by
layer, with what stops each in the demo, where that is shown or tested, and what remains open.

**On the screen.** Press **Run the attacks**. The rows arrive one after another under the three
headings, each marked REFUSED in green, and the summary above them reads "16 of 16 attacks
refused."

## Replaying a recorded run

**The problem.** A run needs Bitcoin Core, and a run's results leave the screen when the next one
starts. Presenting the demo on a computer without Bitcoin Core, or looking again at a run that
failed, needs the run's record.

**The idea.** Every run writes its events to `var/demo/<run>/events.jsonl`, each stamped with the
milliseconds since the run started. Once a run has finished, a list appears under **Run the
demo** naming each recorded run, newest first: its start time in UTC, how it ended ("settled",
"failed at step 7") and any signers that were offline. Choosing one and pressing **Replay** plays
its events through the same screen, pausing between them as recorded, except that a pause longer
than 700 milliseconds, such as Bitcoin Core starting, is shortened. A blue line above the steps
names the file being replayed, and the step durations are the recorded ones. A replayed run that
recorded its inclusion proofs can be checked on the balance tab. Runs recorded before events
carried timestamps replay without durations.

The server lists the 20 newest runs. It reads a run only by the name of a directory under
`var/demo`, so a replay cannot be pointed at any other file. A replay needs the server but not
Bitcoin Core.

The counterpart is a FIX session's message log loaded into a viewer, and it holds: the record is
shown as it was, and nothing is recomputed or signed again.

## Troubleshooting

| Symptom | Check | Fix |
|---------|-------|-----|
| The browser shows `{"detail":"Not Found"}` at <http://127.0.0.1:8000> | Was the server started from the repository root, after `npm --prefix web run build`? | Stop it with Ctrl+C, change to the repository root, build, start it again |
| Terminal 1 prints `ERROR: [Errno 98] error while attempting to bind on address ('127.0.0.1', 8000): address already in use` | `ss -ltnp \| grep :8000` shows what holds the port | Stop the other server, or start this one with `uv run custody-lab serve --port 8001` and open that port |
| Step 1 turns red: `RuntimeError: bitcoind not found on PATH` | `which bitcoind` in terminal 1 | Install Bitcoin Core 31.1 (see the README), then restart the server from a shell where `which bitcoind` finds it |
| A red line under the header: "The demo server is not reachable" | The page cannot reach the server's API: was it opened from `npm --prefix web run dev` with no `custody-lab serve` running? | Start the server in terminal 1 |
| `curl` in terminal 2 works, but the Windows browser does not load the page | WSL's forwarding of `localhost` to Windows | Check the WSL networking settings, or open the page in a browser inside WSL |
| A signer's switch does not move | Is a run going? | The switches unlock when the run ends; they set the next run |
| The balance tab says to run the demo first | Has a run on this page reached step 9? A page reload clears the screen | Run the demo, or replay a recorded run that settled |
| No list of recorded runs under **Run the demo** | `ls var/demo/*/events.jsonl` | A run has to finish before it is listed; the list refreshes when a run ends |
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
| 6. Policy | spends step 3's coin; pays 0.85 BTC and 4.1499969 BTC change; matches instruction yes; fee 310 sats under a 10,000 cap; one approval PENDING; bob and carol approve | [4](chapters/04-policy.md) |
| 7. Sign | signers 1 and 3 signed, signer 2 online and not asked; offline none; verified yes | [2](chapters/02-mpc-custody.md) |
| 8. Broadcast | confirmations 1; fee 310 sats | [5](chapters/05-settlement.md) |
| 9. Reserves | liabilities and assets 4.1499969 BTC; reserve ratio 1.00000; proofs and proof of control yes; four inclusion proofs to check | [6](chapters/06-reserves.md) |

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
7. Any two signers settle the payment. With one, step 7 fails and nothing moves: a liveness
   failure, which can be retried, never a safety failure, which cannot (Taking a signer offline).
8. Each client recomputes its own place in the published snapshot from the balance it expects,
   with software independent of the custodian's, and a balance one satoshi off misses the root
   (Checking a client's balance).
9. Sixteen attacks on the design's rules are each refused, by the component the design assigns
   to that rule and in that component's own words (Attacking the design).
10. A custodian's books and the chain must agree after every movement. A deposit counts once it
    confirms; netting across clients keeps part of the settlement off the chain; coins at one
    address are interchangeable and the ledger says whose they are; and each refusal comes from
    the layer that owns the rule (A day at the custodian).
11. A refresh renews every share without changing the key, so a thief must collect two shares
    within one period; it does not undo a theft of two. A lost share is rebuilt by two others
    without either revealing its own (Key ceremonies).

[Chapter 0](chapters/00-orientation.md) follows the same run with the arithmetic of each step,
and the [contents page](README.md) lists the chapters that explain each mechanism in full.
