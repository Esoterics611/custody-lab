# Inclusion proofs

**In one sentence.** An inclusion proof is the list of sibling nodes on the path from one leaf to
the root of a Merkle tree, one per level, with which the leaf's owner recomputes the root and checks
it against the published one.

## The problem

A client wants to confirm its balance is in the published tree without receiving everyone else's
balances, and the proof must stay small however many clients there are.

## The idea

At each level the client needs only the other child of its parent: it combines its own node with the
sibling, then the result with the next sibling, up to the root. A tree over $n$ leaves needs about
$\log_2 n$ siblings: 10 for a thousand clients, 20 for a million.

In the demo, beta-fund (1.50 BTC) receives two siblings: alpha-capital's leaf (sum 1.1499969) on the
left, then the right-hand parent (sum 1.50). It computes $1.50 + 1.1499969 = 2.6499969$, then
$2.6499969 + 1.50 = 4.1499969$, the published total, and checks the hash at each step. An altered
balance, salt or sibling sum fails.

## Why custody cares

- Each client checks its own balance against the published root without seeing the full list.
- The total is protected only by the clients who check.
- In a sum tree each sibling's sum is revealed: beta-fund learns alpha-capital's exact balance. Each
  leaf's random salt stops outsiders from guessing balances from leaf hashes; hiding the sums needs
  a zero-knowledge proof of liabilities.

## In the demo

`MerkleSumTree.proof` and `verify` in `src/custody_lab/reserves/merkle_sum.py`. The demo checks every
client's proof after each settlement (`custody_lab.demo.pipeline`).

## In the manual

[Chapter 6](../../manual/chapters/06-reserves.md),
"[Hash trees](../../manual/chapters/06-reserves.md#hash-trees)" (a proof built by hand on four items),
"[Salts and what a proof reveals](../../manual/chapters/06-reserves.md#salts-and-what-a-proof-reveals)",
"[Inclusion proofs](../../manual/chapters/06-reserves.md#inclusion-proofs)".

## Sources

R. C. Merkle, CRYPTO 1987; Bitcoin's block-header Merkle root (Bitcoin Core `consensus/merkle.cpp`).
