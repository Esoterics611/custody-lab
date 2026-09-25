from dataclasses import replace

import pytest

from custody_lab.foundations import shamir
from custody_lab.foundations.ec import SECP256K1
from custody_lab.mpc import dkg


def _secret(shares: dict[int, int], ids: tuple[int, int]) -> int:
    # Test-only reconstruction; the protocol itself never does this.
    return shamir.reconstruct([shamir.Share(i, shares[i]) for i in ids])


def test_any_two_shares_open_the_group_key() -> None:
    shares, group_key = dkg.run(threshold=2, count=3)
    for ids in [(1, 2), (1, 3), (2, 3)]:
        assert SECP256K1.mul(_secret(shares, ids), SECP256K1.G) == group_key


def test_bad_proof_of_knowledge_is_rejected() -> None:
    pkg = dkg.Dealer(1, threshold=2).round1()
    assert pkg.proof is not None
    R, mu = pkg.proof
    with pytest.raises(ValueError, match="proof of knowledge"):
        dkg.check_round1(replace(pkg, proof=(R, mu + 1)))


def test_bad_sub_share_is_rejected() -> None:
    dealers = {i: dkg.Dealer(i, threshold=2) for i in (1, 2, 3)}
    packages = {i: d.round1() for i, d in dealers.items()}
    received = {i: d.share_for(3) for i, d in dealers.items()}
    received[2] += 1
    with pytest.raises(ValueError, match="participant 2"):
        dkg.combine(3, packages, received)


def test_refresh_changes_shares_but_not_the_key() -> None:
    old, group_key = dkg.run(threshold=2, count=3)
    new = dkg.refresh(old, threshold=2)
    assert all(new[i] != old[i] for i in old)
    assert _secret(new, (1, 3)) == _secret(old, (2, 3))
    assert SECP256K1.mul(_secret(new, (1, 2)), SECP256K1.G) == group_key


def test_refresh_rejects_a_non_zero_sharing() -> None:
    with pytest.raises(ValueError, match="share zero"):
        dkg.check_round1(dkg.Dealer(1, threshold=2).round1(), refresh=True)
