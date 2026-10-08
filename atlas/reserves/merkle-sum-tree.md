# Merkle sum tree

**In one sentence.** A Merkle sum tree is a hash tree over client balances in which every node also
carries the sum of the balances below it, and every parent's hash covers both children's hashes and
sums, so the root commits to every balance and to the total owed.

## The problem

A custodian wants to publish its total liabilities in a form each client can check includes its own
balance at its true value, without publishing anyone's balance.

## The idea

Each leaf is a client's balance with a hash of its identifier, balance and a random salt. Leaves are
paired; each parent records the sum of its two children and a hash of both children, sums included;
the pairing repeats up to a root whose sum is the total.

The demo's tree after settlement, leaves sorted by identifier: alpha-capital 1.1499969, beta-fund
1.50, delta-trading 0.50 and gamma-treasury 1.00. The parents are 2.6499969 and 1.50, and the root
is 4.1499969 BTC.

**Why the parent must hash both sums.** If the parent hashes only its total, a custodian can show
each client a different split of it. With alice at 1 BTC and bob at 3, it publishes a total of 3,
shows alice a sibling sum of 2 and bob a sibling sum of 0; both add up to 3 and both recompute the
same parent hash. 1 BTC of liabilities has disappeared (Hu, Zhang and Guo 2019). When the parent
hashes each child's sum, alice's and bob's recomputations give different hashes, and one of them
detects the lie.

**Why sums must be non-negative.** An invented client with a negative balance would cancel real
balances in the total. The verifier refuses negative sums and the tree refuses negative balances.

## Why custody cares

- It lets a custodian publish total liabilities without publishing any client's balance.
- The published total is at least the total of the balances that clients verified, and no stronger
  than that: a client who never checks protects nobody.

## In the demo

`src/custody_lab/reserves/merkle_sum.py` (`MerkleSumTree`, `leaf`, `parent`). Tests:
`tests/reserves/test_merkle_sum.py`, including the total-only attack. The demo's step 9 builds the
tree after each settlement.

## In the manual

[Chapter 0](../../manual/chapters/00-orientation.md),
"[Showing that the coins are there: proof of reserves](../../manual/chapters/00-orientation.md#showing-that-the-coins-are-there-proof-of-reserves)";
[chapter 6](../../manual/chapters/06-reserves.md),
"[Adding sums](../../manual/chapters/06-reserves.md#adding-sums)",
"[What each parent must commit to](../../manual/chapters/06-reserves.md#what-each-parent-must-commit-to)",
the worked example, and
"[The attack on a total-only tree](../../manual/chapters/06-reserves.md#the-attack-on-a-total-only-tree)".

## Sources

K. Hu, Z. Zhang, K. Guo, *Computers & Security*, 2019 (IACR ePrint 2018/1139); K. Chalkias,
P. Chatzigiannis, Y. Ji, IACR ePrint 2022/043.
