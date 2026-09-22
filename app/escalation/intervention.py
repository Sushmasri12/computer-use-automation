import asyncio
from typing import Any, Dict

from app.observability.logger import RunLogger
from app.surface.browser import BrowserSurface


class HumanInterventionManager:
    def __init__(
        self,
        surface: BrowserSurface,
        logger: RunLogger,
    ):
        self.surface = surface
        self.logger = logger

    async def request_intervention(
        self,
        capability_name: str,
        goal: str,
        current_step: str,
        reason: str,
    ) -> Dict[str, Any]:

        state_before = await self.surface.get_state()

        screenshot_path = (
            self.logger.failure_screenshot_path(
                "human_intervention"
            )
        )

        try:
            await self.surface.screenshot(
                screenshot_path
            )
        except Exception:
            screenshot_path = None

        self.logger.log(
            "human_intervention_requested",
            {
                "capability": capability_name,
                "goal": goal,
                "current_step": current_step,
                "reason": reason,
                "url": state_before["url"],
                "screenshot": screenshot_path,
            },
        )

        print()
        print("HUMAN INTERVENTION REQUIRED")
        print(f"Capability: {capability_name}")
        print(f"Goal: {goal}")
        print(f"Current step: {current_step}")
        print(f"Reason: {reason}")
        print()
        print(
            "Please use the currently open browser "
            "window to resolve the issue."
        )
        print(
            "Do not close the browser because the "
            "automation must continue in the same session."
        )
        print()

        operator_note = await asyncio.to_thread(
            input,
            (
                "After resolving the issue, describe "
                "what you did and press Enter: "
            ),
        )

        state_after = await self.surface.get_state()

        self.logger.log(
            "human_intervention_completed",
            {
                "capability": capability_name,
                "current_step": current_step,
                "operator_note": operator_note,
                "url_before": state_before["url"],
                "url_after": state_after["url"],
                "state_before": (
                    state_before["visible_text"][:1000]
                ),
                "state_after": (
                    state_after["visible_text"][:1000]
                ),
            },
        )

        print()
        print(
            "Human control returned to automation."
        )
        print()

        return {
            "status": "completed",
            "operator_note": operator_note,
            "state_before": state_before,
            "state_after": state_after,
            "screenshot": screenshot_path,
        }