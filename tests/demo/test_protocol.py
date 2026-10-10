"""Watching the protocol: every round of every ceremony, as the coordinator relays it. No chain.

The message sizes asserted here were observed on the Zcash Foundation crate (frost-core 3.0.0) and
the demo's channel; ``protocol.py`` also checks every message's fields against its length."""

from collections import Counter
from typing import Any

import pytest

from custody_lab.demo import protocol

Done = dict[str, dict[str, Any]]


@pytest.fixture(scope="module")
def run() -> tuple[Done, dict[str, Any]]:
    events: list[Any] = []
    summary = protocol.run(events.append)
    done: Done = {}
    for e in events:  # a step can report done twice; the details merge, as on the dashboard
        if e.status == "done":
            done.setdefault(e.step, {}).update(e.detail)
    assert list(done) == list(protocol.STEPS)
    return done, summary


def _messages(done: Done, step: str, leg: str, kind: str | None = None) -> list[dict[str, Any]]:
    return [
        m
        for m in done[step].get("messages", [])
        if m["leg"] == leg and (kind is None or m["kind"] == kind)
    ]


def test_every_message_is_split_into_fields_that_add_up_to_its_length(
    run: tuple[Done, dict[str, Any]],
) -> None:
    done, summary = run
    every = [m for step in done.values() for m in step.get("messages", [])]
    assert len(every) == summary["messages"]
    for m in every:
        assert sum(n for _, n in m["parts"]) == m["bytes"], m["carries"]
        assert (m["kind"] == "instruction") == (m["bytes"] == 0)


def test_only_sub_shares_refresh_points_deltas_and_sigmas_travel_sealed(
    run: tuple[Done, dict[str, Any]],
) -> None:
    done, _ = run
    sealed = {s for s in done if any(m["kind"] == "sealed" for m in done[s].get("messages", []))}
    assert sealed == {"dkg2", "dkg3", "refresh2", "refresh3", "repair1", "repair2", "repair3"}
    sizes = {m["bytes"] for s in sealed for m in done[s]["messages"] if m["kind"] == "sealed"}
    assert sizes == {65, 60}  # 12-byte nonce + 37-byte round-2 package or 32-byte scalar + tag


@pytest.mark.parametrize(
    ("sent", "delivered"),
    [("dkg2", "dkg3"), ("refresh2", "refresh3"), ("repair1", "repair2"), ("repair2", "repair3")],
)
def test_the_coordinator_delivers_each_sealed_message_unchanged_to_its_recipient(
    run: tuple[Done, dict[str, Any]], sent: str, delivered: str
) -> None:
    done, _ = run

    def routes(messages: list[dict[str, Any]]) -> Counter[tuple[str, str, str]]:
        return Counter((m["origin"], m["destination"], m["fingerprint"]) for m in messages)

    replies = _messages(done, sent, "back", "sealed")
    assert replies and routes(replies) == routes(_messages(done, delivered, "out", "sealed"))
    assert all(f"signer {m['signer']}" == m["destination"] for m in done[delivered]["messages"]
               if m["leg"] == "out" and m["kind"] == "sealed")  # fmt: skip


def test_round_one_packages_reach_every_other_signer_as_sent(
    run: tuple[Done, dict[str, Any]],
) -> None:
    done, _ = run
    for first, second, size in (("dkg1", "dkg2", 137), ("refresh1", "refresh2", 104)):
        sent = {m["origin"]: m["fingerprint"] for m in _messages(done, first, "back")}
        received = _messages(done, second, "out", "clear")
        assert len(received) == 6 and all(m["bytes"] == size for m in received)
        assert all(m["fingerprint"] == sent[m["origin"]] for m in received)
        assert all(m["origin"] != m["destination"] for m in received)


def test_refresh_moves_every_share_and_repair_restores_signer_2s(
    run: tuple[Done, dict[str, Any]],
) -> None:
    done, summary = run
    generated, refreshed = done["dkg3"], done["refresh3"]
    assert generated["group_key"] == refreshed["group_key"] == done["repair3"]["group_key"]
    old, new = generated["verifying_shares"], refreshed["verifying_shares"]
    assert all(old[i] != new[i] for i in ("1", "2", "3"))
    assert done["repair3"]["verifying_shares"] == new
    assert summary["group_key_unchanged"]


def test_both_signatures_verify_under_one_custody_key(run: tuple[Done, dict[str, Any]]) -> None:
    done, summary = run
    assert summary["signatures_valid"] == [True, True]
    first, second = done["aggregate"], done["aggregate_again"]
    assert (first["signers"], second["signers"]) == ([1, 3], [2, 3])
    assert first["custody_key"] == second["custody_key"]
    assert len(bytes.fromhex(first["signature"])) == 64


def test_the_authorisation_carries_most_of_the_signing_bytes(
    run: tuple[Done, dict[str, Any]],
) -> None:
    done, summary = run
    token = _messages(done, "sign", "out", "authorisation")[0]
    assert token["origin"] == "policy engine"
    assert token["parts"][0] == ["ML-DSA-65 signature, in hex", 2 * 3309]  # FIPS 204
    assert summary["authorisation_bytes"] > summary["clear_bytes"] + summary["sealed_bytes"]
    shares = _messages(done, "sign", "back")
    assert [m["bytes"] for m in shares] == [32, 32]


def test_signer_processes_are_not_the_coordinator(run: tuple[Done, dict[str, Any]]) -> None:
    done, _ = run
    processes = done["channel_peers"]["processes"]
    assert len(set(processes.values())) == 4


def test_a_change_of_format_stops_the_run() -> None:
    with pytest.raises(RuntimeError, match="fields add up to"):
        protocol.commitments_parts(bytes(72))
