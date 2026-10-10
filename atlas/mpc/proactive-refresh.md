# Proactive share refresh

**In one sentence.** In a proactive refresh the share holders jointly add a fresh sharing of zero
to their shares, so every share changes, the key does not, and shares from before and after the
refresh cannot be combined.

## The problem

A **mobile adversary** compromises different machines at different times: share 1 this year, share 3
next year. With a 2-of-3 key, two shares stolen at different times are as good as two stolen at once,
unless the shares themselves change in between.

## The idea

Each holder deals a polynomial whose starting value is 0, so adding all the dealings adds 0 to the
secret. Each holder adds the sub-shares it receives to its own share.

On the manual's toy curve the shares of $9 + 5x$ modulo 31 are 14, 19 and 24. The holders deal $3x$,
$7x$ and $x$, whose slopes add to 11, so the shared line becomes $9 + 16x$ and the new shares are 25,
10 and 26. New shares 1 and 3 recover 9 with the usual weights. Old share 1 with new share 3 gives
$17 \times 14 + 15 \times 26 \equiv 8$: the wrong key.

## Why custody cares

- It defends against an attacker who collects shares over time.
- It lets operations rotate share material on a schedule, or after an incident, without moving funds
  to a new address.
- It does not repair a compromised quorum: if $t$ shares leaked before the refresh, the key is gone,
  and the only response is to move the funds.

## In the demo

- Signing path: `SigningCluster.refresh()` runs the ZF crate's `refresh_dkg_part1` to `part3`
  across the three signer processes, with each point sealed to its recipient. The key ceremonies
  (`custody_lab.demo.ceremonies`) show a share stolen before a refresh failing to combine with one
  stolen after it; the protocol tab (`custody_lab.demo.protocol`) shows the three rounds' messages,
  whose round-1 packages carry one commitment fewer than key generation's (104 bytes, not 137).
- Teaching code: `src/custody_lab/mpc/dkg.py` (`refresh`).

## In the manual

[Chapter 2](../../manual/chapters/02-mpc-custody.md):
"[Proactive refresh](../../manual/chapters/02-mpc-custody.md#proactive-refresh)",
"[Proactive refresh on the toy curve](../../manual/chapters/02-mpc-custody.md#proactive-refresh-on-the-toy-curve)",
and the DKG walkthrough, which shows an old and a new share failing to sign together; the
demo walkthrough's "[Key ceremonies](../../manual/demo-walkthrough.md#key-ceremonies)" and "[Watching the
protocol](../../manual/demo-walkthrough.md#watching-the-protocol)".

## Sources

A. Herzberg, S. Jarecki, H. Krawczyk, M. Yung, "Proactive Secret Sharing", CRYPTO 1995.
