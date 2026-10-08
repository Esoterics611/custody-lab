# Inclusion proofs

**Definition.** The sibling of each node on the path from one leaf to the root, one per level.
The holder recomputes each parent and compares the result with the published root. A tree over
$n$ leaves needs about $\log_2 n$ siblings: 20 for a million clients.

**Why custody cares.**
- Each client checks its own balance against the published root without seeing the other
  balances in full.
- The total is protected only by the clients who check.
- In a sum tree each sibling's sum is revealed, so a client learns its neighbours' balances.
  Salting each leaf stops outsiders from guessing balances from leaf hashes.

**In the demo.** `MerkleSumTree.proof` and `verify` in `src/custody_lab/reserves/merkle_sum.py`.
The demo checks every client's proof after each settlement (`custody_lab.demo.pipeline`).

**In the manual.** [Chapter 6](../../manual/chapters/06-reserves.md), "[Hash trees](../../manual/chapters/06-reserves.md#hash-trees)", "[Salts and what a proof reveals](../../manual/chapters/06-reserves.md#salts-and-what-a-proof-reveals)", "[Inclusion proofs](../../manual/chapters/06-reserves.md#inclusion-proofs)".

**Sources.** R. C. Merkle, CRYPTO 1987; Bitcoin's block-header Merkle root (Bitcoin Core
`consensus/merkle.cpp`).
