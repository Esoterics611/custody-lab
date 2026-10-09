"""The dashboard's TypeScript check of a snapshot's proof of control agrees with BIP340 and with
the Python signer.

``web/src/snapshot.ts`` verifies with ``@noble/curves``, sharing no code with
``custody_lab.foundations.schnorr``. These tests run it under Node on the published BIP340 test
vectors, and on snapshots signed by the Python code, unchanged and altered.
"""

import csv
import json
import shutil
import subprocess
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from custody_lab.foundations import schnorr
from custody_lab.reserves.snapshot import Snapshot, publish

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not on PATH")
HARNESS = "web/tests/verify-snapshot.ts"
VECTORS = Path(__file__).parents[1] / "foundations" / "vectors" / "bip340-test-vectors.csv"
SECKEY = (7).to_bytes(32, "big")


def _browser(vectors: list[dict[str, str]], snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    document = {"vectors": vectors, "snapshots": snapshots}
    done = subprocess.run(
        ["node", HARNESS], input=json.dumps(document), capture_output=True, text=True, check=True
    )
    result: dict[str, Any] = json.loads(done.stdout)
    return result


def _signed_snapshot(tmp_path: Path) -> dict[str, Any]:
    snapshot = Snapshot(
        taken_at=datetime(2026, 10, 9, 17, 0, tzinfo=UTC),
        block_height=106,
        block_hash="00" * 32,
        liabilities_root="11" * 32,
        liabilities=Decimal("3.0999907"),
        clients=4,
        assets=Decimal("3.0999907"),
        custody_output_key=schnorr.pubkey_gen(SECKEY).hex(),
        audit_head="22" * 32,
    )
    signature = schnorr.sign(snapshot.attestation_message(), SECKEY, aux_rand=bytes(32))
    document: dict[str, Any] = json.loads(publish(snapshot, signature, tmp_path).read_text())
    return document


def test_every_bip340_vector_verifies_as_published() -> None:
    with VECTORS.open() as f:
        rows = list(csv.DictReader(f))

    verdicts = _browser(
        [
            {"public_key": r["public key"], "message": r["message"], "signature": r["signature"]}
            for r in rows
        ],
        [],
    )["vectors"]

    assert len(rows) == 19
    assert verdicts == [r["verification result"] == "TRUE" for r in rows]


def test_a_python_signed_snapshot_verifies_and_an_altered_one_does_not(tmp_path: Path) -> None:
    signed = _signed_snapshot(tmp_path)
    altered = {**signed, "liabilities": "2.0999907"}  # a debt of 1 BTC hidden

    honest, changed = _browser([], [signed, altered])["snapshots"]

    assert honest["messageMatches"] and honest["signatureValid"]
    assert honest["message"] == signed["attestation"]["message"]
    assert not changed["messageMatches"] and not changed["signatureValid"]
