"""The demo's command line and HTTP server, driven by stand-ins for ``pipeline.run`` so no
regtest node is needed. ``test_pipeline.py`` runs the real pipeline."""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from custody_lab.demo import cli, pipeline, server

GROUP_KEY = "02" + "ab" * 32


def _event(step: str, status: str, **detail: Any) -> pipeline.Event:
    return pipeline.Event(step, status, pipeline.STEPS[step], detail)


def _two_steps(emit: pipeline.Emit) -> None:
    emit(_event("chain", "running"))
    emit(_event("chain", "done", height=101))
    emit(_event("keys", "running"))
    emit(_event("keys", "done", signers=[{"share": 1, "pid": 4242}], group_key=GROUP_KEY))


def _succeeds(emit: pipeline.Emit, workdir: Path) -> dict[str, Any]:
    _two_steps(emit)
    return {"txid": "ff" * 32}


def _fails(emit: pipeline.Emit, workdir: Path) -> dict[str, Any]:
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
    ]
    assert _events(first)[-1]["detail"]["signers"] == [{"share": 1, "pid": 4242}]
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
