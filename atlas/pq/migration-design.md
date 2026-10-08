# Post-quantum migration design

**In one sentence.** A custodian migrates each use of public-key cryptography to post-quantum or
hybrid schemes in order of exposure, starting with what is already exposed and what it alone
controls, and ending with the chain.

## The problem

Signatures fail on the day a quantum computer arrives; encryption fails retroactively, because
ciphertext recorded today can be decrypted then. And some changes are the custodian's to make while
others wait for Bitcoin's community to agree.

## The idea

| Component | Today | Exposure | Step | Controlled by |
|-------------------|-----------------------|-----------------------------|----------------------------|---------------------|
| Share backups | encrypted to a recovery key | harvest now, decrypt later | ML-KEM with X25519 | custodian |
| Authorisations | Ed25519 and ML-DSA-65 | none while ML-DSA holds | done in the demo | custodian |
| Approvals | Ed25519 | forged approvals | hybrid keys | approvers' devices (**verify current**) |
| Proof of control | BIP340 | forged attestations | a post-quantum attestation key alongside | custodian |
| Settlements | FROST BIP340, Taproot key path | key visible on chain | new output type and signature | Bitcoin consensus, research |
| Transport | TLS | recorded sessions | hybrid key exchange | TLS stacks (**verify current**) |

Backups come first, because a copy taken today is broken whenever a quantum computer arrives. The
internal signatures come next, because changing them needs nobody else's agreement. Settlements come
last. A Taproot key-path output shows its key on chain from the moment it is created, so choosing
FROST, which needs Taproot, is also a choice of quantum exposure; outputs that commit to a hash of the
key reveal it only when spent.

## Why custody cares

It turns an open-ended threat into an ordered list of changes, each with an owner, and it shows which
risk the custodian carries until the chain moves.

## In the demo

Authorisation tokens are hybrid Ed25519 + ML-DSA-65. Approvals, proof of control and settlements are
still classical.

## In the manual

[Chapter 7](../../manual/chapters/07-post-quantum.md),
"[What this chapter is for](../../manual/chapters/07-post-quantum.md#what-this-chapter-is-for)" (the
two clocks), "[Migration design](../../manual/chapters/07-post-quantum.md#migration-design)", and
Exercise 5.

## Sources

NIST IR 8547 initial public draft (2024) (**verify current**); BIP 360 (Pay-to-Merkle-Root) and BIP
361 (**verify current**).
