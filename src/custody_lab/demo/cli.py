"""Command line for the demo.

``custody-lab run`` runs the demo once and prints each step as it happens. ``custody-lab day``
runs a busier day (``custody_lab.demo.day``) the same way, and ``custody-lab ceremonies`` the key
ceremonies (``custody_lab.demo.ceremonies``).
``custody-lab attacks`` tries every attack in ``custody_lab.demo.attacks`` and prints who refused
each. ``custody-lab serve`` starts the HTTP server (``custody_lab.demo.server``), which also serves
the dashboard once ``npm --prefix web run build`` has produced ``web/dist``.
"""

from __future__ import annotations

import json
import os
import shutil
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any

import typer
import uvicorn

from custody_lab.demo import attacks as attack_panel
from custody_lab.demo import ceremonies as key_ceremonies
from custody_lab.demo import day as day_scenario
from custody_lab.demo import pipeline, redteam, server

app = typer.Typer(add_completion=False, no_args_is_help=True)
Runs = Annotated[Path, typer.Option(help="Directory that receives one subdirectory per run.")]


def _show(value: Any) -> str:
    if isinstance(value, str | Decimal):
        return str(value)
    return json.dumps(value, default=str, separators=(",", ":"))


def _print(event: pipeline.Event, steps: dict[str, str] = pipeline.STEPS) -> None:
    order = list(steps)
    if event.status == "running":
        typer.echo(f"[{order.index(event.step) + 1}/{len(order)}] {event.title}")
        return
    width = shutil.get_terminal_size().columns
    for key, value in event.detail.items():
        lines = [f"      {key}: {_show(value)}"]
        if key == "books":  # the day's reconciliation, in one line
            agree = "reconciled" if value["reconciled"] else "NOT RECONCILED"
            lines = [f"      books: ledger {value['owed']}, coins {value['held']}: {agree}"]
        elif key == "inclusion_proofs":  # for the dashboard's balance check
            lines = [f"      inclusion_proofs: {len(value)} published"]
        elif isinstance(value, list) and value and all(isinstance(v, dict) for v in value):
            lines = [f"      {key}:"] + [
                "        - " + ", ".join(f"{k}: {_show(v)}" for k, v in row.items())
                for row in value
            ]
        elif isinstance(value, dict) and value and all(isinstance(v, dict) for v in value.values()):
            lines = [f"      {key}:"] + [
                f"        - {name}: " + ", ".join(f"{k}: {_show(v)}" for k, v in row.items())
                for name, row in value.items()
            ]
        for line in lines:
            whole = key == "error" or line.startswith("        - ")  # errors and records wrap
            if len(line) > width and not whole:
                line = line[: width - 3] + "..."
            typer.echo(line)


@app.command()
def run(
    runs: Runs = pipeline.RUNS,
    offline: Annotated[
        list[int] | None,
        typer.Option(help="A signer to stop before step 7; repeat for each."),
    ] = None,
) -> None:
    """Run the demo end to end and print each step; exit 1 if a step fails."""
    workdir = pipeline.new_workdir(runs)
    try:
        summary = pipeline.run(_print, workdir, offline or [])
    except Exception:  # printed above as the failed step's error; no traceback
        typer.echo(f"\nThe run stopped. Its events are in {os.path.relpath(workdir)}/events.jsonl")
        raise typer.Exit(1) from None
    typer.echo("")
    for key, value in summary.items():
        typer.echo(f"{key}: {_show(value)}")


@app.command()
def day(runs: Runs = day_scenario.RUNS) -> None:
    """Run a day of deposits, trading, withdrawals and refusals; exit 1 if a step fails."""
    workdir = pipeline.new_workdir(runs)
    try:
        summary = day_scenario.run(lambda e: _print(e, day_scenario.STEPS), workdir)
    except Exception:  # printed above as the failed step's error; no traceback
        typer.echo(f"\nThe day stopped. Its events are in {os.path.relpath(workdir)}/events.jsonl")
        raise typer.Exit(1) from None
    typer.echo("")
    for key, value in summary.items():
        typer.echo(f"{key}: {_show(value)}")


@app.command()
def ceremonies() -> None:
    """Play the key ceremonies: a stolen share against a refresh, and a lost share repaired."""
    try:
        summary = key_ceremonies.run(lambda e: _print(e, key_ceremonies.STEPS))
    except Exception:  # printed above as the failed step's error; no traceback
        raise typer.Exit(1) from None
    typer.echo("")
    for key, value in summary.items():
        typer.echo(f"{key}: {_show(value)}")


@app.command(name="redteam")
def red_team() -> None:
    """Play the red team on regtest: each attack against a weak rule, then against the defence."""
    workdir = pipeline.new_workdir(redteam.RUNS)
    try:
        summary = redteam.run(lambda e: _print(e, redteam.STEPS), workdir)
    except Exception:  # printed above as the failed step's error; no traceback
        raise typer.Exit(1) from None
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
