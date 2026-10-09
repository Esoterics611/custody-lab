"""Settlement instructions, approvals, and the canonical encoding everything is signed over."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from custody_lab.foundations.hashing import sha256


def _encode(value: object) -> str:
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")  # 1.50 and 1.5 encode identically
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"cannot canonically encode {type(value).__name__}")


def canonical_json(obj: Any) -> bytes:
    """Sorted keys, no whitespace, Decimals and datetimes as strings. Everything that is hashed
    or signed goes through this, so equal content always produces equal bytes."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=_encode).encode()


@dataclass(frozen=True)
class SettlementInstruction:
    """A request to move ``amount`` of ``asset`` to ``destination``, raised by ``initiator``."""

    instruction_id: str
    asset: str
    amount: Decimal
    destination: str
    initiator: str
    created_at: datetime

    def digest(self) -> bytes:
        return sha256(canonical_json(asdict(self)))


@dataclass(frozen=True)
class AddressRegistration:
    """A request to add ``address`` to ``client``'s withdrawal addresses for ``asset``, raised by
    ``initiator``. Approved like a payment, it takes effect only after the policy's delay."""

    registration_id: str
    asset: str
    client: str
    address: str
    initiator: str
    created_at: datetime

    def digest(self) -> bytes:
        # Hashed under a key no instruction has, so an approval of one never counts for the other.
        return sha256(canonical_json({"register_address": asdict(self)}))


@dataclass(frozen=True)
class Approval:
    """An approver's Ed25519 signature over one instruction's digest."""

    instruction_digest: bytes
    approver: str
    signature: bytes

    @staticmethod
    def payload(instruction_digest: bytes, approver: str) -> bytes:
        return canonical_json({"approve": instruction_digest.hex(), "approver": approver})

    @classmethod
    def create(
        cls,
        instruction: SettlementInstruction | AddressRegistration,
        approver: str,
        key: Ed25519PrivateKey,
    ) -> Approval:
        digest = instruction.digest()
        return cls(digest, approver, key.sign(cls.payload(digest, approver)))

    def is_valid(self, public_key: Ed25519PublicKey) -> bool:
        try:
            public_key.verify(self.signature, self.payload(self.instruction_digest, self.approver))
        except InvalidSignature:
            return False
        return True
