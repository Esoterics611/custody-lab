# Module 2: MPC Custody

2026-10-10

Previous: [Chapter 1, Foundations](01-foundations.md) \| [All
chapters](../README.md) \| Next: [Chapter 3, Key
Storage](03-key-storage.md)

> [!WARNING]
>
> ### EDUCATIONAL, NOT PRODUCTION
>
> `custody_lab.mpc.paillier`, `lindell17`, `frost` and `dkg` are
> teaching code. The Lindell 2017 module omits the zero-knowledge proofs
> that make it safe against a cheating party. The demo’s signing path,
> `custody_lab.mpc.cluster`, uses the Zcash Foundation’s
> `frost-secp256k1-tr` crate. That crate is outside the scope of the NCC
> Group audit of the other ZF FROST crates.

<a id="what-this-chapter-is-for"></a>

## What this chapter is for

[Chapter 1](01-foundations.md) ended on a problem. Shamir sharing
protects a key while it is stored: three shares in three places, any one
of which is useless to a thief. But to sign, the shares had to be
combined into the key, and the machine that combined them held the whole
key for as long as signing took. Whoever controlled that machine,
through malware, an insider or a memory dump, would hold the key from
then on.

This chapter removes that machine. The technique is **secure multi-party
computation** (**MPC**): several programs, each holding a private input,
jointly compute an agreed result while each learns only the result. In
custody, the private inputs are key shares and the result is a
signature. [Chapter 0](00-orientation.md) showed the core of it with
school arithmetic: each signer computes a partial signature from its own
share, and the coordinator adds the partial signatures. This chapter
makes that work against real attackers, which takes three things
[chapter 0](00-orientation.md) skipped.

The first is how a key is born without ever existing whole, which is
distributed key generation. The second is how to sign when some of the
parties are actively cheating, which requires commitments and
zero-knowledge proofs. The third is how a key survives years of machines
failing and being replaced, which is what refresh, backup and repair are
for.

| Question | Naive answer | MPC answer | Section |
|----|----|----|----|
| How is the key born? | One machine generates it and splits it | Distributed key generation: every party contributes randomness, and the key is never computed | DKG |
| How does it sign? | Rebuild the key, sign, erase | Each party computes a partial signature from its share; the partials combine into one ordinary signature | Lindell 2017, FROST, CGGMP |
| How does it survive? | Back up the key | Refresh shares on a schedule, back up each share separately, repair a lost share from the others | Refresh, backup |

**Why not multisig.** Bitcoin already has a way to require several
signers: a **multisig** output, whose locking script on the chain says
“any 2 of these 3 public keys must sign”. MPC reaches the same rule by a
different route. On the chain, an MPC key is one ordinary public key and
each payment carries one ordinary signature, so the quorum rule lives
off the chain. The differences follow from that. Multisig publishes the
rule and every participating key when coins are spent, works differently
on every blockchain (some have no equivalent at all), and makes each
payment larger and so more expensive. MPC keeps the rule private, works
on any chain whose signature scheme it supports, and costs the same as a
single-key payment. Its price is a large piece of software that must
itself be correct, which is most of this chapter.

**Two quorums.** The signing quorum in this chapter is made of machines.
It is separate from the approval quorum of people in the policy engine
([chapter 4](04-policy.md)), and the signers in the demo refuse to sign
without the engine’s authorisation. [Chapter 0](00-orientation.md)’s
“Two quorums” section explains why the two are kept apart.

The demo uses this chapter in step 2, where three processes run
distributed key generation, and in step 7, where two of them sign with
FROST.

By the end of this chapter the following should be clear:

- what changes when a computation runs across several machines: parties,
  rounds, a coordinator, and the assumptions made about an attacker;
- how commitments and zero-knowledge proofs stop a cheating party, and
  what Feldman commitments check;
- how Shamir shares become the additive shares that threshold Schnorr
  signing uses;
- how two parties produce an ECDSA signature with Paillier encryption
  (Lindell 2017), and why ECDSA needs that machinery while Schnorr does
  not;
- how FROST signs in two rounds, and what its binding factor prevents;
- how distributed key generation, proactive refresh and share repair
  work, and which attack each one stops.

<a id="first-principles"></a>

## First principles

This section assumes [chapter 1](01-foundations.md)’s first principles:
groups, scalars, the nonce, commitments and the Schnorr exchange. It
adds the vocabulary of protocols that run across several machines.

<a id="parties-rounds-and-a-coordinator"></a>

### Parties, rounds and a coordinator

**The idea.** Each program taking part in an MPC protocol is a
**party**. In the demo each party is a separate operating-system process
holding one key share.

Parties exchange messages in **rounds**. In a round, every party sends
its messages, then waits until it has every other party’s messages
before computing its next step. Each round therefore costs at least one
network round trip, and the number of rounds sets the protocol’s
latency, the way the number of request-response exchanges sets the
latency of a FIX workflow. FROST signs in two rounds, and the first can
run before the message to be signed exists. That leaves one round
between an authorised transaction and its signature.

A **coordinator** relays messages between the parties and combines their
results. It holds no share and cannot sign. In the demo it is the
process that runs `SigningCluster`. It is trusted for availability, not
for secrecy: it can delay or refuse a signing, but a signature it
assembles is valid only if enough share holders took part, and it learns
nothing secret from the messages it relays.

Some messages are **broadcast**, meaning sent to every party;
commitments are an example. Others go over a **private channel** to one
party only, such as the sub-shares in distributed key generation.
Private channels need encryption and mutual authentication, which the
application around the protocol must provide (“How this shows up in
production”).

**Recap.** A protocol runs in rounds of messages between parties; rounds
set latency; the coordinator relays but holds nothing secret.

<a id="three-ways-to-split-a-key"></a>

### Three ways to split a key

**The idea.** [Chapter 1](01-foundations.md) split a key as points on a
line. Two other splits appear in this chapter, and each protocol uses
the one its signature formula needs.

| Split | Rule | Who can sign | Used in |
|----|----|----|----|
| Shamir | $d = f(0)$; party $i$ holds $f(i)$ | any $t$ of $n$ | DKG, FROST, CGGMP |
| Additive | $d = w_1 + w_2 + \dots$ | all holders together | one signing session |
| Multiplicative | $d = x_1 x_2$ | both holders | Lindell 2017 |

- An **additive share** is one of several numbers that add up to the
  key. Every holder is needed, because leaving one out changes the sum.
  Schnorr signing uses additive shares, because the Schnorr formula
  adds: additive pieces of the key give additive pieces of the
  signature.
- A **multiplicative share** is one of two numbers whose product is the
  key. Two-party ECDSA uses them, because the ECDSA formula multiplies.

**Worked by hand on the toy curve.** [Chapter 1](01-foundations.md)
shared the key $d = 9$ modulo 31 on the line $9 + 5x$, giving Shamir
shares $(1, 14)$, $(2, 19)$ and $(3, 24)$. The same key can be held as
the additive shares 21 and 19, since $21 + 19 = 40 = 31 + 9$, or as the
multiplicative shares 5 and 8, since $5 \times 8 = 40 \equiv 9$.

Signing converts Shamir shares into additive shares for the parties who
are present, using [chapter 1](01-foundations.md)’s Lagrange weights.
For parties 1 and 3 the weights are 17 and 15, so party 1’s additive
share is $17 \times 14 = 238 = 7 \times 31 + 21$, which is 21, and party
3’s is $15 \times 24 = 360 =
11 \times 31 + 19$, which is 19. Each party computes its own additive
share from its own Shamir share and the public weight, without seeing
the other’s share. The worked example later in the chapter signs with
exactly these two numbers.

``` python
from custody_lab.foundations import shamir

q = 31
assert [shamir.evaluate([9, 5], x, q) for x in (1, 2, 3)] == [14, 19, 24]
assert (21 + 19) % q == 9 and 5 * 8 % q == 9
lagrange = {i: shamir.lagrange_coefficient(i, [1, 3], q) for i in (1, 3)}
assert [lagrange[1] * 14 % q, lagrange[3] * 24 % q] == [21, 19]
```

**Recap.** Shamir shares are stored; for each signing session, the
parties present turn them into additive shares by multiplying by their
Lagrange weights.

<a id="what-the-attacker-is-assumed-to-do"></a>

### What the attacker is assumed to do

**The problem.** “No single machine can sign” is a claim about
attackers, and it is only meaningful once it says what the attacker can
do. A protocol that is safe against a machine whose logs leak can be
completely broken by a machine that lies.

**The idea.** Every security claim for a protocol names an **adversary
model**: which parties the attacker controls, when, and what those
parties may do. It plays the same role as the fault model of a test
plan, which states which failures the system is required to survive. The
parties the attacker controls are **corrupted**; the rest are
**honest**. A $t$-of-$n$ scheme promises that up to $t - 1$ corrupted
parties learn nothing about the key and cannot sign. $t$ corrupted
parties can sign; that is what the threshold means.

Corrupted parties come in two strengths:

- A **semi-honest** party (also called honest-but-curious) follows the
  protocol exactly, but records everything it sees and tries to learn
  from it later. This models a machine whose memory, logs or backups
  leak.
- A **malicious** party may send anything: wrong values, values chosen
  after seeing the honest parties’ messages, or nothing at all. This
  models an attacker who controls the process.

A protocol that is secure against semi-honest parties can be broken by
one malicious party, for example by sending a malformed encryption key
and reading the honest party’s share out of the answers. The teaching
Lindell 2017 module is secure only against semi-honest parties, because
its zero-knowledge proofs are left out. Commitments and zero-knowledge
proofs, the next two subsections, close that gap.

Three further terms qualify the model:

- **Static or mobile.** A static adversary corrupts a fixed set of
  parties. A **mobile adversary** moves between machines over time,
  collecting a share from one machine this year and from another next
  year. Proactive refresh, later in this chapter, is the defence.
- **Abort and identifiable abort.** When cheating is detected, the
  protocol stops without producing a signature: it **aborts**. With
  **identifiable abort** it also names the cheating party, so the
  operators can exclude that signer and continue with the others.
- **UC security**, for universal composability. A proof in this model
  still holds when many sessions run at the same time and alongside
  other protocols. A proof for one session in isolation does not
  automatically cover concurrent sessions, and a custodian’s signers run
  many at once (“Many sessions at once” shows what goes wrong).

**Recap.** The adversary model says how many parties the attacker
controls and whether they only watch or also lie. The protocols in this
chapter must survive parties that lie.

<a id="commitments"></a>

### Commitments

**The problem.** [Chapter 1](01-foundations.md) showed that a Schnorr
prover who sees the challenge before committing to $R$ can forge. The
same danger appears whenever several parties contribute values: the last
to speak can choose its value after seeing everyone else’s.

**The idea.** A commitment fixes a value now and reveals it later. A
commitment scheme has two properties:

- **Hiding.** The commitment reveals nothing about the committed value.
- **Binding.** The committer cannot later open the commitment to a
  different value.

A sealed-bid auction is the physical version: bids arrive in sealed
envelopes and are opened together, so nobody can adjust a bid after
seeing another. The comparison stops holding at one point. An auctioneer
holds the envelopes and is trusted not to peek; a cryptographic
commitment is published to everyone, and the binding comes from
mathematics, not from a trusted holder.

Two constructions appear in this manual:

- **Hash commitment.** Publish $c = H(v \,\|\, r)$, with $r$ a random
  value, and open it later by revealing $v$ and $r$. Collision
  resistance makes it binding: finding a second $(v', r')$ with the same
  hash is infeasible. The random $r$ makes it hiding. Without $r$, a
  value from a small set, such as an order side, is found by hashing
  each candidate, as the cell below does.
- **Point commitment.** Publish $vG$. It is binding because a point has
  exactly one position on the cycle, and hiding because recovering $v$
  from $vG$ is the discrete logarithm problem. The $R = kG$ in a
  signature is a point commitment to the nonce.

**Feldman commitments make a sharing checkable.** In Shamir sharing, a
party receiving a share cannot tell whether it is a genuine point on the
dealer’s line. Feldman’s scheme lets it check. The dealer publishes each
coefficient of its polynomial multiplied by $G$, which are point
commitments to the coefficients. Because positions add, a receiver $j$
can check its share without learning the coefficients: $f(j)\,G$ must
equal $C_0 + j\,C_1 + j^2 C_2 + \dots$.

Worked by hand for [chapter 1](01-foundations.md)’s sharing
$f(x) = 9 + 5x$: the dealer publishes $C_0 = 9G = (20, 40)$ and
$C_1 = 5G = (12, 12)$. Party 3 received the share 24, and checks that
$24G$ equals $C_0 + 3C_1 = 9G + 15G = 24G$, which is $(25, 25)$: it
passes. A dealer who had sent 25 instead would be caught, because
$25G = (29, 12)$ is a different point. $C_0$ is also the public key of
the shared secret, since $C_0 = 9G$: the commitment to the polynomial’s
starting value is the group key.

``` python
from custody_lab.foundations.ec import TOY, Point
from custody_lab.foundations.hashing import sha256

published = sha256(b"sell")  # a hash commitment with no random r
assert next(v for v in (b"buy", b"sell") if sha256(v) == published) == b"sell"

C0, C1 = TOY.mul(9, TOY.G), TOY.mul(5, TOY.G)
assert (C0, C1) == (Point(20, 40), Point(12, 12))
assert TOY.mul(24, TOY.G) == TOY.add(C0, TOY.mul(3, C1)) == Point(25, 25)
assert TOY.mul(25, TOY.G) == Point(29, 12)  # a wrong share fails the check
print("unsalted commitment opened by guessing; share 24 passes the check")
```

    unsalted commitment opened by guessing; share 24 passes the check

The printed line names both results: the commitment to “sell” without a
random value was opened by trying the two possible sides, and the
genuine share passed the Feldman check.

**Recap.** A commitment fixes a choice before others are revealed.
Feldman commitments let every receiver check that its share lies on the
dealer’s polynomial, and the first one is the group key.

<a id="zero-knowledge-proofs"></a>

### Zero-knowledge proofs

**The problem.** Some values a party sends cannot be checked by looking
at them. A party publishes a point and claims to know its discrete
logarithm; another publishes an encryption key and claims it was built
correctly. If the claim is false, the protocol can be broken, but
checking the claim directly would mean revealing the secret.

**The idea.** A **zero-knowledge proof** convinces a verifier that a
statement about a secret is true without revealing anything else about
the secret. Statements proved in this chapter’s protocols include:

- “I know the discrete logarithm of this point”: the proof of knowledge
  in distributed key generation.
- “This Paillier modulus is the product of two suitable primes”: Lindell
  2017 and CGGMP.
- “This ciphertext encrypts the discrete logarithm of that point”:
  Lindell 2017 key generation.

[Chapter 1](01-foundations.md)’s Schnorr exchange is a zero-knowledge
proof of the first kind. Only someone holding $d$ can answer a challenge
it could not predict, so passing the exchange proves knowledge of $d$.
And the exchange reveals nothing about $d$, for a reason [chapter
1](01-foundations.md)’s forgery makes concrete: anyone who knows $e$ in
advance can produce a transcript $(R, e, s)$ that passes, without
knowing $d$. Such forged transcripts look exactly like real ones. So a
real transcript cannot carry any information about $d$, because a forged
one, made without $d$, would have to carry it too.

**The attack it stops.** With the Fiat-Shamir hash in place of the
verifier, the proof needs no interaction, and `custody_lab.mpc.dkg`
attaches one to each participant’s published commitment $C_0$. It stops
the **rogue-key attack**. In distributed key generation the group key is
the sum of every participant’s $C_0$. A participant who speaks last
could publish $C_0 = AG - (\text{everyone else's } C_0)$ for a number
$A$ it chose, so that the sum, the group key, comes out as $AG$, a key
it alone can sign for. It cannot prove knowledge of the discrete
logarithm of the point it published, because it does not know it. The
cell tries exactly this: participant 3 replaces its commitment with one
built to cancel participant 1’s contribution.

``` python
from dataclasses import replace

from custody_lab.foundations.ec import SECP256K1
from custody_lab.mpc import dkg

honest = dkg.Dealer(3, threshold=2).round1()
dkg.check_round1(honest)  # a genuine proof of knowledge passes
target = dkg.Dealer(1, threshold=2).round1().commitments[0]
known = 12345  # a scalar participant 3 knows
rogue = SECP256K1.add(SECP256K1.mul(known, SECP256K1.G), SECP256K1.neg(target))
# target + rogue = known * G: a group key participant 3 alone could sign for
rejected = False
try:
    dkg.check_round1(replace(honest, commitments=(rogue, *honest.commitments[1:])))
except ValueError as err:
    rejected = True
    print("rejected:", err)
assert rejected
```

    rejected: participant 3: bad proof of knowledge

The printed reason is the check that failed: the proof attached to the
forged commitment does not verify.

**Recap.** A zero-knowledge proof shows a claim about a secret is true
and reveals nothing more. In key generation it stops a participant from
choosing the group key.

<a id="encryption-that-can-be-computed-on"></a>

### Encryption that can be computed on

**The problem.** ECDSA’s signing formula multiplies the nonce’s inverse
by the key. If two parties each hold a piece, one of them has to compute
with the other’s piece, without seeing it.

**The idea.** Ordinary encryption makes a ciphertext opaque: change it
and decryption produces garbage. **Homomorphic** encryption keeps a
structure: an operation on ciphertexts corresponds to an operation on
the plaintexts inside them. Paillier encryption (formal treatment) is
**additively** homomorphic:

- multiplying two ciphertexts gives an encryption of the sum of their
  plaintexts;
- raising a ciphertext to a known power $k$ gives an encryption of $k$
  times its plaintext.

It cannot multiply two encrypted values together, but addition and
multiplication by known numbers are enough for two-party ECDSA. Party
$P_1$ gives $P_2$ an encryption of $P_1$’s key share. $P_2$ multiplies
that encrypted share by numbers of its own and adds its own terms, all
without decrypting, and sends back a ciphertext that only $P_1$ can
decrypt. Paillier is also randomised: encrypting the same value twice
gives different ciphertexts, so nobody can spot two equal plaintexts.

**Worked with a toy key.** $N = 5 \times 7 = 35$. Plaintexts are numbers
modulo 35, and ciphertexts are numbers modulo $35^2 = 1225$. The private
values are $\lambda = \operatorname{lcm}(4, 6) = 12$ and
$\mu = 12^{-1} \bmod 35 = 3$, since $12 \times 3 = 36 \equiv 1$:

| Operation                   | Ciphertext | Decrypts to |
|-----------------------------|------------|-------------|
| Encrypt 4 with randomness 2 | 88         | 4           |
| Encrypt 9 with randomness 3 | 712        | 9           |
| $88 \times 712 \bmod 1225$  | 181        | 13          |
| $88^3 \bmod 1225$           | 372        | 12          |
| Encrypt 4 with randomness 3 | 1062       | 4           |

Row 3 multiplied two ciphertexts and decrypted to $4 + 9 = 13$. Row 4
raised a ciphertext to the power 3 and decrypted to $3 \times 4 = 12$.
Row 5 encrypted 4 again with different randomness and got an unrelated
ciphertext. A real key uses a 2048-bit $N$ (code walkthrough).

``` python
from custody_lab.mpc import paillier

pub = paillier.PublicKey(35)
key = paillier.PrivateKey(pub, lam=12, mu=3)
c4, c9 = pub.encrypt(4, r=2), pub.encrypt(9, r=3)
assert (c4, c9) == (88, 712) and (key.decrypt(c4), key.decrypt(c9)) == (4, 9)
assert pub.add(c4, c9) == 181 and key.decrypt(181) == 13
assert pub.mul(c4, 3) == 372 and key.decrypt(372) == 12
assert pub.encrypt(4, r=3) == 1062 and key.decrypt(1062) == 4
```

**Recap.** Paillier lets one party add to and scale another party’s
encrypted number. That is enough to compute an ECDSA signature across
two parties.

<a id="many-sessions-at-once"></a>

### Many sessions at once

**The problem.** A custodian’s signers do not sign one payment at a
time; they run many signing sessions concurrently. That opens an attack
that no single session has.

**The attack.** In a naive two-round threshold Schnorr protocol, each
signer publishes one nonce commitment per session. An attacker who
controls some signers, or the coordinator, opens many sessions at once
and sees the honest signers’ commitments in all of them before fixing
its own values. It can then choose how to combine them and which
sessions to complete. With enough sessions open, that freedom of choice
makes a signature on a new message, one nobody approved, computable.
This is the **ROS attack**. Drijvers et al. (2019) used Wagner’s
generalised birthday algorithm to make it practical. Benhamouda et
al. (2021) showed it runs in polynomial time, which in practice means
quickly, once the number of concurrent sessions exceeds the bit length
of the group order: 256 for secp256k1. No hash is broken and no share is
stolen. The attack exploits only the attacker’s freedom to choose after
seeing.

**The fix.** FROST removes the choice. Each signer commits to two nonces
per session, a **hiding nonce** $d_i$ and a **binding nonce** $e_i$. Its
effective nonce is $d_i + \rho_i e_i$, where the **binding factor**
$\rho_i$ is a hash of the message and of the full list of commitments in
the session. Any change to the message or to the commitment list changes
every signer’s effective nonce unpredictably, so there is nothing left
to choose after seeing.

**Nonces are single-use state.** For the reason [chapter
1](01-foundations.md) gave, a signer must never reuse a nonce. That
includes never restoring one from a backup, because restoring a used
nonce and signing again is nonce reuse.

**Recap.** Concurrent sessions give an attacker room to choose; FROST’s
binding factor ties every nonce to one message and one set of
commitments, which takes the choice away.

<a id="formal-treatment"></a>

## Formal treatment

<a id="from-shamir-shares-to-additive-shares"></a>

### From Shamir shares to additive shares

Parties in a signing set $S$ hold Shamir shares $s_i = f(i)$ of the key
$d = f(0)$. With the Lagrange coefficients $\lambda_i$ for $S$ ([chapter
1](01-foundations.md)),

$$
d = \sum_{i \in S} \lambda_i s_i ,
$$

so $w_i = \lambda_i s_i$ is an additive share of $d$ for this signing
set. Each party computes its $w_i$ alone. Schnorr is linear, so additive
key shares and additive nonces $k = \sum k_i$ give additive signature
shares $z_i = k_i + e\,w_i$, and their sum $z = \sum z_i$ verifies under
$P = dG$. What the rest of this section adds is protection against a
party who cheats.

<a id="paillier-encryption"></a>

### Paillier encryption

Paillier is public-key encryption with an additive homomorphism. The
public key is a modulus $N = pq$, the product of two large secret
primes, and ciphertexts are numbers modulo $N^2$. Anyone holding only
$N$ can compute

$$
\text{Enc}(a) \cdot \text{Enc}(b) = \text{Enc}(a + b), \qquad \text{Enc}(a)^k = \text{Enc}(k \cdot a) .
$$

Only the holder of the primes can decrypt. ECDSA’s $s = k^{-1}(z + rd)$
multiplies secrets held by different parties, and Paillier lets one
party compute on another’s secret while it stays encrypted.

<a id="two-party-ecdsa-lindell-2017"></a>

### Two-party ECDSA (Lindell 2017)

Keys are multiplicative shares: $P_1$ holds $x_1$, $P_2$ holds $x_2$,
and the public key is $Q = x_1 x_2 G$. At key generation, $P_1$ creates
a Paillier key pair and sends $c_{\text{key}} = \text{Enc}_{P_1}(x_1)$,
its own key share encrypted under its own Paillier key, to $P_2$. To
sign a digest $z$:

| Step | $P_1$ (holds $x_1$, Paillier private key) | $P_2$ (holds $x_2$, $c_{\text{key}}$) |
|----|----|----|
| 1 | $k_1$, send $R_1 = k_1 G$ |  |
| 2 |  | $k_2$, $R = k_2 R_1$, $r = x_R \bmod q$ |
| 3 |  | $c_1 = \text{Enc}(\rho q + k_2^{-1} z)$, $\rho$ random in $[0, q^2)$ |
| 4 |  | $c_3 = c_1 \cdot c_{\text{key}}^{\,k_2^{-1} r x_2}$; send $R_2 = k_2 G$, $c_3$ |
| 5 | $R = k_1 R_2$, $s' = \text{Dec}(c_3) \bmod q = k_2^{-1}(z + r x_1 x_2)$ |  |
| 6 | $s = k_1^{-1} s' \bmod q$, low-S, verify, output $(r, s)$ |  |

Here $q$ is the curve’s group order (written $n$ in [chapter
1](01-foundations.md)). Step by step:

- **Steps 1 and 2** build the shared nonce point. $P_1$ picks $k_1$ and
  $P_2$ picks $k_2$, and $R = k_1 k_2 G$; neither party knows the full
  nonce $k = k_1 k_2$.
- **Steps 3 and 4** are $P_2$ computing on encrypted data. Raising
  $c_{\text{key}}$ to the power $k_2^{-1} r x_2$ gives an encryption of
  $k_2^{-1} r x_2 x_1$, by the second homomorphic rule. Multiplying by
  $c_1$ adds $k_2^{-1} z$, by the first. So $c_3$ encrypts
  $k_2^{-1}(z + r x_1 x_2)$, plus the masking term $\rho q$.
- **Step 5.** $P_1$ decrypts and reduces modulo $q$. The masking term
  $\rho q$ vanishes, because it is a multiple of $q$, but before the
  reduction it hides the exact size of the number $P_2$ computed, which
  would otherwise leak information about $k_2$ and $x_2$.
- **Step 6.** Dividing by $k_1$ gives
  $s = (k_1 k_2)^{-1}(z + r\,x_1 x_2) = k^{-1}(z + r d)$: exactly the
  ECDSA formula, with $d = x_1 x_2$ and $k = k_1 k_2$.

$P_2$ never sees $x_1$ in the clear; $P_1$ never sees $x_2$ or $k_2$.
The full protocol adds zero-knowledge proofs of:

- knowledge of $x_1$, $x_2$, $k_1$ and $k_2$;
- the Paillier modulus $N$ being valid;
- $c_{\text{key}}$ encrypting the discrete logarithm of $P_1$’s public
  share $Q_1 = x_1 G$.

These are what stop a malicious party from biasing the key or extracting
the other party’s share. Coinbase’s cb-mpc implements Lindell 2017 with
those proofs. Its theory document states that the protocol is secure
only if every execution with a key halts once cheating is detected.

<a id="cggmp"></a>

### CGGMP

Canetti, Gennaro, Goldfeder, Makriyannis and Peled (2020) give
$t$-of-$n$ threshold ECDSA with four properties that matter in
operation:

- **UC security**, so it stays secure when many sessions run
  concurrently.
- **Identifiable abort**: a party that cheats is named, not only
  detected.
- **Proactive refresh**, described below.
- **Presigning**: most of the work happens before the message is known,
  leaving one round once it is.

The cost is heavy zero-knowledge machinery over Paillier encryption,
including an auxiliary-information phase that generates safe primes
(primes $p$ for which $(p - 1)/2$ is also prime). Among open-source Rust
libraries, `cggmp21` (LFDT-Lockness) implements it; the audit is by
Kudelski (**verify current**). cb-mpc’s multi-party ECDSA uses a
different protocol based on oblivious transfer (Haitner, Lindell, Nof,
Ranellucci 2018).

<a id="frost"></a>

### FROST

FROST (Komlo and Goldberg 2020; RFC 9591) is threshold Schnorr in two
rounds:

1.  **Commit.** Each signer $i$ draws a hiding nonce $d_i$ and a binding
    nonce $e_i$ and publishes their point commitments $D_i = d_i G$ and
    $E_i = e_i G$. This round can run before the message is known.
2.  **Sign.** For the message $m$ and the list $B$ of every
    participating signer’s commitments, each signer computes:
    - the binding factors $\rho_j = H_1(P, H_4(m), H_5(B), j)$ for every
      signer $j$;
    - the group commitment $R = \sum_j (D_j + \rho_j E_j)$, the combined
      nonce point;
    - the challenge $c = H_2(R, P, m)$, as in a single-signer Schnorr
      signature;

    and returns its signature share

$$
z_i = d_i + e_i \rho_i + \lambda_i s_i c .
$$

$H_1$ to $H_5$ are built from SHA-256 with a different context string
each, so their outputs are unrelated, the same domain separation as
BIP340’s tags ([chapter 1](01-foundations.md), “Hash functions”). $s_i$
is signer $i$’s Shamir share and $\lambda_i$ its Lagrange coefficient
for this signer set. So $z_i$ is the effective nonce $d_i + \rho_i e_i$
plus the challenge times the additive key share $\lambda_i s_i$, which
is the formula of the previous section with FROST’s two-part nonce.

The coordinator outputs $(R, \sum z_i)$, an ordinary Schnorr signature.
The binding factor ties each signer’s effective nonce to this message
and this signer set. That defeats the attack on [chapter
1](01-foundations.md)’s naive two-party Schnorr, where a party picks its
nonce after seeing the other’s, and the ROS attack on concurrent
sessions. For Bitcoin, the `frost-secp256k1-tr` variant makes the output
a BIP340 signature.

<a id="distributed-key-generation"></a>

### Distributed key generation

Pedersen’s distributed key generation runs $n$ Shamir dealings at once,
one by each participant:

1.  Participant $i$ picks a random polynomial $f_i$ of degree $t - 1$.
    It broadcasts **Feldman commitments** $C_{ik} = a_{ik} G$ to its
    coefficients $a_{ik}$, plus a proof of knowledge of $a_{i0}$, the
    discrete logarithm of $C_{i0}$.
2.  It sends $f_i(j)$ privately to each other participant $j$.
3.  Receiver $j$ checks each sub-share it received against the sender’s
    commitments,

$$
f_i(j)\,G = \sum_k j^k\, C_{ik} ,
$$

and sets its share to the sum of everything it received,
$s_j = \sum_i f_i(j)$.

The group key is $P = \sum_i C_{i0}$, the public key of $\sum_i a_{i0}$,
and that secret sum was never in any one place. The proof of knowledge
stops the rogue-key attack described under “Zero-knowledge proofs”.
Feldman checks alone stop it only when at least $t$ honest receivers pin
down the attacker’s polynomial; with $t = n$ they do not (Exercise 4).

<a id="proactive-refresh"></a>

### Proactive refresh

Every holder deals a sharing of **zero**: a polynomial whose starting
value is 0, so its commitment $C_{i0}$ is the point at infinity. Each
holder adds the sub-shares it receives to its share. The group key does
not change, because zero was added to the secret, but every share does,
and the new polynomial is independent of the old one. An attacker who
stole one old share and one new share holds two points on different
polynomials and learns nothing. Refresh therefore defends against a
mobile adversary, one who compromises different machines at different
times. The worked example below runs a refresh by hand.

<a id="backup-recovery-and-repair"></a>

### Backup, recovery and repair

A lost share is a lost vote, and losing more than $n - t$ shares loses
the key, because fewer than $t$ remain. Three tools recover from that:

- **Encrypted share backup.** Each share is encrypted to an offline
  recovery key held under different control from the live share.
- **Publicly verifiable encryption** (cb-mpc’s PVE). Anyone can check
  that a backup ciphertext really encrypts the share matching a known
  public share, without decrypting it. A custodian can therefore show an
  auditor that its backups would work.
- **Share repair.** $t$ holders help rebuild a lost holder’s share
  without revealing their own. ZF FROST provides this as
  `repair_share_part1` to `part3`.

<a id="worked-example"></a>

## Worked example

<a id="threshold-schnorr-on-the-toy-curve"></a>

### Threshold Schnorr on the toy curve

Threshold Schnorr on the toy curve ($\mathbb{F}_{43}$, $n = 31$),
reusing [chapter 1](01-foundations.md)’s Shamir sharing of $d = 9$:
shares $(1, 14)$, $(2, 19)$ and $(3, 24)$. Parties 1 and 3 sign. The
challenge is fixed at $e = 5$, instead of being hashed, so that every
step can be checked by hand.

| Step | Party 1 | Party 3 |
|----|----|----|
| Lagrange coefficient for $\{1, 3\}$ | $\lambda_1 = 17$ | $\lambda_3 = 15$ |
| Additive key share $w_i = \lambda_i s_i$ | $14 \cdot 17 = 238 \equiv 21$ | $24 \cdot 15 = 360 \equiv 19$ |
| Nonce $k_i$ | $3$ | $4$ |
| Signature share $z_i = k_i + e\,w_i$ | $3 + 5 \cdot 21 = 108 \equiv 15$ | $4 + 5 \cdot 19 = 99 \equiv 6$ |

- The additive shares sum to the key: $21 + 19 = 40 \equiv 9 = d$.
  Neither party ever computed 9.
- Combined: $z = 15 + 6 = 21$ and $R = (3 + 4)G = 7G$.
- Verification $zG = R + eP$: $7G + 5 \cdot 9G = 52G = 21G$, since
  $52 = 31 + 21$.

``` python
from custody_lab.foundations import shamir
from custody_lab.foundations.ec import TOY

n, G = TOY.n, TOY.G
shares = {1: 14, 3: 24}
w = {i: shamir.lagrange_coefficient(i, [1, 3], n) * s % n for i, s in shares.items()}
assert w == {1: 21, 3: 19} and sum(w.values()) % n == 9
k, e = {1: 3, 3: 4}, 5
z = {i: (k[i] + e * w[i]) % n for i in shares}
assert z == {1: 15, 3: 6}
R, P = TOY.mul(7, G), TOY.mul(9, G)
assert TOY.mul(sum(z.values()), G) == TOY.add(R, TOY.mul(e, P))
print("R =", R, " zG =", TOY.mul(21, G))
```

    R = Point(x=25, y=18)  zG = Point(x=42, y=36)

The printed line shows the combined nonce point $R = 7G$ and the point
$zG = 21G$ that the verifier compares with $R + eP$.

<a id="distributed-key-generation-on-the-toy-curve"></a>

### Distributed key generation on the toy curve

The sharing used above, $9 + 5x$ with shares 14, 19 and 24, can be
produced by three participants without anyone choosing, or ever seeing,
the key 9. Each participant picks its own line modulo 31 and publishes
Feldman commitments to the line’s starting value and slope:

| Participant                        | Its line | Commitments | Sends to 1 | to 2 | to 3 |
|------------------------------------|----------|-------------|------------|------|------|
| 1                                  | $3 + x$  | $3G$, $1G$  | 4          | 5    | 6    |
| 2                                  | $2 + 5x$ | $2G$, $5G$  | 7          | 12   | 17   |
| 3                                  | $4 - x$  | $4G$, $30G$ | 3          | 2    | 1    |
| Each receiver’s share (column sum) | $9 + 5x$ |             | 14         | 19   | 24   |

Participant 3’s slope is $-1 \equiv 30$, so its slope commitment is
$30G$. Each receiver checks every sub-share it gets. For example,
participant 3 receives 17 from participant 2 and checks that $17G$
equals participant 2’s $C_0 + 3C_1 = 2G + 15G$; it does. Had participant
2 sent 18, the check would compare $18G = (13, 22)$ with $17G = (34, 3)$
and fail.

The group key is the sum of the three starting-value commitments,
$3G + 2G + 4G = 9G = (20, 40)$, which everyone can compute. The key
itself, $3 + 2 + 4 = 9$, would need all three starting values, and each
participant knows only its own.

``` python
lines = {1: (3, 1), 2: (2, 5), 3: (4, 30)}  # each participant's (start, slope) modulo 31
commitments = {i: (TOY.mul(a, G), TOY.mul(b, G)) for i, (a, b) in lines.items()}
share = {}
for j in (1, 2, 3):
    received = {i: (a + b * j) % n for i, (a, b) in lines.items()}
    for i, value in received.items():  # Feldman check of each sub-share
        C0, C1 = commitments[i]
        assert TOY.mul(value, G) == TOY.add(C0, TOY.mul(j, C1))
    share[j] = sum(received.values()) % n
    print(f"participant {j} receives {list(received.values())}, share {share[j]}")
group_key = TOY.add(TOY.add(commitments[1][0], commitments[2][0]), commitments[3][0])
assert share == {1: 14, 2: 19, 3: 24} and group_key == TOY.mul(9, G) == Point(20, 40)
assert TOY.mul(18, G) != TOY.add(commitments[2][0], TOY.mul(3, commitments[2][1]))
```

    participant 1 receives [4, 7, 3], share 14
    participant 2 receives [5, 12, 2], share 19
    participant 3 receives [6, 17, 1], share 24

Each printed line is one participant’s view: the three sub-shares it
received, in the order participant 1, 2, 3, and the share it keeps. The
shares are the ones the threshold example signed with.

<a id="proactive-refresh-on-the-toy-curve"></a>

### Proactive refresh on the toy curve

To refresh, each participant deals a line through zero: participant 1
uses $3x$, participant 2 uses $7x$ and participant 3 uses $x$. Their
slopes add to 11, so the shared line changes from $9 + 5x$ to $9 + 16x$,
and the key is still 9.

| Holder | Old share | Received ($3x$, $7x$, $x$) | New share                |
|--------|-----------|----------------------------|--------------------------|
| 1      | 14        | $3 + 7 + 1 = 11$           | $14 + 11 = 25$           |
| 2      | 19        | $6 + 14 + 2 = 22$          | $19 + 22 = 41 \equiv 10$ |
| 3      | 24        | $9 + 21 + 3 = 33 \equiv 2$ | $24 + 2 = 26$            |

New shares 1 and 3 still recover the key with the same weights:
$17 \times 25 + 15 \times 26 = 425 + 390 = 815 = 26 \times 31 + 9$. An
old share from before the refresh and a new share from after it do not:
$17 \times 14 + 15 \times 26 = 238 + 390 = 628 =
20 \times 31 + 8$, which is 8, not 9. An attacker who stole share 1 last
year and share 3 this year has two points on different lines, and they
give the wrong key.

``` python
zero_lines = {1: 3, 2: 7, 3: 1}  # each participant deals slope * x, a line through zero
old = {1: 14, 2: 19, 3: 24}
new = {j: (old[j] + sum(m * j for m in zero_lines.values())) % n for j in old}
assert new == {1: 25, 2: 10, 3: 26}
assert shamir.reconstruct([shamir.Share(1, new[1]), shamir.Share(3, new[3])], modulus=n) == 9
assert shamir.reconstruct([shamir.Share(1, old[1]), shamir.Share(3, new[3])], modulus=n) == 8
print("new shares", list(new.values()), "recover 9; old 1 with new 3 gives 8")
```

    new shares [25, 10, 26] recover 9; old 1 with new 3 gives 8

<a id="code-walkthrough"></a>

## Code walkthrough

The worked examples used numbers small enough to check by hand. This
section runs the same protocols at full size and checks them against an
independent verifier, a published test vector, and the demo’s own
signing processes.

<a id="two-party-ecdsa"></a>

### Two-party ECDSA

`Party1` and `Party2` exchange three messages. Each object keeps its
secret in a private attribute and exposes only what the protocol sends.
The resulting signature is plain ECDSA, and `cryptography` verifies it
without knowing it came from two parties.

``` python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    Prehashed,
    encode_dss_signature,
)

from custody_lab.foundations.ecdsa import hash_to_int
from custody_lab.foundations.hashing import sha256
from custody_lab.mpc.lindell17 import Party1, Party2

p1, p2 = Party1(), Party2()               # P1 generates a 2048-bit Paillier key
msg1 = p1.keygen_message()                # Q1, Paillier public key, Enc(x1)
Q = p1.keygen_finish(p2.keygen(msg1))     # P2 answers with Q2; both derive Q = x1*x2*G

digest = sha256(b"SETTLE batch=7 asset=BTC qty=0.25000000")
z = hash_to_int(digest)
sig = p1.sign_finish(z, p2.sign(z, p1.sign_commit()))

public_key = ec.EllipticCurvePublicNumbers(Q.x, Q.y, ec.SECP256K1()).public_key()
public_key.verify(
    encode_dss_signature(sig.r, sig.s), digest, ec.ECDSA(Prehashed(hashes.SHA256()))
)
print(f"Paillier N: {msg1.paillier_public.n.bit_length()} bits; signature verified")
```

    Paillier N: 2048 bits; signature verified

The printed line gives the size of $P_1$’s Paillier modulus and confirms
that OpenSSL accepted the two-party signature as ordinary ECDSA.

<a id="frost-against-rfc-9591"></a>

### FROST against RFC 9591

RFC 9591 publishes a test vector for FROST(secp256k1, SHA-256): fixed
inputs and every intermediate value. The educational FROST reproduces it
exactly: nonces, commitments, binding factors, signature shares and the
final signature. The full check is `tests/mpc/test_frost.py`; this cell
repeats the last step.

``` python
import json
from pathlib import Path

from custody_lab.foundations.ec import decode_point
from custody_lab.mpc import frost

v = json.loads(Path("../../tests/mpc/vectors/frost-secp256k1-sha256.json").read_text())
msg = bytes.fromhex(v["inputs"]["message"])
pk = decode_point(bytes.fromhex(v["inputs"]["group_public_key"]))
key_shares = {
    s["identifier"]: int(s["participant_share"], 16)
    for s in v["inputs"]["participant_shares"]
}
nonces, commitments = {}, []
for o in v["round_one_outputs"]["outputs"]:
    i = o["identifier"]
    nonces[i], c = frost.commit(
        i,
        key_shares[i],
        bytes.fromhex(o["hiding_nonce_randomness"]),
        bytes.fromhex(o["binding_nonce_randomness"]),
    )
    commitments.append(c)
zs = [frost.sign(i, key_shares[i], nonces[i], pk, commitments, msg) for i in nonces]
signature = frost.aggregate(pk, commitments, msg, zs)
assert frost.encode_signature(signature).hex() == v["final_output"]["sig"]
print("matches RFC 9591 vector; signers", sorted(nonces))
```

    matches RFC 9591 vector; signers [1, 3]

<a id="dkg-signing-and-refresh"></a>

### DKG, signing and refresh

Three participants run the DKG, and every pair of them signs. After a
refresh the key is unchanged and every share is new, and an old share
combined with a new one produces an invalid signature, the full-size
version of the refresh example.

``` python
from itertools import combinations

from custody_lab.mpc import dkg


def frost_sign(shares, group_key, message):
    rounds = {i: frost.commit(i, s) for i, s in shares.items()}
    cs = [c for _, c in rounds.values()]
    parts = [
        frost.sign(i, shares[i], rounds[i][0], group_key, cs, message) for i in shares
    ]
    return frost.aggregate(group_key, cs, message, parts)


shares, group_key = dkg.run(threshold=2, count=3)
for pair in combinations(shares, 2):
    subset = {i: shares[i] for i in pair}
    assert frost.verify(group_key, b"m", frost_sign(subset, group_key, b"m"))

new = dkg.refresh(shares, threshold=2)
refreshed = frost_sign({1: new[1], 2: new[2]}, group_key, b"m")
assert frost.verify(group_key, b"m", refreshed)
mixed = frost_sign({1: shares[1], 2: new[2]}, group_key, b"m")
print("old + new share signs:", frost.verify(group_key, b"m", mixed))
```

    old + new share signs: False

`False` in the printed line is the expected result: the mixed pair’s
signature does not verify.

<a id="the-demos-signing-path-zf-frost-in-three-processes"></a>

### The demo’s signing path: ZF FROST in three processes

`SigningCluster` starts one operating-system process per share and runs
the crate’s DKG and two-round signing across them. The coordinator, here
the process building this chapter, relays packages and never holds a
share. The DKG sub-shares, which only their recipient may see, travel
over private channels: each signer seals them to the recipient with a
key agreed by X25519 and ChaCha20-Poly1305 encryption
(`custody_lab.mpc.channel`), so the coordinator relays ciphertext it
cannot open. The signers’ channel public keys pass through the
coordinator when the processes start; a coordinator that substituted its
own at that moment could read every sub-share, which is why production
systems provision these keys out of band ([chapter
3](03-key-storage.md)). The signature is checked with [chapter
1](01-foundations.md)’s educational BIP340 verifier, an implementation
independent of the crate.

Each signer releases a signature share only against an authorisation
signed by the policy authority, covering exactly the message in the
signing package. [Chapter 4](04-policy.md) builds the policy engine that
issues it; here the chapter holds the authority key itself.

``` python
import os

from datetime import UTC, datetime, timedelta

from custody_lab.foundations import schnorr
from custody_lab.mpc.cluster import SigningCluster
from custody_lab.policy import authorisation

authority = authorisation.AuthorityKey.generate()  # chapter 4: held by the policy engine
sighash = bytes.fromhex("6a" * 32)  # stands in for a BIP341 sighash (chapter 5)
expires = datetime.now(UTC) + timedelta(seconds=60)
token = authorisation.issue(authority, b"\x00" * 32, sighash, expires).to_bytes()

authority_public = authority.public_bytes()
with SigningCluster(threshold=2, count=3, authority=authority_public) as cluster:
    x_only_key = cluster.dkg()
    print("coordinator pid:", os.getpid())
    for identifier, pid in cluster.holders().items():
        print(f"  share {identifier} held by pid {pid}")
    signature = cluster.sign(sighash, signers=[1, 3], token=token)
assert schnorr.verify(sighash, x_only_key, signature)
print("BIP340 signature from shares 1 and 3 verifies; key", x_only_key.hex()[:16], "...")
```

    coordinator pid: 873155
      share 1 held by pid 873188
      share 2 held by pid 873189
      share 3 held by pid 873190
    BIP340 signature from shares 1 and 3 verifies; key bad0458078f69b47 ...

The printed process identifiers show four different processes: the
coordinator and one per share. The last line shows that signers 1 and 3
together produced a BIP340 signature for the group key, which signer 2
took no part in.

**What the coordinator saw.** `SigningCluster` accepts a `watch`: a
function it calls with every round’s requests as they leave the
coordinator and again with the signers’ replies. The cell below runs the
same key generation and signing under a watch, and prints for each round
how many messages passed through the coordinator and how many of their
bytes were public by design (`clear`), sealed to one signer (`sealed`),
or the policy engine’s authorisation (`auth`).

``` python
from custody_lab.demo.protocol import messages

rounds = []


def watch(calls, replies):
    if replies is not None:  # a round answered: what passed, both ways
        method = next(iter(calls.values()))[0]
        rounds.append((method, messages(method, calls, replies)))


with SigningCluster(2, 3, authority=authority_public, watch=watch) as cluster:
    cluster.dkg()
    expires = datetime.now(UTC) + timedelta(seconds=60)
    fresh = authorisation.issue(authority, b"\x00" * 32, sighash, expires)
    cluster.sign(sighash, signers=[1, 3], token=fresh.to_bytes())

kinds = ("clear", "sealed", "authorisation")
print(f"{'round':12} {'messages':>8} {'clear':>6} {'sealed':>6} {'auth':>6}")
for method, sent in rounds:
    size = [sum(m["bytes"] for m in sent if m["kind"] == k) for k in kinds]
    print(f"{method:12} {len(sent):8} {size[0]:6} {size[1]:6} {size[2]:6}")
sub_shares = [m for method, sent in rounds if method == "dkg2" for m in sent
              if m["leg"] == "back"]
assert len(sub_shares) == 6 and all(m["kind"] == "sealed" for m in sub_shares)
```

    round        messages  clear sealed   auth
    channel_key         6     96      0      0
    set_peers          12    288      0      0
    dkg1                6    411      0      0
    dkg2               12    822    390      0
    dkg3                9    708    390      0
    commit              4    142      0      0
    sign                6    554      0  14094

The first two lines are the private channels: each signer’s 32-byte
public key sent to the coordinator, then all three keys handed to each
signer. `dkg1` is each signer’s 137-byte round-1 package, its Feldman
commitments and its proof of knowledge. In `dkg2` the coordinator
forwards those packages to the other signers, 822 bytes in clear, and
receives six sub-shares, 390 bytes sealed; in `dkg3` it delivers the
same sealed bytes and receives the three signers’ public key packages.
`commit` is the two signers’ nonce commitments. In `sign`, the two
copies of the authorisation are 14,094 bytes, against 554 bytes of FROST
messages: the post-quantum signature on the permission is larger than
the threshold protocol it permits ([chapter 7](07-post-quantum.md)).
Nothing in the `clear` column is secret: commitments, proofs, public
keys and signature shares are public by design, and every value that
would reveal a share is in the `sealed` column. The walkthrough’s
[Watching the protocol](../demo-walkthrough.md#watching-the-protocol)
splits each of these messages into its fields.

<a id="production-ecdsa-libraries-listings-not-executed"></a>

### Production ECDSA libraries (listings, not executed)

These two listings are in C and Rust, which this project does not build;
they show what calling a production threshold-ECDSA library looks like.
First, cb-mpc’s C API for two-party ECDSA signing
(`include/cbmpc/c_api/ecdsa_2p.h`). The caller supplies the network
transport as blocking send and receive callbacks inside `job`, and the
key blob holds this party’s share.

``` c
cbmpc_error_t cbmpc_ecdsa_2p_sign(const cbmpc_2pc_job_t* job, cmem_t key_blob,
                                  cmem_t msg_hash, cmem_t sid_in,
                                  cmem_t* sid_out, cmem_t* sig_der_out);
```

Second, `cggmp21`’s three phases, abridged from the crate documentation
(docs.rs, version 0.6.3): key generation, the auxiliary-information
phase that generates Paillier primes, and signing. `party` is the
caller’s networking; assembling the final key share is left out.

``` rust
let eid = cggmp21::ExecutionId::new(b"execution id, unique per protocol execution");
let incomplete_key_share = cggmp21::keygen::<Secp256k1>(eid, i, n)
    .set_threshold(t)
    .start(&mut OsRng, party)
    .await?;

let pregenerated_primes = cggmp21::PregeneratedPrimes::generate(&mut OsRng);
let aux_info = cggmp21::aux_info_gen(eid, i, n, pregenerated_primes)
    .start(&mut OsRng, party)
    .await?;

let data_to_sign = cggmp21::DataToSign::digest::<Sha256>(b"data to be signed");
let signature = cggmp21::signing(eid, i, &parties_indexes_at_keygen, &key_share)
    .sign(&mut OsRng, party, data_to_sign)
    .await?;
```

<a id="how-this-shows-up-in-production"></a>

## How this shows up in production

**Vendors.** MPC wallets and custody platforms build on the protocols in
this chapter. Fireblocks built MPC-CMP from the same research line as
CGGMP. Coinbase open-sourced cb-mpc, which includes Lindell 2017, HLNR
2018 and a Lindell 2024 Schnorr protocol. Dfns and the LFDT-Lockness
project publish `cggmp21`. The Zcash Foundation publishes FROST. Product
names and protocol choices change (**verify current**).

**The omitted proofs are where real breaks happened.** In 2023, two
public disclosures showed that the key could be extracted from several
open-source GG18/GG20 threshold ECDSA implementations whose
zero-knowledge proofs were missing or weak: Fireblocks’ “BitForge” and
Verichains’ “TSShock”. One weakness behind BitForge was a missing proof
that a party’s Paillier modulus is well formed: a malicious party could
send a modulus with small factors and, over a number of signing
sessions, extract the honest party’s key share. That is the kind of
proof the teaching Lindell 2017 module leaves out. The library choice
matters more than the protocol name.

**Halt on failure.** For Lindell 2017, cb-mpc’s theory document requires
every execution with a key to stop once cheating is detected, because an
attacker who can retry after each failure learns a little more each
time. An operator runbook therefore needs a “freeze key” action wired to
signing failures, not an automatic retry loop.

**Nonces are single-use state.** FROST nonces and CGGMP presignatures
must never be reused or restored from a backup. The demo’s signer
discards its nonces before it checks a request, so a refused request
cannot be retried with the same nonces on a different message.

**Transport and identity are the integrator’s job.** cb-mpc’s README is
explicit that the application around the library authenticates the
parties to each other and protects the channels between them, for
example with mutually authenticated TLS, and that every session
identifier must be unique. The demo uses local pipes between processes
on one machine; [chapter 9](09-capstone.md) discusses the deployed
version.

**Taproot needs a tweak.** A Bitcoin Taproot payment of the kind the
demo makes (a BIP86 key-path spend) is signed under a tweaked key,
$P + H_{\text{TapTweak}}(P)\,G$, not under the group key $P$ itself. The
crate provides `sign_with_tweak` and `aggregate_with_tweak` for this,
and [chapter 5](05-settlement.md) explains the tweak.

**Where the shares live** (an HSM, a secure enclave or a plain server)
is [chapter 3](03-key-storage.md). **What authorises a signature** is
[chapter 4](04-policy.md).

<a id="recap"></a>

## Recap

1.  MPC lets several parties compute a signature from their key shares
    while each learns only the signature. The chain sees one ordinary
    key and one ordinary signature, unlike multisig.
2.  Protocols run in rounds; a coordinator relays messages and holds
    nothing secret. Security is stated against an adversary model:
    semi-honest parties watch, malicious parties lie.
3.  Shamir shares become additive shares for a signing session by
    multiplying each share by its Lagrange weight; Schnorr then signs
    additively.
4.  Commitments fix values before others are revealed; Feldman
    commitments let every receiver check its share; zero-knowledge
    proofs prove claims about secrets, and stop the rogue-key attack.
5.  ECDSA multiplies secrets, so two-party ECDSA computes on an
    encrypted key share with Paillier’s additive homomorphism, and needs
    proofs that each party’s values are well formed.
6.  FROST signs in two rounds. Its binding factor ties every nonce to
    one message and one set of commitments, which defeats attacks that
    rely on choosing after seeing, including ROS.
7.  Distributed key generation creates shares of a key nobody ever held;
    proactive refresh changes every share without changing the key, so
    shares stolen at different times do not combine; backup and repair
    keep the key alive when share holders fail.

[Chapter 3](03-key-storage.md) asks where each share should physically
live, and [chapter 4](04-policy.md) builds the policy engine whose
authorisation every signer checks.

<a id="exercises"></a>

## Exercises

1.  **Compute.** Repeat the toy threshold example with parties 2 and 3,
    the same challenge $e = 5$ and nonces $k_2 = 3$, $k_3 = 4$. Give
    $\lambda_2$, $\lambda_3$, both signature shares and $z$.
2.  **Explain.** Why does each FROST signer publish two nonce
    commitments instead of one?
3.  **Explain.** In Lindell 2017, what would $P_1$ learn if $P_2$
    omitted the $\rho q$ term?
4.  **Attack.** In a 3-of-3 run of the educational DKG, participant 3
    waits for $C_{10}$ and $C_{20}$, then broadcasts
    $C_{30} = A - C_{10} - C_{20}$ for a point $A$ whose discrete log it
    knows. What does the group key become? Can participant 3 still send
    sub-shares that pass the honest parties’ Feldman checks, and which
    check stops the attack?
5.  **Design.** A custodian is choosing between 2-of-3 on-chain multisig
    and 2-of-3 MPC for Bitcoin cold storage. Name three differences a
    risk committee would care about.
6.  **Classify.** For each action by a corrupted signer, say whether a
    semi-honest party could take it or only a malicious one, and name
    what stops it:
    1)  logging every message it receives, together with its own share;
    2)  sending a Paillier modulus that is not the product of two large
        primes;
    3)  returning a signature share computed with a different nonce from
        the one it committed to.
7.  **Compute.** With the toy Feldman commitments $C_0 = 9G$ and
    $C_1 = 5G$ over the toy curve, which values of party 2’s share pass
    the check?

<a id="solutions"></a>

## Solutions

1.  For $\{2, 3\}$: $\lambda_2 = \frac{0-3}{2-3} = 3$,
    $\lambda_3 = \frac{0-2}{3-2} = -2 \equiv 29$.
    $w_2 = 19 \cdot 3 = 57 \equiv 26$ and
    $w_3 = 24 \cdot 29 = 696 \equiv 14$; $26 + 14 = 40 \equiv 9$.
    $z_2 = 3 + 5 \cdot 26 = 133 \equiv 9$ and
    $z_3 = 4 + 5 \cdot 14 = 74 \equiv 12$, so $z = 21$: the same
    signature as before. The key, nonce and challenge are unchanged, and
    only the split differs.

``` python
w = {2: 3 * 19 % n, 3: 29 * 24 % n}
assert w == {2: 26, 3: 14}
assert [(3 + 5 * w[2]) % n, (4 + 5 * w[3]) % n] == [9, 12]
```

2.  With one nonce, $R = \sum D_j$ is fixed as soon as the commitments
    are published. A signer who sees many concurrent sessions can then
    choose which commitments to combine and solve for a forgery (the ROS
    / Wagner attack). The binding nonce, weighted by $\rho_j$, makes
    every signer’s effective nonce depend on the message and the full
    commitment list, so nothing can be chosen after the fact.
3.  The decrypted value would be $k_2^{-1} z + k_2^{-1} r x_2 x_1$
    reduced modulo $N$, not modulo $q$. As a whole number it leaks
    information about $k_2^{-1}$ and $x_2$ through its size and its
    structure across signatures. Adding a random multiple of $q$ hides
    the whole number while leaving its value modulo $q$ unchanged.
4.  The group key becomes $C_{10} + C_{20} + C_{30} = A$, a key the
    attacker alone controls; the honest contributions cancel.
    - Feldman checks do not catch it. With degree 2 and only two honest
      receivers, participant 3 can pick any sub-shares $f_3(1), f_3(2)$
      and then solve for $C_{31}, C_{32}$ as points so that both checks
      pass.
    - In a 2-of-3 run the same trick fails, because two honest receivers
      pin a degree-1 polynomial.
    - The proof of knowledge requires knowing $\log_G C_{30}$, which
      participant 3 does not, so `check_round1` raises “bad proof of
      knowledge”.
5.  Any three of:
    - **Privacy.** Multisig publishes the 2-of-3 policy and all three
      public keys when spent; MPC spends look like a single-key spend.
    - **Chain coverage.** Multisig script differs per chain and some
      chains lack it; MPC needs only the signature scheme.
    - **Cost.** A multisig spend is larger, so fees are higher.
    - **Key rotation.** Changing multisig participants means moving
      funds to a new address; MPC refresh or resharing keeps the
      address.
    - **Assurance.** Multisig’s security rests on the chain’s script
      rules alone; MPC adds a software supply chain (the library and its
      proofs) that has to be audited.
6.  Classification:
    - 1)  Semi-honest: the party follows the protocol and only records
          its own view. The protocol is designed so that this view
          reveals nothing beyond the party’s own share, and up to
          $t - 1$ such parties learn nothing about the key.
    - 2)  Malicious: it deviates from the protocol. A zero-knowledge
          proof that $N$ is well formed stops it. The teaching Lindell
          2017 module omits that proof, and Paillier modulus validity
          was one of the weaknesses in the 2023 disclosures (“How this
          shows up in production”).
    - 3)  Malicious. The share no longer matches the commitment, so the
          combined signature fails to verify and the session aborts. The
          coordinator can also check each share on its own,
          $z_i G = D_i + \rho_i E_i + \lambda_i c\,(s_i G)$, using the
          signer’s commitments and public share $s_i G$. That names the
          signer: identifiable abort.
7.  The check requires $f(2)\,G = C_0 + 2C_1 = 19G$. Only one scalar
    modulo 31 sits at position 19 on the cycle, so only the share 19
    passes. The commitments bind the dealer to one share per party.

``` python
C0, C1 = TOY.mul(9, TOY.G), TOY.mul(5, TOY.G)
expected = TOY.add(C0, TOY.mul(2, C1))
assert [s for s in range(31) if TOY.mul(s, TOY.G) == expected] == [19]
```

<a id="further-reading"></a>

## Further reading

- Y. Lindell, “Fast Secure Two-Party ECDSA Signing”, CRYPTO 2017;
  *Journal of Cryptology* 34, 2021. The two-party protocol with its
  proofs.
- R. Canetti, R. Gennaro, S. Goldfeder, N. Makriyannis, U. Peled, “UC
  Non-Interactive, Proactive, Threshold ECDSA with Identifiable Aborts”,
  ACM CCS 2020 (IACR ePrint 2021/060).
- C. Komlo, I. Goldberg, “FROST: Flexible Round-Optimized Schnorr
  Threshold Signatures”, SAC 2020; RFC 9591 (2024).
- P. Paillier, “Public-Key Cryptosystems Based on Composite Degree
  Residuosity Classes”, EUROCRYPT
  1999. The encryption scheme two-party ECDSA computes under.
- P. Feldman, “A Practical Scheme for Non-interactive Verifiable Secret
  Sharing”, FOCS 1987. The commitments that make a Shamir dealing
  checkable.
- M. Drijvers, K. Edalatnejad, B. Ford, E. Kiltz, J. Loss, G. Neven, I.
  Stepanovs, “On the Security of Two-Round Multi-Signatures”, IEEE
  S&P 2019. Concurrent-session attacks on two-round Schnorr signing.
- F. Benhamouda, T. Lepoint, J. Loss, M. Orrù, M. Raykova, “On the
  (in)security of ROS”, EUROCRYPT
  2021. The polynomial-time attack that FROST’s binding factor prevents.
- R. Gennaro, S. Jarecki, H. Krawczyk, T. Rabin, “Secure Distributed Key
  Generation for Discrete-Log Based Cryptosystems”, *Journal of
  Cryptology* 20, 2007. Why Pedersen’s DKG needs care.
- A. Herzberg, S. Jarecki, H. Krawczyk, M. Yung, “Proactive Secret
  Sharing”, CRYPTO 1995.
- Coinbase, cb-mpc `docs/theory/` and `docs/spec/`. Short, readable
  justifications for each protocol choice.

------------------------------------------------------------------------

Previous: [Chapter 1, Foundations](01-foundations.md) \| [All
chapters](../README.md) \| Next: [Chapter 3, Key
Storage](03-key-storage.md)
