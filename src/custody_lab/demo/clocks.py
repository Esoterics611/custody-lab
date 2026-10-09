"""Clocks: an authorisation's sixty seconds, and signers whose clocks have been set back.

EDUCATIONAL, NOT PRODUCTION. ``run`` starts two sets of 2-of-3 signers, identical except where they
read the time, and a time authority in its own process, then plays seven steps against the real
signer processes, reporting each as an ``Event``. No chain is needed: as in the attack panel, a
32-byte hash of the instruction stands in for a transaction's sighash.

The policy engine issues every authorisation with a 60-second life, and a signer refuses one it
checks after that (manual/attack-vectors.md, vector 4.4; chapter 10, Drift).

1. The first set of signers reads its machines' clocks. The second set was given the time
   authority's public key when it started, and reads only the time authority's signed time.
2. An authorisation used at once is signed with nearly all of its 60 seconds left.
3. An authorisation the coordinator held back for five minutes is refused: it expired four minutes
   ago.
4. An attacker sets signer 1's clock back five minutes. Signer 1 accepts a held-back authorisation;
   signer 3 refuses it, so there is no signature.
5. The attacker sets signer 3's clock back too, as one false time server answering both machines
   would. Both accept, and the signature is valid: broadcast, it would pay.
6. The second set of signers, their machines' clocks set back the same way, refuses: the time
   authority's signed time says the authorisation expired four minutes ago.
7. The coordinator asks the time authority to sign the time for a nonce of its own choosing, and
   presents that signed time with an authorisation. Each signer refuses it: it answers another
   nonce. Without that check it would be accepted, which the step shows.

Each step uses its own authorisation, because a signer records an authorisation as used once it
has accepted it, even when the other signer refused and no signature resulted.

The demo does not wait five minutes. A held-back authorisation is issued by a policy engine whose
clock reads five minutes earlier, as in the attack panel; every other clock reads the true time.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from typing import Any

from custody_lab.demo.attacks import TTL, _Lab, _sighash
from custody_lab.demo.ceremonies import reason
from custody_lab.demo.parties import TimeService
from custody_lab.demo.pipeline import Event
from custody_lab.foundations import schnorr
from custody_lab.mpc.cluster import SigningCluster
from custody_lab.policy import signed_time
from custody_lab.policy.authorisation import Authorisation, AuthorityKey

STEPS = {
    "setup": "Start two sets of signers and a time authority",
    "in_time": "An authorisation used at once is signed",
    "too_late": "An authorisation held back for five minutes is refused",
    "one_clock": "Signer 1's clock set back: signer 3 still refuses",
    "both_clocks": "Both signers' clocks set back: the expired authorisation is signed",
    "attested": "Signers on signed time refuse it, whatever their clocks say",
    "replayed": "A signed time for another nonce is refused",
}
HELD_BACK = timedelta(minutes=5)
SIGNERS = [1, 3]


def _now() -> datetime:
    return datetime.now(UTC)


def _hms(moment: datetime) -> str:
    return f"{moment:%H:%M:%S} UTC"


class _Relay:
    """This process's route to the time authority. It keeps each signed time it passes on, in the
    order the signers asked, and passes on ``substitute`` instead when one is set, as a coordinator
    replaying a recorded signed time would."""

    def __init__(self, service: TimeService) -> None:
        self.public_key = service.public_key
        self._service = service
        self.relayed: list[signed_time.SignedTime] = []
        self.substitute: bytes | None = None

    def stamp(self, nonce: bytes) -> bytes:
        if self.substitute is not None:
            return self.substitute
        signed = self._service.stamp(nonce)
        self.relayed.append(signed_time.SignedTime.from_bytes(signed))
        return signed


def _lifetime(
    token: Authorisation, readings: dict[int, datetime], read_from: str
) -> dict[str, Any]:
    """Where the true time and each signer's reading fall in ``token``'s life, in seconds from
    its issue: the dashboard draws it as a bar."""
    issued = token.expires_at - TTL

    def since(moment: datetime) -> float:
        return round((moment - issued).total_seconds(), 2)

    return {
        "life_s": TTL.total_seconds(),
        "true_s": since(_now()),
        "readings_s": {str(i): since(t) for i, t in readings.items()},
        "read_from": read_from,
    }


def _try_sign(cluster: SigningCluster, message: bytes, token: Authorisation) -> str:
    """Ask signers 1 and 3 to sign and verify the result; return their refusal, or "" if signed."""
    try:
        signature = cluster.sign(message, SIGNERS, token.to_bytes(), taproot=True)
    except (RuntimeError, ValueError) as refused:
        return reason(refused)
    if not schnorr.verify(message, cluster.taproot_output_key(), signature):
        raise RuntimeError("the signature does not verify")
    return ""


def _times(token: Authorisation) -> dict[str, str]:
    return {
        "issued_at": _hms(token.expires_at - TTL),
        "expires_at": _hms(token.expires_at),
        "true_time": _hms(_now()),
    }


def run(emit: Callable[[Event], None]) -> dict[str, Any]:
    """Play the seven steps; return which ones produced a signature."""
    started = time.monotonic()
    current = next(iter(STEPS))

    def report(step: str, status: str, **detail: Any) -> None:
        nonlocal current
        current = step
        at_ms = round((time.monotonic() - started) * 1000)
        emit(Event(step, status, STEPS[step], detail, at_ms))

    authority = AuthorityKey.generate()
    signed: list[str] = []
    parties = ExitStack()
    report("setup", "running")
    try:
        service = parties.enter_context(TimeService())
        relay = _Relay(service)
        own = parties.enter_context(SigningCluster(2, 3, authority.public_bytes()))
        attested = parties.enter_context(SigningCluster(2, 3, authority.public_bytes(), relay))
        own.dkg()
        attested.dkg()
        lab = _Lab(own, authority)
        held_back = lab.engine(clock=lambda: _now() - HELD_BACK)
        report(
            "setup",
            "done",
            own_clock_signers=[{"signer": i, "pid": p} for i, p in own.holders().items()],
            signed_time_signers=[{"signer": i, "pid": p} for i, p in attested.holders().items()],
            time_authority_pid=service.pid,
            coordinator_pid=os.getpid(),
            authorisation_life=f"{TTL.total_seconds():g} seconds",
        )

        def authorise(late: bool) -> tuple[bytes, Authorisation]:
            """An approved 0.85 BTC settlement to the exchange and its authorisation, issued now or,
            with ``late``, five minutes ago."""
            ins = lab.instruction()
            engine = held_back if late else lab.engine()
            token = engine.authorise(ins, lab.approve(ins, "bob", "carol"), _sighash(ins))
            return _sighash(ins), token

        report("in_time", "running")
        message, token = authorise(late=False)
        refusal = _try_sign(own, message, token)
        if refusal:
            raise RuntimeError(f"an authorisation used at once was refused: {refusal}")
        signed.append("in_time")
        done = _now()  # the signers checked the expiry before this
        report(
            "in_time",
            "done",
            **_times(token),
            time_left=f"{(token.expires_at - done).total_seconds():.2f} s of "
            f"{TTL.total_seconds():g} s, once signed",
            signers=SIGNERS,
            signature_valid=True,
            lifetime=_lifetime(token, dict.fromkeys(SIGNERS, done), "own clocks"),
        )

        report("too_late", "running")
        message, token = authorise(late=True)
        refusal = _try_sign(own, message, token)
        report(
            "too_late",
            "done",
            **_times(token),
            held_back_for="five minutes, by the coordinator",
            refusal=refusal,
            lifetime=_lifetime(token, dict.fromkeys(SIGNERS, _now()), "own clocks"),
        )

        report("one_clock", "running")
        own.set_clock(1, -HELD_BACK)
        message, token = authorise(late=True)
        refusal = _try_sign(own, message, token)
        slow = _now() - HELD_BACK
        report(
            "one_clock",
            "done",
            **_times(token),
            signer_1_clock=f"{_hms(slow)}, set back five minutes",
            signer_3_clock=f"{_hms(_now())}, correct",
            refusal=refusal,
            signature="none: one signer is not a quorum",
            lifetime=_lifetime(token, {1: slow, 3: _now()}, "own clocks"),
        )

        report("both_clocks", "running")
        own.set_clock(3, -HELD_BACK)
        message, token = authorise(late=True)
        refusal = _try_sign(own, message, token)
        if refusal:
            raise RuntimeError(f"signers with clocks set back refused: {refusal}")
        signed.append("both_clocks")
        slow = _now() - HELD_BACK
        report(
            "both_clocks",
            "done",
            **_times(token),
            signer_clocks=f"{_hms(slow)}, both set back five minutes",
            signers=SIGNERS,
            signature_valid=True,
            result="a valid signature on a payment whose authorisation expired four minutes ago; "
            "broadcast, it would pay",
            lifetime=_lifetime(token, dict.fromkeys(SIGNERS, slow), "own clocks"),
        )

        report("attested", "running")
        for i in SIGNERS:
            attested.set_clock(i, -HELD_BACK)
        message, token = authorise(late=True)
        relay.relayed.clear()
        refusal = _try_sign(attested, message, token)
        readings = {i: s.time for i, s in zip(SIGNERS, relay.relayed, strict=True)}
        report(
            "attested",
            "done",
            **_times(token),
            signer_clocks=f"{_hms(_now() - HELD_BACK)}, both set back five minutes, not read",
            signed_times={f"signer {i}": _hms(t) for i, t in readings.items()},
            refusal=refusal,
            lifetime=_lifetime(token, readings, "the time authority's signed time"),
        )

        report("replayed", "running")
        message, token = authorise(late=False)
        recorded = signed_time.SignedTime.from_bytes(service.stamp(signed_time.new_nonce()))
        relay.substitute = recorded.to_bytes()
        refusal = _try_sign(attested, message, token)
        relay.substitute = None
        if not refusal:
            raise RuntimeError("the signers accepted a signed time for another nonce")
        # what a signer that checked only the time authority's signature would conclude
        unbound = signed_time.read(recorded, service.public_key, recorded.nonce)
        report(
            "replayed",
            "done",
            **_times(token),
            recorded_signed_time=f"{_hms(recorded.time)}, for a nonce the coordinator chose",
            refusal=refusal,
            without_the_nonce_check=f"the signature verifies and {_hms(unbound)} is before the "
            f"expiry at {_hms(token.expires_at)}: it would be accepted",
        )
    except Exception as exc:
        report(current, "failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        parties.close()
    return {"signed": signed}
