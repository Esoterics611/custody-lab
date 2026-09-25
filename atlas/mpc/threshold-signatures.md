# Threshold signatures

**Definition.** A $t$-of-$n$ threshold signature scheme spreads one private key over $n$ parties so
that any $t$ can jointly produce a signature and fewer cannot. The output is one ordinary signature
under one public key; the key is never assembled.

**Why custody cares.**
- It removes the single machine that holds a whole key.
- Compared with on-chain multisig, the quorum stays off chain, so spends are private, cheaper and
  chain-agnostic. Participants can change without moving funds.
- A custody platform has two quorums: people approving in the policy engine (Module 4) and
  machines holding shares. They are separate controls.

**In the demo.** `src/custody_lab/mpc/cluster.py` (`SigningCluster`): a 2-of-3 FROST cluster, one
process per share.

**In the manual.** Chapter 2, "Intuition" and "From Shamir shares to additive shares".

**Sources.** RFC 9591, section 1; Lindell, "Secure Multiparty Computation" survey, *CACM* 64(1),
2021.
