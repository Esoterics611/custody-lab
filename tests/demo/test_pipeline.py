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
    assert summary["reserve_ratio"] == 1  # the client paid the fee; no house coins at custody

    document = json.loads(Path(summary["snapshot"]).read_text())
    assert document["assets"] == document["liabilities"]
    attestation = document["attestation"]
    assert schnorr.verify(
        bytes.fromhex(attestation["message"]),
        bytes.fromhex(document["custody_output_key"]),
        bytes.fromhex(attestation["bip340_signature"]),
    )
    audit = [json.loads(line) for line in (tmp_path / "audit.jsonl").read_text().splitlines()]
    assert document["audit_head"] in {entry["hash"] for entry in audit}  # the anchored head


def test_a_failing_step_is_reported_and_logged_before_it_propagates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def exchange_unreachable(orders: object) -> None:
        raise ConnectionRefusedError("toy exchange unreachable")

    monkeypatch.setattr(pipeline, "trade", exchange_unreachable)
    events: list[pipeline.Event] = []

    with pytest.raises(ConnectionRefusedError):
        pipeline.run(events.append, tmp_path)

    failed = pipeline.Event(
        "trade",
        "failed",
        pipeline.STEPS["trade"],
        {"error": "ConnectionRefusedError: toy exchange unreachable"},
    )
    assert events[-1] == failed
    logged = (tmp_path / "events.jsonl").read_text().splitlines()
    assert json.loads(logged[-1]) == json.loads(failed.to_json())


def test_a_missing_bitcoind_is_reported_as_the_first_step_failing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: None)
    events: list[pipeline.Event] = []

    with pytest.raises(RuntimeError, match="bitcoind not found"):
        pipeline.run(events.append, tmp_path)

    assert [(e.step, e.status) for e in events] == [("chain", "running"), ("chain", "failed")]
    assert (tmp_path / "events.jsonl").read_text().count("\n") == 2
