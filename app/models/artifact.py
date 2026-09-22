from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    EXTRACT = "extract"
    WAIT = "wait"


class LocatorStrategy(str, Enum):
    ROLE = "role"
    LABEL = "label"
    TEXT = "text"
    CSS = "css"


class RiskLevel(str, Enum):
    SAFE = "safe"
    RISKY = "risky"


class ParameterDefinition(BaseModel):
    name: str
    type: str
    required: bool = True
    description: str


class OutputDefinition(BaseModel):
    name: str
    type: str
    description: str


class Locator(BaseModel):
    strategy: LocatorStrategy
    value: str
    fallback: Optional[str] = None


class CapabilityStep(BaseModel):
    id: str
    action: ActionType
    description: str

    locator: Optional[Locator] = None

    value: Optional[str] = None
    output_name: Optional[str] = None

    risk: RiskLevel = RiskLevel.SAFE

    timeout_ms: int = 5000


class Checkpoint(BaseModel):
    description: str
    locator: Locator
    expected_text: Optional[str] = None


class CapabilityArtifact(BaseModel):
    schema_version: str = "1.0"

    capability_name: str
    capability_version: str

    description: str

    target_app: str
    entry_point: str

    inputs: List[ParameterDefinition]
    outputs: List[OutputDefinition]

    steps: List[CapabilityStep]

    success_checkpoint: Checkpoint

    metadata: Dict[str, Any] = Field(default_factory=dict)