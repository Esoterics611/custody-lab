"""Every attack in the demo's attack panel is refused, by the component the panel names."""

from collections.abc import Iterator

import pytest

from custody_lab.demo import attacks
from custody_lab.policy.engine import Decision, PolicyEngine, Status

REFUSALS = {  # the refusing component's own words
    "pay_an_address_not_on_the_whitelist": "attacker-address is not whitelisted",
    "pay_with_one_approval": "pending: 1 of 2 required approvals",
    "approve_your_own_instruction": "pending: 1 of 2 required approvals",
    "approve_with_a_key_not_on_the_list": "pending: 1 of 2 required approvals",
    "raise_the_amount_after_approval": "pending: 0 of 2 required approvals",
    "pay_the_same_instruction_twice": "denied: instruction already authorised",
    "drain_through_many_payments": "denied: velocity limit 20",
    "forge_an_authorisation": "not signed by the policy authority (Ed25519)",
    "forge_after_breaking_ed25519": "not signed by the policy authority (ML-DSA-65)",
    "replay_a_used_authorisation": "authorisation already used",
    "swap_the_transaction_after_approval": "differs from the authorised message",
    "use_an_expired_authorisation": "expired at",
    "sign_with_one_signer": "IncorrectNumberOfCommitments",
    "alter_a_signed_snapshot": "does not verify over the altered snapshot",
    "understate_a_client_balance": "it does not match",
    "edit_the_audit_log": "content does not match its hash",
}


@pytest.fixture(scope="module")
def attempts() -> Iterator[list[attacks.Attempt]]:
    yield attacks.run(lambda attempt: None)


def test_every_attack_is_refused_with_the_defence_s_own_reason(
    attempts: list[attacks.Attempt],
) -> None:
    assert [a.attack for a in attempts] == list(REFUSALS)
    for attempt in attempts:
        assert attempt.refused, attempt
        assert REFUSALS[attempt.attack] in attempt.reason, attempt
        assert attempt.group in attacks.GROUPS


def test_both_signers_asked_refuse_each_signer_attack(attempts: list[attacks.Attempt]) -> None:
    for attempt in attempts:
        if attempt.group == "signers" and attempt.attack != "sign_with_one_signer":
            assert "signer 1:" in attempt.reason and "signer 3:" in attempt.reason


def test_a_broken_defence_is_reported_as_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    def approve_everything(self: PolicyEngine, ins: object, approvals: object) -> Decision:
        return Decision(Status.APPROVED, "broken engine")

    monkeypatch.setattr(PolicyEngine, "_decide", approve_everything)
    shown: list[attacks.Attempt] = []

    attacks.run(shown.append)

    whitelist = next(a for a in shown if a.attack == "pay_an_address_not_on_the_whitelist")
    assert not whitelist.refused
    assert whitelist.reason == "the policy engine issued an authorisation"
    assert len(shown) == len(attacks.ATTACKS)  # the panel keeps going past a broken defence
