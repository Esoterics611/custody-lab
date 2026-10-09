"""HTTP front end for the demo: each POST starts a run and streams its events back.

``POST /api/runs`` runs ``pipeline.run`` on a worker thread in a fresh directory under the runs
directory. An optional JSON body, ``{"offline": [1]}``, names signers to stop before step 7.
The response carries the run's events as they happen, one JSON object per line
(``application/x-ndjson``), and ends when the run ends; a run that fails ends with its ``failed``
event. The dashboard reads the response body as a stream. It does not use ``EventSource``, which
issues only GET and reconnects on its own, so a reconnect after a run finished would start
another run. A run continues to completion if the client disconnects, and its artefacts stay in
its directory.

``POST /api/day`` runs ``day.run``, a day of deposits, trading, withdrawals and refusals, the
same way, in a fresh directory under the day's runs directory; ``GET /api/day/steps`` lists its
steps.

``POST /api/ceremonies`` plays the key ceremonies (``ceremonies.run``: a share stolen before a
refresh, a share lost and repaired) the same way, with no chain; ``GET /api/ceremonies/steps``
lists their steps.

``POST /api/redteam`` plays the red team on regtest (``redteam.run``: a reorganised deposit and a
misdirected withdrawal, each against a weak rule and then the defence) in a fresh directory under
``var/redteam``; ``GET /api/redteam/steps`` lists its steps.

``POST /api/attacks`` runs ``attacks.run`` the same way and streams one attempt per line: each
attack, the component that refused it and that component's reason. It needs no regtest node.

``GET /api/runs`` lists the recorded runs under the runs directory, newest first, with how each
ended; ``GET /api/runs/<run>`` returns one run's events from its ``events.jsonl``, which the
dashboard replays. Neither needs a regtest node.

``GET /api/steps`` lists the steps in order. When the dashboard has been built (``web/dist``), it
is served at ``/``.
"""

from __future__ import annotations

import json
import logging
import queue
import threading
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, Protocol

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from custody_lab.demo import attacks, ceremonies, day, pipeline, redteam

DASHBOARD = Path("web/dist")
RECENT = 20  # recorded runs listed
log = logging.getLogger(__name__)


class RunRequest(BaseModel):
    offline: list[int] = []


class _Line(Protocol):
    def to_json(self) -> str: ...


def _stream[T: _Line](
    name: str, work: Callable[[Callable[[T], None]], object]
) -> StreamingResponse:
    """Run ``work(emit)`` on a worker thread; stream what it emits, one JSON object per line."""
    items: queue.Queue[T | None] = queue.Queue()

    def target() -> None:
        try:
            work(items.put)
        except Exception:  # a run's failure is already on the stream as its failed event
            log.exception("%s failed", name)
        finally:
            items.put(None)

    def lines() -> Iterator[str]:
        while (item := items.get()) is not None:
            yield item.to_json() + "\n"

    threading.Thread(target=target, name=name).start()
    return StreamingResponse(lines(), media_type="application/x-ndjson")


def _ending(events: list[dict[str, Any]]) -> str:
    """How a recorded run ended, in words."""
    if not events:
        return "no events recorded"
    last = events[-1]
    n = list(pipeline.STEPS).index(last["step"]) + 1
    if last["status"] == "failed":
        return f"failed at step {n}"
    if last["status"] == "done" and n == len(pipeline.STEPS):
        return "settled"
    return f"stopped during step {n}"


def create_app(
    runs: Path = pipeline.RUNS, dashboard: Path = DASHBOARD, days: Path = day.RUNS
) -> FastAPI:
    app = FastAPI(title="custody-lab demo")

    @app.get("/api/steps")
    def steps() -> dict[str, str]:
        return pipeline.STEPS

    @app.post("/api/runs")
    def start_run(request: RunRequest | None = None) -> StreamingResponse:
        offline = (request or RunRequest()).offline
        if not set(offline) <= set(pipeline.SHARES):
            raise HTTPException(422, f"offline signers must be among {list(pipeline.SHARES)}")
        workdir = pipeline.new_workdir(runs)

        def work(emit: pipeline.Emit) -> None:
            pipeline.run(emit, workdir, offline)

        return _stream(f"demo run in {workdir}", work)

    @app.get("/api/runs")
    def recorded_runs() -> list[dict[str, Any]]:
        listed = []
        for log in sorted(runs.glob("*/events.jsonl"), reverse=True)[:RECENT]:
            events = [json.loads(line) for line in log.read_text().splitlines()]
            sign = next((e for e in events if e["step"] == "sign"), None)
            offline: list[int] = sign["detail"].get("offline", []) if sign else []
            listed.append({"run": log.parent.name, "ended": _ending(events), "offline": offline})
        return listed

    @app.get("/api/runs/{run}")
    def recorded_run(run: str) -> list[dict[str, Any]]:
        recorded = {p.name for p in runs.iterdir() if p.is_dir()} if runs.is_dir() else set()
        if run not in recorded:  # so ``run`` is never a path
            raise HTTPException(404, f"no recorded run {run!r}")
        log = runs / run / "events.jsonl"
        if not log.is_file():
            raise HTTPException(404, f"run {run!r} recorded no events")
        return [json.loads(line) for line in log.read_text().splitlines()]

    @app.get("/api/day/steps")
    def day_steps() -> dict[str, str]:
        return day.STEPS

    @app.post("/api/day")
    def start_day() -> StreamingResponse:
        workdir = pipeline.new_workdir(days)

        def work(emit: pipeline.Emit) -> None:
            day.run(emit, workdir)

        return _stream(f"day in {workdir}", work)

    @app.get("/api/ceremonies/steps")
    def ceremony_steps() -> dict[str, str]:
        return ceremonies.STEPS

    @app.post("/api/ceremonies")
    def ceremony() -> StreamingResponse:
        return _stream("key ceremonies", ceremonies.run)

    @app.get("/api/redteam/steps")
    def redteam_steps() -> dict[str, str]:
        return redteam.STEPS

    @app.post("/api/redteam")
    def red_team() -> StreamingResponse:
        workdir = pipeline.new_workdir(redteam.RUNS)

        def work(emit: pipeline.Emit) -> None:
            redteam.run(emit, workdir)

        return _stream(f"red team in {workdir}", work)

    @app.post("/api/attacks")
    def attack() -> StreamingResponse:
        return _stream("attack panel", attacks.run)

    if dashboard.is_dir():
        app.mount("/", StaticFiles(directory=dashboard, html=True), name="dashboard")
    return app
