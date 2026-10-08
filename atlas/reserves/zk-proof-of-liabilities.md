# Zero-knowledge proof of liabilities

**In one sentence.** A zero-knowledge proof of liabilities replaces each sum in the tree with a
hiding commitment and proves, without revealing it, that each committed value is non-negative, so
clients can still verify inclusion while no sibling sum or total is revealed.

## The problem

A Merkle sum tree's inclusion proof reveals each sibling's sum: in a small tree, one client learns
another's exact balance.

## The idea

Each sum becomes a **Pedersen commitment** $C = vG + rH$, where $v$ is the hidden value, $H$ a second
generator whose relation to $G$ nobody knows, and $r$ random. The commitment hides $v$ (for any value
there is an $r$ giving the same $C$) and binds it (opening it to another value would require knowing
how $H$ relates to $G$). Pedersen commitments add, so a parent's commitment is the sum of its
children's and the tree's arithmetic works on hidden values.

Hidden sums bring back the negative-balance attack, because the verifier can no longer see a sum. A
**range proof** on each commitment shows, in zero knowledge, that its value lies in $[0, 2^{64})$.
Provisions (2015) also hides which addresses hold the assets; DAPOL+ (2021) defines what a proof of
liabilities must achieve and gives a scheme using a sparse Merkle tree and Bulletproofs range proofs.

## Why custody cares

- It removes the sum tree's leak of neighbouring balances.
- It can hide the total and, in Provisions, the custodian's addresses.
- It adds a proving system that has to be implemented and audited correctly; reviews of production
  liability proofs have found exploitable defects (Chalkias, Chatzigiannis and Ji 2022).

## In the demo

Not implemented: a chapter section only, as the build plan states.

## In the manual

[Chapter 6](../../manual/chapters/06-reserves.md),
"[Zero-knowledge proofs of liabilities](../../manual/chapters/06-reserves.md#zero-knowledge-proofs-of-liabilities)".

## Sources

G. G. Dagher et al., "Provisions", ACM CCS 2015; Y. Ji, K. Chalkias, "Generalized Proof of
Liabilities" (DAPOL+), ACM CCS 2021; Rust implementation `dapol` (**verify current**).
