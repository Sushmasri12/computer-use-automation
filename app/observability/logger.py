import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


SENSITIVE_KEYS = {
    "password",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "secret",
    "api_key",
    "credential",
}


def redact_text(text: str) -> str:
    patterns = [
        (
            r"(?i)(password\s*[:=]\s*)\S+",
            r"\1[REDACTED]",
        ),
        (
            r"(?i)(token\s*[:=]\s*)\S+",
            r"\1[REDACTED]",
        ),
        (
            r"(?i)(access[_-]?token\s*[:=]\s*)\S+",
            r"\1[REDACTED]",
        ),
        (
            r"(?i)(refresh[_-]?token\s*[:=]\s*)\S+",
            r"\1[REDACTED]",
        ),
        (
            r"(?i)(api[_-]?key\s*[:=]\s*)\S+",
            r"\1[REDACTED]",
        ),
        (
            r"(?i)(authorization\s*[:=]\s*)\S+",
            r"\1[REDACTED]",
        ),
        (
            r"(?i)(secret\s*[:=]\s*)\S+",
            r"\1[REDACTED]",
        ),
        (
            r"(?i)(credential\s*[:=]\s*)\S+",
            r"\1[REDACTED]",
        ),
    ]

    result = text

    for pattern, replacement in patterns:
        result = re.sub(
            pattern,
            replacement,
            result,
        )

    return result


def redact_value(
    key: str,
    value: Any,
) -> Any:

    if key.lower() in SENSITIVE_KEYS:
        return "[REDACTED]"

    if isinstance(value, dict):
        return redact_dict(value)

    if isinstance(value, list):
        return [
            redact_item(item)
            for item in value
        ]

    if isinstance(value, str):
        return redact_text(value)

    return value


def redact_item(value: Any) -> Any:
    if isinstance(value, dict):
        return redact_dict(value)

    if isinstance(value, list):
        return [
            redact_item(item)
            for item in value
        ]

    if isinstance(value, str):
        return redact_text(value)

    return value


def redact_dict(
    data: Dict[str, Any],
) -> Dict[str, Any]:

    return {
        key: redact_value(key, value)
        for key, value in data.items()
    }


class RunLogger:
    def __init__(
        self,
        run_id: str,
        run_type: str,
        evidence_dir: str = "evidence",
    ):
        self.run_id = run_id
        self.run_type = run_type

        self.directory = (
            Path(evidence_dir)
            / run_type
            / run_id
        )

        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.log_path = (
            self.directory
            / "run.jsonl"
        )

    def log(
        self,
        event_type: str,
        data: Dict[str, Any],
    ) -> None:

        event = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "run_id": self.run_id,
            "run_type": self.run_type,
            "event_type": event_type,
            "data": redact_dict(data),
        }

        with self.log_path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(event) + "\n"
            )

    def failure_screenshot_path(
        self,
        step_id: str,
    ) -> str:

        safe_step = re.sub(
            r"[^a-zA-Z0-9_-]",
            "_",
            step_id,
        )

        return str(
            self.directory
            / f"failure_{safe_step}.png"
        )