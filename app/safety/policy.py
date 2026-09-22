from dataclasses import dataclass, field
from typing import Set
from urllib.parse import urlparse

from app.models.artifact import ActionType, RiskLevel


class PolicyViolation(Exception):
    """Raised when an automation action violates the safety policy."""


@dataclass
class SafetyPolicy:
    allowed_hosts: Set[str] = field(
        default_factory=lambda: {
            "127.0.0.1",
            "localhost",
        }
    )

    allowed_routes: Set[str] = field(
        default_factory=lambda: {
            "/",
            "/member/search",
        }
    )

    allowed_actions: Set[ActionType] = field(
        default_factory=lambda: {
            ActionType.NAVIGATE,
            ActionType.CLICK,
            ActionType.TYPE,
            ActionType.EXTRACT,
            ActionType.WAIT,
        }
    )

    allow_risky_actions: bool = False

    def check_url(self, url: str) -> None:
        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            raise PolicyViolation(
                f"URL scheme is not allowed: {parsed.scheme}"
            )

        if parsed.hostname not in self.allowed_hosts:
            raise PolicyViolation(
                f"Host is not allowlisted: {parsed.hostname}"
            )

        path = parsed.path or "/"

        if path not in self.allowed_routes:
            raise PolicyViolation(
                f"Route is not allowlisted: {path}"
            )

    def check_action(
        self,
        action: ActionType,
        risk: RiskLevel = RiskLevel.SAFE,
    ) -> None:

        if action not in self.allowed_actions:
            raise PolicyViolation(
                f"Action type is not allowed: {action.value}"
            )

        if (
            risk == RiskLevel.RISKY
            and not self.allow_risky_actions
        ):
            raise PolicyViolation(
                "Risky action requires human approval."
            )