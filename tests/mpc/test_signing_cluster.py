import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from itertools import combinations
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from custody_lab.foundations import schnorr
from custody_lab.mpc.cluster import Calls, SigningCluster
from custody_lab.policy import authorisation, signed_time

AUTHORITY_KEY = authorisation.AuthorityKey.generate()
MSG = bytes.fromhex("6a" * 32)  # stands in for a 32-byte BIP341 sighash


def token(message: bytes = MSG, ttl: timedelta = timedelta(seconds=60)) -> bytes:
    expires = datetime.now(UTC) + ttl
    return authorisation.issue(AUTHORITY_KEY, b"\x00" * 32, message, expires).to_bytes()


@pytest.fixture(scope="module")
def cluster() -> Iterator[tuple[SigningCluster, bytes]]:
    with SigningCluster(2, 3, AUTHORITY_KEY.public_bytes()) as c:
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
        authorisation.AuthorityKey.generate(),
        b"\x00" * 32,
        MSG,
        datetime.now(UTC) + timedelta(minutes=1),
    ).to_bytes()
    with pytest.raises(RuntimeError, match="policy authority"):
        c.sign(MSG, [1, 2], forged)
    with pytest.raises(RuntimeError, match="expired"):
        c.sign(MSG, [1, 2], token(ttl=timedelta(seconds=-1)))
    once = token()
    c.sign(MSG, [2, 3], once)
    with pytest.raises(RuntimeError, match="already used"):
        c.sign(MSG, [2, 3], once)


def test_two_signers_still_sign_after_the_third_process_stops() -> None:
    with SigningCluster(2, 3, AUTHORITY_KEY.public_bytes()) as c:
        group_key = c.dkg()
        stopped = c.holders()[1]
        c.stop(1)

        signature = c.sign(MSG, [2, 3], token())

        assert schnorr.verify(MSG, group_key, signature)
        assert stopped is not None
        with pytest.raises(ProcessLookupError):
            os.kill(stopped, 0)  # the share's process is gone, not idle
        with pytest.raises(KeyError):
            c.sign(MSG, [1, 2], token())


def test_a_refresh_changes_every_share_and_keeps_the_key() -> None:
    with SigningCluster(2, 3, AUTHORITY_KEY.public_bytes()) as c:
        group_key = c.dkg()
        output_key, before = c.taproot_output_key(), c.public_key_package
        old_1 = c.export_share(1)

        assert c.refresh() == group_key
        assert c.taproot_output_key() == output_key and c.public_key_package != before
        assert c.export_share(1) != old_1
        for pair in combinations((1, 2, 3), 2):  # the new shares sign under the same key
            assert schnorr.verify(MSG, group_key, c.sign(MSG, pair, token()))


def test_shares_from_before_and_after_a_refresh_do_not_combine() -> None:
    from custody_lab.demo.ceremonies import thief_sign

    with SigningCluster(2, 3, AUTHORITY_KEY.public_bytes()) as c:
        c.dkg()
        output_key = c.taproot_output_key()  # thief_sign makes Taproot signatures
        old_public, old_1, old_3 = c.public_key_package, c.export_share(1), c.export_share(3)
        # two shares of one period are the key: the refresh does not change that
        assert schnorr.verify(MSG, output_key, thief_sign(MSG, {1: old_1, 3: old_3}, old_public))
        c.refresh()
        new_3 = c.export_share(3)
        for public in (old_public, c.public_key_package):
            with pytest.raises(ValueError, match="InvalidSignatureShare"):
                thief_sign(MSG, {1: old_1, 3: new_3}, public)


def test_a_refresh_needs_every_signer() -> None:
    with SigningCluster(2, 3, AUTHORITY_KEY.public_bytes()) as c:
        c.dkg()
        c.stop(2)
        with pytest.raises(RuntimeError, match="needs all 3 signers"):
            c.refresh()


def test_a_lost_share_is_repaired_by_two_helpers() -> None:
    with SigningCluster(2, 3, AUTHORITY_KEY.public_bytes()) as c:
        group_key = c.dkg()
        public = c.public_key_package
        c.wipe(2)
        with pytest.raises(RuntimeError, match="no key share"):
            c.sign(MSG, [2, 3], token())

        c.repair(2, [1, 3])

        assert c.public_key_package == public
        for pair in ((1, 2), (2, 3)):
            assert schnorr.verify(MSG, group_key, c.sign(MSG, pair, token()))


class _TimeAuthority:
    """A time authority in this process, answering every nonce with the true time."""

    def __init__(self) -> None:
        self._key = Ed25519PrivateKey.generate()
        self.public_key = self._key.public_key().public_bytes_raw()
        self.replay: bytes | None = None  # a recorded answer to pass on instead

    def stamp(self, nonce: bytes) -> bytes:
        if self.replay is not None:
            return self.replay
        return signed_time.stamp(self._key, nonce, datetime.now(UTC)).to_bytes()


def test_signers_whose_clocks_are_set_back_accept_an_expired_token(
    cluster: tuple[SigningCluster, bytes],
) -> None:
    c, group_key = cluster
    expired = token(ttl=timedelta(minutes=-4))
    c.set_clock(1, -timedelta(minutes=5))
    try:
        with pytest.raises(RuntimeError, match="signer 3: AuthorisationRejected..expired"):
            c.sign(MSG, [1, 3], expired)  # one clock set back: signer 3 still refuses
        c.set_clock(3, -timedelta(minutes=5))
        assert schnorr.verify(MSG, group_key, c.sign(MSG, [1, 3], token(ttl=timedelta(minutes=-4))))
    finally:
        for i in (1, 3):
            c.set_clock(i, timedelta(0))


def test_signers_on_signed_time_ignore_their_clocks_and_refuse_a_replayed_time() -> None:
    time_authority = _TimeAuthority()
    with SigningCluster(2, 3, AUTHORITY_KEY.public_bytes(), time_authority) as c:
        group_key = c.dkg()
        assert schnorr.verify(MSG, group_key, c.sign(MSG, [1, 3], token()))
        for i in (1, 3):
            c.set_clock(i, -timedelta(minutes=5))
        with pytest.raises(RuntimeError, match="signer 1: AuthorisationRejected..expired"):
            c.sign(MSG, [1, 3], token(ttl=timedelta(minutes=-4)))

        time_authority.replay = time_authority.stamp(signed_time.new_nonce())
        with pytest.raises(RuntimeError, match="answers another request"):
            c.sign(MSG, [1, 3], token())
        time_authority.replay = None
        assert schnorr.verify(MSG, group_key, c.sign(MSG, [1, 3], token()))


def _payloads(value: object) -> Iterator[bytes]:
    """Every byte string inside a round's requests or replies."""
    if isinstance(value, bytes):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _payloads(item)
    elif isinstance(value, list | tuple):
        for item in value:
            yield from _payloads(item)


def _verifying_share(share: bytes) -> bytes:
    """share x G, compressed, computed by OpenSSL rather than by the FROST crate."""
    key = ec.derive_private_key(int.from_bytes(share, "big"), ec.SECP256K1())
    return key.public_key().public_bytes(Encoding.X962, PublicFormat.CompressedPoint)


def test_no_share_of_any_period_passes_through_the_coordinator() -> None:
    """Every byte the coordinator relays through key generation, signing, refresh and repair,
    searched for every signer's 32-byte signing share of each period."""
    relayed: list[bytes] = []
    recording = True

    def watch(calls: Calls, replies: dict[int, Any] | None) -> None:
        if recording and replies is not None:
            relayed.extend(_payloads(calls))
            relayed.extend(_payloads(replies))

    shares: set[bytes] = set()

    def copy_shares(c: SigningCluster) -> None:
        """EDUCATIONAL: take each signer's share out of its process, unrecorded, to search for."""
        nonlocal recording
        recording = False
        for i in (1, 2, 3):
            package = c.export_share(i)  # header 5, identifier 32, signing share 32, ...
            share = package[37:69]
            assert _verifying_share(share) in c.public_key_package  # the layout is right
            shares.add(share)
        recording = True

    with SigningCluster(2, 3, AUTHORITY_KEY.public_bytes(), watch=watch) as c:
        c.dkg()
        copy_shares(c)
        c.sign(MSG, [1, 3], token())
        c.refresh()
        copy_shares(c)
        c.wipe(2)
        c.repair(2, [1, 3])
        copy_shares(c)
        c.sign(MSG, [2, 3], token())

    assert len(shares) == 6  # three per period; the repaired share is signer 2's period-2 share
    assert sum(map(len, relayed)) > 30_000
    assert not [s for s in shares for blob in relayed if s in blob]
