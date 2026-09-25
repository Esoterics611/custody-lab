from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec as crypto_ec
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed, encode_dss_signature

from custody_lab.foundations.ec import SECP256K1
from custody_lab.foundations.ecdsa import hash_to_int
from custody_lab.foundations.hashing import sha256
from custody_lab.mpc.lindell17 import Party1, Party2

P1, P2 = Party1(), Party2()
Q = P1.keygen_finish(P2.keygen(P1.keygen_message()))


def test_both_parties_derive_the_same_public_key() -> None:
    assert P1.Q == P2.Q == Q


def test_two_party_signatures_verify_with_cryptography() -> None:
    public_key = crypto_ec.EllipticCurvePublicNumbers(Q.x, Q.y, crypto_ec.SECP256K1()).public_key()
    for msg in (b"settle batch 1", b"settle batch 2", b""):
        digest = sha256(msg)
        z = hash_to_int(digest)
        sig = P1.sign_finish(z, P2.sign(z, P1.sign_commit()))
        assert sig.s <= SECP256K1.n // 2
        der = encode_dss_signature(sig.r, sig.s)
        public_key.verify(der, digest, crypto_ec.ECDSA(Prehashed(hashes.SHA256())))
