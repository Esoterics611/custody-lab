# HSM vs MPC vs TEE

**In one sentence.** There are three places a custody key can live: whole inside one certified
device (HSM), whole inside one processor's protected memory with the code proved by attestation
(TEE), or nowhere at all, as shares on $t$ of $n$ machines that must cooperate (MPC).

## The problem

Each option answers a different question, and a custodian that picks one without knowing which
question it answers is left exposed to the others. An HSM answers "can this key be copied?". A TEE
answers "can the operator of this machine read its memory?". MPC answers "is there one machine whose
compromise is enough?".

## The idea

Ask any key store three questions: where does the key exist unencrypted, who can make it sign, and
what can an outsider verify?

| | HSM | TEE | MPC across plain servers |
|---|---|---|---|
| Key in plaintext | Inside one device | Inside one processor package | Nowhere |
| Root of trust | HSM vendor and certification laboratory | Processor maker or cloud provider | Protocol proof and implementation |
| Outsider's evidence | FIPS 140-3 certificate | Attestation report | Public key, protocol messages |
| Malicious administrator | Cannot extract; can use | Cannot read from the host | Harmless below threshold |
| Physical attacker | Tamper response (Levels 3 and 4) | Outside vendor threat models | Needs $t$ sites |
| New algorithm | Firmware, then revalidation | Software release | Software release |

Each share in an MPC design is itself a key that must live somewhere, so the options combine: MPC
shares inside TEEs spread across clouds, or one share behind an HSM or kept offline.

## Why custody cares

None of the three decides whether a signature should be made. Each signs for whoever reaches its
interface unless policy runs inside the boundary. That question belongs to the policy engine
(chapter 4), and the storage choice only decides how many things an attacker must compromise to
bypass it.

## In the demo

Each share sits in its own operating-system process, a boundary that protects nothing against an
administrator of the host. Chapter 3's worked example gives the production placement of every part:
signers at independent sites with shares in TEEs or behind HSMs, the authority key in an HSM, approver
keys on personal devices.

## In the manual

[Chapter 3](../../manual/chapters/03-key-storage.md):
"[Three questions for any key store](../../manual/chapters/03-key-storage.md#three-questions-for-any-key-store)",
"[Comparison](../../manual/chapters/03-key-storage.md#comparison)",
"[Combinations](../../manual/chapters/03-key-storage.md#combinations)",
"[Worked example](../../manual/chapters/03-key-storage.md#worked-example)".

## Sources

As for [hsm](hsm.md) and [tee](tee.md); NIST IR 8214C, first call for multi-party threshold schemes
(2026, **verify current**); Fireblocks on MPC-CMP in SGX (reported; **verify current**).
