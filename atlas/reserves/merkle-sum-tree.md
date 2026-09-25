# Merkle sum tree

**Definition.** A hash tree over client balances in which every node also carries a sum. Each
parent's hash covers both children's hashes and both children's sums, and its sum is their total,
so the root commits to every balance and to total liabilities.

**Why custody cares.**
- It lets a custodian publish total liabilities without publishing any client's balance.
- If the parent hashes only the total, a custodian can publish the larger child's sum instead of
  the two added together, and both clients' checks still pass (Hu, Zhang and Guo 2019). Hashing
  each child's sum prevents it.
- Sums must be non-negative, or an invented negative balance cancels real ones.

**In the demo.** `src/custody_lab/reserves/merkle_sum.py` (`MerkleSumTree`, `leaf`, `parent`).
Tests: `tests/reserves/test_merkle_sum.py`, including the total-only attack.

**In the manual.** Chapter 6, "Adding sums", "What each parent must commit to", the worked
example and "The attack on a total-only tree".

**Sources.** K. Hu, Z. Zhang, K. Guo, *Computers & Security*, 2019 (IACR ePrint 2018/1139);
K. Chalkias, P. Chatzigiannis, Y. Ji, IACR ePrint 2022/043.
