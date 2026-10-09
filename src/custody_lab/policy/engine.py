"""Default-deny policy engine for settlement instructions.

An instruction is authorised only if every check passes; anything the policy does not explicitly
allow is denied. Checks run in this order, and the first failure decides:

1. The asset has a policy.
2. The amount is a finite, positive Decimal.
3. The amount falls within a tier (tiers set the approval quorum by size; above the top tier is
   denied outright).
4. The destination is whitelisted for the asset.
5. The rolling-window velocity limit holds, counting authorisations already issued.
6. The instruction has not been authorised before.
7. Enough valid, distinct approvals are present. Valid means: signed by a known approver, over
   this instruction's digest, and not the initiator (four-eyes). Too few gives PENDING, not
   DENIED.

The audit log is the engine's only state: velocity and "authorised before" are read back from
it, so the record and the decision cannot disagree.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from enum import StrEnum

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from custody_lab.foundations.hashing import sha256, tagged_hash
from custody_lab.policy import authorisation
from custody_lab.policy.audit import AuditLog, Clock
from custody_lab.policy.authorisation import Authorisation, AuthorityKey
from custody_lab.policy.model import Approval, SettlementInstruction
from custody_lab.reserves.snapshot import ATTESTATION_TAG


class Status(StrEnum):
    APPROVED = "approved"
    PENDING = "pending"
    DENIED = "denied"


@dataclass(frozen=True)
class Decision:
    status: Status
    reason: str
    approvers: tuple[str, ...] = ()
    quorum: int | None = None


@dataclass(frozen=True)
class Tier:
    max_amount: Decimal
    quorum: int


@dataclass(frozen=True)
class AssetPolicy:
    tiers: tuple[Tier, ...]  # ascending by max_amount
    whitelist: frozenset[str]
    velocity_window: timedelta
    velocity_limit: Decimal


@dataclass(frozen=True)
class Policy:
    assets: Mapping[str, AssetPolicy]
    approvers: Mapping[str, Ed25519PublicKey]


class PolicyDenied(Exception):
    def __init__(self, decision: Decision) -> None:
        super().__init__(f"{decision.status}: {decision.reason}")
        self.decision = decision


class PolicyEngine:
    def __init__(
        self,
        policy: Policy,
        authority_key: AuthorityKey,
        audit: AuditLog,
        clock: Clock,
        authorisation_ttl: timedelta = timedelta(seconds=60),
    ) -> None:
        self.policy, self.audit = policy, audit
        self._key, self._clock, self._ttl = authority_key, clock, authorisation_ttl

    @property
    def authority_public_key(self) -> bytes:
        """The hybrid public key (Ed25519 then ML-DSA-65) that signers are configured with."""
        return self._key.public_bytes()

    def _velocity_used(self, asset: str, window: timedelta) -> Decimal:
        since = self._clock() - window
        return sum(
            (
                Decimal(e.payload["amount"])
                for e in self.audit.entries
                if e.event == "authorised" and e.payload["asset"] == asset and e.time > since
            ),
            Decimal(0),
        )

    def _already_authorised(self, digest: bytes) -> bool:
        return any(
            e.event == "authorised" and e.payload["instruction_digest"] == digest.hex()
            for e in self.audit.entries
        )

    def _decide(self, ins: SettlementInstruction, approvals: Sequence[Approval]) -> Decision:
        asset = self.policy.assets.get(ins.asset)
        if asset is None:
            return Decision(Status.DENIED, f"no policy for asset {ins.asset!r}")
        if not ins.amount.is_finite() or ins.amount <= 0:
            return Decision(Status.DENIED, "amount must be a positive number")
        tier = next((t for t in asset.tiers if ins.amount <= t.max_amount), None)
        if tier is None:
            return Decision(Status.DENIED, "amount above the highest tier")
        if ins.destination not in asset.whitelist:
            return Decision(Status.DENIED, f"destination {ins.destination} is not whitelisted")
        used = self._velocity_used(ins.asset, asset.velocity_window)
        if used + ins.amount > asset.velocity_limit:
            return Decision(
                Status.DENIED,
                f"velocity limit {asset.velocity_limit} {ins.asset} per "
                f"{asset.velocity_window / timedelta(hours=1):g} hours; "
                f"{used} {ins.asset} already authorised",
            )
        digest = ins.digest()
        if self._already_authorised(digest):
            return Decision(Status.DENIED, "instruction already authorised")
        counted = sorted(
            {
                a.approver
                for a in approvals
                if a.instruction_digest == digest
                and a.approver != ins.initiator
                and a.approver in self.policy.approvers
                and a.is_valid(self.policy.approvers[a.approver])
            }
        )
        status = Status.APPROVED if len(counted) >= tier.quorum else Status.PENDING
        reason = f"{len(counted)} of {tier.quorum} required approvals"
        return Decision(status, reason, tuple(counted), tier.quorum)

    def evaluate(self, ins: SettlementInstruction, approvals: Sequence[Approval]) -> Decision:
        decision = self._decide(ins, approvals)
        self.audit.append(
            "evaluated",
            {
                "instruction_id": ins.instruction_id,
                "instruction_digest": ins.digest().hex(),
                "status": decision.status.value,
                "reason": decision.reason,
                "approvers": list(decision.approvers),
            },
        )
        return decision

    def authorise(
        self, ins: SettlementInstruction, approvals: Sequence[Approval], message: bytes
    ) -> Authorisation:
        """Evaluate and, if approved, issue a signed authorisation for exactly ``message``.

        Until Module 5, ``message`` is taken on trust as the signing payload for ``ins``. Module 5
        derives it from the instruction (the transaction's sighash) instead.
        """
        decision = self.evaluate(ins, approvals)
        if decision.status is not Status.APPROVED:
            raise PolicyDenied(decision)
        token = authorisation.issue(self._key, ins.digest(), message, self._clock() + self._ttl)
        self.audit.append(
            "authorised",
            {
                "authorisation_id": token.authorisation_id,
                "instruction_id": ins.instruction_id,
                "instruction_digest": ins.digest().hex(),
                "asset": ins.asset,
                "amount": ins.amount,
                "destination": ins.destination,
                "message": message.hex(),
                "expires_at": token.expires_at,
            },
        )
        return token

    def authorise_attestation(self, statement: bytes) -> Authorisation:
        """Authorise the signers to sign a reserves attestation, ``H_tag(statement)``.

        This is the one message class allowed without approvals. The tag makes the message
        domain-separated from every transaction sighash, so the token cannot move funds.
        """
        message = tagged_hash(ATTESTATION_TAG, statement)
        token = authorisation.issue(
            self._key, sha256(statement), message, self._clock() + self._ttl
        )
        self.audit.append(
            "attestation_authorised",
            {"authorisation_id": token.authorisation_id, "message": message.hex()},
        )
        return token
