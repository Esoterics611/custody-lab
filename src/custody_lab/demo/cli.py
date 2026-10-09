"""Command line for the demo.

``custody-lab run`` runs the demo once and prints each step as it happens.
``custody-lab attacks`` tries every attack in ``custody_lab.demo.attacks`` and prints who refused
each. ``custody-lab serve`` starts the HTTP server (``custody_lab.demo.server``), which also serves
the dashboard once ``npm --prefix web run build`` has produced ``web/dist``.
"""

from __future__ import annotations

import json
import shutil
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any

import typer
import uvicorn

from custody_lab.demo import attacks as attack_panel
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
def run(
    runs: Runs = pipeline.RUNS,
    signer: Annotated[
        list[int] | None,
        typer.Option(help="A signer online at step 7; repeat for each. Default: 1 and 3."),
    ] = None,
) -> None:
    """Run the demo end to end and print each step."""
    summary = pipeline.run(_print, pipeline.new_workdir(runs), signer or pipeline.SIGNERS)
    typer.echo("")
    for key, value in summary.items():
        typer.echo(f"{key}: {_show(value)}")


@app.command()
def attacks() -> None:
    """Try every attack on the design and print who refused each; exit 1 if any got through."""
    group = ""

    def show(attempt: attack_panel.Attempt) -> None:
        nonlocal group
        if attempt.group != group:
            group = attempt.group
            typer.echo(attack_panel.GROUPS[group])
        typer.echo(f"  {'refused ' if attempt.refused else 'ACCEPTED'}  {attempt.title}")
        typer.echo(f"            {attempt.defence}: {attempt.reason}")

    attempts = attack_panel.run(show)
    refused = sum(a.refused for a in attempts)
    typer.echo(f"\n{refused} of {len(attempts)} attacks refused")
    if refused < len(attempts):
        raise typer.Exit(1)


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
