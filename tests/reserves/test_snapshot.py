"""Snapshot tests: the published file verifies on its own, and an attestation authorisation lets
the signers sign the attestation and nothing else."""

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from custody_lab.foundations import schnorr
from custody_lab.mpc.cluster import SigningCluster
from custody_lab.policy.audit import AuditLog
from custody_lab.policy.authorisation import AuthorityKey
from custody_lab.policy.engine import Policy, PolicyEngine
from custody_lab.reserves.snapshot import Snapshot, publish

SECKEY = (7).to_bytes(32, "big")


def _now() -> datetime:
    return datetime.now(UTC)


def _snapshot(output_key: bytes) -> Snapshot:
    return Snapshot(
        taken_at=datetime(2026, 9, 25, 9, 0, tzinfo=UTC),
        block_height=103,
        block_hash="00" * 32,
        liabilities_root="11" * 32,
        liabilities=Decimal("4.15"),
        clients=4,
        assets=Decimal("4.1599969"),
        custody_output_key=output_key.hex(),
        audit_head="22" * 32,
    )


def test_published_snapshot_verifies_from_the_file_alone(tmp_path: Path) -> None:
    snapshot = _snapshot(schnorr.pubkey_gen(SECKEY))
    signature = schnorr.sign(snapshot.attestation_message(), SECKEY, aux_rand=bytes(32))
    document = json.loads(publish(snapshot, signature, tmp_path).read_text())

    # A third party needs the file, the standard library and a BIP340 verifier.
    attestation = document.pop("attestation")
    assert document.pop("reserve_ratio") == "1.00241"
    statement = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    prefix = hashlib.sha256(attestation["tag"].encode()).digest()
    message = hashlib.sha256(prefix + prefix + statement).digest()
    assert message.hex() == attestation["message"]
    assert schnorr.verify(
        message,
        bytes.fromhex(document["custody_output_key"]),
        bytes.fromhex(attestation["bip340_signature"]),
    )


def test_an_attestation_token_signs_the_attestation_and_nothing_else() -> None:
    engine = PolicyEngine(Policy({}, {}), AuthorityKey.generate(), AuditLog(_now), _now)
    statement = _snapshot(bytes(32)).statement()
    with SigningCluster(2, 3, engine.authority_public_key) as cluster:
        key = cluster.dkg()
        token = engine.authorise_attestation(statement)
        signature = cluster.sign(token.message, [1, 2], token.to_bytes())
        assert schnorr.verify(token.message, key, signature)

        sighash = b"\x6a" * 32  # stands in for a transaction sighash
        with pytest.raises(RuntimeError, match="differs from the authorised message"):
            cluster.sign(sighash, [1, 3], engine.authorise_attestation(statement).to_bytes())
    assert [e.event for e in engine.audit.entries] == ["attestation_authorised"] * 2
