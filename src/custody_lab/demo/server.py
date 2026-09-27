"""HTTP front end for the demo: each POST starts a run and streams its events back.

``POST /api/runs`` runs ``pipeline.run`` on a worker thread in a fresh directory under the runs
directory. The response carries the run's events as they happen, one JSON object per line
(``application/x-ndjson``), and ends when the run ends; a run that fails ends with its ``failed``
event. The dashboard reads the response body as a stream. It does not use ``EventSource``, which
issues only GET and reconnects on its own, so a reconnect after a run finished would start
another run. A run continues to completion if the client disconnects, and its artefacts stay in
its directory.

``GET /api/steps`` lists the steps in order. When the dashboard has been built (``web/dist``), it
is served at ``/``.
"""

from __future__ import annotations

import logging
import queue
import threading
from collections.abc import Iterator
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from custody_lab.demo import pipeline

DASHBOARD = Path("web/dist")
log = logging.getLogger(__name__)


def create_app(runs: Path = pipeline.RUNS, dashboard: Path = DASHBOARD) -> FastAPI:
    app = FastAPI(title="custody-lab demo")

    @app.get("/api/steps")
    def steps() -> dict[str, str]:
        return pipeline.STEPS

    @app.post("/api/runs")
    def start_run() -> StreamingResponse:
        workdir = pipeline.new_workdir(runs)
        events: queue.Queue[pipeline.Event | None] = queue.Queue()

        def work() -> None:
            try:
                pipeline.run(events.put, workdir)
            except Exception:  # already on the stream as a failed event
                log.exception("demo run in %s failed", workdir)
            finally:
                events.put(None)

        def lines() -> Iterator[str]:
            while (event := events.get()) is not None:
                yield event.to_json() + "\n"

        threading.Thread(target=work, name=f"demo-{workdir.name}").start()
        return StreamingResponse(lines(), media_type="application/x-ndjson")

    if dashboard.is_dir():
        app.mount("/", StaticFiles(directory=dashboard, html=True), name="dashboard")
    return app
