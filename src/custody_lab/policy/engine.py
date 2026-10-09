"""Default-deny policy engine for settlement instructions.

An instruction is authorised only if every check passes; anything the policy does not explicitly
allow is denied. Checks run in this order, and the first failure decides:

1. The asset has a policy.
2. The amount is a finite, positive Decimal.
3. The amount falls within a tier (tiers set the approval quorum by size; above the top tier is
   denied outright).
4. The destination is whitelisted for the asset: listed in the policy, or registered through
   ``register`` and past the registration delay.
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
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from custody_lab.foundations.hashing import sha256, tagged_hash
from custody_lab.policy import authorisation
from custody_lab.policy.audit import AuditLog, Clock
from custody_lab.policy.authorisation import Authorisation, AuthorityKey
from custody_lab.policy.model import AddressRegistration, Approval, SettlementInstruction
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
        registration_delay: timedelta = timedelta(hours=24),
    ) -> None:
        self.policy, self.audit = policy, audit
        self._key, self._clock, self._ttl = authority_key, clock, authorisation_ttl
        self._delay = registration_delay

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

    def _registered(self, asset: str, address: str) -> datetime | None:
        """When ``address`` became, or becomes, payable for ``asset`` by registration."""
        for e in self.audit.entries:
            if e.event == "registered" and e.payload["asset"] == asset:
                if e.payload["address"] == address:
                    effective: datetime = e.payload["effective_at"]
                    return effective
        return None

    def _not_payable(self, asset_name: str, asset: AssetPolicy, address: str) -> str | None:
        """Why ``address`` may not be paid now, or None if it may."""
        if address in asset.whitelist:
            return None
        effective = self._registered(asset_name, address)
        if effective is None:
            return f"destination {address} is not whitelisted"
        if self._clock() < effective:
            return f"destination {address} is registered but payable only from {effective}"
        return None

    def register(
        self, registration: AddressRegistration, approvals: Sequence[Approval]
    ) -> datetime:
        """Approve adding an address to the whitelist; return when it becomes payable.

        A registration needs the quorum of the highest tier, from approvers other than its
        initiator, like the largest payment, and takes effect only after the registration delay,
        so that a registration made by an attacker can be noticed before anything is paid to it.
        Raises ``PolicyDenied`` with a PENDING or DENIED decision otherwise.
        """
        asset = self.policy.assets.get(registration.asset)
        quorum = max((t.quorum for t in asset.tiers), default=0) if asset else 0
        digest = registration.digest()
        counted = sorted(
            {
                a.approver
                for a in approvals
                if a.instruction_digest == digest
                and a.approver != registration.initiator
                and a.approver in self.policy.approvers
                and a.is_valid(self.policy.approvers[a.approver])
            }
        )
        if asset is None:
            decision = Decision(Status.DENIED, f"no policy for asset {registration.asset!r}")
        elif self._not_payable(registration.asset, asset, registration.address) is None or (
            self._registered(registration.asset, registration.address) is not None
        ):
            decision = Decision(Status.DENIED, f"{registration.address} is already registered")
        elif len(counted) < quorum:
            decision = Decision(
                Status.PENDING, f"{len(counted)} of {quorum} required approvals", tuple(counted)
            )
        else:
            decision = Decision(
                Status.APPROVED, f"{len(counted)} of {quorum} required approvals", tuple(counted)
            )
        self.audit.append(
            "registration_evaluated",
            {
                "registration_id": registration.registration_id,
                "status": decision.status.value,
                "reason": decision.reason,
                "approvers": list(decision.approvers),
            },
        )
        if decision.status is not Status.APPROVED:
            raise PolicyDenied(decision)
        effective = self._clock() + self._delay
        self.audit.append(
            "registered",
            {
                "registration_id": registration.registration_id,
                "asset": registration.asset,
                "client": registration.client,
                "address": registration.address,
                "effective_at": effective,
            },
        )
        return effective

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
        refusal = self._not_payable(ins.asset, asset, ins.destination)
        if refusal:
            return Decision(Status.DENIED, refusal)
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
