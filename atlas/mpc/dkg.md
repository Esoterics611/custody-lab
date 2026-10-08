# Distributed key generation

**In one sentence.** In distributed key generation (DKG) every participant deals a Shamir sharing of
its own random secret, each participant's share is the sum of what it receives, and the group key
belongs to a secret, the sum of everyone's, that never exists in any one place.

## The problem

If one machine generates a key and splits it, that machine saw the key, so "no single machine holds
the key" is false from the start. A participant that speaks last could also try to choose the group
key.

## The idea

Each participant picks its own random polynomial, sends each other participant one point on it
privately, and publishes **Feldman commitments** (each coefficient times $G$) so receivers can check
their points. Each receiver adds up the points it received, and the sum is its share.

On the manual's toy curve, three participants pick the lines $3 + x$, $2 + 5x$ and $4 - x$ modulo 31.
Participant 1 receives 4, 7 and 3 and keeps 14; participant 2 receives 5, 12 and 2 and keeps 19;
participant 3 receives 6, 17 and 1 and keeps 24. These are the shares of $9 + 5x$, a line nobody
chose. The group key is the sum of the starting-value commitments, $3G + 2G + 4G = 9G$, which anyone
can compute; the key 9 would need all three starting values, and each participant knows only its own.
A sub-share that fails its Feldman check (participant 2 sending 18 instead of 17) is caught.

Each participant also attaches a zero-knowledge proof that it knows the discrete logarithm of its
first commitment. That stops a **rogue-key attack**, in which the last participant publishes a
commitment built to cancel the others' and make the group key one it alone controls.

## Why custody cares

- Without DKG, the dealer saw the key at birth.
- The proof of knowledge is not optional: Feldman checks alone miss the rogue-key attack when
  $t = n$.

## In the demo

- Signing path: `SigningCluster.dkg()` runs the ZF crate's `dkg::part1` to `part3` across three
  processes, in the demo's step 2.
- Teaching code: `src/custody_lab/mpc/dkg.py` (`Dealer`, `check_round1`, `combine`, `run`).

## In the manual

[Chapter 0](../../manual/chapters/00-orientation.md),
"[Creating the key in pieces](../../manual/chapters/00-orientation.md#creating-the-key-in-pieces)";
[chapter 2](../../manual/chapters/02-mpc-custody.md),
"[Zero-knowledge proofs](../../manual/chapters/02-mpc-custody.md#zero-knowledge-proofs)" (the
rogue-key attack, run in a cell),
"[Distributed key generation](../../manual/chapters/02-mpc-custody.md#distributed-key-generation)",
"[Distributed key generation on the toy curve](../../manual/chapters/02-mpc-custody.md#distributed-key-generation-on-the-toy-curve)",
and Exercise 4.

## Sources

T. Pedersen, EUROCRYPT 1991; R. Gennaro, S. Jarecki, H. Krawczyk, T. Rabin, *Journal of Cryptology*
20 (2007); C. Komlo, I. Goldberg, SAC 2020 (key generation with proof of knowledge).
