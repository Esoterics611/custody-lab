"""Command line for the demo.

``custody-lab run`` runs the demo once and prints each step as it happens. ``custody-lab serve``
starts the HTTP server (``custody_lab.demo.server``), which also serves the dashboard once
``npm --prefix web run build`` has produced ``web/dist``.
"""

from __future__ import annotations

import json
import shutil
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any

import typer
import uvicorn

from custody_lab.demo import pipeline, server

app = typer.Typer(add_completion=False, no_args_is_help=True)
Runs = Annotated[Path, typer.Option(help="Directory that receives one subdirectory per run.")]


def _show(value: Any) -> str:
    if isinstance(value, str | Decimal):
        return str(value)
    return json.dumps(value, default=str, separators=(",", ":"))


def _print(event: pipeline.Event) -> None:
    order = list(pipeline.STEPS)
    if event.status == "running":
        typer.echo(f"[{order.index(event.step) + 1}/{len(order)}] {event.title}")
        return
    width = shutil.get_terminal_size().columns
    for key, value in event.detail.items():
        line = f"      {key}: {_show(value)}"
        typer.echo(line if len(line) <= width else line[: width - 3] + "...")


@app.command()
def run(runs: Runs = pipeline.RUNS) -> None:
    """Run the demo end to end and print each step."""
    summary = pipeline.run(_print, pipeline.new_workdir(runs))
    typer.echo("")
    for key, value in summary.items():
        typer.echo(f"{key}: {_show(value)}")


@app.command()
def serve(
    runs: Runs = pipeline.RUNS,
    dashboard: Annotated[Path, typer.Option(help="Built dashboard to serve at /.")] = (
        server.DASHBOARD
    ),
    host: str = "127.0.0.1",
    port: int = 8000,
) -> None:
    """Serve the demo API and the built dashboard."""
    uvicorn.run(server.create_app(runs, dashboard), host=host, port=port)
