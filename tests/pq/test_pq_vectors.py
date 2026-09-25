"""Post-quantum libraries against NIST ACVP vectors (tests/pq/vectors/acvp-subset.json).

- ML-DSA (FIPS 204) and ML-KEM (FIPS 203) through ``cryptography`` (OpenSSL): key generation from
  seeds, and ML-DSA signature verification including rejected cases.
- SLH-DSA (FIPS 205) through ``custody_pq`` (RustCrypto ``slh-dsa``): key generation for all twelve
  parameter sets, verification, and deterministic signing.

The subset's source commit and the SHA-256 of each source file are recorded in the vector file.
"""

import json
from pathlib import Path
from typing import Any

import custody_pq
import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import mldsa, mlkem

VECTORS: dict[str, Any] = json.loads(
    (Path(__file__).parent / "vectors" / "acvp-subset.json").read_text()
)
ML_DSA: dict[str, Any] = {
    "ML-DSA-44": (mldsa.MLDSA44PrivateKey, mldsa.MLDSA44PublicKey),
    "ML-DSA-65": (mldsa.MLDSA65PrivateKey, mldsa.MLDSA65PublicKey),
    "ML-DSA-87": (mldsa.MLDSA87PrivateKey, mldsa.MLDSA87PublicKey),
}
ML_KEM: dict[str, Any] = {
    "ML-KEM-768": mlkem.MLKEM768PrivateKey,
    "ML-KEM-1024": mlkem.MLKEM1024PrivateKey,
}


def _h(test: dict[str, Any], field: str) -> bytes:
    return bytes.fromhex(test.get(field, ""))


def _id(test: dict[str, Any]) -> str:
    return f"{test['parameterSet']}-{test['tcId']}"


@pytest.mark.parametrize("t", VECTORS["ml_dsa_keygen"], ids=_id)
def test_ml_dsa_key_from_seed(t: dict[str, Any]) -> None:
    private, _ = ML_DSA[t["parameterSet"]]
    assert private.from_seed_bytes(_h(t, "seed")).public_key().public_bytes_raw() == _h(t, "pk")


@pytest.mark.parametrize("t", VECTORS["ml_dsa_sigver"], ids=_id)
def test_ml_dsa_verification(t: dict[str, Any]) -> None:
    _, public = ML_DSA[t["parameterSet"]]
    key = public.from_public_bytes(_h(t, "pk"))
    try:
        key.verify(_h(t, "signature"), _h(t, "message"), _h(t, "context"))
        verified = True
    except InvalidSignature:
        verified = False
    assert verified is t["testPassed"], t.get("reason")


@pytest.mark.parametrize("t", VECTORS["ml_kem_keygen"], ids=_id)
def test_ml_kem_key_from_seed(t: dict[str, Any]) -> None:
    key = ML_KEM[t["parameterSet"]].from_seed_bytes(_h(t, "d") + _h(t, "z"))
    assert key.public_key().public_bytes_raw() == _h(t, "ek")
    shared, ciphertext = key.public_key().encapsulate()
    assert key.decapsulate(ciphertext) == shared


@pytest.mark.parametrize("t", VECTORS["slh_dsa_keygen"], ids=_id)
def test_slh_dsa_key_from_seeds(t: dict[str, Any]) -> None:
    seeds = (_h(t, "skSeed"), _h(t, "skPrf"), _h(t, "pkSeed"))
    assert custody_pq.keygen_internal(t["parameterSet"], *seeds) == (_h(t, "sk"), _h(t, "pk"))


@pytest.mark.parametrize("t", VECTORS["slh_dsa_sigver"], ids=_id)
def test_slh_dsa_verification(t: dict[str, Any]) -> None:
    ps, pk, message = t["parameterSet"], _h(t, "pk"), _h(t, "message")
    verified = custody_pq.verify(ps, pk, message, _h(t, "signature"), _h(t, "context"))
    assert verified is t["testPassed"], t.get("reason")


def test_slh_dsa_deterministic_signature_is_reproduced() -> None:
    (t,) = VECTORS["slh_dsa_siggen"]
    sk = _h(t, "sk")
    pk_seed = sk[32:48]  # FIPS 205 deterministic variant: the randomiser input is PK.seed
    signature = custody_pq.sign(t["parameterSet"], sk, _h(t, "message"), _h(t, "context"), pk_seed)
    assert signature == _h(t, "signature")


def test_slh_dsa_hedged_signatures_differ_and_verify() -> None:
    sk, pk = custody_pq.keygen("SLH-DSA-SHA2-128f")
    first, second = (custody_pq.sign("SLH-DSA-SHA2-128f", sk, b"settle 42") for _ in range(2))
    assert first != second and len(first) == 17088
    assert custody_pq.verify("SLH-DSA-SHA2-128f", pk, b"settle 42", first)
    assert not custody_pq.verify("SLH-DSA-SHA2-128f", pk, b"settle 43", first)
