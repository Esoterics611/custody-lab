"""HTTP front end for the demo: each POST starts a run and streams its events back.

``POST /api/runs`` runs ``pipeline.run`` on a worker thread in a fresh directory under the runs
directory. An optional JSON body, ``{"signers": [2, 3]}``, names the signers online at step 7.
The response carries the run's events as they happen, one JSON object per line
(``application/x-ndjson``), and ends when the run ends; a run that fails ends with its ``failed``
event. The dashboard reads the response body as a stream. It does not use ``EventSource``, which
issues only GET and reconnects on its own, so a reconnect after a run finished would start
another run. A run continues to completion if the client disconnects, and its artefacts stay in
its directory.

``POST /api/attacks`` runs ``attacks.run`` the same way and streams one attempt per line: each
attack, the component that refused it and that component's reason. It needs no regtest node.

``GET /api/steps`` lists the steps in order. When the dashboard has been built (``web/dist``), it
is served at ``/``.
"""

from __future__ import annotations

import logging
import queue
import threading
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Protocol

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from custody_lab.demo import attacks, pipeline

DASHBOARD = Path("web/dist")
log = logging.getLogger(__name__)


class RunRequest(BaseModel):
    signers: list[int] = pipeline.SIGNERS


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


def create_app(runs: Path = pipeline.RUNS, dashboard: Path = DASHBOARD) -> FastAPI:
    app = FastAPI(title="custody-lab demo")

    @app.get("/api/steps")
    def steps() -> dict[str, str]:
        return pipeline.STEPS

    @app.post("/api/runs")
    def start_run(request: RunRequest | None = None) -> StreamingResponse:
        signers = (request or RunRequest()).signers
        if not set(signers) <= set(pipeline.SHARES):
            raise HTTPException(422, f"signers must be among {list(pipeline.SHARES)}")
        workdir = pipeline.new_workdir(runs)

        def work(emit: pipeline.Emit) -> None:
            pipeline.run(emit, workdir, signers)

        return _stream(f"demo run in {workdir}", work)

    @app.post("/api/attacks")
    def attack() -> StreamingResponse:
        return _stream("attack panel", attacks.run)

    if dashboard.is_dir():
        app.mount("/", StaticFiles(directory=dashboard, html=True), name="dashboard")
    return app
