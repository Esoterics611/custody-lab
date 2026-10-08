# Quorum approvals

**In one sentence.** An instruction needs a set number of approvals, fixed by its amount tier, and
each approval is a signature by a registered person, other than the one who raised the instruction,
over that instruction's exact digest.

## The problem

An approval recorded as a database row ("bob approved instruction 42") can be created by anyone who
can write to the database, and nothing ties it to the amount and address bob actually saw.

## The idea

Each approver holds an Ed25519 key pair on a device bound to that person. Approving means signing the
instruction's **digest**, the SHA-256 of its canonical encoding. An approval counts only if all of
these hold:

- it is a valid signature by a registered approver;
- it covers this instruction's digest, so it cannot be moved to another payment;
- it is not from the initiator (four-eyes, maker-checker);
- it is not a duplicate: each approver counts once.

In the demo's step 6, ops-desk raises an instruction for 0.85 BTC, which falls in the two-approval
tier. With bob's approval alone the engine answers PENDING, "1 of 2 required approvals"; with bob's
and carol's it answers APPROVED and issues the authorisation.

## Why custody cares

- The approval quorum (people) and the signing quorum (machines holding key shares) are separate
  controls. The link between them is the engine's signed authorisation, which every signer checks.
  Compromising an approver yields no share, and compromising a signer yields no approval.
- Binding approvals to the digest stops an approval being moved to a different payment, and anyone
  holding the approvals can check later who approved what.

## In the demo

`src/custody_lab/policy/model.py` (`Approval.create`, `Approval.is_valid`); counting in `engine.py`.

## In the manual

[Chapter 0](../../manual/chapters/00-orientation.md),
"[Two quorums](../../manual/chapters/00-orientation.md#two-quorums)";
[chapter 4](../../manual/chapters/04-policy.md),
"[Approvals: four eyes, signed](../../manual/chapters/04-policy.md#approvals-four-eyes-signed)",
"[The decision function](../../manual/chapters/04-policy.md#the-decision-function)", and worked
example rows 2, 3 and 8.

## Sources

NIST SP 800-53 Rev. 5, AC-5 (separation of duties).
