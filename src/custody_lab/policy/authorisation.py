"""The token a signer requires before producing a signature share.

The policy engine signs (Ed25519) four fields:
- a unique id, so each token authorises one signature;
- the instruction digest, so the token traces back to the approvals;
- the exact message bytes the signers will sign;
- an expiry.

A signer checks the signature, the expiry, and that the message in the FROST signing package
equals the authorised message. That last check is what stops a coordinator pairing a valid token
with a different transaction.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from custody_lab.policy.model import canonical_json


class AuthorisationRejected(Exception):
    pass


@dataclass(frozen=True)
class Authorisation:
    authorisation_id: str
    instruction_digest: bytes
    message: bytes
    expires_at: datetime
    signature: bytes

    @staticmethod
    def payload(
        authorisation_id: str, instruction_digest: bytes, message: bytes, expires_at: datetime
    ) -> bytes:
        return canonical_json(
            {
                "authorisation_id": authorisation_id,
                "instruction_digest": instruction_digest.hex(),
                "message": message.hex(),
                "expires_at": expires_at,
            }
        )

    def to_bytes(self) -> bytes:
        return canonical_json(
            {
                "authorisation_id": self.authorisation_id,
                "instruction_digest": self.instruction_digest.hex(),
                "message": self.message.hex(),
                "expires_at": self.expires_at,
                "signature": self.signature.hex(),
            }
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> Authorisation:
        d = json.loads(data)
        return cls(
            d["authorisation_id"],
            bytes.fromhex(d["instruction_digest"]),
            bytes.fromhex(d["message"]),
            datetime.fromisoformat(d["expires_at"]),
            bytes.fromhex(d["signature"]),
        )


def issue(
    key: Ed25519PrivateKey, instruction_digest: bytes, message: bytes, expires_at: datetime
) -> Authorisation:
    authorisation_id = uuid.uuid4().hex
    payload = Authorisation.payload(authorisation_id, instruction_digest, message, expires_at)
    signature = key.sign(payload)
    return Authorisation(authorisation_id, instruction_digest, message, expires_at, signature)


def check(auth: Authorisation, authority: bytes, message: bytes, now: datetime) -> None:
    """Raise unless ``auth`` is signed by ``authority`` (raw Ed25519 public key), unexpired at
    ``now``, and authorises exactly ``message``."""
    payload = Authorisation.payload(
        auth.authorisation_id, auth.instruction_digest, auth.message, auth.expires_at
    )
    try:
        Ed25519PublicKey.from_public_bytes(authority).verify(auth.signature, payload)
    except InvalidSignature:
        raise AuthorisationRejected("not signed by the policy authority") from None
    if now >= auth.expires_at:
        raise AuthorisationRejected(f"expired at {auth.expires_at.isoformat()}")
    if message != auth.message:
        raise AuthorisationRejected("signing package message differs from the authorised message")
