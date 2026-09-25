import pytest
from hypothesis import given
from hypothesis import strategies as st

from custody_lab.foundations import shamir
from custody_lab.foundations.ec import SECP256K1, TOY


@st.composite
def sharings(draw: st.DrawFn) -> tuple[int, int, list[shamir.Share]]:
    count = draw(st.integers(min_value=1, max_value=7))
    threshold = draw(st.integers(min_value=1, max_value=count))
    secret = draw(st.integers(min_value=0, max_value=SECP256K1.n - 1))
    return secret, threshold, shamir.split(secret, threshold, count)


@given(sharings(), st.data())
def test_any_threshold_subset_reconstructs(
    sharing: tuple[int, int, list[shamir.Share]], data: st.DataObject
) -> None:
    secret, threshold, shares = sharing
    size = data.draw(st.integers(min_value=threshold, max_value=len(shares)))
    subset = data.draw(st.permutations(shares))[:size]
    assert shamir.reconstruct(subset) == secret


@given(st.lists(st.integers(min_value=1, max_value=50), min_size=1, max_size=8, unique=True))
def test_lagrange_coefficients_sum_to_one(xs: list[int]) -> None:
    # Interpolating the constant polynomial 1 at x = 0 must give 1.
    q = SECP256K1.n
    assert sum(shamir.lagrange_coefficient(i, xs, q) for i in xs) % q == 1


def test_one_share_of_two_of_three_is_consistent_with_every_secret() -> None:
    share = shamir.split(secret=9, threshold=2, count=3, modulus=TOY.n)[0]
    candidates = {
        c0
        for c0 in range(TOY.n)
        for c1 in range(TOY.n)
        if shamir.evaluate([c0, c1], share.x, TOY.n) == share.y
    }
    assert candidates == set(range(TOY.n))


def test_rejects_threshold_above_count() -> None:
    with pytest.raises(ValueError):
        shamir.split(secret=1, threshold=4, count=3)


def test_rejects_duplicate_shares() -> None:
    shares = shamir.split(secret=5, threshold=2, count=3)
    with pytest.raises(ValueError):
        shamir.reconstruct([shares[0], shares[0]])
