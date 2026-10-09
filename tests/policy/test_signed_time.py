"""Signed time: the time authority's signature over the time and the asker's own nonce."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from custody_lab.policy import authorisation, signed_time

KEY = Ed25519PrivateKey.generate()
PUBLIC = KEY.public_key().public_bytes_raw()
NOW = datetime(2026, 10, 9, 12, 0, tzinfo=UTC)


def test_a_signed_time_for_this_nonce_reads_back() -> None:
    nonce = signed_time.new_nonce()
    signed = signed_time.stamp(KEY, nonce, NOW)
    again = signed_time.SignedTime.from_bytes(signed.to_bytes())
    assert len(nonce) == 32 and signed_time.read(again, PUBLIC, nonce) == NOW


def test_another_key_or_an_altered_time_is_refused() -> None:
    nonce = signed_time.new_nonce()
    forged = signed_time.stamp(Ed25519PrivateKey.generate(), nonce, NOW)
    with pytest.raises(signed_time.TimeRejected, match="not signed by the time authority"):
        signed_time.read(forged, PUBLIC, nonce)
    earlier = replace(signed_time.stamp(KEY, nonce, NOW), time=NOW - timedelta(minutes=5))
    with pytest.raises(signed_time.TimeRejected, match="not signed by the time authority"):
        signed_time.read(earlier, PUBLIC, nonce)


def test_a_recorded_time_is_refused_and_would_otherwise_revive_an_expired_authorisation() -> None:
    """A signed time recorded while an authorisation was valid, presented after it expired."""
    authority = authorisation.AuthorityKey.generate()
    message = b"\x6a" * 32
    token = authorisation.issue(authority, b"\x00" * 32, message, NOW + timedelta(seconds=60))
    recorded = signed_time.stamp(KEY, signed_time.new_nonce(), NOW + timedelta(seconds=10))
    later = signed_time.new_nonce()  # the signer's nonce, five minutes on

    with pytest.raises(signed_time.TimeRejected, match="answers another request"):
        signed_time.read(recorded, PUBLIC, later)
    # Done wrong, checking the signature alone: the recorded time passes the expiry check.
    unbound = signed_time.read(recorded, PUBLIC, recorded.nonce)
    authorisation.check(token, authority.public_bytes(), message, unbound)
    with pytest.raises(authorisation.AuthorisationRejected, match="expired"):
        authorisation.check(token, authority.public_bytes(), message, NOW + timedelta(minutes=5))
