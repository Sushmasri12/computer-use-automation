import asyncio
import uuid

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.artifact.store import ArtifactStore
from app.observability.logger import RunLogger
from app.replay.engine import ReplayEngine
from app.safety.policy import SafetyPolicy
from app.surface.browser import BrowserSurface


class RecoveryDemoEngine(ReplayEngine):
    """
    Demo-only replay engine.

    It simulates one transient timeout on the
    member-ID typing step. The normal ReplayEngine
    should detect the timeout, retry the same
    deterministic step, and then continue normally.
    """

    def __init__(
        self,
        surface,
        policy,
        logger,
    ):
        super().__init__(
            surface=surface,
            policy=policy,
            logger=logger,
        )

        self.transient_failure_triggered = False

    async def _execute_step(
        self,
        step,
        inputs,
        outputs,
    ):
        if (
            step.id == "step_2"
            and not self.transient_failure_triggered
        ):
            self.transient_failure_triggered = True

            raise PlaywrightTimeoutError(
                "Simulated transient UI timeout."
            )

        await super()._execute_step(
            step,
            inputs,
            outputs,
        )


async def main():
    store = ArtifactStore()

    artifact = store.load(
        capability_name=(
            "lookup_member_savings_balance"
        ),
        capability_version="1.0.0",
    )

    run_id = (
        f"recovery-{uuid.uuid4().hex[:8]}"
    )

    logger = RunLogger(
        run_id=run_id,
        run_type="recovery",
    )

    surface = BrowserSurface(
        headless=False
    )

    policy = SafetyPolicy()

    engine = RecoveryDemoEngine(
        surface=surface,
        policy=policy,
        logger=logger,
    )

    print(
        "Starting recoverable-condition demo..."
    )
    print(
        "A transient timeout will be simulated "
        "once at step_2."
    )
    print()

    result = await engine.replay(
        artifact=artifact,
        inputs={
            "member_id": "12345",
        },
    )

    print(
        "Replay status:",
        result.status.value,
    )

    if result.outputs:
        print(
            "Outputs:",
            result.outputs,
        )

    if result.failure_type:
        print(
            "Failure type:",
            result.failure_type.value,
        )

    if result.message:
        print(
            "Message:",
            result.message,
        )

    print(
        "Recovery evidence saved under:",
        logger.directory,
    )


if __name__ == "__main__":
    asyncio.run(main())