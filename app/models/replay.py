from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ReplayStatus(str, Enum):
    SUCCESS = "success"
    BUSINESS_OUTCOME = "business_outcome"
    FAILURE = "failure"


class FailureType(str, Enum):
    VALIDATION_ERROR = "validation_error"
    PERMISSION_DENIED = "permission_denied"
    SESSION_EXPIRED = "session_expired"
    TIMEOUT = "timeout"
    ELEMENT_NOT_FOUND = "element_not_found"
    CHECKPOINT_FAILED = "checkpoint_failed"
    POLICY_VIOLATION = "policy_violation"
    UNEXPECTED_DIALOG = "unexpected_dialog"
    APPLICATION_ERROR = "application_error"
    UNKNOWN = "unknown"


class ReplayResult(BaseModel):
    status: ReplayStatus

    capability_name: str
    capability_version: str

    outputs: Dict[str, Any] = Field(
        default_factory=dict
    )

    business_outcome: Optional[str] = None

    failed_step_id: Optional[str] = None
    failure_type: Optional[FailureType] = None

    expected: Optional[str] = None
    observed: Optional[str] = None

    message: Optional[str] = None

    evidence_path: Optional[str] = None