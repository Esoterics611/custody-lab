"""The demo's command line and HTTP server, driven by stand-ins for ``pipeline.run`` so no
regtest node is needed. ``test_pipeline.py`` runs the real pipeline."""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from custody_lab.demo import attacks, cli, pipeline, server

GROUP_KEY = "02" + "ab" * 32


def _event(step: str, status: str, **detail: Any) -> pipeline.Event:
    return pipeline.Event(step, status, pipeline.STEPS[step], detail)


def _two_steps(emit: pipeline.Emit) -> None:
    emit(_event("chain", "running"))
    emit(_event("chain", "done", height=101))
    emit(_event("keys", "running"))
    emit(_event("keys", "done", signers=[{"share": 1, "pid": 4242}], group_key=GROUP_KEY))


def _succeeds(emit: pipeline.Emit, workdir: Path, offline: list[int]) -> dict[str, Any]:
    _two_steps(emit)
    emit(_event("sign", "running", offline=offline))
    return {"txid": "ff" * 32}


def _fails(emit: pipeline.Emit, workdir: Path, offline: list[int]) -> dict[str, Any]:
    _two_steps(emit)
    emit(_event("sign", "running", signers=[1, 3]))
    emit(_event("sign", "failed", error="RuntimeError: aggregated signature does not verify"))
    raise RuntimeError("aggregated signature does not verify")


@pytest.fixture
def succeeding_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pipeline, "run", _succeeds)


@pytest.fixture
def failing_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pipeline, "run", _fails)


def _events(response: httpx.Response) -> list[dict[str, Any]]:
    return [json.loads(line) for line in response.text.splitlines()]


@pytest.mark.usefixtures("succeeding_run")
def test_a_run_streams_its_events_in_order_from_its_own_directory(tmp_path: Path) -> None:
    client = TestClient(server.create_app(tmp_path, tmp_path / "no-dashboard"))

    first, second = client.post("/api/runs"), client.post("/api/runs")

    assert first.headers["content-type"] == "application/x-ndjson"
    assert [(e["step"], e["status"]) for e in _events(first)] == [
        ("chain", "running"),
        ("chain", "done"),
        ("keys", "running"),
        ("keys", "done"),
        ("sign", "running"),
    ]
    assert _events(first)[3]["detail"]["signers"] == [{"share": 1, "pid": 4242}]
    assert _events(first)[-1]["detail"]["offline"] == []
    assert _events(second) == _events(first)
    assert len(list(tmp_path.iterdir())) == 2


@pytest.mark.usefixtures("failing_run")
def test_a_failed_run_ends_its_stream_with_the_failed_event(tmp_path: Path) -> None:
    client = TestClient(server.create_app(tmp_path, tmp_path / "no-dashboard"))

    events = _events(client.post("/api/runs"))

    assert events[-1] == {
        "step": "sign",
        "status": "failed",
        "title": pipeline.STEPS["sign"],
        "detail": {"error": "RuntimeError: aggregated signature does not verify"},
        "at_ms": 0,
    }


def test_the_built_dashboard_is_served_at_the_root_beside_the_api(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<p>dashboard</p>")
    client = TestClient(server.create_app(tmp_path / "runs", dist))

    assert client.get("/").text == "<p>dashboard</p>"
    assert list(client.get("/api/steps").json()) == list(pipeline.STEPS)


@pytest.mark.usefixtures("succeeding_run")
def test_run_prints_each_step_its_details_and_the_summary(tmp_path: Path) -> None:
    result = CliRunner().invoke(cli.app, ["run", "--runs", str(tmp_path)], env={"COLUMNS": "80"})

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        f"[1/9] {pipeline.STEPS['chain']}",
        "      height: 101",
        f"[2/9] {pipeline.STEPS['keys']}",
        '      signers: [{"share":1,"pid":4242}]',
        "      group_key: 02" + "ab" * 29 + "...",  # cut to the 80-column terminal
        f"[7/9] {pipeline.STEPS['sign']}",
        "",
        "txid: " + "ff" * 32,
    ]
    assert len(list(tmp_path.iterdir())) == 1


@pytest.mark.usefixtures("failing_run")
def test_run_prints_the_failure_and_exits_non_zero(tmp_path: Path) -> None:
    result = CliRunner().invoke(cli.app, ["run", "--runs", str(tmp_path)])

    assert result.exit_code == 1
    assert "      error: RuntimeError: aggregated signature does not verify" in result.output
    assert isinstance(result.exception, RuntimeError)


@pytest.mark.usefixtures("succeeding_run")
def test_a_run_can_take_signers_offline_and_refuses_unknown_ones(tmp_path: Path) -> None:
    client = TestClient(server.create_app(tmp_path, tmp_path / "no-dashboard"))

    named = client.post("/api/runs", json={"offline": [1]})
    unknown = client.post("/api/runs", json={"offline": [4]})

    assert _events(named)[-1]["detail"]["offline"] == [1]
    assert unknown.status_code == 422
    assert len(list(tmp_path.iterdir())) == 1  # the refused request made no run directory


def test_run_passes_the_offline_signers_to_the_pipeline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    received: list[list[int]] = []

    def record(emit: pipeline.Emit, workdir: Path, offline: list[int]) -> dict[str, Any]:
        received.append(offline)
        return {}

    monkeypatch.setattr(pipeline, "run", record)
    args = ["run", "--runs", str(tmp_path), "--offline", "1", "--offline", "3"]

    assert CliRunner().invoke(cli.app, args).exit_code == 0
    assert CliRunner().invoke(cli.app, ["run", "--runs", str(tmp_path)]).exit_code == 0
    assert received == [[1, 3], []]


def test_the_attack_panel_streams_every_attempt_refused(tmp_path: Path) -> None:
    client = TestClient(server.create_app(tmp_path, tmp_path / "no-dashboard"))

    response = client.post("/api/attacks")

    assert response.headers["content-type"] == "application/x-ndjson"
    attempts = _events(response)
    assert [a["attack"] for a in attempts] == [f.__name__ for *_, f in attacks.ATTACKS]
    assert all(a["refused"] for a in attempts)
    assert list(tmp_path.iterdir()) == []  # attacks leave no run directory


def test_attacks_prints_each_refusal_and_the_count() -> None:
    result = CliRunner().invoke(cli.app, ["attacks"])

    assert result.exit_code == 0, result.output
    assert "  refused   Replay an authorisation that has already been used" in result.output
    assert result.output.endswith(
        f"{len(attacks.ATTACKS)} of {len(attacks.ATTACKS)} attacks refused\n"
    )
