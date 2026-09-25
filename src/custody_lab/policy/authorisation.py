"""The token a signer requires before producing a signature share.

The policy engine signs four fields:
- a unique id, so each token authorises one signature;
- the instruction digest, so the token traces back to the approvals;
- the exact message bytes the signers will sign;
- an expiry.

The authority key is **hybrid**: every token carries an Ed25519 signature and an ML-DSA-65
(FIPS 204) signature over the same payload, and a signer accepts it only if both verify. A
forger then has to break both schemes. A large quantum computer would break Ed25519, and ML-DSA
is a newer and less-studied design. This is the one signature path the custodian controls end
to end, so it can move to post-quantum signatures before the chain does.

A signer checks both signatures, the expiry, and that the message in the FROST signing package
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
from cryptography.hazmat.primitives.asymmetric.mldsa import MLDSA65PrivateKey, MLDSA65PublicKey

from custody_lab.policy.model import canonical_json

ED25519_KEY_BYTES = 32
MLDSA_CONTEXT = b"custody-lab/authorisation"  # FIPS 204 context string: domain separation


class AuthorisationRejected(Exception):
    pass


@dataclass(frozen=True)
class AuthorityKey:
    """The policy authority's hybrid signing key: Ed25519 and ML-DSA-65."""

    classical: Ed25519PrivateKey
    post_quantum: MLDSA65PrivateKey

    @classmethod
    def generate(cls) -> AuthorityKey:
        return cls(Ed25519PrivateKey.generate(), MLDSA65PrivateKey.generate())

    def public_bytes(self) -> bytes:
        """The 32-byte Ed25519 public key followed by the 1952-byte ML-DSA-65 public key."""
        return (
            self.classical.public_key().public_bytes_raw()
            + self.post_quantum.public_key().public_bytes_raw()
        )


@dataclass(frozen=True)
class Authorisation:
    authorisation_id: str
    instruction_digest: bytes
    message: bytes
    expires_at: datetime
    signature: bytes  # Ed25519
    pq_signature: bytes  # ML-DSA-65

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
                "pq_signature": self.pq_signature.hex(),
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
            bytes.fromhex(d["pq_signature"]),
        )


def issue(
    key: AuthorityKey, instruction_digest: bytes, message: bytes, expires_at: datetime
) -> Authorisation:
    authorisation_id = uuid.uuid4().hex
    payload = Authorisation.payload(authorisation_id, instruction_digest, message, expires_at)
    return Authorisation(
        authorisation_id,
        instruction_digest,
        message,
        expires_at,
        key.classical.sign(payload),
        key.post_quantum.sign(payload, MLDSA_CONTEXT),
    )


def check(auth: Authorisation, authority: bytes, message: bytes, now: datetime) -> None:
    """Raise unless both of ``auth``'s signatures verify under ``authority``
    (``AuthorityKey.public_bytes``), it is unexpired at ``now``, and it authorises exactly
    ``message``."""
    payload = Authorisation.payload(
        auth.authorisation_id, auth.instruction_digest, auth.message, auth.expires_at
    )
    classical = Ed25519PublicKey.from_public_bytes(authority[:ED25519_KEY_BYTES])
    post_quantum = MLDSA65PublicKey.from_public_bytes(authority[ED25519_KEY_BYTES:])
    try:
        classical.verify(auth.signature, payload)
    except InvalidSignature:
        raise AuthorisationRejected("not signed by the policy authority (Ed25519)") from None
    try:
        post_quantum.verify(auth.pq_signature, payload, MLDSA_CONTEXT)
    except InvalidSignature:
        raise AuthorisationRejected("not signed by the policy authority (ML-DSA-65)") from None
    if now >= auth.expires_at:
        raise AuthorisationRejected(f"expired at {auth.expires_at.isoformat()}")
    if message != auth.message:
        raise AuthorisationRejected("signing package message differs from the authorised message")
