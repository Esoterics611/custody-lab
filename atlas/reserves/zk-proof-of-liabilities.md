# Zero-knowledge proof of liabilities

**Definition.** A proof of liabilities in which each sum is a hiding commitment (Pedersen,
$vG + rH$) and each commitment carries a range proof that its value is in $[0, 2^{64})$. Clients
still verify inclusion, but no sibling sum or total is revealed.

**Why custody cares.**
- It removes the sum tree's leak of neighbouring balances.
- It can hide the total and, in Provisions, which addresses hold the assets.
- It adds a proving system that has to be implemented and audited correctly.

**In the demo.** Not implemented (chapter section only, per the build plan).

**In the manual.** [Chapter 6](../../manual/chapters/06-reserves.md), "[Zero-knowledge proofs of liabilities](../../manual/chapters/06-reserves.md#zero-knowledge-proofs-of-liabilities)".

**Sources.** G. G. Dagher et al., "Provisions", ACM CCS 2015; Y. Ji, K. Chalkias, "Generalized
Proof of Liabilities" (DAPOL+), ACM CCS 2021; Rust implementation `dapol` (**verify current**).
