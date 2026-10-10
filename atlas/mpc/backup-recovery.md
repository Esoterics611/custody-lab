# Share backup, recovery and repair

**In one sentence.** Three mechanisms keep a threshold key alive when share holders fail: encrypted
backups of each share, backups whose validity anyone can check, and repair of a lost share by the
other holders.

## The problem

A threshold key survives the loss of some shares, but not too many: with $t$-of-$n$, losing more
than $n - t$ shares leaves fewer than $t$, and the coins are locked forever. Machines fail, sites are
lost and staff leave, so shares need backups, and the backups must neither be useless when needed
nor become a back door.

## The idea

- **Encrypted share backup.** Each share is encrypted to an offline recovery key held under
  different control from the live share. Each share needs its own recovery key: if one key opened
  every backup, that key and the backups together would be the whole key.
- **Publicly verifiable encryption** (cb-mpc's PVE). Anyone can check that a backup ciphertext
  encrypts the share matching a known public share, without decrypting it, so a custodian can show
  an auditor that its backups would work.
- **Share repair.** $t$ holders help rebuild a lost holder's share without revealing their own, so a
  holder can be restored without a full re-key.

Backups must cover shares, never nonces: a nonce restored from backup and used again leaks the
share. For long-term secrecy the backup's encryption should resist a future quantum computer,
because a copy taken today can be decrypted whenever one exists (chapter 7).

## Why custody cares

- It decides whether the loss of a site is an outage or a loss of funds.
- Backups must be provably valid and held under different control from the live shares.
- Repair restores a holder without moving the coins to a new key.

## In the demo

- Share repair is on the signing path: `SigningCluster.repair()` runs ZF FROST's
  `keys::repairable::repair_share_part1` to `part3` across the signer processes, with every delta
  and sigma sealed to its recipient. The key ceremonies (`custody_lab.demo.ceremonies`) rebuild a
  wiped share, and the protocol tab (`custody_lab.demo.protocol`) shows the four 60-byte sealed
  deltas and two sealed sigmas that do it.
- Backups are not on the signing path. Chapter 7 encrypts a teaching DKG share to an ML-KEM
  recovery key. cb-mpc provides PVE (`docs/spec/publicly-verifiable-encryption-spec.pdf`).

## In the manual

[Chapter 2](../../manual/chapters/02-mpc-custody.md),
"[Backup, recovery and repair](../../manual/chapters/02-mpc-custody.md#backup-recovery-and-repair)";
[chapter 7](../../manual/chapters/07-post-quantum.md),
"[A share backup under ML-KEM](../../manual/chapters/07-post-quantum.md#a-share-backup-under-ml-kem)";
the walkthrough's "[Key ceremonies](../../manual/demo-walkthrough.md#key-ceremonies)" and "[Watching the
protocol](../../manual/demo-walkthrough.md#watching-the-protocol)".

## Sources

cb-mpc README, "Key Management Responsibilities"; ZF FROST crate documentation.
