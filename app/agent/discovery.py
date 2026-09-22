from typing import Any, Dict, List

from app.agent.llm import LLMClient
from app.models.artifact import ActionType, RiskLevel
from app.observability.logger import RunLogger
from app.safety.policy import SafetyPolicy
from app.surface.browser import BrowserSurface


class DiscoveryAgent:
    def __init__(
        self,
        surface: BrowserSurface,
        llm: LLMClient,
        policy: SafetyPolicy,
        logger: RunLogger,
        max_steps: int = 10,
    ):
        self.surface = surface
        self.llm = llm
        self.policy = policy
        self.logger = logger
        self.max_steps = max_steps

        self.history: List[Dict[str, Any]] = []
        self.recorded_steps: List[Dict[str, Any]] = []
        self.outputs: Dict[str, Any] = {}

    async def run(
        self,
        goal: str,
        target_url: str,
    ) -> Dict[str, Any]:

        # Safety check before opening the target.
        self.policy.check_url(target_url)

        await self.surface.start()

        try:
            await self.surface.navigate(target_url)

            self.logger.log(
                "discovery_started",
                {
                    "goal": goal,
                    "target_url": target_url,
                },
            )

            for step_number in range(
                1,
                self.max_steps + 1,
            ):
                # OBSERVE
                state = await self.surface.get_state()

                self.logger.log(
                    "observation",
                    {
                        "step_number": step_number,
                        "url": state["url"],
                        "title": state["title"],
                        "visible_text": state["visible_text"],
                    },
                )

                # DECIDE
                decision = self.llm.decide(
                    goal=goal,
                    state=state,
                    history=self.history,
                )

                self.logger.log(
                    "llm_decision",
                    {
                        "step_number": step_number,
                        "decision": decision,
                    },
                )

                action = decision["action"]

                # ACT
                if action == "fill":
                    await self._handle_fill(decision)

                elif action == "click":
                    await self._handle_click(decision)

                elif action == "extract":
                    await self._handle_extract(decision)

                elif action == "done":
                    self.history.append(decision)

                    self.logger.log(
                        "discovery_completed",
                        {
                            "reason": decision.get(
                                "reason",
                                "Goal completed.",
                            ),
                            "outputs": self.outputs,
                        },
                    )

                    return {
                        "status": "success",
                        "goal": goal,
                        "target_url": target_url,
                        "steps": self.recorded_steps,
                        "outputs": self.outputs,
                        "history": self.history,
                    }

                elif action == "stuck":
                    reason = decision.get(
                        "reason",
                        "Agent could not safely continue.",
                    )

                    self.logger.log(
                        "discovery_stuck",
                        {
                            "step_number": step_number,
                            "reason": reason,
                        },
                    )

                    return {
                        "status": "stuck",
                        "goal": goal,
                        "reason": reason,
                        "steps": self.recorded_steps,
                        "outputs": self.outputs,
                    }

                else:
                    raise ValueError(
                        f"Unsupported LLM action: {action}"
                    )

                self.history.append(decision)

            # Dead-end / maximum-step protection.
            self.logger.log(
                "discovery_stopped",
                {
                    "reason":
                        "Maximum step limit reached."
                },
            )

            return {
                "status": "stuck",
                "goal": goal,
                "reason":
                    "Maximum step limit reached.",
                "steps": self.recorded_steps,
                "outputs": self.outputs,
            }

        except Exception as exc:
            screenshot_path = (
                self.logger.failure_screenshot_path(
                    "discovery"
                )
            )

            try:
                await self.surface.screenshot(
                    screenshot_path
                )
            except Exception:
                screenshot_path = None

            self.logger.log(
                "discovery_failed",
                {
                    "error": str(exc),
                    "screenshot": screenshot_path,
                },
            )

            return {
                "status": "failure",
                "goal": goal,
                "error": str(exc),
                "evidence_path": screenshot_path,
                "steps": self.recorded_steps,
            }

        finally:
            await self.surface.close()

    async def _handle_fill(
        self,
        decision: Dict[str, Any],
    ) -> None:

        # Every action must pass the safety policy.
        self.policy.check_action(
            ActionType.TYPE,
            RiskLevel.SAFE,
        )

        label = decision["label"]
        value = decision["value"]

        await self.surface.fill_by_label(
            label,
            value,
        )

        self.recorded_steps.append(
            {
                "action": "type",
                "description": decision.get(
                    "reason",
                    f"Fill {label}",
                ),
                "locator": {
                    "strategy": "label",
                    "value": label,
                },
                "value": value,
            }
        )

    async def _handle_click(
        self,
        decision: Dict[str, Any],
    ) -> None:

        # Every action must pass the safety policy.
        self.policy.check_action(
            ActionType.CLICK,
            RiskLevel.SAFE,
        )

        role = decision.get(
            "role",
            "button",
        )

        name = decision["name"]

        if role != "button":
            raise ValueError(
                f"Unsupported click role: {role}"
            )

        await self.surface.click_by_role(
            role,
            name,
        )

        self.recorded_steps.append(
            {
                "action": "click",
                "description": decision.get(
                    "reason",
                    f"Click {name}",
                ),
                "locator": {
                    "strategy": "role",
                    "value": name,
                },
            }
        )

    async def _handle_extract(
        self,
        decision: Dict[str, Any],
    ) -> None:

        # Every action must pass the safety policy.
        self.policy.check_action(
            ActionType.EXTRACT,
            RiskLevel.SAFE,
        )

        selector = decision["selector"]
        output_name = decision["output_name"]

        value = await self.surface.get_text(
            selector
        )

        self.outputs[output_name] = value

        self.recorded_steps.append(
            {
                "action": "extract",
                "description": decision.get(
                    "reason",
                    f"Extract {output_name}",
                ),
                "locator": {
                    "strategy": "css",
                    "value": selector,
                },
                "output_name": output_name,
            }
        )