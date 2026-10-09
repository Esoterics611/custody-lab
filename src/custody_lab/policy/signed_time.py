"""Signed time: a time authority's statement of the time, bound to the asker's own nonce.

EDUCATIONAL, NOT PRODUCTION. A signer checks an authorisation's expiry against the time. Read from
the signer machine's own clock, that time is whatever the clock says, and whoever can set the clock
(an administrator of the machine, or an attacker who answers its time requests) decides whether an
expired authorisation still counts (manual/attack-vectors.md, vector 4.4).

A signer that takes its time from a time authority does this for every signature:

1. It draws a fresh 32-byte random nonce and sends it out.
2. The time authority signs the nonce together with its current time, with Ed25519.
3. The signer checks the signature under the time authority's public key, which it was given when
   it started, and that the nonce is the one it drew; then it uses the signed time.

The nonce is what stops a replay. A signed time recorded before an authorisation expired answers
another nonce, so the signer refuses it, and every time a signer accepts was signed after it drew
its nonce. The time is then as right as the time authority's own clock, which an attacker of the
custodian's machines does not reach.

This is the core of Roughtime (RFC 10049, Experimental, October 2026; **verify current**).
Roughtime adds what this module leaves out: a radius stating the server's uncertainty, a Merkle
tree so one signature answers many requests, an online key certified by an offline long-term key,
and requests chained across several servers, so that a server that lies about the time can be
proven to have done so.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from datetime import datetime

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from custody_lab.policy.model import canonical_json

NONCE_BYTES = 32


class TimeRejected(Exception):
    pass


@dataclass(frozen=True)
class SignedTime:
    nonce: bytes
    time: datetime
    signature: bytes  # Ed25519, by the time authority

    @staticmethod
    def payload(nonce: bytes, time: datetime) -> bytes:
        return canonical_json({"nonce": nonce.hex(), "time": time})

    def to_bytes(self) -> bytes:
        return canonical_json(
            {"nonce": self.nonce.hex(), "time": self.time, "signature": self.signature.hex()}
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> SignedTime:
        d = json.loads(data)
        return cls(
            bytes.fromhex(d["nonce"]),
            datetime.fromisoformat(d["time"]),
            bytes.fromhex(d["signature"]),
        )


def new_nonce() -> bytes:
    return secrets.token_bytes(NONCE_BYTES)


def stamp(key: Ed25519PrivateKey, nonce: bytes, now: datetime) -> SignedTime:
    """The time authority's answer to ``nonce``: ``now``, signed together with it."""
    return SignedTime(nonce, now, key.sign(SignedTime.payload(nonce, now)))


def read(signed: SignedTime, time_authority: bytes, nonce: bytes) -> datetime:
    """The signed time, once its signature verifies under ``time_authority`` (raw Ed25519) and it
    answers ``nonce``; raise ``TimeRejected`` otherwise."""
    key = Ed25519PublicKey.from_public_bytes(time_authority)
    try:
        key.verify(signed.signature, SignedTime.payload(signed.nonce, signed.time))
    except InvalidSignature:
        raise TimeRejected("the signed time is not signed by the time authority") from None
    if signed.nonce != nonce:
        raise TimeRejected("the signed time answers another request: its nonce is not this one")
    return signed.time
