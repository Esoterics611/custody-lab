# Share backup, recovery and repair

**Definition.** Three mechanisms keep a threshold key alive when share holders fail:
- Encrypted backups of each share to an offline recovery key.
- Publicly verifiable encryption: anyone can check that a backup encrypts the share matching a
  known public share.
- Share repair: $t$ holders help rebuild a lost share without revealing their own.

**Why custody cares.**
- Losing more than $n - t$ shares loses the funds.
- Backups must be provably valid (an auditor can check them) and held under different control
  from the live shares.
- Repair restores a holder without a full re-key.

**In the demo.** Not implemented. cb-mpc provides PVE (`docs/spec/publicly-verifiable-encryption-spec.pdf`).
ZF FROST provides `keys::repairable::repair_share_part1` to `part3` (observed in the crate source).

**In the manual.** Chapter 2, "Backup, recovery and repair".

**Sources.** cb-mpc README, "Key Management Responsibilities"; ZF FROST crate documentation.
