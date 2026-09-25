"""FIX 5.0 SP2 order flow between the custody client and a toy exchange, over asyncio TCP.

EDUCATIONAL, NOT PRODUCTION. Messages are FIX 5.0 SP2 application messages on the FIXT.1.1
session layer:
- BeginString is ``FIXT.1.1``.
- Logon carries DefaultApplVerID(1137)=9 (FIX50SP2).

``simplefix`` encodes and parses messages; it computes BodyLength and CheckSum. The session layer
here is the minimum the demo needs:
- Logon, NewOrderSingle, ExecutionReport and Logout, with MsgSeqNum checked on receipt.
- No heartbeats, resend requests or gap fill.
- The toy exchange fills every limit order in full at its limit price.

Execution reports follow the house FIX 5.0 SP2 rules of engagement (fix-client ``ROE.md``):
LastQty/LastPx and TradeDate/TransactTime on each fill, and no AvgPx (optional in FIX 5.0 SP2);
any average is the receiver's arithmetic. Execution reports are the only input to settlement; the
rest of the system never sees FIX.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import itertools
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

import simplefix

BEGIN_STRING = "FIXT.1.1"
DEFAULT_APPL_VER_ID = "9"  # FIX50SP2
LOGON_FIELDS = [(98, "0"), (108, "30"), (1137, DEFAULT_APPL_VER_ID)]  # EncryptMethod, HeartBtInt
CLIENT_ID, EXCHANGE_ID = "CUSTODY-CLIENT", "TOY-EXCHANGE"
SIDE_CODES = {"buy": "1", "sell": "2"}
SIDES = {v: k for k, v in SIDE_CODES.items()}


@dataclass(frozen=True)
class Order:
    cl_ord_id: str
    symbol: str  # e.g. "BTC-USD"
    side: str  # "buy" or "sell"
    qty: Decimal
    price: Decimal


@dataclass(frozen=True)
class Fill:
    exec_id: str
    cl_ord_id: str
    symbol: str
    side: str
    qty: Decimal
    price: Decimal


def _decimal(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _utc_timestamp() -> str:
    """UTCTimestamp with milliseconds, e.g. 20260924-17:29:10.072."""
    return datetime.now(UTC).strftime("%Y%m%d-%H:%M:%S.%f")[:-3]


class Session:
    """One side of a FIX session over an asyncio stream, with sequence-number checking."""

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        sender: str,
        target: str,
        transcript: list[str],
    ) -> None:
        self._reader, self._writer = reader, writer
        self._sender, self._target = sender, target
        self._parser = simplefix.FixParser()
        self._out_seq, self._in_seq = itertools.count(1), 1
        self._transcript = transcript

    async def send(self, msg_type: str, fields: Sequence[tuple[int, str]]) -> None:
        msg = simplefix.FixMessage()
        msg.append_pair(8, BEGIN_STRING, header=True)
        msg.append_pair(35, msg_type, header=True)
        msg.append_pair(49, self._sender, header=True)
        msg.append_pair(56, self._target, header=True)
        msg.append_pair(34, next(self._out_seq), header=True)
        msg.append_pair(52, _utc_timestamp(), header=True)
        for tag, value in fields:
            msg.append_pair(tag, value)
        raw = msg.encode()
        self._transcript.append(raw.replace(b"\x01", b"|").decode())
        self._writer.write(raw)
        await self._writer.drain()

    async def receive(self) -> simplefix.FixMessage:
        while (msg := self._parser.get_message()) is None:
            data = await self._reader.read(4096)
            if not data:
                raise ConnectionError("session closed by peer")
            self._parser.append_buffer(data)
        seq = int(msg.get(34))
        if seq != self._in_seq:
            raise ValueError(f"MsgSeqNum {seq}, expected {self._in_seq}")
        self._in_seq += 1
        return msg

    async def close(self) -> None:
        self._writer.close()
        await self._writer.wait_closed()


class ToyExchange:
    """Accepts one client session and fills each NewOrderSingle in full at its limit price."""

    def __init__(self, transcript: list[str]) -> None:
        self._transcript = transcript
        self._exec_ids = (f"E{n:04d}" for n in itertools.count(1))
        self._server: asyncio.Server | None = None

    async def start(self) -> int:
        self._server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        port: int = self._server.sockets[0].getsockname()[1]
        return port

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        session = Session(reader, writer, EXCHANGE_ID, CLIENT_ID, self._transcript)
        try:
            while True:
                msg = await session.receive()
                msg_type = msg.get(35).decode()
                if msg_type == "A":
                    await session.send("A", LOGON_FIELDS)
                elif msg_type == "D":
                    await session.send("8", self._fill(msg))
                elif msg_type == "5":
                    await session.send("5", [])
                    return
        finally:
            await session.close()

    def _fill(self, order: simplefix.FixMessage) -> list[tuple[int, str]]:
        exec_id = next(self._exec_ids)
        qty, price = order.get(38).decode(), order.get(44).decode()
        return [
            (37, f"O-{exec_id}"),  # OrderID
            (11, order.get(11).decode()),  # ClOrdID
            (17, exec_id),  # ExecID
            (150, "F"),  # ExecType: trade
            (39, "2"),  # OrdStatus: filled
            (55, order.get(55).decode()),
            (54, order.get(54).decode()),
            (38, qty),
            (32, qty),  # LastQty: filled in full
            (31, price),  # LastPx: at the limit
            (151, "0"),  # LeavesQty
            (14, qty),  # CumQty
            (75, datetime.now(UTC).strftime("%Y%m%d")),  # TradeDate
            (60, _utc_timestamp()),  # TransactTime
        ]


async def _run_client(port: int, orders: Sequence[Order], transcript: list[str]) -> list[Fill]:
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    session = Session(reader, writer, CLIENT_ID, EXCHANGE_ID, transcript)
    await session.send("A", LOGON_FIELDS)
    if (await session.receive()).get(35) != b"A":
        raise ConnectionError("logon rejected")
    fills = []
    for order in orders:
        await session.send(
            "D",
            [
                (11, order.cl_ord_id),
                (55, order.symbol),
                (54, SIDE_CODES[order.side]),
                (60, _utc_timestamp()),  # TransactTime
                (38, _decimal(order.qty)),
                (40, "2"),  # OrdType: limit
                (44, _decimal(order.price)),
            ],
        )
        report = await session.receive()
        if report.get(150) != b"F":
            raise ValueError(f"order {order.cl_ord_id} not filled")
        fills.append(
            Fill(
                report.get(17).decode(),
                report.get(11).decode(),
                report.get(55).decode(),
                SIDES[report.get(54).decode()],
                Decimal(report.get(32).decode()),
                Decimal(report.get(31).decode()),
            )
        )
    await session.send("5", [])
    await session.receive()
    await session.close()
    return fills


def trade(orders: Sequence[Order]) -> tuple[list[Fill], list[str]]:
    """Run one client session against a fresh toy exchange; return fills and the FIX transcript
    (both directions, in order, with SOH shown as ``|``)."""
    transcript: list[str] = []

    async def main() -> list[Fill]:
        exchange = ToyExchange(transcript)
        port = await exchange.start()
        try:
            return await _run_client(port, orders, transcript)
        finally:
            await exchange.stop()

    try:
        asyncio.get_running_loop()
    except RuntimeError:  # no loop in this thread: the usual case
        return asyncio.run(main()), transcript
    # Called from inside an event loop (a notebook, an async server): run on a worker thread.
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, main()).result(), transcript
