"""Private channels between signers: messages the coordinator relays but cannot read.

Key generation, refresh and repair send values that only one recipient may see: a DKG sub-share
is a point on the sender's secret line, and anyone holding every sub-share can compute every
share. The coordinator relays these messages, so they travel sealed: encrypted and authenticated
from one signer to another.

Each signer holds an X25519 channel key. To seal a message for a recipient, the sender combines its
own private key with the recipient's public key (Diffie-Hellman), derives a ChaCha20-Poly1305 key
from the result with HKDF-SHA256, bound to both identifiers and to the protocol step, and
encrypts. Only the recipient can compute the same key, and only the sender could have produced a
ciphertext that opens with it, so the channel is private and mutually authenticated, given that
each side holds the other's genuine public key.

That condition is the remaining trust: the demo's channel public keys are collected and handed out
by the process that starts the signers, which is also the coordinator. A coordinator that
substitutes its own keys at start-up could read every message. In production the keys are
provisioned out of band, for example as attested enclave keys or HSM certificates (chapter 3).
The keys are static, so the channel has no forward secrecy: a signer's channel key stolen later
opens the messages recorded earlier.
"""

from __future__ import annotations

import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

NONCE_BYTES = 12


def new_key() -> X25519PrivateKey:
    return X25519PrivateKey.generate()


def public_bytes(key: X25519PrivateKey) -> bytes:
    return key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def _aead(
    own: X25519PrivateKey, peer: bytes, sender: int, recipient: int, step: str
) -> ChaCha20Poly1305:
    shared = own.exchange(X25519PublicKey.from_public_bytes(peer))
    info = f"custody-lab/channel/{step}/{sender}->{recipient}".encode()
    key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(shared)
    return ChaCha20Poly1305(key)


def seal(
    own: X25519PrivateKey, peer: bytes, sender: int, recipient: int, step: str, data: bytes
) -> bytes:
    """Encrypt ``data`` from ``sender`` to ``recipient`` for one protocol ``step``."""
    nonce = os.urandom(NONCE_BYTES)
    return nonce + _aead(own, peer, sender, recipient, step).encrypt(nonce, data, None)


def open_(
    own: X25519PrivateKey, peer: bytes, sender: int, recipient: int, step: str, sealed: bytes
) -> bytes:
    """Decrypt a message sealed by ``sender`` for ``recipient``; raise ``InvalidTag`` if it was
    altered, sealed for someone else, or sealed for another step."""
    nonce, ciphertext = sealed[:NONCE_BYTES], sealed[NONCE_BYTES:]
    return _aead(own, peer, sender, recipient, step).decrypt(nonce, ciphertext, None)
