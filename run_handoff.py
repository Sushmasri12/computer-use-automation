import asyncio
import uuid

from app.escalation.intervention import HumanInterventionManager
from app.observability.logger import RunLogger
from app.safety.policy import SafetyPolicy
from app.surface.browser import BrowserSurface


TARGET_URL = "http://127.0.0.1:5000"


async def main():
    run_id = f"handoff-{uuid.uuid4().hex[:8]}"

    logger = RunLogger(
        run_id=run_id,
        run_type="handoff",
    )

    surface = BrowserSurface(
        headless=False
    )

    policy = SafetyPolicy()

    intervention = HumanInterventionManager(
        surface=surface,
        logger=logger,
    )

    try:
        policy.check_url(TARGET_URL)

        await surface.start()
        await surface.navigate(TARGET_URL)

        print("Automation started.")
        print(
            "Simulating a blocked condition "
            "that requires human intervention."
        )

        result = await intervention.request_intervention(
            capability_name=(
                "lookup_member_savings_balance"
            ),
            goal=(
                "Look up a member and retrieve "
                "the savings balance."
            ),
            current_step="member_lookup",
            reason=(
                "Automation is blocked and requires "
                "operator assistance before continuing."
            ),
        )

        logger.log(
            "automation_resumed",
            {
                "status": result["status"],
                "operator_note": (
                    result["operator_note"]
                ),
            },
        )

        print("Automation resumed successfully.")
        print(
            "Operator note:",
            result["operator_note"],
        )
        print(
            "Evidence saved under:",
            logger.directory,
        )

    finally:
        await surface.close()


if __name__ == "__main__":
    asyncio.run(main())