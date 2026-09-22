import pytest

from app.models.artifact import (
    ActionType,
    RiskLevel,
)
from app.safety.policy import (
    PolicyViolation,
    SafetyPolicy,
)


def test_localhost_is_allowed():
    policy = SafetyPolicy()

    policy.check_url(
        "http://127.0.0.1:5000"
    )


def test_localhost_name_is_allowed():
    policy = SafetyPolicy()

    policy.check_url(
        "http://localhost:5000"
    )


def test_external_host_is_blocked():
    policy = SafetyPolicy()

    with pytest.raises(PolicyViolation):
        policy.check_url(
            "https://example.com"
        )


def test_invalid_scheme_is_blocked():
    policy = SafetyPolicy()

    with pytest.raises(PolicyViolation):
        policy.check_url(
            "file:///etc/passwd"
        )


def test_safe_action_is_allowed():
    policy = SafetyPolicy()

    policy.check_action(
        ActionType.CLICK,
        RiskLevel.SAFE,
    )


def test_risky_action_is_blocked_by_default():
    policy = SafetyPolicy()

    with pytest.raises(PolicyViolation):
        policy.check_action(
            ActionType.CLICK,
            RiskLevel.RISKY,
        )


def test_risky_action_can_be_explicitly_allowed():
    policy = SafetyPolicy(
        allow_risky_actions=True
    )

    policy.check_action(
        ActionType.CLICK,
        RiskLevel.RISKY,
    )

def test_allowed_route_is_accepted():
    policy = SafetyPolicy()

    policy.check_url(
        "http://127.0.0.1:5000/member/search"
    )


def test_unapproved_route_is_blocked():
    policy = SafetyPolicy()

    with pytest.raises(PolicyViolation):
        policy.check_url(
            "http://127.0.0.1:5000/admin"
        )