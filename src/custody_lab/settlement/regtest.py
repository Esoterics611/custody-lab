"""A Bitcoin Core regtest node owned by this process, and a minimal JSON-RPC client.

``RegtestNode`` starts ``bitcoind`` on free ports in a data directory of its own and waits for
RPC readiness with ``bitcoin-cli -rpcwait``, which blocks until the node answers. It stops the
node on exit. Tests and the demo never share a chain with a node started by hand
(``scripts/regtest.sh``).
"""

from __future__ import annotations

import base64
import json
import shutil
import socket
import subprocess
import urllib.request
from decimal import Decimal
from pathlib import Path
from types import TracebackType
from typing import Any


class RPCError(Exception):
    pass


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port: int = s.getsockname()[1]
        return port


class BitcoinRPC:
    def __init__(self, url: str, cookie_file: Path) -> None:
        self._url, self._cookie_file = url, cookie_file

    def wallet(self, name: str) -> BitcoinRPC:
        return BitcoinRPC(f"{self._url.split('/wallet/')[0]}/wallet/{name}", self._cookie_file)

    def call(self, method: str, *params: Any) -> Any:
        auth = base64.b64encode(self._cookie_file.read_bytes().strip()).decode()
        payload = {"jsonrpc": "1.0", "id": method, "method": method, "params": params}
        body = json.dumps(payload, default=str)  # Decimal amounts go as strings; Core accepts them
        request = urllib.request.Request(
            self._url,
            data=body.encode(),
            headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request) as response:
                reply = json.loads(response.read(), parse_float=Decimal)  # BTC amounts
        except urllib.error.HTTPError as exc:  # Core returns 500 with a JSON error body
            reply = json.loads(exc.read(), parse_float=Decimal)
        if reply.get("error"):
            raise RPCError(f"{method}: {reply['error']['message']}")
        return reply["result"]


class RegtestNode:
    def __init__(self, datadir: Path) -> None:
        if shutil.which("bitcoind") is None:
            raise RuntimeError("bitcoind not found on PATH (see CLAUDE.md, Toolchain)")
        self.datadir = datadir
        self.rpc_port, self.p2p_port = _free_port(), _free_port()
        self._process: subprocess.Popen[bytes] | None = None

    def _args(self) -> list[str]:
        return [f"-datadir={self.datadir}", "-regtest", f"-rpcport={self.rpc_port}"]

    def start(self) -> BitcoinRPC:
        self.datadir.mkdir(parents=True, exist_ok=True)
        self._process = subprocess.Popen(
            ["bitcoind", *self._args(), f"-port={self.p2p_port}", "-listen=0",
             "-txindex=1", "-fallbackfee=0.0001", "-printtoconsole=0"],
        )  # fmt: skip
        subprocess.run(
            ["bitcoin-cli", *self._args(), "-rpcwait", "-rpcwaittimeout=60", "getblockcount"],
            check=True,
            capture_output=True,
        )
        return self.rpc

    @property
    def rpc(self) -> BitcoinRPC:
        return BitcoinRPC(f"http://127.0.0.1:{self.rpc_port}", self.datadir / "regtest" / ".cookie")

    def stop(self) -> None:
        if self._process is not None and self._process.poll() is None:
            self.rpc.call("stop")
            self._process.wait(timeout=60)
        self._process = None

    def __enter__(self) -> BitcoinRPC:
        return self.start()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.stop()
