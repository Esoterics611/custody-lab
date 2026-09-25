from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from custody_lab.policy import authorisation
from custody_lab.policy.authorisation import Authorisation, AuthorisationRejected

KEY = Ed25519PrivateKey.generate()
AUTHORITY = KEY.public_key().public_bytes_raw()
NOW = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
MSG = b"\x02" * 32


def _token(expires_in: timedelta = timedelta(seconds=60)) -> Authorisation:
    return authorisation.issue(KEY, b"\x00" * 32, MSG, NOW + expires_in)


def test_valid_token_round_trips_and_passes() -> None:
    token = Authorisation.from_bytes(_token().to_bytes())
    authorisation.check(token, AUTHORITY, MSG, NOW)


def test_token_from_another_authority_is_rejected() -> None:
    other = Ed25519PrivateKey.generate().public_key().public_bytes_raw()
    with pytest.raises(AuthorisationRejected, match="policy authority"):
        authorisation.check(_token(), other, MSG, NOW)


def test_expired_token_is_rejected() -> None:
    with pytest.raises(AuthorisationRejected, match="expired"):
        authorisation.check(_token(timedelta(seconds=-1)), AUTHORITY, MSG, NOW)


def test_token_for_another_message_is_rejected() -> None:
    with pytest.raises(AuthorisationRejected, match="differs"):
        authorisation.check(_token(), AUTHORITY, b"\x03" * 32, NOW)
