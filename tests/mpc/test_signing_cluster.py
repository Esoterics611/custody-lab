import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from itertools import combinations

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from custody_lab.foundations import schnorr
from custody_lab.mpc.cluster import SigningCluster
from custody_lab.policy import authorisation

AUTHORITY_KEY = Ed25519PrivateKey.generate()
MSG = bytes.fromhex("6a" * 32)  # stands in for a 32-byte BIP341 sighash


def token(message: bytes = MSG, ttl: timedelta = timedelta(seconds=60)) -> bytes:
    expires = datetime.now(UTC) + ttl
    return authorisation.issue(AUTHORITY_KEY, b"\x00" * 32, message, expires).to_bytes()


@pytest.fixture(scope="module")
def cluster() -> Iterator[tuple[SigningCluster, bytes]]:
    with SigningCluster(2, 3, AUTHORITY_KEY.public_key().public_bytes_raw()) as c:
        yield c, c.dkg()


def test_two_of_three_in_separate_processes(cluster: tuple[SigningCluster, bytes]) -> None:
    c, group_key = cluster
    pids = c.holders()
    assert len(set(pids.values())) == 3 and os.getpid() not in pids.values()
    for pair in combinations((1, 2, 3), 2):
        signature = c.sign(MSG, pair, token())
        assert len(signature) == 64
        assert schnorr.verify(MSG, group_key, signature)  # independent BIP340 verifier


def test_one_signer_cannot_sign(cluster: tuple[SigningCluster, bytes]) -> None:
    with pytest.raises((RuntimeError, ValueError)):
        cluster[0].sign(MSG, [1], token())


def test_signers_refuse_a_token_for_a_different_message(
    cluster: tuple[SigningCluster, bytes],
) -> None:
    with pytest.raises(RuntimeError, match="differs from the authorised message"):
        cluster[0].sign(b"\x66" * 32, [1, 2], token(MSG))


def test_signers_refuse_forged_expired_and_replayed_tokens(
    cluster: tuple[SigningCluster, bytes],
) -> None:
    c, _ = cluster
    forged = authorisation.issue(
        Ed25519PrivateKey.generate(), b"\x00" * 32, MSG, datetime.now(UTC) + timedelta(minutes=1)
    ).to_bytes()
    with pytest.raises(RuntimeError, match="policy authority"):
        c.sign(MSG, [1, 2], forged)
    with pytest.raises(RuntimeError, match="expired"):
        c.sign(MSG, [1, 2], token(ttl=timedelta(seconds=-1)))
    once = token()
    c.sign(MSG, [2, 3], once)
    with pytest.raises(RuntimeError, match="already used"):
        c.sign(MSG, [2, 3], once)
