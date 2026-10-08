# Module 7: Post-Quantum Cryptography

2026-10-08

Previous: [Chapter 6, Proof of Reserves](06-reserves.md) \| [All
chapters](../README.md) \| Next: [Chapter 8, Industry and
Regulation](08-industry.md)

> [!WARNING]
>
> ### EDUCATIONAL, NOT PRODUCTION
>
> `custody_lab.pq.wots` (WOTS+ and XMSS as FIPS 205 defines them) is
> teaching code, checked against the NIST ACVP vectors. ML-DSA and
> ML-KEM come from `cryptography` (OpenSSL). SLH-DSA comes from
> RustCrypto `slh-dsa` through the `custody_pq` extension; that crate’s
> README states it has never been independently audited. The Lamport and
> LWE cells are illustrations, not implementations of a standard.

<a id="what-this-chapter-is-for"></a>

## What this chapter is for

Every key in chapters [1](01-foundations.md) to [6](06-reserves.md)
rests on one of two problems being hard: the discrete logarithm
([chapter 1](01-foundations.md)’s “easy forwards, infeasible backwards”)
or, for Paillier encryption, factoring large numbers. A **quantum
computer** is a machine that computes with quantum-mechanical states
rather than ordinary bits. For most tasks it is no faster than an
ordinary computer. For a few specific mathematical problems it is
enormously faster, and those two are among them. A large enough one
running **Shor’s algorithm** would compute a private key from its public
key quickly. Every public key in this manual would then give up its
private key: the secp256k1 custody key, the Ed25519 approval keys, the
Paillier modulus. No such computer exists (**verify current**). The
question for a custodian is what has to be done before one does.

Two clocks run differently, and they decide the order of the work.

- **Signatures** fail on the day the computer arrives. A forged approval
  or a stolen coin needs the computer at the time of the attack. But
  anything whose public key is already visible can be attacked on that
  day, and a Taproot output shows its key on the chain from the moment
  it is created.
- **Encryption** fails retroactively. Ciphertext recorded today can be
  decrypted later. A key-share backup encrypted to an elliptic-curve
  recovery key is exposed as soon as someone copies it, even though the
  break comes years later. This is **harvest now, decrypt later**.

A FIX engineer has lived through a smaller version of this: deprecating
TLS versions and cipher suites across every session an exchange accepts.
The comparison stops holding at the chain. An exchange can change its
cipher suites on a date it chooses; a custodian cannot change the
signature scheme Bitcoin accepts. The parts the custodian controls can
move now, and the demo moves one of them: its policy authorisations are
signed with both Ed25519 and ML-DSA, a signature scheme designed to
resist quantum computers.

By the end of this chapter the following should be clear:

- which primitives in chapters [1](01-foundations.md) to
  [6](06-reserves.md) a large quantum computer breaks, and which it only
  weakens;
- how a signature can be built from a hash function alone: Lamport keys,
  Winternitz chains with their checksum, and a Merkle tree of one-time
  keys, and why reusing a one-time key is fatal;
- the structure of the three NIST standards, ML-KEM, ML-DSA and SLH-DSA,
  their sizes, and the problem each rests on;
- why post-quantum signatures are hard to produce with a threshold of
  signers;
- the order in which a custodian should migrate, and which steps it
  controls.

<a id="first-principles"></a>

## First principles

This section assumes [chapter 1](01-foundations.md) (hashes,
signatures), [chapter 2](02-mpc-custody.md) (commitments), [chapter
3](03-key-storage.md) (symmetric encryption and key encapsulation) and
[chapter 6](06-reserves.md) (Merkle trees).

<a id="what-a-quantum-computer-breaks"></a>

### What a quantum computer breaks

**The idea.** Two quantum algorithms matter for this manual, and they do
very different damage.

- **Shor’s algorithm** solves the discrete logarithm and factoring in a
  number of steps that grows only modestly with the key size. Recovering
  a 256-bit private key goes from about $2^{128}$ steps to a number of
  quantum operations that grows roughly with the cube of the key length,
  which a large enough machine would complete in practical time. Every
  scheme built on those problems is *broken*: changing the key size does
  not help.
- **Grover’s algorithm** speeds up brute-force search of a space of
  $2^k$ values to about $2^{k/2}$ steps. That halves the effective size
  of a key or hash: a 256-bit key behaves like a 128-bit one, which is
  still far beyond reach. Schemes that rest on hash functions or
  symmetric ciphers are only *weakened*, and choosing 256-bit sizes
  restores the margin.

| Primitive | Where in this manual | Effect of a large quantum computer |
|----|----|----|
| secp256k1 ECDSA, BIP340 | chapters [1](01-foundations.md), [2](02-mpc-custody.md), [5](05-settlement.md) | broken: the private key follows from the public key |
| Ed25519 | [chapter 4](04-policy.md) approvals | broken |
| Paillier | [chapter 2](02-mpc-custody.md) | broken: it rests on factoring |
| Feldman, Pedersen commitments | chapters [2](02-mpc-custody.md), [6](06-reserves.md) | binding broken (discrete logarithm); Pedersen hiding survives |
| SHA-256, tagged hashes | everywhere | weakened only |
| Merkle trees, hash commitments | chapters [4](04-policy.md), [6](06-reserves.md) | weakened only |
| AES-256 | [chapter 3](03-key-storage.md), this chapter | weakened only |

The replacements NIST standardised in 2024 rest on two kinds of problem
that no known quantum algorithm solves efficiently: inverting hash
functions, and finding short vectors in lattices. The next three
sections build the hash-based kind from nothing; the fourth gives the
idea behind the lattice kind.

**Recap.** Shor breaks every discrete-logarithm and factoring scheme
outright; Grover only halves the strength of hashes and symmetric keys.

<a id="signatures-from-a-hash-alone-lamport"></a>

### Signatures from a hash alone: Lamport

**The problem.** If elliptic-curve keys fall, something else must
produce signatures. Hash functions survive, and it turns out a hash
function is all a signature needs, at a price.

**The idea.** Lamport’s scheme (1979) works bit by bit:

- **Key.** Pick 256 pairs of random secrets, one pair for each bit of a
  message digest: one secret for “this bit is 0” and one for “this bit
  is 1”. The public key is the hash of every secret.
- **Sign.** For each bit of the message digest, reveal the secret for
  that bit’s value.
- **Verify.** Hash each revealed secret and compare it with the matching
  public-key entry.

Nobody can sign without the secrets, because producing a secret from its
hash means inverting the hash function.

**What breaks: reuse.** The key is **one-time**. Each signature reveals
half of the secrets, and a second signature on a different digest
reveals more: wherever the two digests differ, both secrets of that pair
are now public. After enough signatures, an attacker knows both secrets
at almost every position and can sign a message of its choosing. The
cell signs eight messages with one key, then forges a ninth:

``` python
import hashlib


def H(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def digest_bits(message: bytes) -> list[int]:
    value = int.from_bytes(H(message), "big")
    return [(value >> (255 - i)) & 1 for i in range(256)]


secret = [[H(b"lamport" + bytes([b]) + i.to_bytes(2, "big")) for b in (0, 1)] for i in range(256)]
public = [[H(s) for s in pair] for pair in secret]


def sign(message: bytes) -> list[bytes]:
    return [secret[i][b] for i, b in enumerate(digest_bits(message))]


def verify(message: bytes, signature: list[bytes]) -> bool:
    return all(H(s) == public[i][b] for i, (s, b) in enumerate(zip(signature, digest_bits(message))))


leaked: list[dict[int, bytes]] = [{} for _ in range(256)]
for k in range(1, 9):  # eight signatures with one key
    message = f"pay {k} BTC to exchange".encode()
    for i, (b, s) in enumerate(zip(digest_bits(message), sign(message))):
        leaked[i][b] = s
tries = 0
while True:
    tries += 1
    target = f"pay 1000 BTC to attacker, attempt {tries}".encode()
    if all(b in leaked[i] for i, b in enumerate(digest_bits(target))):
        break
forged = [leaked[i][b] for i, b in enumerate(digest_bits(target))]
assert verify(target, forged) and tries == 2
print(f"positions with one leaked secret: {sum(len(p) == 1 for p in leaked)} of 256")
print(f"forged {target.decode()!r} after {tries} tries")
```

    positions with one leaked secret: 1 of 256
    forged 'pay 1000 BTC to attacker, attempt 2' after 2 tries

The first printed line shows how few positions still had only one secret
leaked after eight signatures. The second shows that a forgery on an
arbitrary message took two attempts: the attacker just tries messages
until every bit of the digest lands on a leaked secret.

**Recap.** A hash function alone gives a signature, but each key may
sign once.

<a id="winternitz-chains-and-the-checksum"></a>

### Winternitz chains and the checksum

**The problem.** Lamport’s signatures are large: two 32-byte secrets per
bit of the digest, 16 KB of key for one signature. Winternitz signatures
sign several bits per secret.

**The idea.** Take one secret and hash it repeatedly, forming a **hash
chain**: position 0 is the secret, position 1 is its hash, position 2
the hash of that, and so on. The last position goes into the public key.
To sign a digit $a$, the signer reveals position $a$. The verifier
hashes it the remaining steps to the end and compares with the public
key.

**Worked by hand**, with chains of length 4, so each chain signs one
digit from 0 to 3. To sign the digit 2, the signer reveals position 2,
and the verifier hashes once to reach position 3, the public end.

The chain runs only forward, and that is a weakness. Anyone holding
position 2 can hash it once to get position 3, which is a valid
signature for the digit 3. A signature on 2 can be turned into a
signature on 3 without the secret.

A **checksum** stops this. The signer also signs, on a second chain, the
value $3 - a$: here $3 - 2 = 1$, so it reveals position 1 of the
checksum chain. To raise the message digit to 3, an attacker would also
have to lower the checksum digit to $3 - 3 = 0$, which means going from
position 1 back to position 0 of the checksum chain: inverting the hash.
Raising any message digit lowers the checksum, so every forgery needs
one backward step somewhere.

``` python
def chain(start: bytes, steps: int) -> bytes:
    for _ in range(steps):
        start = H(start)
    return start


message_secret, checksum_secret = H(b"message chain"), H(b"checksum chain")
public_ends = (chain(message_secret, 3), chain(checksum_secret, 3))


def toy_sign(digit: int) -> tuple[bytes, bytes]:
    return chain(message_secret, digit), chain(checksum_secret, 3 - digit)


def toy_verify(digit: int, sig: tuple[bytes, bytes]) -> bool:
    return (chain(sig[0], 3 - digit), chain(sig[1], digit)) == public_ends


sig = toy_sign(2)
assert toy_verify(2, sig)
raised = (H(sig[0]), sig[1])  # advance the message chain one step: digit 3
assert not toy_verify(3, raised)  # the checksum chain would have to step backwards
print("digit 2 signed; raising it to 3 fails on the checksum chain")
```

    digit 2 signed; raising it to 3 fails on the checksum chain

**WOTS+ in the standard.** WOTS+ is the version FIPS 205 standardises,
with chains of length 16, so each chain signs a 4-bit digit. Every hash
call also takes a public seed and a 32-byte **address** naming its
layer, tree, key pair, chain and step, so no two calls anywhere in the
scheme hash the same input. For SLH-DSA-SHA2-128f a digest is 16 bytes:
32 message digits plus 3 checksum digits, 35 chains in all. The cell
runs the teaching WOTS+ and repeats the advancing attack on a real
signature:

``` python
import secrets

from custody_lab.pq import wots

sk_seed, pk_seed = secrets.token_bytes(wots.N), secrets.token_bytes(wots.N)
adrs = wots.top_layer_address()
adrs.set_type_and_clear(wots.WOTS_HASH)
public_key = wots.wots_public_key(sk_seed, pk_seed, adrs.copy())

message = bytes.fromhex("0123456789abcdef0123456789abcdef")
digits = wots.digits_with_checksum(message)
signature = wots.wots_sign(message, sk_seed, pk_seed, adrs.copy())
recovered = wots.wots_public_key_from_signature(signature, message, pk_seed, adrs.copy())
assert recovered == public_key

raised = bytes([message[0] + 16]) + message[1:]  # first digit 0 -> 1
step = adrs.copy()
step.set_chain(0)
advanced = [wots.chain(signature[0], digits[0], 1, pk_seed, step), *signature[1:]]
assert wots.wots_public_key_from_signature(advanced, raised, pk_seed, adrs.copy()) != public_key
print("digits:", digits[:8], "... checksum digits:", digits[wots.LEN1:])
print("one chain advanced a step: the checksum no longer matches")
```

    digits: [0, 1, 2, 3, 4, 5, 6, 7] ... checksum digits: [0, 15, 0]
    one chain advanced a step: the checksum no longer matches

The first printed line shows the message digits (the hexadecimal digits
of the message, one per chain) and the three checksum digits. The second
confirms that advancing one chain, the forgery the checksum exists to
stop, produces a public key that does not match.

**Recap.** A hash chain signs a digit by revealing a position along it;
a checksum on a second chain makes any attempt to raise a digit require
stepping some chain backwards.

<a id="a-merkle-tree-of-one-time-keys"></a>

### A Merkle tree of one-time keys

**The problem.** A one-time key is not enough for a custodian that signs
every day.

**The idea.** **XMSS** puts $2^{h'}$ WOTS+ public keys at the leaves of
a Merkle tree ([chapter 6](06-reserves.md)), and the tree’s root becomes
the long-term public key. A signature is one WOTS+ signature from one
leaf, plus the authentication path from that leaf to the root, which
proves the one-time key belongs to the long-term key.

That makes the signer **stateful**. It must never use a leaf twice, so
it has to record which leaves it has used, and restoring a signer from a
backup can bring back a leaf it has already used. XMSS and LMS (NIST SP
800-208) are stateful schemes and are standardised on that basis, with
that operational risk stated.

**SLH-DSA** (FIPS 205) removes the state. It stacks XMSS trees into a
**hypertree** of $d$ layers, in which each tree signs the root of the
tree below it. It signs the message itself with **FORS**, a few-time
scheme (one that tolerates a small number of signatures per key), at a
leaf chosen by a hash of the message. With $2^{66}$ leaves in the
SHA2-128f parameter set, two messages landing on the same leaf often
enough to matter is negligible, and nothing has to be recorded. The
price is size: a 17,088-byte signature. The public root is the root of
the top layer’s tree. The cell computes it from NIST’s seeds and
compares it with NIST’s expected public key.

``` python
import json
from pathlib import Path

vectors = json.loads(Path("../../tests/pq/vectors/acvp-subset.json").read_text())
nist = next(t for t in vectors["slh_dsa_keygen"] if t["parameterSet"] == "SLH-DSA-SHA2-128f")
seed_sk, seed_pk = bytes.fromhex(nist["skSeed"]), bytes.fromhex(nist["pkSeed"])
assert seed_pk + wots.keygen_root(seed_sk, seed_pk) == bytes.fromhex(nist["pk"])

root = wots.keygen_root(sk_seed, pk_seed)
leaf_signature = wots.xmss_sign(message, sk_seed, 5, pk_seed, wots.top_layer_address())
assert wots.xmss_root_from_signature(leaf_signature, message, pk_seed, wots.top_layer_address()) == root
print(f"NIST tcId {nist['tcId']}: teaching root matches; leaf 5 path has",
      len(leaf_signature.auth_path), "siblings")
```

    NIST tcId 21: teaching root matches; leaf 5 path has 3 siblings

The printed line names the NIST test case whose public key the teaching
code reproduced, and the number of siblings in an XMSS authentication
path: one per level of the tree.

**Recap.** XMSS turns many one-time keys into one long-term key with a
Merkle tree, at the cost of remembering which leaves are used; SLH-DSA
picks leaves by hash from a tree so large that no record is needed.

<a id="lattices-in-one-bit"></a>

### Lattices in one bit

**The problem.** Hash-based signatures are large. The other NIST family,
built on lattices, is much smaller and also gives encryption, which
hashes alone cannot.

**The idea.** ML-KEM and ML-DSA rest on **learning with errors** (LWE).
Take a secret list of numbers $s$ and publish many equations
$b_i = a_i \cdot s + e_i \bmod q$, where each $a_i$ is a random list of
numbers, $a_i \cdot s$ is the sum of their products with $s$, and each
**error** $e_i$ is a small random number, such as $-1$, $0$ or $1$.
Without the errors, a handful of equations would give $s$ by ordinary
elimination, the method taught in school for simultaneous equations.
With the errors, elimination amplifies them until the answer is noise,
and recovering $s$ from large instances is believed hard for quantum
computers as well as ordinary ones (Regev 2005).

**Encryption follows.** To encrypt a bit, add up a random subset of the
published equations, and add $\lfloor q/2 \rfloor$ (half the modulus) if
the bit is 1. The holder of $s$ subtracts $s$’s contribution and is left
with the bit’s offset plus a sum of small errors: a result near 0 means
0, and a result near $q/2$ means 1. Everyone else sees only sums of
noisy equations. The toy below uses $q = 97$, a secret of length 4 and
eight equations, small enough to break by exhaustive search; ML-KEM-768
uses vectors of polynomials with 768 coefficients in all.

``` python
import random

q, n, m = 97, 4, 8
rng = random.Random(7)
s = [rng.randrange(q) for _ in range(n)]
A = [[rng.randrange(q) for _ in range(n)] for _ in range(m)]
e = [rng.choice((-1, 0, 1)) for _ in range(m)]
b = [(sum(a * x for a, x in zip(row, s)) + err) % q for row, err in zip(A, e)]


def encrypt(bit: int, subset: list[int]) -> tuple[list[int], int]:
    u = [sum(subset[i] * A[i][j] for i in range(m)) % q for j in range(n)]
    return u, (sum(subset[i] * b[i] for i in range(m)) + bit * (q // 2)) % q


def decrypt(u: list[int], v: int) -> int:
    x = (v - sum(ui * si for ui, si in zip(u, s))) % q
    return 0 if min(x, q - x) < q // 4 else 1


subsets = [[(k >> i) & 1 for i in range(m)] for k in range(2**m)]
assert all(decrypt(*encrypt(bit, r)) == bit for bit in (0, 1) for r in subsets)
print("secret", s, "errors", e)
print("all", 2 * len(subsets), "(bit, subset) pairs decrypt correctly")
```

    secret [41, 19, 50, 83] errors [1, -1, 0, 0, -1, 1, -1, 1]
    all 512 (bit, subset) pairs decrypt correctly

The cell encrypts both bit values under every one of the 256 possible
subsets and decrypts all 512 correctly. The error sum is at most 8 in
absolute value, well inside the $q/4 = 24$ margin, so decryption never
fails here. Real parameters choose the error distribution so that
failure is negligible.

**Recap.** LWE hides a secret behind equations with small errors; the
holder of the secret can strip the equations away and read a bit from
what is left.

<a id="formal-treatment"></a>

## Formal treatment

<a id="ml-kem-fips-203"></a>

### ML-KEM (FIPS 203)

[Chapter 3](03-key-storage.md) introduced a key encapsulation mechanism:
the sender runs `encapsulate` on the recipient’s public key and obtains
a 32-byte shared secret and a ciphertext; the recipient runs
`decapsulate` on the ciphertext and obtains the same secret. ML-KEM is
built on module-LWE: the numbers in the LWE equations above become
polynomials, and the lists become short vectors of polynomials, which
makes keys smaller for the same security. Parameter sets 512, 768 and
1024 target NIST security categories 1, 3 and 5, roughly the strength of
AES-128, AES-192 and AES-256.

<a id="ml-dsa-fips-204"></a>

### ML-DSA (FIPS 204)

ML-DSA is a Fiat-Shamir signature ([chapter 1](01-foundations.md)) over
module lattices. In outline, with a secret $s_1$ whose coefficients are
small:

$$
y \xleftarrow{\$} \text{(small)}, \quad w = Ay, \quad c = H(\mu \,\|\, \text{HighBits}(w)), \quad z = y + c\,s_1 .
$$

$y$ plays the nonce’s role, $w$ the commitment’s, $c$ the challenge’s
(computed from the message digest $\mu$ and the commitment), and $z$ the
response’s. This has the same shape as Schnorr’s $s = k + e\,d$. The
difference is **rejection**: if $z$ is too large, or a condition on the
low bits fails, the signer discards the attempt and starts again with a
new $y$. Without rejection, the distribution of $z$ would show traces of
$s_1$, because small numbers do not hide each other the way uniformly
random numbers modulo $n$ do. This is **Fiat-Shamir with aborts**
(Lyubashevsky 2009). Signing takes several attempts on average, and each
rejected attempt must stay secret.

<a id="slh-dsa-fips-205"></a>

### SLH-DSA (FIPS 205)

A signature is a randomiser $R$, a FORS signature on the message digest,
and $d$ XMSS signatures up the hypertree. The verifier recomputes the
FORS public key, then each XMSS root in turn, and compares the last with
the public root. Security rests only on the hash function. The “s”
parameter sets give smaller, slower signatures and the “f” sets larger,
faster ones.

<a id="sizes"></a>

### Sizes

The cell measures every scheme in the manual with the libraries the
project uses.

``` python
import custody_pq
from cryptography.hazmat.primitives.asymmetric import mldsa, mlkem
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from custody_lab.foundations import schnorr

bip340_key = (3).to_bytes(32, "big")
ed = Ed25519PrivateKey.generate()
dsa = mldsa.MLDSA65PrivateKey.generate()
kem = mlkem.MLKEM768PrivateKey.generate()
slh = {ps: custody_pq.keygen(ps) for ps in ("SLH-DSA-SHA2-128s", "SLH-DSA-SHA2-128f")}
rows = [
    ("BIP340 (secp256k1)", len(schnorr.pubkey_gen(bip340_key)),
     len(schnorr.sign(bytes(32), bip340_key, bytes(32)))),
    ("Ed25519", len(ed.public_key().public_bytes_raw()), len(ed.sign(b"m"))),
    ("ML-DSA-65", len(dsa.public_key().public_bytes_raw()), len(dsa.sign(b"m"))),
    *[(ps.removeprefix("SLH-DSA-"), len(pk), len(custody_pq.sign(ps, sk, b"m")))
      for ps, (sk, pk) in slh.items()],
    ("ML-KEM-768 (ciphertext)", len(kem.public_key().public_bytes_raw()),
     len(kem.public_key().encapsulate()[1])),
]
assert [r[1:] for r in rows] == [(32, 64), (32, 64), (1952, 3309), (32, 7856), (32, 17088),
                                 (1184, 1088)]
print(f"{'scheme':<26}{'public key':>12}{'signature':>12}")
for name, pk_len, sig_len in rows:
    print(f"{name:<26}{pk_len:>12,}{sig_len:>12,}")
```

    scheme                      public key   signature
    BIP340 (secp256k1)                  32          64
    Ed25519                             32          64
    ML-DSA-65                        1,952       3,309
    SHA2-128s                           32       7,856
    SHA2-128f                           32      17,088
    ML-KEM-768 (ciphertext)          1,184       1,088

Sizes are in bytes. ML-DSA-65’s signature is about 50 times a BIP340
signature, and SLH-DSA’s is between 120 and 270 times; for ML-KEM the
last column is the ciphertext, not a signature. On a blockchain, where
every byte costs fees, these sizes are the main obstacle to adoption.

<a id="the-demos-hybrid-authorisation"></a>

### The demo’s hybrid authorisation

The policy engine’s authorisation ([chapter 4](04-policy.md)) is the one
signature path the custodian controls end to end. Its token carries two
signatures over the same payload: Ed25519, and ML-DSA-65 with the FIPS
204 context string `custody-lab/authorisation`, a label that keeps these
signatures from being valid in any other context. A signer accepts a
token only if both verify. A forger would have to break both schemes:
Ed25519 falls to a quantum computer, and ML-DSA is new enough that a
flaw in it cannot be ruled out. The authority’s public key is 1,984
bytes (32 + 1,952), and each token carries 64 + 3,309 bytes of
signature.

<a id="threshold-post-quantum-signatures"></a>

## Threshold post-quantum signatures

[Chapter 2](02-mpc-custody.md) relied on Schnorr’s linearity: shares of
$k$ and $d$ give shares of $s$ that simply add. The post-quantum
signatures lose that property.

- **ML-DSA.** $z = y + c\,s_1$ is linear too, but the rejection test
  applies to the combined $z$. Parties cannot each test their own share,
  because a share that passes can still produce a combined $z$ that must
  be rejected. Testing the combined value without revealing it needs
  secure computation of a norm, and every rejected attempt must stay
  hidden. The authors of Threshold Raccoon (EUROCRYPT 2024) describe
  Dilithium, the basis of ML-DSA, as not easy to make threshold
  efficiently. Their scheme is designed for thresholds but does not
  produce FIPS 204 signatures. Research since 2025 produces FIPS
  204-compatible threshold ML-DSA under restrictions: Trilithium (two
  parties with a correlated-randomness helper), Quorus, and schemes for
  up to six parties (**verify current**).
- **SLH-DSA.** Signing evaluates the hash function thousands of times on
  secret seeds. There is no algebraic structure to split, so a threshold
  version means evaluating SHA-256 inside a generic secure computation,
  at a cost many orders of magnitude above signing alone.
- **Stateful schemes.** XMSS and LMS add a distributed-state problem:
  several signers must agree on which leaf is next, and no leaf may ever
  be used twice.

A custodian therefore has no audited, standard threshold post-quantum
signature today (**verify current**). The options are: a post-quantum
key held inside an HSM under an M-of-N administrative quorum ([chapter
1](01-foundations.md)’s Shamir model, with its single point of rebuild),
on-chain multisignature when the chain offers post-quantum scripts, or
waiting for threshold ML-DSA to mature.

<a id="migration-design"></a>

## Migration design

Order the work by exposure, and separate what the custodian controls
from what it does not.

| Component | Today | Exposure | Step | Controlled by |
|----|----|----|----|----|
| Share backups ([chapter 2](02-mpc-custody.md)) | encrypted to a recovery key | harvest now, decrypt later | ML-KEM, combined with X25519 | custodian |
| Authorisations ([chapter 4](04-policy.md)) | Ed25519 and ML-DSA-65 | none while ML-DSA holds | done in the demo | custodian |
| Approvals ([chapter 4](04-policy.md)) | Ed25519 | forged approvals | hybrid keys | approvers’ devices (**verify current**) |
| Proof of control ([chapter 6](06-reserves.md)) | BIP340 | forged attestations | a post-quantum attestation key alongside | custodian |
| Settlements ([chapter 5](05-settlement.md)) | FROST BIP340, Taproot key path | key visible on chain | new output type and signature | Bitcoin consensus, research |
| Transport (FIX, internal) | TLS | recorded sessions | hybrid key exchange | TLS stacks (**verify current**) |

The order follows the two clocks. Share backups come first, because a
copy taken today is broken whenever a quantum computer arrives; nothing
can be done for a ciphertext already copied. Internal signatures the
custodian controls come next, because changing them needs nobody else’s
agreement. Settlement signatures come last, because they depend on the
chain.

Three facts shape the chain row.

- **Taproot shows the key.** A key-path output (BIP 341) holds the
  output key itself, so every coin at the demo’s custody address is
  exposed for as long as it sits there. Outputs that commit to a hash of
  the key (P2WPKH) reveal the key only when spent. FROST’s Schnorr
  signatures need Taproot, so choosing FROST for signing is also
  choosing on-chain key exposure; threshold ECDSA (CGGMP, [chapter
  2](02-mpc-custody.md)) can use hashed outputs.
- **Bitcoin’s proposals.** BIP 360, merged into the BIP repository in
  2026, defines Pay-to-Merkle-Root: Taproot without the key path, so
  keys stay hidden until spend. It does not add a post-quantum signature
  itself. BIP 361 proposes a sunset for legacy signature types (**verify
  current** for both: status, activation and content).
- **Timelines.** NIST IR 8547 (initial public draft, 2024) proposes
  deprecating quantum-vulnerable public-key algorithms after 2030 and
  disallowing them after 2035 (**verify current**).

<a id="worked-example"></a>

## Worked example

The WOTS+ checksum for the all-zero 16-byte digest, with chains of
length 16:

| Step | Computation | Value |
|----|----|----|
| Message digits | 32 nibbles (4-bit digits) of 0x00…00 | all 0 |
| Checksum | $\sum_{i=1}^{32} (15 - 0)$ | 480 |
| Shift | $(8 - (3 \cdot 4) \bmod 8) \bmod 8 = 4$ bits: $480 \cdot 16$ | 7680 = 0x1E00 |
| Checksum digits | the first three nibbles of 0x1E00 | 1, 14, 0 |
| Revealed positions | 32 message chains at 0, checksum chains at 1, 14, 0 | 35 values |

The shift step aligns the checksum’s bits to whole bytes before it is
split into three 4-bit digits. The signature of the zero digest reveals
the 32 message chains’ secrets themselves, at position 0. An attacker
can advance them to sign any digest. But any change raises some message
digit, which lowers the checksum below 480. The checksum digits (1, 14,
0) would then have to move backwards on at least one chain.

``` python
digits = wots.digits_with_checksum(bytes(16))
assert digits[:wots.LEN1] == [0] * 32 and digits[wots.LEN1:] == [1, 14, 0]
assert (32 * 15) << 4 == 0x1E00
print("checksum digits of the zero digest:", digits[wots.LEN1:])
```

    checksum digits of the zero digest: [1, 14, 0]

<a id="code-walkthrough"></a>

## Code walkthrough

<a id="slh-dsa-ml-dsa-and-ml-kem-from-the-libraries"></a>

### SLH-DSA, ML-DSA and ML-KEM from the libraries

The full NIST checks run in `tests/pq/`: key generation for every
SLH-DSA parameter set, SLH-DSA verification and deterministic signing,
and ML-DSA and ML-KEM key generation and ML-DSA verification. This cell
repeats one of each on the stored vectors.

``` python
from cryptography.exceptions import InvalidSignature

t = vectors["slh_dsa_siggen"][0]
sk = bytes.fromhex(t["sk"])
reproduced = custody_pq.sign(t["parameterSet"], sk, bytes.fromhex(t["message"]),
                             bytes.fromhex(t["context"]), sk[32:48])
assert reproduced == bytes.fromhex(t["signature"])

t = vectors["ml_dsa_keygen"][3]
key = mldsa.MLDSA65PrivateKey.from_seed_bytes(bytes.fromhex(t["seed"]))
assert t["parameterSet"] == "ML-DSA-65"
assert key.public_key().public_bytes_raw() == bytes.fromhex(t["pk"])

rejected = next(t for t in vectors["ml_dsa_sigver"] if not t["testPassed"])
try:
    mldsa.MLDSA44PublicKey.from_public_bytes(bytes.fromhex(rejected["pk"])).verify(
        bytes.fromhex(rejected["signature"]), bytes.fromhex(rejected["message"]),
        bytes.fromhex(rejected["context"]))
    raise AssertionError("NIST's invalid signature verified")
except InvalidSignature:
    pass
print("SLH-DSA signature reproduced; ML-DSA key reproduced;")
print(f"ML-DSA rejects NIST's case: {rejected['reason']!r}")
```

    SLH-DSA signature reproduced; ML-DSA key reproduced;
    ML-DSA rejects NIST's case: 'modified message'

The last line quotes NIST’s own description of why that test signature
is invalid; the library rejected it, as it must.

<a id="a-share-backup-under-ml-kem"></a>

### A share backup under ML-KEM

A key share from [chapter 2](02-mpc-custody.md)’s teaching DKG,
encrypted to a recovery key with ML-KEM-768 and AES-256-GCM: the KEM
delivers a fresh AES key, and AES-GCM encrypts the share under it
([chapter 3](03-key-storage.md)). A recording of the ciphertext stays
unreadable to a future quantum computer, as long as ML-KEM holds.
Production designs combine ML-KEM with X25519, an elliptic-curve key
exchange, so that the backup also stays safe if ML-KEM falls.

``` python
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from custody_lab.mpc import dkg

shares, group_key = dkg.run(threshold=2, count=3)
share = shares[1].to_bytes(32, "big")

recovery = mlkem.MLKEM768PrivateKey.generate()  # held offline, under separate control
shared, encapsulated = recovery.public_key().encapsulate()
nonce = os.urandom(12)
backup = (encapsulated, nonce, AESGCM(shared).encrypt(nonce, share, b"share-backup/1"))

kem_ciphertext, n12, sealed = backup
restored = AESGCM(recovery.decapsulate(kem_ciphertext)).decrypt(n12, sealed, b"share-backup/1")
assert restored == share
print(f"backup: {len(kem_ciphertext)} + {len(n12)} + {len(sealed)} bytes; share restored")
```

    backup: 1088 + 12 + 48 bytes; share restored

The printed sizes are the three parts of the backup: the 1,088-byte
encapsulation, the 12-byte nonce, and the 32-byte share with its 16-byte
tag.

<a id="the-hybrid-authorisation"></a>

### The hybrid authorisation

Each half of the token is checked on its own. A token with a valid
Ed25519 signature but a foreign ML-DSA signature is refused, and so is
the reverse. The signers in chapters [2](02-mpc-custody.md),
[4](04-policy.md), [5](05-settlement.md) and [6](06-reserves.md) run
this same check before every share they produce.

``` python
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from custody_lab.policy import authorisation
from custody_lab.policy.authorisation import AuthorisationRejected, AuthorityKey

authority = AuthorityKey.generate()
now = datetime.now(UTC)
token = authorisation.issue(authority, bytes(32), b"\x6a" * 32, now + timedelta(minutes=1))
authorisation.check(token, authority.public_bytes(), b"\x6a" * 32, now)

other = authorisation.issue(AuthorityKey.generate(), bytes(32), b"\x6a" * 32,
                            now + timedelta(minutes=1))
for half in ("pq_signature", "signature"):
    try:
        authorisation.check(replace(token, **{half: getattr(other, half)}),
                            authority.public_bytes(), b"\x6a" * 32, now)
        raise AssertionError("a half-forged token passed")
    except AuthorisationRejected as refused:
        print("refused:", refused)
print(f"authority key {len(authority.public_bytes())} bytes; token {len(token.to_bytes())} bytes")
```

    refused: not signed by the policy authority (ML-DSA-65)
    refused: not signed by the policy authority (Ed25519)
    authority key 1984 bytes; token 7047 bytes

<a id="how-this-shows-up-in-production"></a>

## How this shows up in production

**Standards.** NIST published FIPS 203 (ML-KEM), FIPS 204 (ML-DSA) and
FIPS 205 (SLH-DSA) in August 2024. SP 800-208 covers the stateful XMSS
and LMS.

**Libraries.** OpenSSL now ships ML-KEM, ML-DSA and SLH-DSA;
`cryptography` 50 exposes the first two on this host, and RustCrypto
publishes pure-Rust crates for all three (**verify current** for audit
status).

**Key exchange first.** Major browsers and TLS stacks already negotiate
hybrid X25519 + ML-KEM key exchange, because recorded traffic is the
exposure that exists today (**verify current**).

**HSMs.** Vendor support for ML-DSA and ML-KEM inside HSMs depends on
firmware version and certification status (**verify current**). A
custodian’s approval devices set the pace for hybrid approvals.

**Bitcoin.** BIP 360 and BIP 361 are proposals; activation needs
community consensus and has no date. Coins whose public keys are already
on chain, including every Taproot key-path output, cannot be protected
by a later change unless their owners move them first.

<a id="recap"></a>

## Recap

1.  A large quantum computer running Shor’s algorithm breaks every
    discrete-logarithm and factoring scheme in this manual; Grover’s
    algorithm only halves the strength of hashes and symmetric keys.
2.  Signatures fail on the day the computer arrives; encryption fails
    retroactively, so recorded ciphertext is exposed today.
3.  A hash function alone gives one-time signatures (Lamport); hash
    chains with a checksum sign several bits per secret (Winternitz); a
    Merkle tree turns many one-time keys into one long-term key (XMSS),
    and a hypertree removes the need to track used leaves (SLH-DSA).
4.  Lattice schemes rest on learning with errors: equations with small
    errors hide a secret. ML-KEM encapsulates keys; ML-DSA signs with
    Fiat-Shamir with aborts.
5.  Post-quantum signatures are much larger than BIP340’s and hard to
    produce with a threshold: ML-DSA’s rejection test needs the combined
    value, and SLH-DSA has no algebra to split.
6.  A custodian should migrate backups first, then the internal
    signatures it controls, and settlements when the chain allows. The
    demo already signs its authorisations with Ed25519 and ML-DSA-65
    together.

[Chapter 8](08-industry.md) places the custody system in the financial
industry and its regulation.

<a id="exercises"></a>

## Exercises

1.  **Recall.** Which of these survive a large quantum computer
    unchanged in design, and which are broken: BIP340 signatures, the
    [chapter 6](06-reserves.md) Merkle sum tree, Paillier encryption, a
    hash commitment, a Pedersen commitment’s hiding property?
2.  **Compute.** Give the WOTS+ checksum digits for a 16-byte digest
    whose 32 digits are all 15.
3.  **Compute.** Lamport key reuse: after $k$ signatures on independent
    random digests, how many of the 256 positions are expected to have
    only one leaked secret? Evaluate for $k = 2$ and $k = 8$.
4.  **Explain.** Why does the demo’s signer require both halves of the
    hybrid token, rather than accepting either?
5.  **Design.** A custodian keeps its cold storage in Taproot key-path
    outputs under a FROST key. What is its quantum exposure today, and
    what could it change without waiting for Bitcoin?
6.  **Explain.** Why is ML-DSA harder to sign with a threshold than
    BIP340, although both responses have the form “random value plus
    challenge times secret”?

<a id="solutions"></a>

## Solutions

1.  The Merkle sum tree, hash commitments and Pedersen hiding survive:
    they rest on hash functions or on information-theoretic hiding.
    BIP340 (discrete logarithm) and Paillier (factoring) are broken.
2.  Each digit contributes $15 - 15 = 0$, so the checksum is 0 and its
    digits are 0, 0, 0.

``` python
assert wots.digits_with_checksum(b"\xff" * 16)[wots.LEN1:] == [0, 0, 0]
```

3.  A position has only one leaked secret when all $k$ digests agree on
    that bit, with probability $2 \cdot 2^{-k} = 2^{1-k}$. The
    expectation is $256 \cdot 2^{1-k}$: 128 for $k = 2$ and 2 for
    $k = 8$. A random target digest is then signable with probability
    about $2^{-128}$ and $1/4$ respectively; the cell above needed two
    tries.

``` python
assert [256 * 2 ** (1 - k) for k in (2, 8)] == [128, 2]
```

4.  Accepting either would make the token only as strong as the weaker
    scheme: a quantum attacker would forge the Ed25519 half, and an
    attacker with an ML-DSA break would forge the other. Requiring both
    makes a forgery need both breaks.
5.  Every coin at the address is exposed from the moment the output was
    created, because the output key is on chain. Changes within its
    control:
    - move long-term holdings to outputs that commit to a key hash,
      which reveal the key only at spend, accepting threshold ECDSA
      instead of FROST;
    - never reuse an address;
    - move its internal signatures (authorisations, approvals,
      attestations) and share backups to hybrid schemes;
    - track BIP 360 so it can move funds when a post-quantum output type
      activates.
6.  BIP340’s $s = k + e\,d$ is accepted unconditionally, so shares add.
    ML-DSA must reject any $z$ that is too large and restart, and that
    test applies to the combined $z$. A share that passes locally can
    still produce a combined $z$ that fails, so the parties must
    evaluate the test jointly and keep rejected attempts secret.

<a id="further-reading"></a>

## Further reading

- NIST FIPS 203, 204 and 205 (August 2024); NIST SP 800-208 (2020); NIST
  IR 8547 initial public draft (2024).
- P. W. Shor, “Polynomial-Time Algorithms for Prime Factorization and
  Discrete Logarithms on a Quantum Computer”, *SIAM Journal on
  Computing* 26(5), 1997. L. K. Grover, “A Fast Quantum Mechanical
  Algorithm for Database Search”, STOC 1996.
- L. Lamport, “Constructing Digital Signatures from a One Way Function”,
  SRI International CSL-98, 1979. R. C. Merkle, “A Certified Digital
  Signature”, CRYPTO 1989. A. Hülsing, “W-OTS+: Shorter Signatures for
  Hash-Based Signature Schemes”, AFRICACRYPT 2013.
- D. J. Bernstein et al., “The SPHINCS+ Signature Framework”, ACM
  CCS 2019. The design FIPS 205 standardises.
- O. Regev, “On Lattices, Learning with Errors, Random Linear Codes, and
  Cryptography”, STOC 2005. V. Lyubashevsky, “Fiat-Shamir with Aborts”,
  ASIACRYPT 2009.
- R. del Pino, S. Katsumata, M. Maller, F. Mouhartem, T. Prest, M.-J.
  Saarinen, “Threshold Raccoon: Practical Threshold Signatures from
  Standard Lattice Assumptions”, EUROCRYPT 2024 (IACR ePrint 2024/184).
- Trilithium (IACR ePrint 2025/675) and Quorus (IACR ePrint 2025/1163):
  FIPS 204-compatible distributed ML-DSA.
- BIP 360 (Pay-to-Merkle-Root) and BIP 361 (legacy signature sunset),
  Bitcoin BIP repository (**verify current**).

------------------------------------------------------------------------

Previous: [Chapter 6, Proof of Reserves](06-reserves.md) \| [All
chapters](../README.md) \| Next: [Chapter 8, Industry and
Regulation](08-industry.md)
