# Distributed key generation

**Definition.** Every participant deals a Shamir sharing of its own random secret, with Feldman
commitments $C_{ik} = a_{ik}G$ so that receivers can verify their sub-shares. Each final share is
the sum of the received sub-shares. The group key is $\sum C_{i0}$, and its secret exists nowhere.
Each participant also proves knowledge of $a_{i0}$.

**Why custody cares.**
- Without DKG, a dealer saw the key at birth, so "no single machine held the key" is false from
  the start.
- The proof of knowledge stops a rogue-key attack in which a participant cancels the others'
  contributions. Feldman checks alone miss it when $t = n$.

**In the demo.**
- Signing path: `SigningCluster.dkg()` runs the ZF crate's `dkg::part1` to `part3` across three
  processes.
- Teaching code: `src/custody_lab/mpc/dkg.py` (`Dealer`, `check_round1`, `combine`, `run`).

**In the manual.** Chapter 2, "Distributed key generation", Exercise 4.

**Sources.** T. Pedersen, EUROCRYPT 1991; Gennaro, Jarecki, Krawczyk, Rabin, *Journal of
Cryptology* 20 (2007); Komlo and Goldberg 2020 (KeyGen with proof of knowledge).
