# Module 5: Trading to Settlement

2026-10-08

Previous: [Chapter 4, Policy and Authorisation](04-policy.md) \| [All
chapters](../README.md) \| Next: [Chapter 6, Proof of
Reserves](06-reserves.md)

> [!WARNING]
>
> ### EDUCATIONAL, NOT PRODUCTION
>
> Four parts of this module are teaching code:
>
> - The FIX session layer: no heartbeats or resend.
> - The toy exchange.
> - The transaction builder, written from BIP 341 and validated by its
>   test vectors.
> - A regtest-only chain setup.
>
> Bitcoin Core is real, and it validates every transaction this chapter
> broadcasts.

<a id="what-this-chapter-is-for"></a>

## What this chapter is for

A FIX engineer knows the first half of this chapter already. Orders go
out, execution reports come back, and at the end of a cycle the back
office settles the net position. This chapter follows that net position
the rest of the way: from the fills to an on-chain payment that Bitcoin
Core accepts and mines, through the policy engine of [chapter
4](04-policy.md) and the signing cluster of [chapter
2](02-mpc-custody.md).

Two things are new to someone from traditional markets. The first is
where the assets sit while trading happens, which decides what a client
loses if an exchange fails. The second is what a Bitcoin payment is: not
a debit and a credit in an account ledger, but a signed message that
consumes coins and creates new ones. The chapter builds both from the
beginning, then settles a real transaction on a private Bitcoin network
while it is built.

The demo’s settlement path, which this chapter covers end to end:

| Step | Component | Output |
|----|----|----|
| 1 | FIX session (5.0 SP2 over FIXT.1.1) with the toy exchange | ExecutionReports |
| 2 | Netting | one net obligation per asset |
| 3 | Settlement instruction | asset, amount, destination (the exchange’s settlement address) |
| 4 | Policy engine ([chapter 4](04-policy.md)) | approvals, then an authorisation for one sighash |
| 5 | Transaction builder | one-input Taproot spend, checked against the instruction |
| 6 | FROST cluster ([chapter 2](02-mpc-custody.md)) | a 64-byte BIP340 signature from 2 of 3 processes |
| 7 | Bitcoin Core | broadcast, mined, confirmed |

By the end of this chapter the following should be clear:

- why clients pre-funding exchanges was a risk, and what off-exchange
  settlement changes;
- how fills net into one obligation, worked by hand;
- Bitcoin’s transaction model: coins as outputs, change and fee, locking
  scripts and witnesses;
- what a sighash commits to, and why one sighash authorises exactly one
  transaction;
- how a Taproot key-path payment is built and signed, including the
  BIP86 tweak;
- which checks tie a transaction to the instruction the policy engine
  approved.

<a id="first-principles"></a>

## First principles

This section covers where assets sit during trading, netting, and the
Bitcoin half of the chapter from the ledger model to confirmation. The
FIX messages are in the formal treatment.

<a id="settling-against-an-exchange"></a>

### Settling against an exchange

**The problem.** In the usual crypto-exchange arrangement, the client
**pre-funds the exchange**: it moves coins into the exchange’s wallets
before it can trade. From then on the coins are under the exchange’s
control. If the exchange fails, the client is an unsecured creditor in
an insolvency, with no particular claim on the coins it deposited. The
collapse of FTX in November 2022 made that concrete for many
institutions.

**The idea.** **Off-exchange settlement** reverses the arrangement:

- the client’s assets stay with its custodian, in an account the
  custodian locks for trading;
- the exchange shows the client a mirrored trading balance, backed by
  those locked assets;
- at the end of each settlement cycle, only the **net** obligation
  moves, in one direction, from the custodian to the exchange or back.

A securities engineer will recognise the shape: trading against a
balance held elsewhere, with delivery at the end of a cycle, is how a
clearing member trades against an exchange while the securities stay at
the depository. The comparison stops holding at delivery: here the
custodian itself signs and broadcasts the payment, and there is no
central depository between the parties.

Copper’s ClearLoop is the best-known example: settlement cycles of a few
hours, and exchanges also post collateral with the custodian. Similar
networks exist from other custodians (**verify current**). The demo
implements the settlement side: the fills arrive, the custodian nets
them and delivers the net bitcoin.

**Recap.** Pre-funding exposes the client to the exchange’s failure;
off-exchange settlement keeps the assets with the custodian and moves
only the net amount each cycle.

<a id="many-fills-one-delivery"></a>

### Many fills, one delivery

**The idea.** Over a cycle a client trades many times in both
directions. Settling each fill separately would mean one on-chain
payment per fill, each with a fee and a confirmation wait. **Netting**
adds the cycle’s fills up into one obligation per asset, the way a
clearing house nets a day’s trades into one delivery per participant.

**Worked by hand**, with the demo’s four fills:

| Order | Side | BTC | Price (USD) | BTC change for the client | USD change for the client |
|----|----|----|----|----|----|
| C1 | sell | 0.40 | 64,000.00 | $-0.40$ | $+25{,}600.00$ |
| C2 | buy | 0.15 | 63,950.50 | $+0.15$ | $-9{,}592.575$ |
| C3 | sell | 0.35 | 64,010.00 | $-0.35$ | $+22{,}403.50$ |
| C4 | sell | 0.25 | 64,020.00 | $-0.25$ | $+16{,}005.00$ |
| Net |  |  |  | $-0.85$ | $+54{,}415.925$ |

A sale reduces the client’s bitcoin and increases its dollars; a
purchase does the opposite. The net is $-0.85$ BTC: the client owes the
exchange 0.85 BTC, which the custodian sends on chain. The exchange owes
the client USD 54,415.925, which moves over ordinary payment rails and
is outside the demo ([chapter 8](08-industry.md) discusses what happens
when one side settles and the other does not).

**Recap.** Netting turns a cycle of fills into one delivery per asset
and direction.

<a id="coins-are-outputs-not-balances"></a>

### Coins are outputs, not balances

**The problem.** An account ledger, such as a central bank’s real-time
gross settlement system, keeps one balance per account: a payment debits
one balance and credits another. Bitcoin keeps no balances, and building
a transaction requires its actual model.

**The idea.** Bitcoin’s ledger is the set of **unspent transaction
outputs (UTXOs)**. Each UTXO is an amount together with a condition for
spending it. A wallet’s balance is the sum of the UTXOs it can spend.

A transaction consumes whole UTXOs as **inputs** and creates new
**outputs**. An output is spent entirely or not at all, like a banknote.
To pay 0.85 BTC out of a 5.00 BTC UTXO, the transaction creates two
outputs: 0.85 BTC to the payee, and the remainder less the fee back to
the payer as **change**. Each input names the output it spends by its
**outpoint**: the identifier of the transaction that created it (the
**txid**, a hash of that transaction) and the output’s index in that
transaction.

**The fee** is not a field in the transaction. It is the total of the
inputs minus the total of the outputs, and the miner who includes the
transaction collects it. This has a dangerous consequence: a transaction
that leaves out its change output pays the whole difference to the
miner, and nothing in Bitcoin’s rules objects. `transfer.check_matches`
therefore computes the fee from the input and the outputs and refuses
anything above a cap (Exercise 4).

**Satoshis.** Amounts on chain are whole numbers of **satoshis**: 1 BTC
is 100,000,000 satoshis. The code keeps amounts as `Decimal` BTC
everywhere else and converts only at this boundary (`bitcoin.to_sats`),
so no amount is ever a binary floating-point number. Bitcoin Core does
not relay an output below the **dust** limit (330 satoshis for a Taproot
output under its default policy), so the builder adds change below that
limit to the fee instead of creating it.

The banknote comparison stops holding on ownership. A banknote belongs
to whoever holds it; a UTXO belongs to whoever can meet its spending
condition.

**Recap.** Bitcoin tracks coins, not balances. A payment spends whole
coins and creates new ones, including change, and whatever is left over
is the fee.

<a id="locking-and-unlocking"></a>

### Locking and unlocking

**The idea.** Each output carries a **locking script** (`scriptPubKey`):
a short program stating the condition a spender must meet. The spender
supplies a **witness**, the data that meets it. For every output the
demo creates, the condition is “a valid signature under this one key”,
and the witness is that signature.

A **Taproot** output (BIP 341, active on Bitcoin since November 2021)
has the 34-byte locking script `OP_1 <32-byte key>`: `OP_1` marks it as
a version 1 witness program, and the 32 bytes are an x-only public key
([chapter 1](01-foundations.md)). It can be spent in two ways:

- **key path:** a BIP340 signature under the 32-byte key;
- **script path:** revealing one of a set of alternative scripts
  committed inside the key, and satisfying that script.

The demo uses the key path only. BIP86 **tweaks** the key so that it
provably commits to an empty set of scripts (formal treatment), so no
hidden script path can exist.

An **address** is a locking script written for people: a checksummed
text encoding (bech32m, BIP 350) of the witness version and the key.
Taproot addresses start with `bc1p` on the main network and `bcrt1p` on
regtest. Paying an address means creating an output with that locking
script. The custody address is derived from the FROST group key, so only
a quorum of signers can spend what it receives.

**SegWit** (BIP 141, 2017) moved signatures into a separate witness
section, which the txid does not cover. The signature malleability
described in [chapter 1](01-foundations.md) therefore cannot change a
transaction’s identifier.

**Recap.** An output is locked by a script; a Taproot key-path output
needs one BIP340 signature under its key; an address is that script in
human-readable form.

<a id="what-the-signature-covers-the-sighash"></a>

### What the signature covers: the sighash

**The problem.** A signature signs a 32-byte message. For a transaction,
that message cannot be the whole serialised transaction, because the
witness that will hold the signature is part of it: the signature would
have to sign itself.

**The idea.** The message is the **sighash**, a hash over the
transaction’s fields with the witness left out. The default Taproot
sighash covers:

- the transaction’s version and locktime;
- every input’s outpoint, amount, locking script and sequence number;
- every output.

Changing any amount or destination changes the sighash, and a signature
over the old sighash no longer verifies. One sighash therefore
authorises exactly one transaction. That is why the policy engine’s
authorisation names a sighash ([chapter 4](04-policy.md)), and why each
signer compares it with the message it is asked to sign.

The **locktime** field and each input’s **sequence** number carry time
locks and replacement signals. The demo sets locktime 0 and sequence
`0xFFFFFFFD`, which allows the transaction to be replaced by one that
pays a higher fee if it gets stuck.

**Worked in code.** The cell builds the worked example’s transaction
offline: one 5.00 BTC input, 0.85 BTC to the payee, change back to
custody. Then it makes the two changes discussed above: it removes the
change output, which `check_matches` must refuse, and it pays the payee
one satoshi more, which must change the sighash.

``` python
from custody_lab.settlement import bitcoin, transfer

custody = bitcoin.p2tr_script(b"\x11" * 32)  # OP_1 <32-byte key>
payee = b"\x00\x14" + b"\x22" * 20  # a SegWit v0 locking script
utxo = transfer.Utxo("ab" * 32, 0, 500_000_000, custody)
stx = transfer.build([utxo], 85_000_000, payee, custody)
assert [o.amount for o in stx.tx.outputs] == [85_000_000, 414_999_690]
assert stx.fee == 310
print(custody[:2].hex(), "+ 32-byte key:", len(custody), "byte locking script")

no_change = bitcoin.Transaction(stx.tx.inputs, stx.tx.outputs[:1])
burn = transfer.SettlementTx(no_change, stx.spent, stx.fee)
refused = False
try:
    transfer.check_matches(burn, 85_000_000, payee, custody, max_fee=10_000)
except ValueError as err:
    refused = True
    print("no change output:", err)
assert refused

one_more = (bitcoin.TxOut(85_000_001, payee), stx.tx.outputs[1])
altered = transfer.SettlementTx(
    bitcoin.Transaction(stx.tx.inputs, one_more), stx.spent, stx.fee
)
assert altered.sighash() != stx.sighash()
print("one more satoshi to the payee: different sighash")
```

    5120 + 32-byte key: 34 byte locking script
    no change output: fee 415000000 sats outside [0, 10000]
    one more satoshi to the payee: different sighash

The first printed line shows the locking script’s first two bytes,
`5120` (`OP_1` and a 32-byte push), and its length. The second is
`check_matches` refusing the transaction without change, because its fee
would be 4.15 BTC. The third confirms that one satoshi changes what is
signed.

**Recap.** The sighash is the fingerprint of everything in a transaction
except its signatures; a signature over it approves that transaction and
no other.

<a id="blocks-confirmation-and-regtest"></a>

### Blocks, confirmation and regtest

**The idea.** Nodes check each transaction they receive and hold valid
ones in a waiting pool, the **mempool**. Miners select transactions from
it by fee rate, in satoshis per virtual byte. A virtual byte is a size
measure in which each witness byte counts as a quarter, which made
SegWit transactions cheaper. Miners assemble the chosen transactions
into a **block**. A block is valid only with a **proof of work**: a hash
of its header below a target value, found by trial. Each block names its
predecessor, so the blocks form a chain.

A transaction in a block has one **confirmation**, and each later block
adds one. Reversing it requires redoing the proof of work of its block
and of every later one faster than the rest of the network, so each
confirmation makes reversal more expensive. A custodian’s policy sets
how many confirmations it waits for before it treats a receipt as final;
six is the customary figure for large Bitcoin transfers.

**Regtest** is a Bitcoin Core mode for local testing. Proof of work is
trivial, blocks are mined on command (`generatetoaddress`), and the
coins have no value. Newly mined coins can be spent only after 100
further blocks, which is why the demo mines 101 blocks before it funds
the custody address.

**Recap.** Valid transactions wait in the mempool until a miner puts
them in a block; each block on top is another confirmation; regtest
makes blocks on demand.

<a id="formal-treatment"></a>

## Formal treatment

<a id="the-fix-leg"></a>

### The FIX leg

The demo speaks FIX 5.0 SP2 application messages on the FIXT.1.1 session
layer. The numbers in parentheses are FIX tag numbers.

- **Session.** `8=FIXT.1.1`; Logon carries `1137=9` (DefaultApplVerID =
  FIX50SP2, the application version for the whole session); sequence
  numbers start at 1 each session.
- **NewOrderSingle (D).** ClOrdID(11), Symbol(55), Side(54),
  TransactTime(60), OrderQty(38), OrdType(40)=2 for a limit order,
  Price(44).
- **ExecutionReport (8), fills.** ExecType(150)=F (trade) and
  OrdStatus(39)=2 (filled), with OrderID(37), ExecID(17), ClOrdID(11),
  LastQty(32), LastPx(31), CumQty(14), LeavesQty(151), TradeDate(75) and
  TransactTime(60).
- **No AvgPx(6).** It is optional in 5.0 SP2, and an average is a
  derived number: a second source of truth that can disagree with the
  fills. The receiver computes what it needs from LastQty(32) and
  LastPx(31).

Settlement consumes fills only; nothing downstream of the trading module
parses FIX.

<a id="netting"></a>

### Netting

For fills $f$ with side $\sigma_f = +1$ (buy) or $-1$ (sell), quantity
$q_f$ and price $p_f$:

$$
\Delta_{\text{base}} = \sum_f \sigma_f q_f, \qquad \Delta_{\text{quote}} = -\sum_f \sigma_f q_f p_f .
$$

$\Delta_{\text{base}}$ is the change in the client’s bitcoin and
$\Delta_{\text{quote}}$ the change in its dollars.
$\Delta_{\text{base}} < 0$ means the client owes the exchange
$|\Delta_{\text{base}}|$ BTC, which the custodian sends on chain. The
quote leg (USD) settles over fiat rails and is out of scope here.

<a id="taproot-outputs-and-the-bip86-tweak"></a>

### Taproot outputs and the BIP86 tweak

A Taproot output locks coins to an x-only key $Q$: the scriptPubKey is
`OP_1 <Q>` (34 bytes). $Q$ is not the FROST group key $P$ itself but $P$
**tweaked**:

$$
Q = P + t\,G, \qquad t = H_{\text{TapTweak}}(P_x) .
$$

Taproot lets a key commit to a tree of alternative spending scripts by
folding the tree’s hash into the tweak. With no script tree, as here,
the tweak is the tagged hash of $P$’s $x$-coordinate alone: this is
BIP86. Its purpose is assurance. Anyone who knows $P$ can recompute $Q$
and confirm that no script tree was folded in, so nobody, including
whoever ran the key generation, can later spend through a hidden script.

The signers must sign for $Q$, not $P$. Because $Q = P + tG$, the
private key for $Q$ is $d + t$, with BIP340’s sign adjustment if a point
has an odd $y$ ([chapter 1](01-foundations.md)); the FROST crate shifts
the shares accordingly (`sign_with_tweak`). Three independent
implementations compute $Q$ in the demo and must agree:

- the Rust crate;
- `settlement/bitcoin.py`;
- Bitcoin Core, via the descriptor `tr(P)`.

<a id="what-a-key-path-signature-signs-the-bip341-sighash"></a>

### What a key-path signature signs: the BIP341 sighash

The signature is over

$$
m = H_{\text{TapSighash}}(\,0\text{x}00 \,\|\, \text{hash\_type} \,\|\, \text{version} \,\|\, \text{locktime}
\,\|\, h_{\text{prevouts}} \,\|\, h_{\text{amounts}} \,\|\, h_{\text{scripts}} \,\|\, h_{\text{sequences}}
\,\|\, h_{\text{outputs}} \,\|\, \text{spend\_type} \,\|\, \text{input\_index})
$$

for the default hash type. Each $h$ is a SHA-256 over one field from
every input or output: all the outpoints, all the amounts, all the
locking scripts, all the sequence numbers, all the outputs. It commits
to the amount and script of *every* input being spent, not just the one
being signed. A signer that is told the input values can therefore trust
the fee it is signing, because a lie about any input’s value produces a
different sighash and an invalid signature (Exercise 3). The witness for
a key-path spend is the single 64-byte signature.

<a id="binding-the-transaction-to-the-instruction"></a>

### Binding the transaction to the instruction

Before the policy engine authorises a sighash, the settlement layer
checks the transaction (`transfer.check_matches`):

- it pays exactly the instructed amount to the instructed address;
- every other output returns to the custody key;
- the fee, computed from the input minus the outputs, is within a cap.

The authorisation then names that sighash, and every signer compares it
with the message inside its FROST signing package ([chapter
4](04-policy.md)).

<a id="worked-example"></a>

## Worked example

Four fills in one cycle, the same as in “Many fills, one delivery”:

| ClOrdID | Side | Qty (BTC) | Price (USD) | $\sigma q$ | $-\sigma q p$   |
|---------|------|-----------|-------------|------------|-----------------|
| C1      | sell | 0.40      | 64,000      | −0.40      | +25,600.00      |
| C2      | buy  | 0.15      | 63,950.50   | +0.15      | −9,592.575      |
| C3      | sell | 0.35      | 64,010      | −0.35      | +22,403.50      |
| C4      | sell | 0.25      | 64,020      | −0.25      | +16,005.00      |
| **Net** |      |           |             | **−0.85**  | **+54,415.925** |

The client delivers 0.85 BTC, which is 85,000,000 satoshis, and receives
USD 54,415.925 over fiat rails. The transaction has one input and two
outputs (payment and change). The builder estimates its size as 11 bytes
of fixed overhead, 58 for the key-path input and 43 for each output:
$(11 + 58 + 2 \cdot 43) = 155$ virtual bytes. At 2 satoshis per virtual
byte the fee is 310 satoshis. Spending a 5.00 BTC UTXO leaves change of
$500{,}000{,}000 - 85{,}000{,}000 - 310 = 414{,}999{,}690$ satoshis. The
demo charges the fee to alpha-capital, the client being settled, so the
custody address holds client coins only ([chapter 8](08-industry.md)).

The cell runs the real FIX session against the toy exchange and nets the
fills it returns:

``` python
from decimal import Decimal

from custody_lab.settlement import bitcoin, transfer
from custody_lab.settlement.netting import net
from custody_lab.trading.fix import Order, trade

orders = [
    Order("C1", "BTC-USD", "sell", Decimal("0.40"), Decimal("64000")),
    Order("C2", "BTC-USD", "buy", Decimal("0.15"), Decimal("63950.50")),
    Order("C3", "BTC-USD", "sell", Decimal("0.35"), Decimal("64010")),
    Order("C4", "BTC-USD", "sell", Decimal("0.25"), Decimal("64020")),
]
fills, transcript = trade(orders)
position = net(fills)
assert position.base == Decimal("-0.85") and position.quote == Decimal("54415.925")
amount = bitcoin.to_sats(-position.base)
fee = bitcoin.estimated_vsize(1, 2) * 2
assert (amount, fee, 500_000_000 - amount - fee) == (85_000_000, 310, 414_999_690)
print(f"net {position.base} {position.base_asset}, {position.quote} {position.quote_asset}")
```

    net -0.85 BTC, 54415.925 USD

<a id="code-walkthrough"></a>

## Code walkthrough

<a id="the-fix-session"></a>

### The FIX session

The transcript of the session above, one line per message: who sent it,
the message type (35), the sequence number (34), and the application
fields that matter.

``` python
KEEP = {"35", "34", "1137", "11", "54", "38", "44", "150", "39", "32", "31"}
for raw in transcript:
    fields = dict(pair.split("=", 1) for pair in raw.strip("|").split("|"))
    who = "client  ->" if fields["49"] == "CUSTODY-CLIENT" else "exchange->"
    shown = " ".join(f"{t}={v}" for t, v in fields.items() if t in KEEP)
    print(who, shown)
print("BeginString:", transcript[0].split("|")[0])
```

    client  -> 35=A 34=1 1137=9
    exchange-> 35=A 34=1 1137=9
    client  -> 35=D 34=2 11=C1 54=2 38=0.4 44=64000
    exchange-> 35=8 34=2 11=C1 150=F 39=2 54=2 38=0.4 32=0.4 31=64000
    client  -> 35=D 34=3 11=C2 54=1 38=0.15 44=63950.5
    exchange-> 35=8 34=3 11=C2 150=F 39=2 54=1 38=0.15 32=0.15 31=63950.5
    client  -> 35=D 34=4 11=C3 54=2 38=0.35 44=64010
    exchange-> 35=8 34=4 11=C3 150=F 39=2 54=2 38=0.35 32=0.35 31=64010
    client  -> 35=D 34=5 11=C4 54=2 38=0.25 44=64020
    exchange-> 35=8 34=5 11=C4 150=F 39=2 54=2 38=0.25 32=0.25 31=64020
    client  -> 35=5 34=6
    exchange-> 35=5 34=6
    BeginString: 8=FIXT.1.1

The first two lines are the Logon exchange (35=A), each carrying
`1137=9`. Then each NewOrderSingle (35=D) is followed by the exchange’s
ExecutionReport (35=8) with ExecType 150=F and OrdStatus 39=2: a full
fill, at the order’s price (LastPx, 31) and quantity (LastQty, 32). The
session ends with a Logout (35=5) in each direction.

<a id="settling-on-regtest"></a>

### Settling on regtest

The full path on a throwaway regtest node:

1.  The cluster runs DKG, and three implementations agree on the custody
    address.
2.  The custody address is funded with 5.00 BTC.
3.  The policy engine approves the net instruction.
4.  The builder’s transaction is checked against the instruction.
5.  Two of three signer processes sign the authorised sighash.
6.  Bitcoin Core accepts and mines the transaction.

``` python
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from custody_lab.foundations import schnorr
from custody_lab.mpc.cluster import SigningCluster
from custody_lab.policy.audit import AuditLog
from custody_lab.policy.authorisation import AuthorityKey
from custody_lab.policy.engine import AssetPolicy, Policy, PolicyEngine, Tier
from custody_lab.policy.model import Approval, SettlementInstruction
from custody_lab.settlement import chain
from custody_lab.settlement.regtest import RegtestNode


def now() -> datetime:
    return datetime.now(UTC)


approvers = {n: Ed25519PrivateKey.generate() for n in ("bob", "carol")}
node = RegtestNode(Path(tempfile.mkdtemp(prefix="ch5-")) / "node")
rpc = node.start()
rpc.call("createwallet", "exchange")
exchange = rpc.wallet("exchange")
mine_to = exchange.call("getnewaddress")
rpc.call("generatetoaddress", 101, mine_to)
settle_to = exchange.call("getnewaddress", "", "bech32")  # the exchange's address

btc = AssetPolicy(
    (Tier(Decimal("10"), 2),), frozenset({settle_to}), timedelta(hours=24), Decimal("20")
)
policy = Policy({"BTC": btc}, {n: k.public_key() for n, k in approvers.items()})
engine = PolicyEngine(policy, AuthorityKey.generate(), AuditLog(now), now)

# 1. DKG; three implementations agree on the custody address.
cluster = SigningCluster(2, 3, authority=engine.authority_public_key)
internal = cluster.dkg()
output_key = cluster.taproot_output_key()
address = chain.custody_address(rpc, internal)
assert output_key == bitcoin.taproot_tweak(internal)
assert chain.script_pubkey(rpc, address) == bitcoin.p2tr_script(output_key)
print("custody address:", address[:24] + "...", "(Rust = Python = Core)")

# 2. Fund it.
exchange.call("sendtoaddress", address, "5.00")
rpc.call("generatetoaddress", 1, mine_to)

# 3-4. Instruction, transaction, check, authorisation.
ins = SettlementInstruction("settle-1", "BTC", -position.base, settle_to, "ops", now())
destination = chain.script_pubkey(rpc, settle_to)
change = bitcoin.p2tr_script(output_key)
utxos = chain.custody_utxos(rpc, output_key)
stx = transfer.build(utxos, amount, destination, change)
transfer.check_matches(stx, amount, destination, change, max_fee=10_000)
approvals = [Approval.create(ins, n, k) for n, k in approvers.items()]
token = engine.authorise(ins, approvals, stx.sighash()).to_bytes()

# 5. Two of three signer processes sign; 6. Core accepts and mines.
signature = cluster.sign(stx.sighash(), [1, 3], token, taproot=True)
assert schnorr.verify(stx.sighash(), output_key, signature)
txid = rpc.call("sendrawtransaction", stx.finalize(signature))
rpc.call("generatetoaddress", 1, mine_to)
tx_info = rpc.call("getrawtransaction", txid, True)
left = [str(bitcoin.to_btc(u.amount)) for u in chain.custody_utxos(rpc, output_key)]
cluster.close()
node.stop()

print("sighash:", stx.sighash().hex()[:32] + "...")
print("txid:   ", txid[:32] + "...", f"fee {stx.fee} sats")
print("confirmations:", tx_info["confirmations"])
print("custody UTXOs after settlement:", left)
```

    custody address: bcrt1p82kwh5nf3mrnc8rqal... (Rust = Python = Core)
    sighash: 8db864cd37da24d7dc1777c7a1976894...
    txid:    72e2eee479dd3f2702f050492a4b81eb... fee 310 sats
    confirmations: 1
    custody UTXOs after settlement: ['4.1499969']

Reading the output from the top: the custody address begins `bcrt1p`, a
regtest Taproot address, and the Rust crate, the project’s Python and
Bitcoin Core all derived it identically. The sighash is the 32 bytes the
authorisation named and the signers signed. The txid is the identifier
Bitcoin Core assigned when it accepted the transaction. One confirmation
means one block was mined on top. The custody address now holds one coin
of 4.1499969 BTC: the change.

<a id="how-this-shows-up-in-production"></a>

## How this shows up in production

**Off-exchange networks.** Copper’s ClearLoop launched in 2022. Assets
are delegated from the client’s custody account to a trading allocation,
exchanges post collateral with the custodian, and settlement runs on
multi-hour cycles. The agreement between client, exchange and custodian
defines who may instruct a settlement and what happens if one side does
not deliver. Several other custodians run comparable networks (**verify
current**).

**Settlement cycle length is a risk dial.** Shorter cycles mean less
unsettled exposure, but more on-chain transactions and fees. Longer
cycles net better and leave more exposure open.

**Fees.** Production wallets estimate fees from the current mempool
instead of using a fixed rate. To unstick a transaction they use
replace-by-fee (the demo’s inputs signal it), or child-pays-for-parent,
in which a new transaction spending the stuck one’s change pays a fee
high enough for both. And they enforce a fee cap, as `check_matches`
does.

**Finality.** Six confirmations is the customary Bitcoin threshold for
large transfers. The settlement system must also handle chain
reorganisations, in which recent blocks are replaced and a confirmed
transaction can drop back to unconfirmed.

**Signer-side verification.** Here the settlement layer checks the
transaction and the signers check only the sighash. A production signer
decodes the transaction itself (PSBT, BIP 174 and 370, is the usual
interchange format for unsigned transactions) and re-applies the
destination and fee rules. That removes the settlement host from the set
of components that must be trusted.

**UTXO management.** One large UTXO per settlement is simple but
serialises settlements, because each must wait for the previous one’s
change. Production systems keep a pool of UTXOs, consolidate them when
fees are low, and avoid reusing addresses, for privacy.

<a id="recap"></a>

## Recap

1.  Pre-funding an exchange makes the client an unsecured creditor if
    the exchange fails; off-exchange settlement keeps assets with the
    custodian and moves only the net each cycle.
2.  Netting turns a cycle’s fills into one obligation per asset: the
    demo’s four fills net to 0.85 BTC owed to the exchange.
3.  Bitcoin has no balances: a transaction spends whole UTXOs and
    creates new outputs, including change, and the difference is the
    fee, which `check_matches` caps.
4.  A Taproot output is locked to one x-only key; the key-path witness
    is one 64-byte BIP340 signature; BIP86 tweaks the key to prove there
    is no hidden script path.
5.  The signature covers the sighash, which commits to every input’s
    amount and script and every output; one sighash authorises one
    transaction.
6.  The settlement layer checks the transaction against the instruction
    before the policy engine authorises its sighash, and Bitcoin Core
    accepts the signed result.

[Chapter 6](06-reserves.md) takes the custody address after this
settlement and publishes a proof that it still holds what the clients
are owed.

<a id="exercises"></a>

## Exercises

1.  **Compute.** Add a fifth fill, buy 0.9 BTC at 64,100. What is the
    net obligation, and which direction does BTC move?
2.  **Compute.** A settlement of 0.3 BTC spends a 0.30000500 BTC UTXO at
    2 sat/vB. What outputs does `transfer.build` produce, and what is
    the fee?
3.  **Explain.** Why does the BIP341 sighash commit to the amounts of
    all inputs, when SegWit v0 committed only to the amount of the input
    being signed?
4.  **Attack.** A compromised settlement host builds a transaction that
    pays the approved 0.85 BTC to the approved address and sends 0.01
    BTC back to the custody key, leaving the rest of a 5.00 BTC input as
    fee. Which check stops it, and what would happen without that check?
5.  **Design.** The exchange fails between two settlement cycles, owing
    the client 2 BTC from the last cycle. What protects the client under
    the off-exchange model, and what does not?

<a id="solutions"></a>

## Solutions

1.  Net base $= -0.85 + 0.9 = +0.05$: the exchange owes the client 0.05
    BTC, so BTC moves from the exchange to the custody address. The
    custodian signs nothing; it confirms receipt.
2.  Input 30,000,500 sats; payment 30,000,000; fee estimate 310; change
    $30{,}000{,}500 - 30{,}000{,}000 - 310 = 190$ sats, below the
    330-sat dust limit. So the transaction has one output, and the fee
    is $310 + 190 = 500$ sats.

``` python
u = transfer.Utxo("ab" * 32, 0, 30_000_500, bitcoin.p2tr_script(b"\x11" * 32))
s = transfer.build([u], 30_000_000, b"\x00\x14" + b"\x22" * 20, u.script_pubkey)
assert len(s.tx.outputs) == 1 and s.fee == 500
```

3.  Under SegWit v0 a signer saw only its own input’s amount. An
    attacker could lie about the value of the other inputs to an offline
    or hardware signer and make it sign a transaction with a much larger
    fee than it believed. Committing to every input’s amount and script
    makes a lie produce an invalid signature.
4.  `check_matches` computes the fee as
    $500{,}000{,}000 - 85{,}000{,}000 - 1{,}000{,}000 = 414{,}000{,}000$
    sats and rejects it against the 10,000-sat cap. Without the cap the
    policy engine would authorise that sighash and the signers would
    sign it. About 4.14 BTC would go to whichever miner included the
    transaction, while every destination and amount check passed.
5.  What protects the client:
    - Its custodied assets never left the custodian, so they are not
      part of the exchange’s estate.
    - Collateral the exchange posted with the custodian can cover the 2
      BTC owed, depending on the agreement.

    What does not:
    - Anything the exchange owed beyond its posted collateral.
    - Fiat legs held at the exchange.
    - Positions opened since the last settlement.

    The exposure is bounded by one cycle, not by the whole account.

<a id="further-reading"></a>

## Further reading

- BIP 341 (Taproot), BIP 86 (key-path-only outputs), BIP 350 (bech32m).
  The rules implemented in `settlement/bitcoin.py`, with the test
  vectors it passes.
- BIP 174 and BIP 370 (PSBT). The format production signers exchange
  unsigned transactions in.
- FIX Trading Community, FIX 5.0 SP2 and FIXT.1.1 specifications.
- Copper, *ClearLoop* product documentation (**verify current**).
- A. Antonopoulos, D. Harding, *Mastering Bitcoin*, 3rd edition
  (O’Reilly, 2023), chapters on transactions and Taproot.

------------------------------------------------------------------------

Previous: [Chapter 4, Policy and Authorisation](04-policy.md) \| [All
chapters](../README.md) \| Next: [Chapter 6, Proof of
Reserves](06-reserves.md)
