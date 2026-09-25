# Proactive share refresh

**Definition.** Holders jointly add a fresh sharing of zero to their shares. The public key is
unchanged, every share changes, and old and new shares cannot be combined.

**Why custody cares.**
- It defends against a mobile adversary who compromises different machines over time.
- It lets operations rotate share material on a schedule, or after an incident, without moving
  funds to a new address.
- It is not a fix for a compromised quorum: if $t$ shares leaked before the refresh, the key is
  gone.

**In the demo.** Teaching code: `src/custody_lab/mpc/dkg.py` (`refresh`). The ZF crate provides
`keys::refresh` for the signing path; the demo does not call it yet.

**In the manual.** Chapter 2, "Proactive refresh", and the DKG walkthrough, which shows old and new
shares failing to sign together.

**Sources.** Herzberg, Jarecki, Krawczyk, Yung, "Proactive Secret Sharing", CRYPTO 1995.
