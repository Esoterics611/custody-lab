import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from custody_lab.mpc import paillier

KEY = paillier.generate_keypair(bits=512)  # small for speed; Lindell 2017 tests use 2048
PK = KEY.public
plaintexts = st.integers(min_value=0, max_value=PK.n - 1)


@pytest.mark.parametrize("n", [2, 3, 97, 2**127 - 1])
def test_primes(n: int) -> None:
    assert paillier.is_probable_prime(n)


@pytest.mark.parametrize("n", [1, 561, 1105, 2**128 + 1])  # 561, 1105: Carmichael numbers
def test_composites(n: int) -> None:
    assert not paillier.is_probable_prime(n)


@settings(max_examples=25)
@given(plaintexts, plaintexts)
def test_decrypt_and_homomorphic_add(a: int, b: int) -> None:
    ca, cb = PK.encrypt(a), PK.encrypt(b)
    assert KEY.decrypt(ca) == a
    assert KEY.decrypt(PK.add(ca, cb)) == (a + b) % PK.n


@settings(max_examples=25)
@given(plaintexts, st.integers(min_value=0, max_value=2**256))
def test_homomorphic_scalar_multiplication(a: int, k: int) -> None:
    assert KEY.decrypt(PK.mul(PK.encrypt(a), k)) == a * k % PK.n


def test_encryption_is_randomised() -> None:
    assert PK.encrypt(42) != PK.encrypt(42)
