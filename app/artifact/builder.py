from typing import Any, Dict, List

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


class ArtifactBuilder:
    def build_member_lookup(
        self,
        discovery_result: Dict[str, Any],
        member_id_used: str,
    ) -> CapabilityArtifact:

        if discovery_result.get("status") != "success":
            raise ValueError(
                "Cannot build an artifact from an unsuccessful discovery run."
            )

        recorded_steps: List[Dict[str, Any]] = (
            discovery_result.get("steps", [])
        )

        capability_steps: List[CapabilityStep] = []

        capability_steps.append(
            CapabilityStep(
                id="step_1",
                action=ActionType.NAVIGATE,
                description=(
                    "Open the member servicing portal."
                ),
                value=discovery_result["target_url"],
                risk=RiskLevel.SAFE,
            )
        )

        step_number = 2

        for recorded in recorded_steps:
            action = ActionType(
                recorded["action"]
            )

            locator_data = recorded.get(
                "locator"
            )

            locator = None

            if locator_data:
                locator = Locator(
                    strategy=LocatorStrategy(
                        locator_data["strategy"]
                    ),
                    value=locator_data["value"],
                    fallback=locator_data.get(
                        "fallback"
                    ),
                )

            value = recorded.get("value")

            if (
                action == ActionType.TYPE
                and value == member_id_used
            ):
                value = "{{member_id}}"

            description = recorded.get(
                "description",
                f"Execute {action.value}",
            )

            description = (
                self._sanitize_member_id(
                    description,
                    member_id_used,
                )
            )

            capability_steps.append(
                CapabilityStep(
                    id=f"step_{step_number}",
                    action=action,
                    description=description,
                    locator=locator,
                    value=value,
                    output_name=recorded.get(
                        "output_name"
                    ),
                    risk=RiskLevel.SAFE,
                )
            )

            step_number += 1

        output_definitions = []

        for output_name in discovery_result.get(
            "outputs",
            {}
        ):
            output_definitions.append(
                OutputDefinition(
                    name=output_name,
                    type="string",
                    description=(
                        f"Value extracted for "
                        f"{output_name}."
                    ),
                )
            )

        discovery_goal = (
            discovery_result.get("goal")
            or (
                "Look up a member and read "
                "their current savings balance."
            )
        )

        discovery_goal = (
            self._sanitize_member_id(
                discovery_goal,
                member_id_used,
            )
        )

        return CapabilityArtifact(
            schema_version="1.0",
            capability_name=(
                "lookup_member_savings_balance"
            ),
            capability_version="1.0.0",
            description=(
                "Look up a member by member ID "
                "and return the member's current "
                "savings balance."
            ),
            target_app=(
                "member_servicing_portal"
            ),
            entry_point=(
                discovery_result["target_url"]
            ),
            inputs=[
                ParameterDefinition(
                    name="member_id",
                    type="string",
                    required=True,
                    description=(
                        "Member identifier used "
                        "for lookup."
                    ),
                )
            ],
            outputs=output_definitions,
            steps=capability_steps,
            success_checkpoint=Checkpoint(
                description=(
                    "Member Details page is "
                    "displayed."
                ),
                locator=Locator(
                    strategy=LocatorStrategy.CSS,
                    value="h1",
                ),
                expected_text="Member Details",
            ),
            metadata={
                "source": "llm_discovery",
                "discovery_goal":
                    discovery_goal,
                "contains_runtime_secrets":
                    False,
            },
        )

    @staticmethod
    def _sanitize_member_id(
        text: str,
        member_id_used: str,
    ) -> str:

        if not text:
            return text

        return text.replace(
            str(member_id_used),
            "{{member_id}}",
        )