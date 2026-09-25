import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec as crypto_ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    Prehashed,
    decode_dss_signature,
    encode_dss_signature,
)
from hypothesis import given, settings
from hypothesis import strategies as st

from custody_lab.foundations import ecdsa
from custody_lab.foundations.ec import SECP256K1, TOY, Point
from custody_lab.foundations.hashing import sha256

PREHASHED_SHA256 = crypto_ec.ECDSA(Prehashed(hashes.SHA256()))
keys = st.integers(min_value=1, max_value=SECP256K1.n - 1)


def _crypto_public_key(Q: Point) -> crypto_ec.EllipticCurvePublicKey:
    return crypto_ec.EllipticCurvePublicNumbers(Q.x, Q.y, crypto_ec.SECP256K1()).public_key()


@settings(max_examples=20, deadline=None)
@given(keys, st.binary())
def test_cryptography_accepts_our_signature(d: int, msg: bytes) -> None:
    Q = SECP256K1.mul(d, SECP256K1.G)
    assert Q is not None
    digest = sha256(msg)
    sig = ecdsa.sign(d, ecdsa.hash_to_int(digest))
    der = encode_dss_signature(sig.r, sig.s)
    _crypto_public_key(Q).verify(der, digest, PREHASHED_SHA256)  # raises if invalid


@settings(max_examples=20, deadline=None)
@given(keys, st.binary())
def test_we_accept_cryptography_signature(d: int, msg: bytes) -> None:
    private_key = crypto_ec.derive_private_key(d, crypto_ec.SECP256K1())
    numbers = private_key.public_key().public_numbers()
    digest = sha256(msg)
    r, s = decode_dss_signature(private_key.sign(digest, PREHASHED_SHA256))
    Q = Point(numbers.x, numbers.y)
    assert ecdsa.verify(Q, ecdsa.hash_to_int(digest), ecdsa.Signature(r, s))


@settings(max_examples=10, deadline=None)
@given(keys)
def test_signature_is_low_s_and_bound_to_message(d: int) -> None:
    Q = SECP256K1.mul(d, SECP256K1.G)
    assert Q is not None
    z = ecdsa.hash_to_int(sha256(b"pay 1.5 BTC to bc1q..."))
    sig = ecdsa.sign(d, z)
    assert sig.s <= SECP256K1.n // 2
    assert ecdsa.verify(Q, z, sig)
    assert not ecdsa.verify(Q, z + 1, sig)


def test_tampered_signature_rejected_by_cryptography() -> None:
    d, Q = ecdsa.generate_keypair()
    digest = sha256(b"settlement batch 42")
    sig = ecdsa.sign(d, ecdsa.hash_to_int(digest))
    der = encode_dss_signature(sig.r, (sig.s + 1) % SECP256K1.n)
    with pytest.raises(InvalidSignature):
        _crypto_public_key(Q).verify(der, digest, PREHASHED_SHA256)


def test_toy_curve_every_key_and_nonce() -> None:
    z = 17
    for d in range(1, TOY.n):
        Q = TOY.mul(d, TOY.G)
        assert Q is not None
        for k in range(1, TOY.n):
            try:
                sig = ecdsa.sign(d, z, curve=TOY, k=k)
            except ValueError:
                continue  # this nonce gives r = 0 or s = 0
            assert ecdsa.verify(Q, z, sig, curve=TOY)
