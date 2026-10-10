"""Watch the protocol: every message between the coordinator and the signers, round by round.

EDUCATIONAL, NOT PRODUCTION. ``run`` starts the demo's 2-of-3 signing cluster with a watch on the
coordinator's end of the pipes (``SigningCluster(watch=...)``) and plays every ceremony the demo
uses on it: private channels, key generation, signing, refresh, share repair, and signing with the
repaired share. No chain is needed.

Each round is reported as an ``Event`` listing every message that passed through the coordinator,
both ways: what it carries, whom it came from and whom it is for, its size, and its kind, which
says what the coordinator can read:

- *instruction*: the coordinator telling a signer which step to run, or a signer answering that it
  has; no protocol bytes;
- *clear*: public by design: channel public keys, commitments, proofs, public key packages, the
  signing package, signature shares;
- *sealed*: encrypted to one signer (``custody_lab.mpc.channel``); the coordinator relays it and
  cannot open it;
- *authorisation*: the policy engine's signed token, which every signer checks.

The signers never talk to each other directly. A message from one signer to another reaches the
coordinator as a reply in one round and goes on to its recipient as a request in the next; the
two carry the same bytes, and the same fingerprint.

Every message with bytes is also split into its fields (``parts``), following the Zcash
Foundation crate's serialization (postcard, frost-core 3.0.0: a 5-byte header holding the format
version and the CRC-32 of the ciphersuite name) and the demo's own formats. The fields are read
from each message as it passes and their sizes checked against its length, so a change of format
stops the run instead of drawing a wrong picture.
"""

from __future__ import annotations

import json
import os
import time
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import custody_frost as cf

from custody_lab.demo.pipeline import Event
from custody_lab.foundations import schnorr
from custody_lab.foundations.hashing import sha256, tagged_hash
from custody_lab.mpc import channel
from custody_lab.mpc.cluster import Calls, SigningCluster
from custody_lab.policy.audit import AuditLog
from custody_lab.policy.authorisation import AuthorityKey
from custody_lab.policy.engine import Policy, PolicyEngine
from custody_lab.reserves.snapshot import ATTESTATION_TAG

STEPS = {
    "channel_keys": "Each signer sends the coordinator its channel public key",
    "channel_peers": "The coordinator hands every signer the channel keys",
    "dkg1": "Key generation, round 1: each signer commits to a secret line",
    "dkg2": "Key generation, round 2: sealed sub-shares, signer to signer",
    "dkg3": "Key generation, round 3: each signer adds its sub-shares into a share",
    "commit": "Signing, round 1: signers 1 and 3 commit to one-time nonces",
    "sign": "Signing, round 2: each signer checks the authorisation and signs its part",
    "aggregate": "The coordinator adds the signature shares into one signature",
    "refresh1": "Refresh, round 1: each signer commits to a line through zero",
    "refresh2": "Refresh, round 2: sealed points on those lines, signer to signer",
    "refresh3": "Refresh, round 3: every share changes, the key does not",
    "lost": "Signer 2's share is erased, as a failed disk would erase it",
    "repair1": "Repair, round 1: helpers 1 and 3 split their help into sealed deltas",
    "repair2": "Repair, round 2: each helper sums its deltas into one sealed sigma",
    "repair3": "Repair, round 3: signer 2 adds the sigmas into its rebuilt share",
    "commit_again": "Signing again, round 1: signers 2 and 3 commit to nonces",
    "sign_again": "Signing again, round 2: the rebuilt share signs its part",
    "aggregate_again": "The coordinator adds the signature shares into one signature",
}

CEREMONIES = {
    "Private channels": ["channel_keys", "channel_peers"],
    "Key generation": ["dkg1", "dkg2", "dkg3"],
    "Signing": ["commit", "sign", "aggregate"],
    "Refresh": ["refresh1", "refresh2", "refresh3"],
    "Repair": ["lost", "repair1", "repair2", "repair3"],
    "Signing with the repaired share": ["commit_again", "sign_again", "aggregate_again"],
}
CEREMONY = {step: name for name, steps in CEREMONIES.items() for step in steps}

# What each round does, in plain words, for the dashboard. Numbers that depend on the run are on
# the messages, not here.
EXPLAIN = {
    "channel_keys": "Before any key exists, each signer makes a channel key pair, for sealing "
    "messages that only one other signer may read, and sends the public half to the coordinator. "
    "This is the one trust the demo still places in the coordinator: had it handed out keys of "
    "its own instead, it could open every sealed message that follows. In production these keys "
    "are provisioned out of band.",
    "channel_peers": "The coordinator hands every signer all three channel public keys. From now "
    "on, a signer seals a message for another signer under a key only those two can compute.",
    "dkg1": "Each signer picks a random line: a secret starting value and a random slope. It "
    "publishes a Feldman commitment to each (the value times the generator G, which fixes the "
    "value without revealing it) and a proof of knowledge of the starting value, so that no "
    "signer can publish a commitment it cannot open. Everything in this round is public by "
    "design.",
    "dkg2": "The coordinator forwards each round-1 package to the other two signers. Each signer "
    "checks the proofs, then computes, for each other signer, the height of its own line at that "
    "signer's number: a sub-share. Each sub-share is sealed to its recipient. A coordinator that "
    "could read them would see two points on every line, enough to rebuild every line and so the "
    "key; sealed, it relays 65 bytes it cannot open.",
    "dkg3": "The coordinator delivers each sealed sub-share to its recipient. Each signer opens "
    "its two, checks each against the sender's commitments, and adds them to its own line's "
    "height at its number: the sum is its share of the key. It reports the public key package: "
    "every signer's verifying share (its share times G) and the group public key. The coordinator "
    "checks that all three reports agree.",
    "commit": "Signers 1 and 3 each draw two one-time nonces and send only their commitments, the "
    "hiding commitment D and the binding commitment E, each a nonce times G. The nonces never "
    "leave the signer's process and are used once.",
    "sign": "The coordinator builds the signing package, both signers' commitments and the 32 "
    "bytes to sign, and sends it with the policy engine's authorisation. Each signer checks the "
    "authorisation's two signatures, its expiry, that it names exactly these 32 bytes and that it "
    "is unused, and only then returns a 32-byte signature share. The authorisation is most of the "
    "bytes in this round: its ML-DSA-65 signature is post-quantum, and large.",
    "aggregate": "The coordinator adds the two signature shares into one 64-byte BIP340 "
    "signature, with no secret of its own. Had a share been wrong, the signature would not verify "
    "and the coordinator would check each share against its signer's verifying share to name the "
    "culprit, as the key ceremonies show. Here the demo's from-scratch BIP340 verifier accepts it "
    "under the custody key.",
    "refresh1": "Each signer picks a new random line, this time starting at zero. A line through "
    "zero needs no commitment to its starting value, so each package carries one commitment fewer "
    "than in key generation and is 33 bytes shorter.",
    "refresh2": "As in key generation: the coordinator forwards the round-1 packages, and each "
    "signer sends every other signer the height of its zero line at that signer's number, "
    "sealed.",
    "refresh3": "Each signer opens its two sealed points and adds them, and its own, to its "
    "share. The three lines all start at zero, so the shares move and the key they share does "
    "not. The coordinator sends the current public key package with the sealed points; each "
    "signer returns the new one: three new verifying shares, the same group public key.",
    "lost": "The demo tells signer 2 to erase its share, as a failed disk without a backup would. "
    "This message is the demo's, not the protocol's.",
    "repair1": "Helpers 1 and 3 each compute a value from their own share, weighted for "
    "rebuilding signer 2's, and split it into two random-looking deltas that add up to it, one "
    "per helper, itself included. Every delta is sealed, even the one a helper keeps for itself, "
    "because it too passes through the coordinator.",
    "repair2": "Each helper adds the two deltas it received, one from each helper, into one "
    "sigma, sealed to signer 2. No delta or sigma on its own reveals anything about a helper's "
    "share.",
    "repair3": "Signer 2 opens the two sigmas and adds them: the sum is its lost share, rebuilt. "
    "The public key package it is given is unchanged, because the share is the same one it had.",
    "commit_again": "Signers 2 and 3 commit to fresh nonces, as in the first signing.",
    "sign_again": "Signer 2 signs its part with the rebuilt share, under a new authorisation; an "
    "authorisation is good for one signing only.",
    "aggregate_again": "The two shares add into a signature that verifies under the same custody "
    "key as before the refresh and the repair.",
}

# Signing rounds, each followed by the coordinator's aggregation, which sends no message.
_AGGREGATE = {"sign": "aggregate", "sign_again": "aggregate_again"}
# The cluster's rounds in the order run() makes them: step, signer method.
ROUNDS = [
    ("channel_keys", "channel_key"),
    ("channel_peers", "set_peers"),
    ("dkg1", "dkg1"),
    ("dkg2", "dkg2"),
    ("dkg3", "dkg3"),
    ("commit", "commit"),
    ("sign", "sign"),
    ("refresh1", "refresh1"),
    ("refresh2", "refresh2"),
    ("refresh3", "refresh3"),
    ("lost", "wipe"),
    ("repair1", "repair1"),
    ("repair2", "repair2"),
    ("repair3", "repair3"),
    ("commit_again", "commit"),
    ("sign_again", "sign"),
]

Parts = list[tuple[str, int]]
HEADER = ("header: format version and ciphersuite tag", 5)
TAG_BYTES = 16  # ChaCha20-Poly1305


def _now() -> datetime:
    return datetime.now(UTC)


def _checked(what: str, data: bytes, parts: Parts) -> Parts:
    expected = sum(n for _, n in parts)
    if expected != len(data):
        raise RuntimeError(f"{what}: {len(data)} bytes, but its fields add up to {expected}")
    return parts


def round1_parts(data: bytes) -> Parts:
    """A DKG or refresh round-1 package: Feldman commitments and a proof of knowledge."""
    count = data[5]
    return _checked(
        "round-1 package",
        data,
        [
            HEADER,
            ("number of commitments", 1),
            (f"{count} Feldman commitment{'s' if count > 1 else ''}, 33 bytes each", 33 * count),
            ("proof length", 1),
            ("proof of knowledge: R, x-only", 32),
            ("proof of knowledge: z", 32),
        ],
    )


def sealed_parts(data: bytes, inside: str, inside_bytes: int) -> Parts:
    return _checked(
        "sealed message",
        data,
        [
            ("nonce", channel.NONCE_BYTES),
            (f"ciphertext of {inside}", inside_bytes),
            ("authentication tag", TAG_BYTES),
        ],
    )


def public_key_package_parts(data: bytes) -> Parts:
    count = data[5]
    return _checked(
        "public key package",
        data,
        [
            HEADER,
            ("number of signers", 1),
            (f"{count} identifiers and verifying shares, 65 bytes each", 65 * count),
            ("group public key", 33),
            ("threshold", 2),
        ],
    )


def commitments_parts(data: bytes) -> Parts:
    return _checked(
        "nonce commitments",
        data,
        [HEADER, ("hiding nonce commitment D", 33), ("binding nonce commitment E", 33)],
    )


def signing_package_parts(data: bytes) -> Parts:
    count = data[5]
    return _checked(
        "signing package",
        data,
        [
            HEADER,
            ("number of signers", 1),
            (f"{count} identifiers and their nonce commitments, 103 bytes each", 103 * count),
            ("message length", 1),
            ("message: the 32 bytes to sign", 32),
        ],
    )


def authorisation_parts(data: bytes) -> Parts:
    fields = json.loads(data)
    pq, classical = len(fields["pq_signature"]), len(fields["signature"])
    return _checked(
        "authorisation",
        data,
        [
            ("ML-DSA-65 signature, in hex", pq),
            ("Ed25519 signature, in hex", classical),
            ("identifier, instruction digest, message, expiry, JSON", len(data) - pq - classical),
        ],
    )


def keys(public_key_package: bytes) -> dict[str, Any]:
    """The verifying shares and group public key a public key package records, read from its
    bytes; the group key is checked against the crate's own reading of the same package."""
    count = public_key_package[5]
    shares = {}
    for k in range(count):
        at = 6 + 65 * k
        identifier = int.from_bytes(public_key_package[at : at + 32], "big")
        shares[str(identifier)] = public_key_package[at + 32 : at + 65].hex()
    group = public_key_package[6 + 65 * count : 6 + 65 * count + 33]
    if set(shares) != {str(i) for i in range(1, count + 1)}:
        raise RuntimeError(f"public key package: identifiers {sorted(shares)}")
    if group[1:] != cf.group_public_key(public_key_package):
        raise RuntimeError("public key package: the group key is not where it should be")
    return {"verifying_shares": shares, "group_key": group.hex()}


def _fingerprint(data: bytes) -> str:
    """The first 12 hex digits of SHA-256: enough to see the same bytes arrive."""
    return sha256(data).hex()[:12]


def _signer(i: int) -> str:
    return f"signer {i}"


def _say(leg: str, signer: int, says: str) -> dict[str, Any]:
    ends = ("coordinator", _signer(signer))
    origin, destination = ends if leg == "out" else ends[::-1]
    return {
        "leg": leg,
        "signer": signer,
        "carries": says,
        "origin": origin,
        "destination": destination,
        "kind": "instruction",
        "bytes": 0,
        "parts": [],
    }


def _carry(
    leg: str, signer: int, carries: str, ends: tuple[str, str], kind: str, data: bytes, parts: Parts
) -> dict[str, Any]:
    return {
        "leg": leg,
        "signer": signer,
        "carries": carries,
        "origin": ends[0],
        "destination": ends[1],
        "kind": kind,
        "bytes": len(data),
        "parts": [list(p) for p in parts],
        "fingerprint": _fingerprint(data),
    }


SUB_SHARE = "a round-2 package: header and a 32-byte sub-share"
ZERO_POINT = "a round-2 package: header and a 32-byte point on a line through zero"
CHANNEL_KEY = [("X25519 public key", 32)]


def _relayed(i: int, what: str, inside: str, size: int, sealed: dict[int, bytes]) -> list[Any]:
    """Sealed messages from other signers, delivered to signer ``i``."""
    me = _signer(i)
    return [
        _carry(
            "out",
            i,
            f"signer {j}'s {what} for {'itself' if j == i else me}",
            (_signer(j), me),
            "sealed",
            data,
            sealed_parts(data, inside, size),
        )
        for j, data in sorted(sealed.items())
    ]


def _sealed_by(i: int, what: str, inside: str, size: int, sealed: dict[int, bytes]) -> list[Any]:
    """Sealed messages from signer ``i``, each for one signer."""
    return [
        _carry(
            "back",
            i,
            f"its {what} for {'itself' if k == i else _signer(k)}",
            (_signer(i), _signer(k)),
            "sealed",
            data,
            sealed_parts(data, inside, size),
        )
        for k, data in sorted(sealed.items())
    ]


def messages(method: str, calls: Calls, replies: dict[int, Any]) -> list[dict[str, Any]]:
    """The messages of one round, requests first: what the coordinator sent each signer, then
    what each signer sent back. ``calls`` and ``replies`` are as ``SigningCluster`` passes them
    to its watch."""
    out: list[dict[str, Any]] = []
    back: list[dict[str, Any]] = []
    for i, (_, args) in calls.items():
        me, reply = _signer(i), replies[i]
        to_me, from_me = ("coordinator", me), (me, "coordinator")

        match method:
            case "channel_key":
                out.append(_say("out", i, "send your channel public key"))
                part = _checked("channel key", reply, CHANNEL_KEY)
                ends = (me, "every signer")
                back.append(_carry("back", i, "its channel public key", ends, "clear", reply, part))
            case "set_peers":
                for j, key in args[0].items():
                    carries = f"signer {j}'s channel public key"
                    part = _checked("channel key", key, CHANNEL_KEY)
                    out.append(_carry("out", i, carries, (_signer(j), me), "clear", key, part))
                back.append(_say("back", i, "done"))
            case "dkg1" | "refresh1":
                count, threshold = args
                name = "key generation" if method == "dkg1" else "refresh"
                out.append(_say("out", i, f"start {name}: {count} signers, any {threshold} sign"))
                ends, part = (me, "every other signer"), round1_parts(reply)
                back.append(_carry("back", i, "its round-1 package", ends, "clear", reply, part))
            case "dkg2" | "refresh2":
                for j, package in args[0].items():
                    carries, part = f"signer {j}'s round-1 package", round1_parts(package)
                    out.append(_carry("out", i, carries, (_signer(j), me), "clear", package, part))
                if method == "dkg2":
                    back += _sealed_by(i, "sub-share", SUB_SHARE, 37, reply)
                else:
                    back += _sealed_by(i, "point", ZERO_POINT, 37, reply)
            case "dkg3" | "refresh3":
                if method == "dkg3":
                    out += _relayed(i, "sub-share", SUB_SHARE, 37, args[0])
                else:
                    out += _relayed(i, "point", ZERO_POINT, 37, args[0])
                    current = "the current public key package"
                    part = public_key_package_parts(args[1])
                    out.append(_carry("out", i, current, to_me, "clear", args[1], part))
                carries, part = (
                    "the public key package it computed",
                    public_key_package_parts(reply),
                )
                back.append(_carry("back", i, carries, from_me, "clear", reply, part))
            case "commit":
                out.append(_say("out", i, "commit to two one-time nonces"))
                carries, part = "its nonce commitments", commitments_parts(reply)
                back.append(_carry("back", i, carries, from_me, "clear", reply, part))
            case "sign":
                package, token = args[0], args[1]
                part = signing_package_parts(package)
                out.append(_carry("out", i, "the signing package", to_me, "clear", package, part))
                carries, part = "the policy engine's authorisation", authorisation_parts(token)
                ends = ("policy engine", me)
                out.append(_carry("out", i, carries, ends, "authorisation", token, part))
                part = _checked("signature share", reply, [("signature share z", 32)])
                back.append(_carry("back", i, "its signature share", from_me, "clear", reply, part))
            case "wipe":
                out.append(_say("out", i, "erase your share (the demo's disk failure)"))
                back.append(_say("back", i, "done"))
            case "repair1":
                helpers, participant = args
                with_whom = " and ".join(str(h) for h in helpers)
                says = f"help rebuild signer {participant}'s share, with signers {with_whom}"
                out.append(_say("out", i, says))
                back += _sealed_by(i, "delta", "a 32-byte delta", 32, reply)
            case "repair2":
                out += _relayed(i, "delta", "a 32-byte delta", 32, args[0])
                back += _sealed_by(i, "sigma", "a 32-byte sigma", 32, {args[1]: reply})
            case "repair3":
                out += _relayed(i, "sigma", "a 32-byte sigma", 32, args[0])
                part = public_key_package_parts(args[1])
                out.append(
                    _carry("out", i, "the public key package", to_me, "clear", args[1], part)
                )
                back.append(_say("back", i, "done"))
            case _:
                raise RuntimeError(f"no description for the signers' {method!r} round")
    return out + back


def run(emit: Callable[[Event], None]) -> dict[str, Any]:
    """Play every ceremony on a watched cluster; return the totals the coordinator relayed."""
    started = time.monotonic()
    rounds = iter(ROUNDS)
    current = next(iter(STEPS))
    relayed: Counter[str] = Counter()

    def report(step: str, status: str, **detail: Any) -> None:
        nonlocal current
        current = step
        at_ms = round((time.monotonic() - started) * 1000)
        emit(Event(step, status, STEPS[step], detail, at_ms))

    def begin(step: str) -> None:
        report(step, "running", ceremony=CEREMONY[step], explanation=EXPLAIN[step])

    def watch(calls: Calls, replies: dict[int, Any] | None) -> None:
        methods = {method for method, _ in calls.values()}
        if replies is None:
            step, method = next(rounds)
            if methods != {method}:
                raise RuntimeError(f"expected the {method!r} round, saw {sorted(methods)}")
            begin(step)
            return
        (method,) = methods
        hops = messages(method, calls, replies)
        for m in hops:
            relayed[m["kind"]] += m["bytes"]
        relayed["messages"] += len(hops)
        detail: dict[str, Any] = {"messages": hops}
        if method in ("dkg3", "refresh3"):
            detail |= keys(next(iter(replies.values())))
        if method == "repair3":
            detail |= keys(next(iter(calls.values()))[1][1])
        step = current
        report(step, "done", **detail)
        if step in _AGGREGATE:
            begin(_AGGREGATE[step])

    engine = PolicyEngine(Policy({}, {}), AuthorityKey.generate(), AuditLog(_now), _now)
    signatures: list[bool] = []

    def sign(cluster: SigningCluster, statement: bytes, signers: list[int]) -> None:
        token = engine.authorise_attestation(statement)
        message = tagged_hash(ATTESTATION_TAG, statement)
        signature = cluster.sign(message, signers, token.to_bytes(), taproot=True)
        valid = schnorr.verify(message, cluster.taproot_output_key(), signature)
        signatures.append(valid)
        report(
            current,
            "done",
            signers=signers,
            signature=signature.hex(),
            signature_valid=valid,
            custody_key=cluster.taproot_output_key().hex(),
        )

    try:
        with SigningCluster(2, 3, engine.authority_public_key, watch=watch) as cluster:
            report(
                "channel_peers",
                "done",
                processes={"coordinator": os.getpid()}
                | {_signer(i): pid for i, pid in cluster.holders().items()},
            )
            group = cluster.dkg()
            sign(cluster, b"proof of control, before the refresh", [1, 3])
            cluster.refresh()
            cluster.wipe(2)
            cluster.repair(2, [1, 3])
            sign(cluster, b"proof of control, after the repair", [2, 3])
            unchanged = cf.group_public_key(cluster.public_key_package) == group
    except Exception as exc:
        report(current, "failed", error=f"{type(exc).__name__}: {exc}")
        raise
    return {
        "rounds": len(ROUNDS),
        "messages": relayed["messages"],
        "clear_bytes": relayed["clear"],
        "sealed_bytes": relayed["sealed"],
        "authorisation_bytes": relayed["authorisation"],
        "signatures_valid": signatures,
        "group_key_unchanged": unchanged,
    }
