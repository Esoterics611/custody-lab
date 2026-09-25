# Post-quantum migration design

**Definition.** The order in which a custodian moves each use of public-key cryptography to
post-quantum or hybrid schemes: by exposure first, and by who controls the change.

**Why custody cares.**
- Encryption with a long secrecy lifetime (share backups, recorded transport) is exposed today.
- Internal signatures (authorisations, approvals, attestations) are the custodian's to change.
- Chain signatures wait for the chain. A Taproot key-path output shows its key on chain from
  creation, so FROST's need for Taproot is also a choice of quantum exposure.

**In the demo.** Authorisation tokens are hybrid Ed25519 + ML-DSA-65. Approvals, proof of control
and settlements are still classical.

**In the manual.** Chapter 7, "Migration design", Exercise 5.

**Sources.** NIST IR 8547 initial public draft (2024) (**verify current**); BIP 360
(Pay-to-Merkle-Root) and BIP 361 (**verify current**).
