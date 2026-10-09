# Module 10: Custody in Practice: Custodians, Assets, Losses and the Frontier

2026-10-09

Previous: [Chapter 9, Capstone](09-capstone.md) \| [All
chapters](../README.md)

> [!WARNING]
>
> ### EDUCATIONAL, NOT PRODUCTION
>
> The cells in this chapter run the demo’s own code: the teaching
> signature modules of [chapter 1](01-foundations.md), the attack
> panel’s signing cluster (Zcash Foundation `frost-secp256k1-tr` through
> `custody_frost`) and the reserves tree. Statements about companies,
> assets and incidents come from public sources read on 2026-10-09,
> listed under Further reading. Each is **reported**, not checked by
> this project, and anything that changes over time is marked **verify
> current**.

<a id="what-this-chapter-is-for"></a>

## What this chapter is for

Chapters [0](00-orientation.md) to [9](09-capstone.md) build one custody
design and run it. Anyone who presents it will be asked four questions
it does not answer by itself. How do the custodians that hold billions
protect their keys? Can this design hold ether, solana or a stablecoin,
and what changes if it does? What has actually gone wrong for
custodians, and would this design have stopped it? And what is coming
next?

This chapter answers each from public sources, and ties each answer to
the chapter that explains the mechanism. Its central finding is
uncomfortable and useful: the large losses of 2025 and 2026 examined
here did not come from stolen keys. The keys were intact, the approvals
were real, and the transactions were signed correctly. What failed was
the check of what was being approved.

By the end of this chapter the following should be clear:

- the three ways leading custodians keep keys today, and where each puts
  the approval quorum;
- why the signature rule of each chain decides what a custodian’s
  signing system must produce, and which other rules differ from chain
  to chain;
- what the large recent losses have in common, and which of the demo’s
  controls address it and which do not;
- why proven threshold protocols have still been broken in practice;
- what is being standardised now, for threshold signing on Bitcoin and
  for the quantum transition.

<a id="first-principles"></a>

## First principles

<a id="three-ways-to-keep-a-key"></a>

### Three ways to keep a key

**The problem.** [Chapter 3](03-key-storage.md) compared hardware
security modules, MPC and secure enclaves in principle. A reader will
want to know which of them the custodians that hold the most actually
use, and the answer is not one of them: all three are in production,
often combined.

**The idea in plain words.** A custodian has to decide two things: where
the key lives, and where the approval quorum is checked before the key
is used. Three arrangements are in use.

1.  **The whole key inside a hardware security module, which checks the
    approvals itself.** Anchorage Digital’s documentation says private
    key material “is generated and processed in air-gapped HSMs” and is
    “not exported outside the HSM boundary in plaintext”, and that the
    HSMs “process the transaction only when both the organization and
    Anchorage Digital have approved”. Each approver’s identity key is
    “created and stored in the iOS Secure Enclave”. The page does not
    mention MPC. The approval quorum is enforced by the same hardware
    that holds the key.
2.  **Key shares in separate places, combined by an MPC protocol.**
    Fireblocks states that it uses MPC-CMP, an “open-source and
    peer-reviewed algorithm”, that the “key shares are implemented
    across multiple Trusted Execution Environments (Intel SGX)”, and
    that “at no point does Fireblocks have enough key shares to
    unilaterally sign a transaction”. The approval quorum is a policy
    layer in front of the signers, as in this demo.
3.  **Encrypted keys, released by several approvers together.**
    Coinbase’s annual report for 2025 says that “wallet private keys are
    never stored in plaintext format in any location”, that “the
    cryptographic consensus of multiple human approvers is required to
    decrypt a private key for both hot and cold wallets”, that its
    custody company’s assets are managed “using a proprietary
    combination of software and hardware security modules”, and that it
    seeks “to hold no more than 2% of assets under custody in hot
    wallets”. The part of the report read for this chapter does not say
    whether the custody company signs with MPC.

The counterpart in a bank is the vault. Arrangement 1 is a vault whose
lock checks two officers’ cards before it opens; arrangement 2 is a
combination split between officers, never written down whole;
arrangement 3 is a sealed envelope that opens only when several officers
sign for it. The comparison stops at what an opened vault gives away. A
bank vault holds cash that can be counted and recovered; a used key can
sign anything, so in all three arrangements the key must never be usable
outside the approved path.

**How the demo compares.** The demo is arrangement 2: three shares in
three processes, the policy engine as the approval layer, and each
signer checking the policy’s authorisation itself ([chapter
4](04-policy.md)). What it leaves out is the protection around each
share ([chapter 3](03-key-storage.md)): its three processes run on one
computer.

| Arrangement | Where the key lives | Where the quorum is checked | Example (reported) |
|----|----|----|----|
| Key inside an HSM | Whole, inside air-gapped hardware | Inside the HSM | Anchorage Digital |
| MPC shares | Split; never whole | A policy layer before the signers | Fireblocks; this demo |
| Encrypted key | Whole, encrypted; HSMs | The approvers who decrypt it | Coinbase (as described) |

**Recap.** All three arrangements keep the key out of any one person’s
reach; they differ in where the approval is enforced. The next sections
show that this placement, not the key’s storage, is where the recent
losses happened.

<a id="what-each-asset-asks-of-a-custodian"></a>

### What each asset asks of a custodian

**The problem.** The demo holds bitcoin and signs Bitcoin transactions.
A custodian holding the largest assets must produce the signature each
chain checks, and must follow rules that differ from chain to chain:
some of them decide whether a payment arrives at all.

**The idea in plain words.** A chain checks every transaction against
one fixed signature rule. A signature made under any other rule is
refused, however valid it is under its own. So a custodian needs one
signing protocol per rule it serves, and a threshold version of each if
it uses MPC. Two families of curve cover most large assets: secp256k1,
Bitcoin’s curve, used with ECDSA by Ethereum and most chains derived
from it; and Curve25519, used with Ed25519 by Solana, Cardano and
others. This is why MPC products ship one protocol for ECDSA and one for
EdDSA.

Beyond the signature, chains differ in how they record balances.
Bitcoin’s coins are separate outputs, spent whole ([chapter
5](05-settlement.md)). Ethereum, Solana, XRP and most others use an
**account model**: each address has one balance, and each transaction
carries a counter or reference that fixes its order and, on some chains,
how long it stays valid.

**Worked example: one key, two rules.** The cell below takes one secret
key and signs one message with BIP340 Schnorr, the rule Bitcoin’s
Taproot outputs check. It then presents the same 64 bytes to the ECDSA
rule, as an Ethereum node would check them, under the same key. Finally
it makes a real ECDSA signature with the same key.

``` python
import hashlib

from custody_lab.foundations import ecdsa, schnorr
from custody_lab.foundations.ec import SECP256K1

d = 0xC0FFEE                           # one secret key
seckey = d.to_bytes(32, "big")
Q = SECP256K1.mul(d, SECP256K1.G)      # its public point
message = hashlib.sha256(b"pay 0.85 BTC to the exchange").digest()
z = ecdsa.hash_to_int(message)

taproot = schnorr.sign(message, seckey, aux_rand=bytes(32))
as_ecdsa = ecdsa.Signature(int.from_bytes(taproot[:32], "big"),
                           int.from_bytes(taproot[32:], "big"))
ethereum = ecdsa.sign(d, z)

checks = {
    "Schnorr signature, Schnorr rule":
        schnorr.verify(message, schnorr.pubkey_gen(seckey), taproot),
    "the same 64 bytes, ECDSA rule": ecdsa.verify(Q, z, as_ecdsa),
    "ECDSA signature, ECDSA rule": ecdsa.verify(Q, z, ethereum),
}
for name, ok in checks.items():
    print(f"{name:<34}{'accepted' if ok else 'refused'}")
assert list(checks.values()) == [True, False, True]
```

    Schnorr signature, Schnorr rule   accepted
    the same 64 bytes, ECDSA rule     refused
    ECDSA signature, ECDSA rule       accepted

The first line is the demo’s case: a Schnorr signature checked by the
Schnorr rule. The second shows the same bytes refused by the ECDSA rule,
although the key is the same: the demo’s FROST cluster could not sign
for an Ethereum account. The third shows that the key itself is not the
obstacle: the ECDSA rule accepts an ECDSA signature from it. Holding
ether with MPC therefore needs a threshold ECDSA protocol ([chapter
2](02-mpc-custody.md) describes Lindell 2017 and CGGMP), not FROST.

Three rules in the table below change what a custodian must do, so they
are defined here. To be **slashed** is to lose part of a staked balance
as a penalty, because the validator’s key signed two conflicting
messages; a staking key run on two machines at once can do that by
accident. A **destination tag** is a number attached to a payment that
tells a shared address which client it is for; a deposit sent without it
arrives but cannot be credited to anyone until it is traced. A **durable
nonce** is a Solana feature that lets a signed transaction stay valid
until it is used, instead of expiring within about a minute and a half:
convenient for offline signing, and, as the next section shows,
dangerous. Stablecoin issuers keep a **freeze function** in the token’s
contract: Circle’s terms reserve the right “to block the transfer of
USDC to and from an address on chain”, and Tether’s Ethereum contract
includes `addBlackList` and `destroyBlackFunds`. A custodian’s books can
therefore show a balance it is unable to deliver.

**The largest assets.** CoinGecko’s ranking by market value, read on
2026-10-09 at 09:27 UTC, begins Bitcoin, Ether, Tether (USDT), BNB, XRP,
USDC, Solana and TRON (**verify current**). The table summarises what
each asks of a custodian, from the sources under Further reading.

| Asset | Signature rule | Ledger | A rule that changes custody (reported) |
|----|----|----|----|
| BTC | ECDSA, or BIP340 Schnorr for Taproot | Coins (UTXO) | The fee is whatever the inputs leave over; nothing expires |
| ETH | ECDSA on secp256k1 | Accounts | Each account’s nonce orders its transactions; staking keys are a separate BLS key, and a validator can be slashed |
| USDT, USDC | As the chain each is issued on | Tokens | The issuer can freeze an address’s balance |
| XRP | ECDSA by default; Ed25519 supported | Accounts | A destination tag names the client inside a shared address; an account keeps a reserve it cannot spend |
| SOL | Ed25519 | Accounts | A transaction expires within about a minute and a half unless it uses a durable nonce; accounts keep a minimum balance |

**What breaks when it is done wrong.** A custodian that treats every
chain like Bitcoin loses money in ways that have nothing to do with
keys: a deposit without its tag sits unattributed, a client cannot
withdraw a balance that must stay as a reserve, a staking key run twice
is slashed, and a frozen stablecoin balance is counted as an asset.

**Recap.** The chain chooses the signature rule, so the custodian’s
signing system must produce it: FROST for Taproot, threshold ECDSA for
Ethereum-family accounts, threshold EdDSA for Solana. And each chain
adds rules that the policy engine and the ledger must model.

<a id="approved-but-wrong"></a>

### Approved, but wrong

**The problem.** Every control in this demo protects the key and the
approval. Yet the four largest losses this chapter examines, from
February 2025 to September 2026, did not involve a stolen key or a
forged approval.

**What happened, as reported.**

- **Bybit, February 2025.** The FBI attributed the theft of
  “approximately \$1.5 billion USD in virtual assets” to North Korea’s
  TraderTraitor group. Safe, whose multisig wallet Bybit used, reported
  that the attack came through “a compromised Safe{Wallet} developer
  machine”; an analysis described “injecting malicious JavaScript into
  app.safe.global, which was accessed by Bybit’s signers”. Bybit
  described the transaction its signers approved as “a scheduled move of
  ETH from our ETH Multisig Cold Wallet to our Hot Wallet”, which had
  been manipulated by an attack that “masked the signing interface”. It
  gave the attacker control of the cold wallet.
- **Drift Protocol, April 2026.** At least \$280 million was lost after
  the attacker obtained “2/5 multisig approvals from Security Council
  members”. The attacker “leveraged durable nonce accounts and
  pre-signed transactions to delay execution”.
- **Bitget, September 2026.** \$387.5 million moved to
  attacker-controlled addresses. The company said the attacker “had
  compromised a critical backend system within Bitget’s wallet
  infrastructure” and “spoofed transaction data and invoked the
  authorization process”; “private keys were not compromised”.
- **Liquid Network, September 2026.** About 4,000 L-BTC, bitcoin on
  Blockstream’s sidechain, were minted without bitcoin behind them. The
  analysis read for this chapter attributes it to “a cache-key collision
  vulnerability” in the range-proof verification code, after which “the
  attacker was able to use the legitimate peg-out process” to exchange
  them for bitcoin.

**The idea in plain words.** Each loss passed through a working
approval. At Bybit the signers approved what their screen showed them,
and the screen had been changed: **blind signing**, approving data one
cannot read for oneself. At Drift real approvals were collected and
held, and because the transactions never expired, they were a standing
permission waiting to be used. At Bitget the authorisation process was
fed spoofed data by a system it trusted. At Liquid no key and no
approval was involved at all: a verification bug created a liability
with nothing behind it, and the normal exit paid it out.

The counterpart is invoice fraud in corporate payments: an approver
signs off a payment to a supplier whose bank details were changed in the
invoice. The defence is the same: confirm what is being paid, and to
whom, through a channel the requester does not control. The comparison
stops at recall: a bank can sometimes reverse a fraudulent transfer; a
confirmed blockchain payment stays where it went.

**What the demo does about each.** Four of the demo’s controls answer
these cases directly, and one does not.

1.  *What the approval covers.* The policy engine authorises the
    transaction’s sighash, computed by the settlement code from the
    instruction ([chapter 5](05-settlement.md)), not anything a screen
    displays; and each signer checks that it is asked to sign exactly
    that sighash. A transaction swapped after approval is refused by the
    signers.
2.  *How long an approval lasts.* An authorisation is valid for 60
    seconds and once only ([chapter 4](04-policy.md)). A Drift-style
    held approval expires; a replay is refused.
3.  *Whether the books match the chain.* Reconciliation after every
    movement and the proof of reserves ([chapter 6](06-reserves.md) and
    the walkthrough’s day) catch a liability with no coins behind it.
4.  *Independent people.* The approval and signing quorums are separate
    ([chapter 0](00-orientation.md), “Two quorums”).

What the demo does not answer is Bitget’s case. Its approvers sign the
instruction that ops-desk raises, as built by the custodian’s own
systems. If the system that builds the instruction is compromised, the
approvers approve the attacker’s instruction. The defences lie outside
this demo: showing each approver the decoded destination and amount on a
device of their own, and checking destinations against records the
requesting system cannot write.

The first cell runs two of the attack panel’s attempts against the real
signing cluster: a transaction swapped after approval, and an
authorisation used five minutes after it was issued.

``` python
import re

from custody_lab.demo import attacks


def per_signer(reason: str) -> list[str]:
    lines = reason.split("; ")
    return [re.sub(r"^(signer \d+): \w+\('(.*)'\)$", r"\1: \2", x)
            for x in lines]


with attacks.lab() as setup:
    swapped = attacks.swap_the_transaction_after_approval(setup)
    stale = attacks.use_an_expired_authorisation(setup)

print("A transaction swapped after approval:")
for line in per_signer(swapped):
    print("  " + line)
print("An authorisation used five minutes after it was issued:")
for line in per_signer(stale):
    print("  " + line.split(" at ")[0])
assert "differs from the authorised message" in swapped
assert "expired" in stale
```

    A transaction swapped after approval:
      signer 1: signing package message differs from the authorised message
      signer 3: signing package message differs from the authorised message
    An authorisation used five minutes after it was issued:
      signer 1: expired
      signer 3: expired

Under the first heading, signers 1 and 3 each refuse to sign a message
other than the one the authorisation names. Under the second, the same
signers refuse an authorisation past its lifetime. Neither refusal needs
the coordinator’s cooperation: each signer process checks for itself.

The second cell is Liquid’s lesson on the demo’s own ledger. It credits
delta-trading with 0.40 BTC that never arrived on chain, as a
verification bug would, and compares the books with the 5.00 BTC the
custody address holds.

``` python
from decimal import Decimal

from custody_lab.demo.pipeline import LEDGER
from custody_lab.reserves.merkle_sum import MerkleSumTree

held = Decimal("5.00")                       # coins at the custody address
books = dict(LEDGER)
print(f"books {MerkleSumTree(books).root.total:.2f} BTC, held {held} BTC")
books["delta-trading"] += Decimal("0.40")    # a credit with no coin behind it
owed = MerkleSumTree(books).root.total
ratio = (held / owed).quantize(Decimal("0.00001"))
print(f"books {owed:.2f} BTC, held {held} BTC, reserve ratio {ratio}")
assert ratio < 1
```

    books 5.00 BTC, held 5.00 BTC
    books 5.40 BTC, held 5.00 BTC, reserve ratio 0.92593

The first line is the demo’s starting position: the books and the chain
agree. The second shows the unbacked credit: the books now say 5.40 BTC,
the chain still holds 5.00, and the reserve ratio falls to 0.92593.
Every key and every approval is intact; only the comparison of books
with chain shows the gap.

**Recap.** A key that is safe and an approval that is genuine are
necessary, not sufficient. The approval must cover exactly what will be
signed, it must expire, the data it approves must come from a source the
requester cannot alter, and the books must be reconciled with the chain.
[Chapter 4](04-policy.md)’s policy engine and [chapter
6](06-reserves.md)’s proof of reserves are the demo’s versions of the
first, second and fourth.

<a id="when-the-proof-is-right-and-the-code-is-wrong"></a>

### When the proof is right and the code is wrong

**The problem.** [Chapter 2](02-mpc-custody.md) presents threshold
protocols with security proofs. Threshold ECDSA implementations used by
large wallet providers have nonetheless been broken, some so that a
single participant could take the whole key.

**What happened, as reported.** In August 2023 Fireblocks published
BitForge, “a series of zero-day vulnerabilities in some of the most
widely adopted implementations”, affecting “GG-18, GG-20, and
Lindell17”. In GG18 and GG20 implementations a “missing zero-knowledge
proof” allowed “exfiltrating the full private key”; “some
implementations are vulnerable to key extraction in 16 signatures”. In
Lindell17 implementations the key could be taken “after approximately
200 signature requests”. In the same month Verichains presented TSSHOCK
at Black Hat USA, stating that “most implementations of GG18, GG20, and
CGGMP21 are vulnerable” and demonstrating “a full private key extraction
by a single malicious party after 1-2 signatures”.

**The idea in plain words.** Threshold ECDSA is hard because ECDSA’s
signing equation multiplies secrets together, and multiplying shares
without revealing them needs encryption that can be computed on
(Paillier, [chapter 2](02-mpc-custody.md)) and proofs that each party
used it honestly. The breaks were in those proofs and parameter checks:
a check left out, or a proof that could be satisfied dishonestly. The
signature scheme was never broken; the code around it was. Schnorr-based
FROST, which the demo uses, has no Paillier step, because Schnorr’s
signing equation is linear in the secret ([chapter
1](01-foundations.md)).

The counterpart is a trading venue’s matching engine: the matching rules
can be correct while an input-validation gap lets one participant
corrupt the book. The comparison stops at the consequence: here one
dishonest participant leaves with the key.

**Recap.** A protocol’s proof covers the protocol as written. An
implementation must perform every check the proof assumes, which is why
[chapter 0](00-orientation.md) insists that every from-scratch
implementation in this project be checked against an external oracle,
and why the demo signs with the Zcash Foundation’s crate rather than its
own FROST.

<a id="what-is-being-standardised"></a>

### What is being standardised

**The problem.** A design built today will run for years. Two changes
are under way that affect this one directly: how threshold Schnorr
signing is standardised for Bitcoin, and how Bitcoin and custodians
prepare for quantum computers.

**Threshold signing on Bitcoin.** RFC 9591 standardised FROST in 2024,
but a Bitcoin proposal for FROST signing, BIP 445, states that RFC 9591
“is incompatible with Bitcoin’s BIP340 X-only public keys”, and
specifies a variant that is; it is an open proposal, not yet merged
(**verify current**). The demo’s crate handles Taproot’s x-only keys
itself. Two neighbouring designs are relevant to a custodian. **MuSig2**
(BIP 327) aggregates the keys of every signer into one, so it is n-of-n:
every key holder must sign. **ROAST** is a wrapper around FROST that
keeps a signing session completing when some signers stall or misbehave,
so one unavailable node cannot block a payment. The library the demo
uses, `frost-core` 3.0.0, also ships share refresh and share repair
(observed in its source): the operations [chapter 2](02-mpc-custody.md)
teaches, now available in the same crate.

**The quantum transition.** BIP 360, “Pay-to-Merkle-Root”, is a draft
that keeps Taproot’s script tree but removes the key path, so that an
output’s public key is not on chain while coins wait in it; its authors
state it protects against “long exposure attacks” but “does not, by
itself, protect against short exposure quantum attacks”. BIP 361, also a
draft, proposes first forbidding payments to quantum-vulnerable
addresses, then, “five years after activation”, restricting ECDSA and
Schnorr spends to a quantum-safe rescue protocol. NIST’s first call for
multi-party threshold schemes (NIST IR 8214C, 2026) includes
post-quantum candidates, with a submission deadline “expected to be set
to 2027-Mar-01 (it will not be before)”. Both proposals and the call are
open (**verify current**). For a custodian, the demo’s Taproot key-path
outputs are exactly the outputs BIP 360 is written to avoid; [chapter
7](07-post-quantum.md) explains why, and why its authorisations already
carry an ML-DSA signature.

**Secure enclaves under physical attack.** Arrangement 2 above often
places shares inside secure enclaves. In October 2025 researchers from
Georgia Tech and Purdue published TEE.fail, a memory-bus interposer that
“should cost you under \$1000” and can “extract cryptographic keys from
Intel TDX and AMD SEV-SNP”; it needs physical access to the server. An
enclave’s attestation proves which code runs, under the vendor’s threat
model; a custodian’s threat model includes people with access to the
data centre ([chapter 3](03-key-storage.md)).

**Recap.** Bitcoin threshold signing is being standardised in a form
compatible with the Taproot keys the demo uses; Bitcoin’s quantum
proposals would retire the key-path outputs it relies on; and enclaves,
one of the three places custodians keep shares, have been shown open to
physical extraction.

<a id="how-this-shows-up-in-production"></a>

## How this shows up in production

The demo’s design choices map onto the industry’s as follows. Its shares
in separate processes are arrangement 2, which Fireblocks and others run
with shares in enclaves or on separate parties’ machines. Its
signer-side check of the policy’s authorisation is the control the Bybit
and Bitget losses lacked at the point of signing: the check that the
thing signed is the thing approved, computed from data the requester
could not alter. Its 60-second authorisation is the control the Drift
loss lacked: an approval that expires. Its reconciliation and proof of
reserves address the Liquid loss’s lesson: intact keys do not mean
intact reserves. What it does not model are the operational rules of
chains other than Bitcoin (tags, reserves, freezes, staking), the
protection of each share ([chapter 3](03-key-storage.md)), and the
independence of the approvers’ devices from the systems that build what
they approve.

<a id="recap"></a>

## Recap

1.  Leading custodians keep keys in three ways: whole inside HSMs that
    check approvals themselves, as MPC shares behind a policy layer, or
    encrypted and released by several approvers. The demo is the second.
2.  The chain fixes the signature rule. A Schnorr signature is refused
    where ECDSA is checked, from the same key, so a custodian needs one
    threshold protocol per rule it serves.
3.  Chains differ in rules that decide whether money arrives or can
    leave: destination tags, reserves, transaction lifetime, freezes and
    slashing.
4.  The largest recent losses passed through genuine approvals: blind
    signing at Bybit, held pre-signed transactions at Drift, spoofed
    data at Bitget, and an unbacked liability at Liquid. The approval
    must cover exactly what is signed, must expire, must rest on data
    the requester cannot alter, and the books must be reconciled with
    the chain.
5.  Threshold ECDSA implementations have been broken in the proofs
    around Paillier encryption; the signature schemes were not. FROST
    avoids that step.
6.  FROST for Bitcoin, Bitcoin’s quantum migration and threshold
    post-quantum signatures are all being standardised now (**verify
    current**).

<a id="exercises"></a>

## Exercises

1.  **Recall.** Name the three ways of keeping a key described in this
    chapter, and where each checks the approval quorum.
2.  **Compute.** The demo’s books show 5.00 BTC and the custody address
    holds 5.00 BTC. A bug credits two clients 0.25 BTC each with no
    coins behind them. What reserve ratio does the snapshot show?
3.  **Explain.** Why could the demo’s FROST cluster not sign for an
    Ethereum account, although it uses the same curve?
4.  **Apply.** A signing ceremony is collected on Monday for a payment
    that will be broadcast on Friday. Which control in the demo refuses
    it, and what would a custodian need instead if the delay were
    legitimate?
5.  **Design.** Bitget’s case: the system that builds instructions is
    compromised. Using only ideas from chapters [4](04-policy.md) and
    [9](09-capstone.md), propose two changes so that approvers would
    notice a spoofed destination.

<a id="solutions"></a>

## Solutions

1.  Inside an HSM, which checks the quorum itself (Anchorage, as
    reported); MPC shares, with the quorum checked by a policy layer
    before the signers (Fireblocks, this demo); and an encrypted key,
    with the quorum being the approvers whose consensus decrypts it
    (Coinbase, as described in its annual report).
2.  The books owe 5.00 + 0.25 + 0.25 = 5.50 BTC against 5.00 BTC held,
    so the ratio is 5.00 / 5.50 = 0.90909.
3.  The chain checks a signature rule, not just a key. Ethereum accounts
    check ECDSA; the cluster produces BIP340 Schnorr signatures. The
    cell `one-key-two-rules` shows the Schnorr signature refused by the
    ECDSA rule and an ECDSA signature from the same key accepted.
4.  The authorisation’s 60-second lifetime and single use: on Friday it
    has expired, so the signers refuse it. A legitimate delayed payment
    needs a new authorisation at the time of signing, with the approvals
    repeated or carried forward under a rule the policy states.
5.  First, the approvers sign the decoded destination and amount, shown
    on a device of their own, rather than an instruction digest built by
    the compromised system ([chapter 4](04-policy.md)’s approvals are
    already signatures over the instruction’s exact contents; the change
    is where the contents are displayed and checked). Second,
    destinations are checked against a whitelist that the
    instruction-building system cannot write, changed only through a
    separate, delayed registration (the walkthrough’s day: registered
    withdrawal addresses).

<a id="further-reading"></a>

## Further reading

All read on 2026-10-09. Company, regulatory and incident facts are
**verify current**.

- Anchorage Digital, documentation, “Security”:
  `docs.anchorage.com/knowledge-base/platform/users/security`.
- Fireblocks, “Security principles”: `fireblocks.com/principles`.
- Coinbase Global, Form 10-K for 2025, filed with the SEC (`sec.gov`,
  CIK 1679788).
- CoinGecko, `api.coingecko.com/api/v3/coins/markets`, ranking by market
  capitalisation, 2026-10-09 09:27 UTC.
- Circle, USDC terms (updated 12 December 2025), section 13,
  `circle.com/legal/usdc-terms`; Tether, `TetherToken` contract on
  Ethereum (the freeze functions).
- FBI, Public Service Announcement I-022625-PSA, 26 February 2025
  (Bybit).
- BleepingComputer, “Lazarus hacked Bybit via a breached Safe{Wallet}
  developer machine” (2025), and “Drift loses \$280 million” (2 April
  2026).
- The Block, report on Bitget’s wallet losses (24 September 2026).
- Halborn, “Explained: the Liquid Network hack” (September 2026).
- Fireblocks, “BitForge” (9 August 2023); Verichains, “TSSHOCK” (Black
  Hat USA, 10 August 2023).
- BIP 327 (MuSig2); BIP 445 pull request, “FROST Signing Protocol for
  BIP340 Signatures” (open); BIP 360, “Pay-to-Merkle-Root”; BIP 361,
  “Post Quantum Migration and Legacy Signature Sunset”.
- RFC 9591, “The Flexible Round-Optimized Schnorr Threshold (FROST)
  Protocol” (2024).
- T. Ruffing, V. Ronge, E. Jin, J. Schneider-Bensch, D. Schröder,
  “ROAST: Robust Asynchronous Schnorr Threshold Signatures”, ACM CCS
  2022.
- NIST IR 8214C, “First Call for Multi-Party Threshold Schemes” (2026),
  `csrc.nist.gov/projects/threshold-cryptography`.
- TEE.fail, `tee.fail` (Georgia Institute of Technology and Purdue
  University, October 2025).

------------------------------------------------------------------------

Previous: [Chapter 9, Capstone](09-capstone.md) \| [All
chapters](../README.md)
