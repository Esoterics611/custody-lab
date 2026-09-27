# HSM vs MPC vs TEE

**Definition.** Three places a custody key can live. An HSM keeps the whole key inside one
certified device. A TEE keeps it in one processor's protected memory, and proves the code by
attestation. MPC keeps it nowhere: $t$ of $n$ machines holding shares must cooperate.

| | HSM | TEE | MPC across plain servers |
|---|---|---|---|
| Key in plaintext | Inside one device | Inside one processor package | Nowhere |
| Root of trust | HSM vendor and certification laboratory | Processor maker or cloud provider | Protocol proof and implementation |
| Outsider's evidence | FIPS 140-3 certificate | Attestation report | Public key, protocol messages |
| Malicious administrator | Cannot extract; can use | Cannot read from the host | Harmless below threshold |
| Physical attacker | Tamper response (Levels 3 and 4) | Outside vendor threat models | Needs $t$ sites |
| New algorithm | Firmware, then revalidation | Software release | Software release |

**Why custody cares.** None of the three decides whether a signature should be made. Each signs
for whoever reaches its interface unless policy runs inside the boundary. Production designs
combine them: MPC shares inside TEEs across clouds, or one share behind an HSM or offline.

**In the demo.** Each share sits in its own operating-system process, a boundary that protects
nothing against root on the host. Chapter 3's worked example gives the production placement of
every part.

**In the manual.** Chapter 3, "Comparison", "Combinations", "Worked example".

**Sources.** As for [hsm](hsm.md) and [tee](tee.md); NIST IR 8214C, first call for multi-party
threshold schemes (2026, **verify current**); Fireblocks on MPC-CMP in SGX (reported;
**verify current**).
