# Module 3: Key Storage

2026-10-08

Previous: [Chapter 2, MPC Custody](02-mpc-custody.md) \| [All
chapters](../README.md) \| Next: [Chapter 4, Policy and
Authorisation](04-policy.md)

> [!WARNING]
>
> ### EDUCATIONAL, NOT PRODUCTION
>
> This chapter has no module in `custody_lab`, and no cell talks to real
> hardware. The attestation report below has the shape of an SGX quote
> or a Nitro attestation document, not its format; the “processor” is an
> Ed25519 key. The key-wrapping cell uses `cryptography`’s AES key wrap
> and checks it against the RFC 3394 test vector.

<a id="what-this-chapter-is-for"></a>

## What this chapter is for

[Chapter 2](02-mpc-custody.md) split the custody key so that no single
machine holds it. Each machine still holds a share, and a share is a
secret number in some process’s memory. [Chapter 0](00-orientation.md)
warned that in the demo all three signer processes run on one computer,
where an administrator can read the memory of all three. This chapter
asks the question [chapter 2](02-mpc-custody.md) left open: where should
each share, and every other key in the system, physically live?

Three kinds of attacker motivate the question. An administrator, or
malware with administrator rights, on a signing server can read any
ordinary process’s memory. A thief who takes a backup tape gets whatever
is on it. And the people who run the data centre, or the cloud provider,
have physical access to the hardware. Different storage defends against
different ones.

Three answers are in production use:

- A **hardware security module** (**HSM**) is a separate,
  tamper-resistant device that generates keys, keeps them and signs with
  them. Keys enter and leave it only encrypted. Software outside asks it
  to sign; it never hands the key over.
- A **trusted execution environment** (**TEE**) is a region of an
  ordinary server’s processor and memory that the server’s own operating
  system cannot read. The key sits in normal memory, encrypted by the
  processor. The protected region is called an **enclave**.
- **MPC** ([chapter 2](02-mpc-custody.md)) keeps the key in no single
  place: each machine holds a share, and a threshold of them sign
  together.

Each answers a different question. An HSM answers “can this key be
copied?”. A TEE answers “can the operator of this machine read its
memory?”. MPC answers “is there one machine whose compromise is
enough?”. None of them answers “should this signature be made?”. That is
[chapter 4](04-policy.md)’s policy engine, and each option here signs
whatever an authenticated caller asks, unless the policy check runs
inside the protected boundary.

Payments engineers know the HSM as the payment HSM: PIN blocks are
translated inside the device, and the host never sees a clear PIN. The
comparison stops holding at finality. A misused card key leads to fraud
that a dispute process can often reverse, and the key is replaced by
reissuing cards. A Bitcoin settlement signed by a misused key is final,
and the custody key cannot be replaced without moving every coin it
controls to a new address.

By the end of this chapter the following should be clear:

- for an HSM, a TEE and an MPC cluster, where the key exists
  unencrypted, who can make it sign, and what an outside party can
  verify about either;
- how a key is wrapped under another key, and why an HSM exports keys
  only in that form;
- how remote attestation works, and why releasing a secret to an enclave
  must check three things in the attestation report, not two;
- which attacks each option does not defend against, including the
  memory-bus attacks published since 2025;
- where each part of the demo would live in a production deployment, and
  why.

<a id="first-principles"></a>

## First principles

This section assumes [chapter 1](01-foundations.md)’s hashes and
signatures. It also uses ordinary symmetric encryption, which the manual
has not covered so far, so it starts there.

<a id="three-questions-for-any-key-store"></a>

### Three questions for any key store

**The idea.** Three questions separate the options, and they are worth
asking of any key-storage product:

1.  **Where does the key exist unencrypted?** In an HSM, only inside the
    device. In a TEE, only inside the processor chip; the memory chips
    hold it encrypted. With MPC, nowhere: each share exists unencrypted
    on one machine, and the key on none.
2.  **Who can make it sign?** Whoever can authenticate to the HSM’s
    interface, send requests to the enclave’s code, or reach $t$
    signers. Protecting the key’s bytes is not the same as protecting
    its use: a key nobody can copy is still dangerous if anybody can ask
    it to sign.
3.  **What can an outsider verify?** For an HSM, a certificate that the
    device model passed a laboratory evaluation. For a TEE, a signed
    report naming the exact code that runs. For MPC, the public key and
    the protocol messages.

The **trusted computing base** (**TCB**) of a key is everything that
must behave correctly for the key to stay secret: hardware, firmware,
operating system, application code, and the people with administrative
access. A smaller TCB means fewer things that can go wrong. Each option
shrinks the TCB in a different direction: the HSM by moving the key into
a small dedicated device, the TEE by excluding the operating system, and
MPC by requiring several independent TCBs to fail at once.

<a id="symmetric-encryption-in-brief"></a>

### Symmetric encryption in brief

**The problem.** Several mechanisms in this chapter (wrapping a key for
backup, sealing a secret in an enclave, sending a share to a new signer)
encrypt one secret under another. They all use the same three building
blocks, none of which earlier chapters needed.

**Symmetric encryption.** Chapters [1](01-foundations.md) and
[2](02-mpc-custody.md) used key pairs, with a private and a public half.
Symmetric encryption uses one secret key for both directions: the same
key encrypts and decrypts. AES, the Advanced Encryption Standard, is the
one in universal use. It is much faster than any public-key scheme,
which is why public-key methods are normally used only to agree on or
deliver a symmetric key, and AES then does the bulk work.

**Authenticated encryption.** Plain encryption hides data but does not
detect tampering: flip a bit of the ciphertext and decryption silently
produces different data. Authenticated encryption adds a short check
value, the **tag**, computed from the key and the whole ciphertext.
Decryption recomputes it and refuses to return anything if it does not
match. AES-GCM is the common form. It also needs a fresh 12-byte nonce
for every encryption under one key; as with signatures, reusing it
breaks the scheme, although the reasons differ.

**Key derivation.** A **key derivation function** turns one secret into
many independent keys, each labelled for its purpose: derive(secret,
“backup”) and derive(secret, “seal/v1.4”) give unrelated keys, and
neither reveals the secret or the other. HKDF (RFC 5869) is the standard
construction, built from a hash function.

**Key encapsulation.** A **key encapsulation mechanism** (**KEM**) is
the public-key way to deliver a symmetric key. Anyone holding a public
key can create a fresh random secret together with an encapsulation of
it; only the holder of the matching private key can recover the secret
from the encapsulation. Both sides then use the secret as an AES key.
The code walkthrough uses ML-KEM, a KEM designed to resist quantum
computers; [chapter 7](07-post-quantum.md) explains its construction.

``` python
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

aes_key, nonce = AESGCM.generate_key(bit_length=256), os.urandom(12)
ciphertext = AESGCM(aes_key).encrypt(nonce, b"key share 2", None)
assert AESGCM(aes_key).decrypt(nonce, ciphertext, None) == b"key share 2"
try:
    tampered = bytes([ciphertext[0] ^ 1]) + ciphertext[1:]
    AESGCM(aes_key).decrypt(nonce, tampered, None)
    raise AssertionError("a modified ciphertext decrypted")
except InvalidTag:
    print(f"{len(ciphertext)} bytes: 11 of data + 16 of tag; one flipped bit is refused")
```

    27 bytes: 11 of data + 16 of tag; one flipped bit is refused

The printed line shows the cost of authentication, a 16-byte tag on
every ciphertext, and its benefit: a single flipped bit makes decryption
fail instead of returning altered data.

**Recap.** AES encrypts with one shared key; GCM adds a tag that detects
tampering; HKDF derives labelled keys from one secret; a KEM delivers a
fresh AES key to the holder of a private key.

<a id="key-wrapping"></a>

### Key wrapping

**The problem.** A key sometimes has to leave its device: for a backup,
or to copy it between the HSMs of one cluster so either can sign. It
must not leave readable.

**The idea.** It leaves **wrapped**: encrypted under a **key-encryption
key** (**KEK**) that itself never leaves the device. AES key wrap (RFC
3394; NIST SP 800-38F) is the standard construction for this. Unlike
AES-GCM it needs no nonce, because the data it encrypts is itself a
random key, and it carries an integrity check, so a modified wrapped key
fails to unwrap instead of unwrapping to a wrong key. RFC 3394 publishes
a test vector, and the cell checks the library against it:

``` python
from cryptography.hazmat.primitives.keywrap import InvalidUnwrap, aes_key_unwrap, aes_key_wrap

kek = bytes.fromhex("000102030405060708090A0B0C0D0E0F")  # RFC 3394, section 4.1
key = bytes.fromhex("00112233445566778899AABBCCDDEEFF")
wrapped = aes_key_wrap(kek, key)
assert wrapped == bytes.fromhex("1FA68B0A8112B447AEF34BD8FB5A7B829D3E862371D2CFE5")
assert aes_key_unwrap(kek, wrapped) == key

tampered = bytes([wrapped[0] ^ 1]) + wrapped[1:]
try:
    aes_key_unwrap(kek, tampered)
    raise AssertionError("a modified wrapped key unwrapped")
except InvalidUnwrap:
    print(f"{len(key)}-byte key wrapped into {len(wrapped)} bytes; a flipped bit is refused")
```

    16-byte key wrapped into 24 bytes; a flipped bit is refused

The wrapped key is 8 bytes longer than the key: those 8 bytes are the
integrity check.

**Key attributes.** An HSM labels each key with attributes that control
what may happen to it. In the PKCS#11 interface (formal treatment), a
**sensitive** key never leaves in plaintext, and an **extractable** key
may leave wrapped. A key generated as non-extractable cannot leave at
all through the standard interface. Its backups then use the vendor’s
own cloning or encrypted key-blob mechanism, which ties the custodian to
that vendor: the backup opens only in another of that vendor’s devices.

**Recap.** Keys travel only wrapped under a key that stays inside the
device; attributes fix, at creation, whether a key may travel at all.

<a id="tamper-response-and-certification-levels"></a>

### Tamper response and certification levels

**The problem.** An HSM’s promise that keys never leave is worth
something only if opening the device does not reveal them.

**The idea.** An HSM defends its keys physically in three ways:

- **tamper evidence**: seals and coatings that show the device was
  opened;
- **tamper resistance**: an enclosure that is hard to open;
- **tamper response**: sensors (a wire mesh around the electronics,
  light, temperature, voltage) that trigger **zeroisation**, overwriting
  the keys before an attacker reaches them.

**Certification.** A buyer cannot test these claims, so an accredited
laboratory does, against **FIPS 140-3**, the US and Canadian standard
for cryptographic modules (aligned with ISO/IEC 19790). It certifies a
module at one of four **security levels**:

| Level | Physical security | Operator authentication |
|----|----|----|
| 1 | None required; a software library can qualify | None required |
| 2 | Tamper evidence | Role-based |
| 3 | Tamper resistance with detection and response; environmental failure protection or testing | Identity-based |
| 4 | A complete protective envelope; protection against environmental and fault-injection attacks | Multi-factor |

A certificate covers one module version. A firmware update that adds an
algorithm, such as BIP340 or ML-DSA, is outside the certificate until
the new version is validated, which can take many months. NIST’s curve
recommendations (SP 800-186) allow secp256k1, Bitcoin’s curve, for
blockchain-related applications only, so a custodian’s auditors may ask
why a non-standard curve is in use; that clause is the answer.

**Recap.** Physical tamper response erases keys when the device is
opened; a FIPS 140-3 level states, for one firmware version, how much of
that a laboratory confirmed.

<a id="remote-attestation"></a>

### Remote attestation

**The problem.** A TEE has no sealed box to certify. Its protection
depends on the exact code running inside the enclave: a signer that
checks the policy authorisation before signing is safe, and a patched
signer that skips the check is not, although both run in a genuine
enclave. Anyone about to trust an enclave, for example by sending it a
key share, needs to know which code it runs.

**The idea.** The processor proves what code it runs. The proof works
like a signed build manifest, with the processor itself as the signer:

- A **measurement** is a hash of the code and initial data loaded into
  the enclave, computed by the processor as it loads them. One changed
  byte gives a different measurement.
- An **attestation report** is the measurement plus up to 64 bytes of
  **report data** chosen by the code inside the enclave. The report is
  signed by a key that the processor maker built into the chip and
  certified: the **root of trust**.
- A verifier checks the signature up to the maker’s root certificate,
  compares the measurement with the value it expects for code it has
  reviewed, and reads the report data.

This is **remote attestation**. It differs from [chapter
6](06-reserves.md)’s attestation, which is the custodian’s signed
statement about its reserves. Remote attestation is the hardware’s
signed statement about software.

The cell models it. An Ed25519 key stands in for the key inside the
chip. The reviewed signer build produces a report with the expected
measurement. A patched build that skips the authorisation check produces
a report that is just as genuinely signed, with a different measurement.

``` python
import hashlib

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

chip = Ed25519PrivateKey.generate()  # stands in for the key the maker built into the processor
maker_root = chip.public_key()       # what every verifier trusts


def load_and_report(image: bytes, report_data: bytes) -> tuple[bytes, bytes]:
    """The processor measures what it loads; the code inside chooses the report data."""
    body = hashlib.sha256(image).digest() + report_data.ljust(64, b"\0")
    return body, chip.sign(body)


reviewed = b"signer v1.4: check the authorisation, then sign"
expected = hashlib.sha256(reviewed).digest()

body, signature = load_and_report(reviewed, b"")
maker_root.verify(signature, body)  # raises InvalidSignature unless the chip signed it
assert body[:32] == expected

patched = reviewed.replace(b"check the authorisation, then ", b"")
body, signature = load_and_report(patched, b"")
maker_root.verify(signature, body)  # a genuine report from genuine hardware
assert body[:32] != expected        # of code nobody reviewed
print(f"patched build: measurement {body[:4].hex()}..., expected {expected[:4].hex()}...")
```

    patched build: measurement 254a8d67..., expected 0c083143...

The printed line shows the patched build’s measurement next to the
expected one. Both reports pass the signature check. So the signature
proves genuine hardware, and only the comparison with the expected
measurement proves the right code. A verifier that checks the signature
alone accepts the patched signer.

**Recap.** An attestation report is the chip’s signature over a hash of
the code it loaded, plus data the code chose. Trust it only after
checking the signature and the measurement, and, as the code walkthrough
shows, the report data.

<a id="sealing"></a>

### Sealing

**The problem.** An enclave has no storage of its own that the host
cannot read: anything it writes to disk passes through the host’s
operating system. Yet a signer must keep its share across restarts.

**The idea.** The enclave **seals** the secret: it encrypts it under a
key that the processor derives, with a key derivation function, from a
secret built into the chip and from the enclave’s identity. Only the
same chip, running an enclave with the same identity, can derive that
key again. There are two choices of identity:

- **seal to the measurement**: only identical code can unseal, so an
  upgrade loses access unless the old version hands the secret over
  first;
- **seal to the signer**: any build signed by the same developer key can
  unseal, so upgrades work, and a stolen developer key unseals every
  secret.

``` python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

device_secret = os.urandom(32)  # built into the chip; only the processor can read it


def sealing_key(identity: bytes) -> bytes:
    return HKDF(hashes.SHA256(), 32, salt=None, info=b"seal/" + identity).derive(device_secret)


v14, v15 = hashlib.sha256(b"signer v1.4").digest(), hashlib.sha256(b"signer v1.5").digest()
nonce = os.urandom(12)
sealed = AESGCM(sealing_key(v14)).encrypt(nonce, b"key share 2", None)
assert AESGCM(sealing_key(v14)).decrypt(nonce, sealed, None) == b"key share 2"
try:
    AESGCM(sealing_key(v15)).decrypt(nonce, sealed, None)
    raise AssertionError("another measurement unsealed the share")
except InvalidTag:
    print("v1.5 cannot unseal what v1.4 sealed to its own measurement")
```

    v1.5 cannot unseal what v1.4 sealed to its own measurement

Version 1.5 derives a different sealing key, so authenticated decryption
refuses the sealed share. Exercise 4 asks how to carry a share across
such an upgrade.

AWS Nitro Enclaves have no persistent storage and no sealing at all. An
enclave there fetches its secrets after every start from a key service
that checks its attestation first. The code walkthrough builds that
pattern.

**Recap.** Sealing encrypts a secret under a key only the same chip and
the same enclave identity can derive; sealing to the measurement
survives no upgrade, and sealing to the signer trusts the developer’s
key.

<a id="side-channels"></a>

### Side channels

**The problem.** Hardware isolation stops other programs from reading
protected memory. It does not stop an attacker from observing what the
protected code does: how long it takes, how much power it draws, which
parts of the processor’s cache it touches.

**The idea.** A **side channel** is any such observable effect that
depends on a secret. The classic example is a comparison that stops at
the first differing byte: the longer it runs, the more leading bytes of
the guess were right. An attacker can then find a secret one byte at a
time, at most 256 guesses per byte, instead of guessing the whole secret
at once. The cell does this against a 3-byte secret. It counts loop
steps in place of measuring time, so the result is the same on every
run.

``` python
secret = bytes.fromhex("5ec2e7")


def steps_to_compare(guess: bytes) -> int:  # what the attacker times
    for i, (a, b) in enumerate(zip(guess, secret)):
        if a != b:
            return i
    return len(secret)


found, tries = b"", 0
for position in range(len(secret)):
    for byte in range(256):
        tries += 1
        candidate = found + bytes([byte]) + bytes(len(secret) - position - 1)
        if steps_to_compare(candidate) > position:
            found += bytes([byte])
            break
assert found == secret
print(f"recovered {found.hex()} in {tries} tries; blind search needs up to {256**3:,}")
```

    recovered 5ec2e7 in 522 tries; blind search needs up to 16,777,216

The printed line compares the attack’s cost with blind search: a few
hundred tries against 16.7 million. For a 32-byte key the gap is 8,192
tries against $2^{256}$.

**The defence** is **constant-time** code, whose running time and memory
accesses do not depend on secret values; Python’s `hmac.compare_digest`
compares bytes that way. A Level 4 HSM must also resist physical side
channels such as power measurement. Several published attacks on Intel
SGX, Foreshadow and SGAxe among them, were side channels in the
processor itself, which no application code could have avoided.

**Recap.** Isolation hides memory, not behaviour; secret-dependent
timing, power or cache use leak the secret piece by piece, and
constant-time code is the defence.

<a id="formal-treatment"></a>

## Formal treatment

<a id="hardware-security-modules"></a>

### Hardware security modules

- **Form factors.** Network appliances, PCIe cards that plug into a
  server, and smart cards or USB tokens for individual people. Cloud
  providers also rent single-tenant HSMs as a service.
- **Interface.** **PKCS#11** (OASIS) is the C programming interface most
  HSMs expose. It covers sessions, logins by role, handles that refer to
  key objects without revealing them, attributes such as sensitive and
  extractable, and named mechanisms such as `CKM_ECDSA` for signing and
  `CKM_AES_KEY_WRAP` for wrapping. Version 3.2, approved as an OASIS
  Standard in 2026, adds ML-KEM, ML-DSA and SLH-DSA (**verify
  current**).
- **Key ceremony.** The HSM’s master key and the custody keys are
  created in a scripted, witnessed session. Administrative authority is
  split across smart cards held by different people under an M-of-N
  quorum: [chapter 1](01-foundations.md)’s Shamir sharing, rebuilt
  inside the device.
- **What it protects.** The key’s bytes, against copying by anyone,
  administrators included.
- **What it does not protect.** Use. A host that holds the login can
  sign any message. Vendors therefore sell programmable HSMs that run
  custom code, such as a policy check, inside the boundary (**verify
  current** for each vendor’s offering).
- **Algorithms.** secp256k1 ECDSA is widely supported. BIP340 Schnorr,
  the Taproot tweak and threshold protocols depend on each vendor’s
  firmware (**verify current**).

<a id="trusted-execution-environments"></a>

### Trusted execution environments

Three terms recur. The **hypervisor** is the software layer that runs
virtual machines on a physical server; in a public cloud the provider
runs it. **Microcode** is the processor’s own updatable internal
program; security fixes to a processor usually ship as microcode
updates. **Memory encryption** means the processor encrypts data on its
way out to the memory chips and decrypts it on the way back, so the
memory chips only ever hold ciphertext.

- **Process enclaves: Intel SGX.** An enclave is a region of one
  application’s address space. The processor encrypts its pages in
  memory and refuses access to them from any other code, including the
  operating system and the hypervisor. Intel deprecated SGX on client
  processors from the 11th generation Core and continues it on Xeon
  server processors (**verify current**). Its small TCB is the appeal.
  Its record of side-channel and fault attacks is the cost: Foreshadow
  (2018), Plundervolt (2019), SGAxe (2020) and ÆPIC Leak (2022). Each
  was fixed by a microcode update, after which attestation reports the
  old microcode as out of date, so a verifier can refuse unpatched
  machines.
- **Confidential virtual machines: AMD SEV-SNP, Intel TDX.** A whole
  virtual machine’s memory is encrypted and protected against the
  hypervisor. The TCB is larger, since it includes a full guest
  operating system, but ordinary software runs unmodified.
- **AWS Nitro Enclaves.** Not a processor feature: AWS’s Nitro
  hypervisor carves an isolated virtual machine out of an EC2 instance.
  The enclave has no persistent storage, no interactive access and no
  external network; it talks only to its parent instance over a local
  socket (vsock). Its attestation document is signed through AWS’s Nitro
  certificate chain and carries measurements in numbered registers
  called PCRs: PCR0 holds the hash of the enclave image, PCR8 that of
  the certificate that signed the image. An AWS KMS key policy can
  require a given PCR value before it decrypts anything for an enclave.
  The root of trust is AWS, not a processor maker.
- **Physical attacks on memory.** Server memory encryption leaves a gap
  that a small circuit board placed between the processor and a memory
  module, an **interposer**, can exploit by watching or altering the
  encrypted traffic. Four such attacks were published between late 2025
  and September 2026:
  - WireTap: server SGX on DDR4 memory, passive;
  - Battering RAM: SGX and SEV-SNP, active, under USD 50 in parts;
  - TEE.fail: TDX and SEV-SNP on DDR5 memory;
  - DDRop (September 2026): TDX, SGX and SEV-SNP, about USD 159 in
    parts.

  Intel and AMD state that physical interposer attacks are outside their
  threat models (reported; **verify current**). A TEE therefore protects
  against the operator’s software and against remote attackers. It does
  not protect against someone with physical access to the server, and in
  a public cloud that includes the provider’s staff and supply chain.

<a id="mpc-as-a-storage-choice"></a>

### MPC as a storage choice

[Chapter 2](02-mpc-custody.md) built the protocols. As a storage
decision:

- **What it protects.** Compromising fewer than $t$ machines, their
  administrators included, reveals nothing. That holds only if the
  machines are independent: different operators, clouds, operating
  system images and software supply chains. Three signers that share an
  administrator are one signer.
- **What it does not protect.** $t$ compromised machines; a flaw in the
  protocol implementation ([chapter 2](02-mpc-custody.md)’s BitForge and
  TSShock); and anyone able to make $t$ machines sign, which is again
  policy.
- **Each share is itself a key to store.** A share can sit in plain
  memory, in a TEE or behind an HSM. MPC multiplies the storage problem
  by $n$ and lowers what each copy must guarantee.
- **Agility and evidence.** A new protocol or curve is a software
  release, with no firmware certification to wait for. There is also no
  certification scheme for threshold protocols comparable to FIPS 140-3.
  NIST’s first call for multi-party threshold schemes (NIST IR 8214C) is
  taking submissions, with no standard yet (**verify current**).

<a id="combinations"></a>

### Combinations

- **MPC shares inside TEEs.** Fireblocks states that its MPC-CMP key
  shares, and its policy engine, run inside Intel SGX enclaves spread
  across several public clouds (reported; **verify current**).
  Attestation lets each signer check that its peers run reviewed code.
- **MPC with a client-held or offline share.** One share stays with the
  client or on a device that is never connected to a network, so the
  service operator cannot sign alone.
- **HSM with policy inside.** A programmable HSM runs the approval check
  inside its boundary, so a compromised host cannot obtain an unapproved
  signature.
- **On-chain multisig with each key in an HSM.** The threshold is
  enforced by the chain instead of a protocol ([chapter
  2](02-mpc-custody.md), Exercise 5).

<a id="comparison"></a>

### Comparison

The table gathers the chapter’s answers in one place.

|  | HSM | TEE | MPC across plain servers |
|----|----|----|----|
| Key in plaintext | Inside one device | Inside one processor package, per enclave | Nowhere; each share on one machine |
| Root of trust | HSM vendor and certification laboratory | Processor maker (SGX, TDX, SEV-SNP) or cloud provider (Nitro) | Protocol security proof and its implementation |
| Evidence for an outsider | FIPS 140-3 certificate for the module version | Attestation report naming the code | Public key and protocol messages; no certification scheme |
| Malicious administrator | Cannot extract the key; can use it | Cannot read the enclave from the host | Harmless below the threshold |
| Physical attacker | Tamper response at Levels 3 and 4 | Outside the vendors’ threat models | Needs $t$ separate sites |
| New algorithm | Firmware update, then revalidation | Software release, new measurement | Software release |
| Latency | One device call per signature | Local computation | Network rounds between sites (two for FROST) |
| Backup | Wrapped export or vendor cloning | Sealing, or release after attestation | Encrypted share backups; proactive refresh |
| Running cost | Appliances, ceremonies, data-centre presence | Ordinary cloud instances | Several independent operators |

<a id="worked-example"></a>

## Worked example

Where each part of the demo would live in production. Each placement
follows from the three questions: what the part holds, who could misuse
it, and what would detect that.

- **The signers** hold shares, and the whole point of the threshold is
  that compromising one host is not enough. They therefore go to
  independent sites, each share protected by a TEE or an HSM so that the
  site’s own administrators cannot read it.
- **The coordinator** holds no secret. Compromising it can stop signing
  but cannot produce an unapproved signature, so a plain server
  suffices.
- **The policy authority key** is the most powerful key in the system
  after the shares: whoever holds it can authorise any transaction the
  signers’ checks allow. It belongs inside an HSM or inside the signers’
  enclaves, next to the policy code that uses it.
- **The approver keys** belong to people, so they go on devices bound to
  one person: smart cards, FIDO security keys or a phone’s secure
  element.
- **Share backups** are used only to recover from disaster, so their
  recovery key stays offline in an HSM that only an M-of-N quorum of
  officers can operate.
- **The audit log** is not secret, but it must not be rewritten, so it
  goes to append-only storage with its latest hash published elsewhere
  ([chapter 4](04-policy.md)).

| Demo part | In the demo | In production | Why |
|----|----|----|----|
| Signers 1 to 3 | One operating-system process each, on one host | One signer per independent site, its share in a TEE or behind an HSM | Compromise must require $t$ sites, not one host’s root account |
| Coordinator | The pipeline’s own process | A plain server | It holds no secret; it can only deny service |
| Policy authority key (Ed25519 and ML-DSA-65) | In memory | Inside an HSM or the signers’ enclaves, next to the policy code | Whoever holds it can authorise any transaction the signers’ checks allow |
| Approver keys (bob, carol) | In memory | Smart cards, FIDO security keys or phone secure elements | One key per person, bound to the person |
| Share backups | Recovery key in memory | An offline HSM under an M-of-N card quorum | Used only in a recovery ceremony |
| Audit log | Memory and a file | Append-only storage with its head anchored | Integrity matters, not secrecy |

An operating-system process boundary, the demo’s stand-in for every row,
protects nothing against an administrator of the same host. The demo
shows the shape of the system, not its storage.

<a id="code-walkthrough"></a>

## Code walkthrough

<a id="releasing-a-share-to-an-attested-signer"></a>

### Releasing a share to an attested signer

This is the pattern that Nitro Enclaves and AWS KMS implement, built
from the models above. A new signer instance starts with no share. It
has to convince a key-release service that it is the reviewed signer
build running in a genuine enclave, and the share must reach it
encrypted so that nothing in between, including the host, can read it.

1.  Inside the enclave, the signer generates an ML-KEM key pair. It puts
    the hash of the public key in the report data, and sends the
    attestation report and the public key to the key-release service.
2.  The service checks three things: the report’s signature against the
    maker’s root, the measurement against the reviewed build, and that
    the report data is the hash of the public key it was sent.
3.  Only then does it encapsulate a fresh AES key to that public key and
    send the share encrypted under it.

The third check in step 2 stops a relay attack. An attacker who obtains
a genuine report from a genuine enclave could otherwise send it together
with the attacker’s own public key and receive the share. Because the
report data commits to one public key, the report only vouches for that
key.

``` python
from cryptography.hazmat.primitives.asymmetric import mlkem

from custody_lab.mpc import dkg

shares, _ = dkg.run(threshold=2, count=3)
share = shares[2].to_bytes(32, "big")


def release(share: bytes, body: bytes, signature: bytes,
            public_key: bytes) -> tuple[bytes, bytes, bytes]:
    maker_root.verify(signature, body)
    if body[:32] != expected:
        raise PermissionError("not the reviewed signer build")
    if body[32:64] != hashlib.sha256(public_key).digest():
        raise PermissionError("report does not bind this public key")
    secret, encapsulated = mlkem.MLKEM768PublicKey.from_public_bytes(public_key).encapsulate()
    nonce = os.urandom(12)
    return encapsulated, nonce, AESGCM(secret).encrypt(nonce, share, b"share-release/1")


enclave_key = mlkem.MLKEM768PrivateKey.generate()  # generated inside the enclave
public_key = enclave_key.public_key().public_bytes_raw()
body, signature = load_and_report(reviewed, hashlib.sha256(public_key).digest())

encapsulated, nonce, ciphertext = release(share, body, signature, public_key)
received = AESGCM(enclave_key.decapsulate(encapsulated)).decrypt(nonce, ciphertext,
                                                                 b"share-release/1")
assert received == share

attacker = mlkem.MLKEM768PrivateKey.generate().public_key().public_bytes_raw()
patched_report = load_and_report(patched, hashlib.sha256(public_key).digest())
for case, request in {"patched build": (*patched_report, public_key),
                      "substituted key": (body, signature, attacker)}.items():
    try:
        release(share, *request)
        raise AssertionError(f"{case}: share released")
    except PermissionError as refused:
        print(f"{case}: {refused}")
```

    patched build: not the reviewed signer build
    substituted key: report does not bind this public key

The genuine request receives the share; the two printed lines are the
two refusals. The patched build fails on its measurement, and the
relayed report with a substituted key fails on its report data.

The service never sees the enclave’s private key, and the share crosses
the network only encrypted to a key generated inside the attested
enclave. The model leaves two checks out that a real verifier makes. It
checks the report’s freshness, by requiring a value it chose (a nonce or
timestamp) in the report data, so an old report cannot be replayed. And
it checks the processor’s security version, so that it refuses reports
from machines with out-of-date microcode.

<a id="how-this-shows-up-in-production"></a>

## How this shows up in production

**FIPS 140-2 retired.** NIST moved every FIPS 140-2 certificate to the
historical list on 21 September 2026 (reported; **verify current**).
Such devices keep working, but no longer meet a procurement requirement
for an active validation. FIPS 140-3 is the only standard in force.

**Cloud HSMs.** AWS CloudHSM (`hsm2m.medium`) and Azure Managed HSM are
validated at FIPS 140-3 Level 3, both on Marvell LiquidSecurity hardware
(reported; **verify current**).

**Custody platforms.** Fireblocks runs MPC shares in SGX enclaves across
clouds (reported). Its Key Link product lets a client keep its keys in
its own HSM or key management service instead of MPC (reported by
Securosys; **verify current**).

**TEE research pace.** The four interposer attacks listed above appeared
within about a year, and the vendors place physical attacks of this kind
outside their threat models. A design that relies on a TEE against the
hosting provider needs a second control: a threshold across providers,
or a share outside the cloud.

**Post-quantum in HSMs.** PKCS#11 3.2 defines ML-KEM, ML-DSA and SLH-DSA
mechanisms, and at least one vendor documents ML-DSA for its HSMs
(**verify current**). Validated firmware sets the pace for [chapter
7](07-post-quantum.md)’s hybrid approvals.

<a id="recap"></a>

## Recap

1.  A share is still a key, and it lives somewhere. Three options exist:
    an HSM keeps it inside a tamper-resistant device, a TEE keeps it
    inside the processor away from the operating system, and MPC keeps
    the whole key nowhere.
2.  Ask any key store three questions: where the key exists unencrypted,
    who can make it sign, and what an outsider can verify. Protecting
    the key’s bytes does not protect its use.
3.  Keys leave an HSM only wrapped under a key that never leaves;
    sealing does the same job for an enclave, tied to the enclave’s
    identity.
4.  FIPS 140-3 certifies one firmware version of a module at one of four
    levels; a new algorithm waits for revalidation.
5.  Remote attestation is the chip’s signature over the hash of the code
    it runs. Before trusting an enclave, check the signature, the
    measurement and the report data.
6.  Side channels leak secrets through timing, power or cache use, and
    isolation does not stop them. Interposer attacks put physical
    attackers outside the TEE vendors’ threat models.
7.  In production, each signer goes to an independent site with its
    share in a TEE or behind an HSM, and the policy authority key goes
    next to the policy code.

[Chapter 4](04-policy.md) builds the policy engine whose authorisation
every signer checks, the control that answers “should this be signed?”,
which no storage option answers.

<a id="exercises"></a>

## Exercises

1.  **Recall.** For an HSM, a TEE and 2-of-3 MPC across plain servers,
    where does the private key exist in plaintext?
2.  **Compute.** The side-channel cell recovered a 3-byte secret. How
    many tries does the same attack need, at most, for a 16-byte secret,
    and how does that compare with blind search?
3.  **Explain.** Why must the key-release service check the report data,
    and not only the signature and the measurement?
4.  **Apply.** A signer build moves from v1.4 to v1.5. Under sealing to
    the measurement, what happens to its sealed share? Give two ways to
    carry the signer across the upgrade.
5.  **Design.** A custodian runs 2-of-3 MPC with all three signers in
    SGX enclaves in one cloud provider’s region. What does the
    interposer research change about this design, and what placement
    removes the weakness?
6.  **Classify.** Which of HSM, TEE and MPC defends against each of
    these: (a) an attacker with root on a signing host who reads process
    memory; (b) a stolen backup tape; (c) the same root attacker
    submitting signing requests from that host; (d) an approver’s
    compromised laptop?

<a id="solutions"></a>

## Solutions

1.  Inside the HSM; inside the processor package, with memory holding it
    encrypted; nowhere, since each share is on one machine and the key
    is never assembled.
2.  At most 256 tries per byte, so $16 \cdot 256 = 4096$, against up to
    $2^{128}$ for blind search. The leak turns an exponential search
    into a linear one.

``` python
assert 16 * 256 == 4096 and 2**128 > 10**38
```

3.  The signature and the measurement show that some genuine enclave
    runs the reviewed build. They say nothing about who sent the
    request. An attacker can relay a genuine report and attach its own
    public key; only the binding in the report data ties the report to
    the key the share is encrypted to.
4.  v1.5 has a different measurement, so it derives a different sealing
    key and cannot unseal the share. Ways across:
    - v1.4 hands the share to v1.5 through the release pattern above,
      with v1.5’s measurement as the expected value;
    - the cluster runs a proactive refresh ([chapter
      2](02-mpc-custody.md)) with v1.5 as the recipient, so no old share
      needs to move;
    - the builds seal to the signer instead, accepting that the
      developer key can then unseal every share.
5.  All three enclaves share one physical control domain. The interposer
    attacks give someone with physical access to that provider’s servers
    a path to every share, and that party is outside the vendors’ threat
    models. Place the signers with different providers, or keep one
    share outside the cloud: on premises behind an HSM, or on an offline
    device.
6.  1)  All three. The key is not in host memory in any of them; under
        MPC the attacker reads one share, which is harmless below the
        threshold. (b) All three, provided the backup is wrapped, sealed
        or encrypted and the key that opens it stays in the HSM, the
        processor or the recovery quorum. (c) Only MPC, while the
        attacker holds fewer than $t$ hosts. An HSM or a TEE signs for
        whoever reaches its interface, unless a policy check runs inside
        the boundary. (d) None of them: the approval quorum and its keys
        on separate devices are the defence ([chapter 4](04-policy.md)).

<a id="further-reading"></a>

## Further reading

- NIST FIPS 140-3 (2019) and ISO/IEC 19790:2012; the NIST Cryptographic
  Module Validation Program search for current certificates.
- RFC 3394, “Advanced Encryption Standard (AES) Key Wrap Algorithm”
  (2002); NIST SP 800-38F (2012). The key-wrapping cell’s source.
- RFC 5869, “HMAC-based Extract-and-Expand Key Derivation Function
  (HKDF)” (2010). The key derivation the sealing cell uses.
- OASIS, “PKCS \#11 Specification Version 3.2” (2026). The HSM
  interface, including post-quantum mechanisms.
- NIST SP 800-186 (2023). Which curves NIST recommends, and the
  blockchain exception for secp256k1.
- V. Costan and S. Devadas, “Intel SGX Explained”, IACR ePrint 2016/086.
  How enclaves, measurement and attestation work.
- AWS, *Nitro Enclaves User Guide*, “Cryptographic attestation”; AWS
  KMS, “Condition keys for Nitro Enclaves”. The key-release pattern as
  deployed.
- J. Van Bulck et al., “Foreshadow: Extracting the Keys to the Intel SGX
  Kingdom with Transient Out-of-Order Execution”, USENIX Security 2018.
  The first major SGX break.
- WireTap (wiretap.fail), Battering RAM, TEE.fail (tee.fail), and DDRop
  (ACM CCS 2026): the interposer attacks (**verify current**).
- NIST IR 8214C, “NIST First Call for Multi-Party Threshold Schemes”
  (2026). The route to a threshold standard.

------------------------------------------------------------------------

Previous: [Chapter 2, MPC Custody](02-mpc-custody.md) \| [All
chapters](../README.md) \| Next: [Chapter 4, Policy and
Authorisation](04-policy.md)
