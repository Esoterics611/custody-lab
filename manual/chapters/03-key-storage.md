# Module 3: Key Storage

2026-09-27

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

<a id="learning-objectives"></a>

## Learning objectives

- State, for an HSM, a TEE and an MPC cluster, where the key exists in
  plaintext, who can make it sign, and what an outside party can verify
  about either.
- Wrap a key under a key-encryption key, and explain why an HSM exports
  keys only in that form.
- Explain remote attestation: what a measurement is, what the signed
  report binds, and why a key release must check the report data as well
  as the signature and the measurement.
- Name the attacks each option does not defend against, including the
  memory-bus interposer attacks published since 2025.
- Place each part of the demo on the storage a production deployment
  would use, and justify the placement.

<a id="intuition"></a>

## Intuition

Every signature in chapters [1](01-foundations.md) to
[7](07-post-quantum.md) comes from a secret number in some process’s
memory. [Chapter 2](02-mpc-custody.md) split that number so that no
process holds all of it. This chapter asks where each piece lives. Three
answers are in production use.

- A **hardware security module** (**HSM**) is a separate device that
  generates keys, keeps them and signs with them. Keys enter and leave
  it only encrypted. Software outside asks it to sign; it never hands
  the key over.
- A **trusted execution environment** (**TEE**) is a region of an
  ordinary server’s processor and memory that the server’s own operating
  system cannot read. The key sits in normal RAM, encrypted by the
  processor. The protected region is an **enclave**.
- **MPC** ([chapter 2](02-mpc-custody.md)) keeps the key in no single
  place: each machine holds a share, and a threshold of them sign
  together.

Each answers a different question. An HSM answers “can this key be
copied?” A TEE answers “can the operator of this machine read its
memory?” MPC answers “is there one machine whose compromise is enough?”
None answers “should this signature be made?” That is [chapter
4](04-policy.md)’s policy engine, and each option here signs whatever an
authenticated caller asks unless the policy check runs inside the
protected boundary.

Payments engineers know the HSM as the payment HSM: PIN blocks are
translated inside the device, and the host never sees a clear PIN. The
analogy breaks at finality. A misused card key leads to fraud that a
dispute process can often reverse, and the key is rotated by reissuing
cards. A Bitcoin settlement signed by a misused key is final, and the
custody key cannot be rotated without moving every coin it controls.

<a id="first-principles"></a>

## First principles

This section assumes [chapter 1](01-foundations.md) (hashes and
signatures) and [chapter 7](07-post-quantum.md) (ML-KEM).

<a id="three-questions-for-any-key-store"></a>

### Three questions for any key store

1.  **Where does the key exist in plaintext?** In an HSM, only inside
    the device. In a TEE, only inside the processor package; RAM holds
    it encrypted. With MPC, nowhere: each share exists in plaintext on
    one machine, and the key on none.
2.  **Who can make it sign?** Whoever can authenticate to the HSM’s
    interface, send requests to the enclave’s code, or reach $t$
    signers. Protecting the key’s bytes is not the same as protecting
    its use.
3.  **What can an outsider verify?** For an HSM, a certificate that the
    device model passed a laboratory evaluation. For a TEE, a signed
    report naming the exact code that runs. For MPC, the public key and
    the protocol messages.

The **trusted computing base** (**TCB**) of a key is everything that
must behave correctly for the key to stay secret: hardware, firmware,
operating system, application code, and the people with administrative
access. Each option shrinks the TCB in a different direction.

<a id="key-wrapping"></a>

### Key wrapping

A key that must leave its device, for a backup or to move between the
HSMs of one cluster, leaves **wrapped**: encrypted under a
**key-encryption key** (**KEK**) that itself never leaves. AES key wrap
(RFC 3394; NIST SP 800-38F) is the standard construction. It is
deterministic and carries an integrity check, so a modified wrapped key
fails to unwrap instead of unwrapping to a wrong key.

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

An HSM labels each key with attributes. In the PKCS#11 interface
described below, a **sensitive** key never leaves in plaintext, and an
**extractable** key may leave wrapped. A key generated as
non-extractable cannot leave at all through the standard interface. Its
backups use the vendor’s own cloning or encrypted key-blob mechanism,
which ties the custodian to that vendor.

<a id="tamper-response-and-certification-levels"></a>

### Tamper response and certification levels

An HSM defends its keys physically in three ways:

- **tamper evidence**: seals and coatings that show the device was
  opened;
- **tamper resistance**: an enclosure that is hard to open;
- **tamper response**: sensors (a wire mesh, light, temperature,
  voltage) that trigger **zeroisation**, overwriting the keys before an
  attacker reaches them.

**FIPS 140-3**, the US and Canadian standard for cryptographic modules
(aligned with ISO/IEC 19790), certifies a module at one of four
**security levels**:

| Level | Physical security | Operator authentication |
|----|----|----|
| 1 | None required; a software library can qualify | None required |
| 2 | Tamper evidence | Role-based |
| 3 | Tamper resistance with detection and response; environmental failure protection or testing | Identity-based |
| 4 | A complete protective envelope; protection against environmental and fault-injection attacks | Multi-factor |

A certificate covers one module version. A firmware update that adds an
algorithm, such as BIP340 or ML-DSA, is outside the certificate until
the new version is validated. NIST’s curve recommendations (SP 800-186)
allow secp256k1 for blockchain-related applications only.

<a id="remote-attestation"></a>

### Remote attestation

A TEE has no sealed box. Instead, the processor proves what code it
runs.

- A **measurement** is a hash of the code and initial data loaded into
  the enclave, computed by the processor as it loads them. One changed
  byte gives a different measurement.
- An **attestation report** is the measurement plus up to 64 bytes of
  **report data** chosen by the code inside. It is signed by a key that
  the processor maker certified and built into the chip: the **root of
  trust**.
- A **verifier** checks the signature up to the maker’s root
  certificate, compares the measurement with the value it expects for
  reviewed code, and reads the report data.

This is **remote attestation**. It differs from [chapter
6](06-reserves.md)’s attestation, which is the custodian’s signed
statement about reserves. Remote attestation is the hardware’s signed
statement about software.

``` python
import hashlib
import os

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

The signature proves genuine hardware. Only the comparison with the
expected measurement proves the right code. A verifier that checks the
signature alone accepts the patched signer.

<a id="sealing"></a>

### Sealing

An enclave has no storage that the host cannot read. To keep a secret
across restarts, it **seals** it: it encrypts the secret under a key
that the processor derives from a device secret and the enclave’s
identity. There are two choices of identity:

- **seal to the measurement**: only identical code can unseal, so an
  upgrade loses access unless the old version hands the secret over;
- **seal to the signer**: any build signed by the same developer key can
  unseal, so upgrades work, and a stolen developer key unseals every
  secret.

``` python
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
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

AWS Nitro Enclaves have no persistent storage and no sealing primitive.
An enclave there fetches its secrets after every start from a key
service that checks its attestation first. The code walkthrough builds
that pattern.

<a id="side-channels"></a>

### Side channels

Hardware isolation stops other programs from reading protected memory.
It does not stop an attacker from observing what the protected code
does: how long it takes, how much power it draws, which cache lines it
touches. A **side channel** is any such observable effect that depends
on a secret. In the cell below, a comparison that stops at the first
differing byte reveals how many leading bytes matched. The cell counts
loop steps in place of timing, so the result is repeatable.

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

The defence is **constant-time** code, whose running time and memory
accesses do not depend on secrets (`hmac.compare_digest` for
comparisons). A Level 4 HSM must also resist physical side channels.
Several published attacks on SGX, Foreshadow and SGAxe among them, are
side channels in the processor itself.

<a id="formal-treatment"></a>

## Formal treatment

<a id="hardware-security-modules"></a>

### Hardware security modules

- **Form factors.** Network appliances, PCIe cards, and smart cards or
  USB tokens for individual people. Cloud providers also rent
  single-tenant HSMs as a service.
- **Interface.** **PKCS#11** (OASIS) is the C interface most HSMs
  expose. It covers sessions, logins by role, handles to key objects,
  attributes such as sensitive and extractable, and named mechanisms
  (`CKM_ECDSA`, `CKM_AES_KEY_WRAP`). Version 3.2, approved as an OASIS
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

- **Process enclaves: Intel SGX.** An enclave is a region of one
  application’s address space. The processor encrypts its pages in RAM
  and refuses access to them from any other code, including the
  operating system and the hypervisor. Intel deprecated SGX on client
  processors from the 11th generation Core and continues it on Xeon
  server processors (**verify current**). Its small TCB is the appeal.
  Its record of side-channel and fault attacks is the cost: Foreshadow
  (2018), Plundervolt (2019), SGAxe (2020) and ÆPIC Leak (2022). Each
  was fixed by a microcode update, after which attestation reports the
  old microcode as out of date.
- **Confidential virtual machines: AMD SEV-SNP, Intel TDX.** A whole
  virtual machine’s memory is encrypted and protected against the
  hypervisor. The TCB is larger, since it includes a full guest
  operating system, but ordinary software runs unmodified.
- **AWS Nitro Enclaves.** Not a processor feature: the Nitro hypervisor
  carves an isolated virtual machine out of an EC2 instance. The enclave
  has no persistent storage, no interactive access and no external
  network; it talks only to its parent instance over a local socket
  (vsock). Its attestation document is signed through AWS’s Nitro PKI
  and carries PCR measurements: PCR0 for the image, PCR8 for the
  certificate that signed the image. An AWS KMS key policy can require a
  given PCR value before it decrypts for an enclave. The root of trust
  is AWS, not a processor maker.
- **Physical attacks on memory.** Server memory encryption leaves a gap
  that a small circuit board between processor and memory module, an
  **interposer**, can use. Four such attacks were published between late
  2025 and September 2026:
  - WireTap: server SGX on DDR4, passive;
  - Battering RAM: SGX and SEV-SNP, active, under USD 50 in parts;
  - TEE.fail: TDX and SEV-SNP on DDR5;
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
  system images and software supply chains.
- **What it does not protect.** $t$ compromised machines; a flaw in the
  protocol implementation ([chapter 2](02-mpc-custody.md)’s BitForge and
  TSSHOCK); and anyone able to make $t$ machines sign, which is again
  policy.
- **Each share is itself a key to store.** A share can sit in plain
  memory, in a TEE or behind an HSM. MPC multiplies the storage problem
  by $n$ and lowers what each copy must guarantee.
- **Agility and evidence.** A new protocol or curve is a software
  release, with no firmware certification. There is also no
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
  client or on an air-gapped device, so the service operator cannot sign
  alone.
- **HSM with policy inside.** A programmable HSM runs the approval check
  inside its boundary, so a compromised host cannot obtain an unapproved
  signature.
- **On-chain multisig with each key in an HSM.** The threshold is
  enforced by the chain instead of a protocol ([chapter
  2](02-mpc-custody.md), Exercise 5).

<a id="comparison"></a>

### Comparison

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

Where each part of the demo would live in production:

| Demo part | In the demo | In production | Why |
|----|----|----|----|
| Signers 1 to 3 | One operating-system process each, on one host | One signer per independent site, its share in a TEE or behind an HSM | Compromise must require $t$ sites, not one host’s root account |
| Coordinator | The pipeline’s own process | A plain server | It holds no secret; it can only deny service |
| Policy authority key (Ed25519 and ML-DSA-65) | In memory | Inside an HSM or the signers’ enclaves, next to the policy code | Whoever holds it can authorise any transaction the signers’ checks allow |
| Approver keys (bob, carol) | In memory | Smart cards, FIDO security keys or phone secure elements | One key per person, bound to the person |
| Share backups ([chapter 7](07-post-quantum.md)) | Recovery key in memory | An offline HSM under an M-of-N card quorum | Used only in a recovery ceremony |
| Audit log | Memory and a file | Append-only storage with its head anchored | Integrity matters, not secrecy |

An operating-system process boundary, the demo’s stand-in for every row,
protects nothing against root on the same host. The demo shows the shape
of the system, not its storage.

<a id="code-walkthrough"></a>

## Code walkthrough

<a id="releasing-a-share-to-an-attested-signer"></a>

### Releasing a share to an attested signer

This is the pattern that Nitro Enclaves and AWS KMS implement, built
from the model above. A new signer instance starts empty.

1.  Inside the enclave, the signer generates an ML-KEM key pair. It puts
    the hash of the public key in the report data and sends the report
    and the public key to the key-release service.
2.  The service checks the report’s signature against the maker’s root,
    and the measurement against the reviewed build. It also checks that
    the report data is the hash of the public key it was sent.
3.  Only then does it encapsulate to that public key and send the share,
    encrypted.

The third check in step 2 stops a relay. An attacker who obtains a
genuine report cannot attach its own public key to it.

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

The service never sees the enclave’s private key, and the share crosses
the network only encrypted to a key generated inside the attested
enclave. The model leaves two things out. A real verifier also checks
the report’s freshness (a nonce or timestamp it chose) and the
processor’s security version, so that it refuses reports from machines
with out-of-date microcode.

<a id="how-this-shows-up-in-production"></a>

## How this shows up in production

- **FIPS 140-2 retired.** NIST moved every FIPS 140-2 certificate to the
  historical list on 21 September 2026 (reported; **verify current**).
  Such devices keep working, but no longer meet a procurement
  requirement for an active validation. FIPS 140-3 is the only standard
  in force.
- **Cloud HSMs.** AWS CloudHSM (`hsm2m.medium`) and Azure Managed HSM
  are validated at FIPS 140-3 Level 3, both on Marvell LiquidSecurity
  hardware (reported; **verify current**).
- **Custody platforms.** Fireblocks runs MPC shares in SGX enclaves
  across clouds (reported). Its Key Link product lets a client keep its
  keys in its own HSM or key management service instead of MPC (reported
  by Securosys; **verify current**).
- **TEE research pace.** The four interposer attacks listed above
  appeared within about a year, and the vendors place physical attacks
  of this kind outside their threat models. A design that relies on a
  TEE against the hosting provider needs a second control: a threshold
  across providers, or a share outside the cloud.
- **Post-quantum in HSMs.** PKCS#11 3.2 defines ML-KEM, ML-DSA and
  SLH-DSA mechanisms, and at least one vendor documents ML-DSA for its
  HSMs (**verify current**). Validated firmware sets the pace for
  [chapter 7](07-post-quantum.md)’s hybrid approvals.

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

1.  Inside the HSM; inside the processor package, with RAM holding it
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
