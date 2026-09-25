import json
from itertools import combinations
from pathlib import Path

from custody_lab.foundations import shamir
from custody_lab.foundations.ec import SECP256K1, Point, decode_point, encode_point
from custody_lab.mpc import dkg, frost

# RFC 9591 test vectors for FROST(secp256k1, SHA-256), fetched 2026-09-24 from
# https://github.com/cfrg/draft-irtf-cfrg-frost/blob/master/poc/frost-secp256k1-sha256.json
# sha256 5bda3e29f8e7a0883ceaa0e4bc2f71582bbb4f04058a4657dd5aa276f32372bd
V = json.loads((Path(__file__).parent / "vectors" / "frost-secp256k1-sha256.json").read_text())
INPUTS = V["inputs"]
MSG = bytes.fromhex(INPUTS["message"])
SECRET = int(INPUTS["group_secret_key"], 16)
PK = decode_point(bytes.fromhex(INPUTS["group_public_key"]))
SHARES = {s["identifier"]: int(s["participant_share"], 16) for s in INPUTS["participant_shares"]}
ROUND1 = {o["identifier"]: o for o in V["round_one_outputs"]["outputs"]}
SIG_SHARES = {o["identifier"]: int(o["sig_share"], 16) for o in V["round_two_outputs"]["outputs"]}


def _round1() -> tuple[dict[int, frost.Nonces], list[frost.Commitment]]:
    nonces, commitments = {}, []
    for i, o in ROUND1.items():
        nonces[i], commitment = frost.commit(
            i,
            SHARES[i],
            bytes.fromhex(o["hiding_nonce_randomness"]),
            bytes.fromhex(o["binding_nonce_randomness"]),
        )
        commitments.append(commitment)
    return nonces, commitments


def test_dealer_shares_and_group_key() -> None:
    coefficients = [int(c, 16) for c in INPUTS["share_polynomial_coefficients"]]
    shares = shamir.split(SECRET, threshold=2, count=3, coefficients=coefficients)
    assert {s.x: s.y for s in shares} == SHARES
    assert SECP256K1.mul(SECRET, SECP256K1.G) == PK


def test_round_one_nonces_and_commitments() -> None:
    nonces, commitments = _round1()
    for c in commitments:
        o = ROUND1[c.identifier]
        assert nonces[c.identifier] == frost.Nonces(
            int(o["hiding_nonce"], 16), int(o["binding_nonce"], 16)
        )
        assert encode_point(c.hiding).hex() == o["hiding_nonce_commitment"]
        assert encode_point(c.binding).hex() == o["binding_nonce_commitment"]


def test_binding_factors() -> None:
    _, commitments = _round1()
    rho = frost.binding_factors(PK, commitments, MSG)
    for i, o in ROUND1.items():
        rho_input = frost.binding_factor_input(PK, commitments, MSG, i)
        assert rho_input.hex() == o["binding_factor_input"]
        assert rho[i] == int(o["binding_factor"], 16)


def test_signature_shares_and_final_signature() -> None:
    nonces, commitments = _round1()
    shares = {i: frost.sign(i, SHARES[i], nonces[i], PK, commitments, MSG) for i in ROUND1}
    assert shares == SIG_SHARES
    signature = frost.aggregate(PK, commitments, MSG, list(shares.values()))
    assert frost.encode_signature(signature).hex() == V["final_output"]["sig"]
    assert frost.verify(PK, MSG, signature)


def _sign(shares: dict[int, int], group_key: Point, msg: bytes) -> tuple[Point, int]:
    rounds = {i: frost.commit(i, s) for i, s in shares.items()}
    commitments = [c for _, c in rounds.values()]
    z = [frost.sign(i, shares[i], rounds[i][0], group_key, commitments, msg) for i in shares]
    return frost.aggregate(group_key, commitments, msg, z)


def test_dkg_shares_sign_with_every_pair() -> None:
    shares, group_key = dkg.run(threshold=2, count=3)
    for pair in combinations(shares, 2):
        subset = {i: shares[i] for i in pair}
        assert frost.verify(group_key, b"settle 42", _sign(subset, group_key, b"settle 42"))


def test_refreshed_shares_sign_and_do_not_mix_with_old() -> None:
    old, group_key = dkg.run(threshold=2, count=3)
    new = dkg.refresh(old, threshold=2)
    assert frost.verify(group_key, b"m", _sign({1: new[1], 2: new[2]}, group_key, b"m"))
    assert not frost.verify(group_key, b"m", _sign({1: old[1], 2: new[2]}, group_key, b"m"))
