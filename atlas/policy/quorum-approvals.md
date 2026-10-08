# Quorum approvals

**Definition.** An instruction needs $q$ valid approvals, with $q$ set by the amount tier. An
approval counts only if it meets all of these:
- it is an Ed25519 signature by a registered approver;
- it covers this instruction's digest;
- it is not from the initiator (four-eyes, maker-checker);
- it is not a duplicate.

**Why custody cares.**
- The approval quorum (people) and the signing quorum (machines holding key shares) are separate
  controls. The link between them is the engine's signed authorisation, which every signer checks.
- Binding approvals to the instruction digest stops an approval being moved to a different
  payment.

**In the demo.** `src/custody_lab/policy/model.py` (`Approval.create`, `Approval.is_valid`);
counting in `engine.py`.

**In the manual.** [Chapter 4](../../manual/chapters/04-policy.md), "[Intuition](../../manual/chapters/04-policy.md#intuition)", "[The decision function](../../manual/chapters/04-policy.md#the-decision-function)", worked example rows 2, 3 and
8.

**Sources.** NIST SP 800-53 Rev. 5, AC-5 (separation of duties).
