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


def test_signers_two_and_three_settle_with_signer_one_stopped(tmp_path: Path) -> None:
    events: list[pipeline.Event] = []
    summary = pipeline.run(events.append, tmp_path, offline=[1])

    sign = next(e for e in events if e.step == "sign" and e.status == "done")
    assert sign.detail["signers"] == [2, 3] and sign.detail["offline"] == [1]
    assert summary["reserve_ratio"] == 1


def test_one_signer_alone_fails_at_signing_and_broadcasts_nothing(tmp_path: Path) -> None:
    events: list[pipeline.Event] = []

    with pytest.raises(RuntimeError, match="1 of 3 signers online and 2 are required"):
        pipeline.run(events.append, tmp_path, offline=[1, 3])

    assert (events[-1].step, events[-1].status) == ("sign", "failed")
    assert "IncorrectNumberOfCommitments" in events[-1].detail["error"]
    assert not any(e.step == "broadcast" for e in events)


@pytest.mark.parametrize(
    ("offline", "asked"),
    [((), [1, 3]), ((2,), [1, 3]), ((1,), [2, 3]), ((3,), [1, 2]), ((1, 3), [2]), ((1, 2, 3), [])],
)
def test_the_coordinator_asks_signers_one_and_three_while_they_are_online(
    offline: tuple[int, ...], asked: list[int]
) -> None:
    assert pipeline._asked(offline, threshold=2) == asked
