# Threshold signatures

**In one sentence.** A $t$-of-$n$ threshold signature scheme spreads one private key over $n$
parties so that any $t$ of them can jointly produce an ordinary signature under one public key,
fewer cannot, and the key itself is never assembled anywhere.

## The problem

Shamir sharing protects a key while it is stored, but to sign, the shares must be combined, and the
machine that combines them holds the whole key. Whoever controls that machine, through malware, an
insider or a memory dump, holds the key from then on.

## The idea

Each party computes a **partial signature** from its own share, and the partial signatures combine
into the signature. This works for Schnorr because its formula only adds and multiplies by public
numbers: $s = k + e\,d$. If each party turns its Shamir share into an additive share by multiplying
by its Lagrange weight, the partial results add up to the whole.

On the manual's toy curve the key 9 is shared as $(1, 14)$, $(2, 19)$, $(3, 24)$ modulo 31. Parties 1
and 3 multiply by their weights 17 and 15 to get additive shares 21 and 19 (which sum to 40, that is
9). With nonces 3 and 4 and challenge 5, their partial signatures are $3 + 5 \times 21 \equiv 15$ and
$4 + 5 \times 19 \equiv 6$, which add to 21: the signature the whole key would have produced. Neither
party ever computed 9.

## Why custody cares

- It removes the single machine that holds a whole key, at creation (with distributed key
  generation) and at signing.
- Compared with on-chain multisig, the quorum stays off the chain: a spend is one ordinary signature,
  so it is private, costs the same as a single-key spend and works on any chain whose signature
  scheme is supported. Participants can be refreshed without moving funds.
- The cost is a protocol and an implementation that must themselves be correct; most known breaks
  were in implementations with missing proofs.
- A custody platform has two quorums: people approving in the policy engine (chapter 4) and
  machines holding shares. They are separate controls.

## In the demo

`src/custody_lab/mpc/cluster.py` (`SigningCluster`): a 2-of-3 FROST cluster, one operating-system
process per share, used in the demo's steps 2 and 7.

## In the manual

[Chapter 0](../../manual/chapters/00-orientation.md),
"[Signing with pieces: threshold signing](../../manual/chapters/00-orientation.md#signing-with-pieces-threshold-signing)"
(worked with school arithmetic); [chapter 2](../../manual/chapters/02-mpc-custody.md),
"[What this chapter is for](../../manual/chapters/02-mpc-custody.md#what-this-chapter-is-for)",
"[From Shamir shares to additive shares](../../manual/chapters/02-mpc-custody.md#from-shamir-shares-to-additive-shares)"
and "[Threshold Schnorr on the toy curve](../../manual/chapters/02-mpc-custody.md#threshold-schnorr-on-the-toy-curve)".

## Sources

RFC 9591, section 1; Y. Lindell, "Secure Multiparty Computation", *CACM* 64(1), 2021.
