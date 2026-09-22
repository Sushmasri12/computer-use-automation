from pathlib import Path

from app.artifact.store import ArtifactStore
from app.models.artifact import (
    ActionType,
    CapabilityArtifact,
    CapabilityStep,
    Checkpoint,
    Locator,
    LocatorStrategy,
    OutputDefinition,
    ParameterDefinition,
    RiskLevel,
)


def create_test_artifact() -> CapabilityArtifact:
    return CapabilityArtifact(
        schema_version="1.0",
        capability_name="lookup_member_savings_balance",
        capability_version="1.0.0",
        description=(
            "Look up a member by member ID and "
            "return the savings balance."
        ),
        target_app="member_servicing_portal",
        entry_point="http://127.0.0.1:5000",
        inputs=[
            ParameterDefinition(
                name="member_id",
                type="string",
                required=True,
                description="Member identifier.",
            )
        ],
        outputs=[
            OutputDefinition(
                name="savings_balance",
                type="string",
                description="Current savings balance.",
            )
        ],
        steps=[
            CapabilityStep(
                id="step_1",
                action=ActionType.NAVIGATE,
                description="Open member portal.",
                value="http://127.0.0.1:5000",
                risk=RiskLevel.SAFE,
            ),
            CapabilityStep(
                id="step_2",
                action=ActionType.TYPE,
                description="Enter member ID.",
                locator=Locator(
                    strategy=LocatorStrategy.LABEL,
                    value="Member ID",
                ),
                value="{{member_id}}",
                risk=RiskLevel.SAFE,
            ),
            CapabilityStep(
                id="step_3",
                action=ActionType.CLICK,
                description="Search member.",
                locator=Locator(
                    strategy=LocatorStrategy.ROLE,
                    value="Search Member",
                ),
                risk=RiskLevel.SAFE,
            ),
            CapabilityStep(
                id="step_4",
                action=ActionType.EXTRACT,
                description="Read savings balance.",
                locator=Locator(
                    strategy=LocatorStrategy.CSS,
                    value="#savings-balance",
                ),
                output_name="savings_balance",
                risk=RiskLevel.SAFE,
            ),
        ],
        success_checkpoint=Checkpoint(
            description=(
                "Member Details page is displayed."
            ),
            locator=Locator(
                strategy=LocatorStrategy.CSS,
                value="h1",
            ),
            expected_text="Member Details",
        ),
    )


def test_artifact_is_versioned():
    artifact = create_test_artifact()

    assert artifact.schema_version == "1.0"
    assert artifact.capability_version == "1.0.0"


def test_artifact_has_typed_input():
    artifact = create_test_artifact()

    assert len(artifact.inputs) == 1
    assert artifact.inputs[0].name == "member_id"
    assert artifact.inputs[0].type == "string"
    assert artifact.inputs[0].required is True


def test_artifact_uses_parameterized_member_id():
    artifact = create_test_artifact()

    type_steps = [
        step
        for step in artifact.steps
        if step.action == ActionType.TYPE
    ]

    assert len(type_steps) == 1
    assert type_steps[0].value == "{{member_id}}"


def test_artifact_defines_expected_output():
    artifact = create_test_artifact()

    assert len(artifact.outputs) == 1
    assert artifact.outputs[0].name == "savings_balance"
    assert artifact.outputs[0].type == "string"


def test_artifact_has_success_checkpoint():
    artifact = create_test_artifact()

    checkpoint = artifact.success_checkpoint

    assert checkpoint.expected_text == "Member Details"
    assert checkpoint.locator.strategy == LocatorStrategy.CSS
    assert checkpoint.locator.value == "h1"


def test_artifact_has_ordered_actions():
    artifact = create_test_artifact()

    actions = [
        step.action
        for step in artifact.steps
    ]

    assert actions == [
        ActionType.NAVIGATE,
        ActionType.TYPE,
        ActionType.CLICK,
        ActionType.EXTRACT,
    ]


def test_artifact_store_round_trip(tmp_path: Path):
    artifact = create_test_artifact()

    store = ArtifactStore(
        directory=str(tmp_path)
    )

    saved_path = store.save(artifact)

    assert saved_path.exists()

    loaded = store.load(
        capability_name=artifact.capability_name,
        capability_version=artifact.capability_version,
    )

    assert loaded == artifact