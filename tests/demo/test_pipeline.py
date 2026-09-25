import json
import shutil
from pathlib import Path

import pytest

from custody_lab.demo import pipeline
from custody_lab.foundations import schnorr

pytestmark = [
    pytest.mark.regtest,
    pytest.mark.skipif(shutil.which("bitcoind") is None, reason="bitcoind not on PATH"),
]


def test_demo_runs_every_step_and_publishes_a_verifiable_snapshot(tmp_path: Path) -> None:
    events: list[pipeline.Event] = []
    summary = pipeline.run(events.append, tmp_path)

    assert [e.step for e in events if e.status == "done"] == list(pipeline.STEPS)
    assert summary["reserve_ratio"] > 1

    document = json.loads(Path(summary["snapshot"]).read_text())
    attestation = document["attestation"]
    assert schnorr.verify(
        bytes.fromhex(attestation["message"]),
        bytes.fromhex(document["custody_output_key"]),
        bytes.fromhex(attestation["bip340_signature"]),
    )
    audit = [json.loads(line) for line in (tmp_path / "audit.jsonl").read_text().splitlines()]
    assert document["audit_head"] in {entry["hash"] for entry in audit}  # the anchored head
