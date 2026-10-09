from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from custody_lab.policy import authorisation
from custody_lab.policy.authorisation import Authorisation, AuthorisationRejected, AuthorityKey

KEY = AuthorityKey.generate()
AUTHORITY = KEY.public_bytes()
NOW = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
MSG = b"\x02" * 32


def _token(expires_in: timedelta = timedelta(seconds=60)) -> Authorisation:
    return authorisation.issue(KEY, b"\x00" * 32, MSG, NOW + expires_in)


def test_valid_token_round_trips_and_passes() -> None:
    token = Authorisation.from_bytes(_token().to_bytes())
    authorisation.check(token, AUTHORITY, MSG, NOW)
    assert len(AUTHORITY) == 32 + 1952 and len(token.pq_signature) == 3309  # FIPS 204 sizes


def test_token_from_another_authority_is_rejected() -> None:
    other = AuthorityKey.generate().public_bytes()
    with pytest.raises(AuthorisationRejected, match="policy authority"):
        authorisation.check(_token(), other, MSG, NOW)


def test_both_signatures_are_required() -> None:
    """A forger who breaks only one scheme (Ed25519 by a quantum computer, or ML-DSA by a flaw)
    still cannot produce a token."""
    genuine, forged = (
        _token(),
        authorisation.issue(
            AuthorityKey.generate(), b"\x00" * 32, MSG, NOW + timedelta(seconds=60)
        ),
    )
    only_classical = replace(genuine, pq_signature=forged.pq_signature)
    only_post_quantum = replace(genuine, signature=forged.signature)
    with pytest.raises(AuthorisationRejected, match="ML-DSA-65"):
        authorisation.check(only_classical, AUTHORITY, MSG, NOW)
    with pytest.raises(AuthorisationRejected, match="Ed25519"):
        authorisation.check(only_post_quantum, AUTHORITY, MSG, NOW)


def test_expired_token_is_rejected() -> None:
    with pytest.raises(AuthorisationRejected, match="expired"):
        authorisation.check(_token(timedelta(seconds=-1)), AUTHORITY, MSG, NOW)


def test_token_for_another_message_is_rejected() -> None:
    with pytest.raises(AuthorisationRejected, match="differs"):
        authorisation.check(_token(), AUTHORITY, b"\x03" * 32, NOW)
