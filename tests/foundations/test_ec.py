from cryptography.hazmat.primitives.asymmetric import ec as crypto_ec
from hypothesis import given, settings
from hypothesis import strategies as st

from custody_lab.foundations.ec import SECP256K1, TOY, Point

TOY_POINTS: list[Point | None] = [*TOY.points(), None]


def test_generators_are_on_their_curves() -> None:
    assert SECP256K1.is_on_curve(SECP256K1.G)
    assert TOY.is_on_curve(TOY.G)


def test_n_times_generator_is_infinity() -> None:
    assert SECP256K1.mul(SECP256K1.n, SECP256K1.G) is None
    assert TOY.mul(TOY.n, TOY.G) is None


def test_toy_curve_group_has_n_elements() -> None:
    assert len(TOY_POINTS) == TOY.n


@given(st.sampled_from(TOY_POINTS), st.sampled_from(TOY_POINTS), st.sampled_from(TOY_POINTS))
def test_toy_group_law(P: Point | None, Q: Point | None, R: Point | None) -> None:
    assert TOY.add(P, Q) == TOY.add(Q, P)
    assert TOY.add(TOY.add(P, Q), R) == TOY.add(P, TOY.add(Q, R))
    assert TOY.add(P, TOY.neg(P)) is None
    assert TOY.is_on_curve(TOY.add(P, Q))


@settings(max_examples=25, deadline=None)
@given(st.integers(min_value=1, max_value=SECP256K1.n - 1))
def test_public_key_matches_cryptography(d: int) -> None:
    expected = crypto_ec.derive_private_key(d, crypto_ec.SECP256K1()).public_key().public_numbers()
    assert SECP256K1.mul(d, SECP256K1.G) == Point(expected.x, expected.y)
