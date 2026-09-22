import asyncio
import copy
import uuid

from app.artifact.store import ArtifactStore
from app.observability.logger import RunLogger
from app.replay.engine import ReplayEngine
from app.safety.policy import SafetyPolicy
from app.surface.browser import BrowserSurface


async def main():
    # Load the valid saved artifact.
    store = ArtifactStore()

    artifact = store.load(
        capability_name="lookup_member_savings_balance",
        capability_version="1.0.0",
    )

    # Work with an in-memory copy only.
    # The real saved artifact is not modified.
    failure_artifact = copy.deepcopy(artifact)

    # Deliberately break the extraction locator.
    # This represents unrecoverable UI drift:
    # the element expected by the capability no longer exists.
    for step in failure_artifact.steps:
        if step.output_name == "savings_balance":
            step.locator.value = "#missing-savings-balance"
            step.timeout_ms = 1500

    run_id = f"failure-{uuid.uuid4().hex[:8]}"

    logger = RunLogger(
        run_id=run_id,
        run_type="failure",
    )

    surface = BrowserSurface(
        headless=False
    )

    policy = SafetyPolicy()

    engine = ReplayEngine(
        surface=surface,
        policy=policy,
        logger=logger,
    )

    print("Starting hard-failure demo...")
    print(
        "Simulating unrecoverable UI drift "
        "with a missing savings-balance element."
    )
    print()

    result = await engine.replay(
        artifact=failure_artifact,
        inputs={
            "member_id": "12345",
        },
    )

    print(
        "Replay status:",
        result.status.value,
    )

    if result.failure_type:
        print(
            "Failure type:",
            result.failure_type.value,
        )

    if result.failed_step_id:
        print(
            "Failed step:",
            result.failed_step_id,
        )

    if result.expected:
        print(
            "Expected:",
            result.expected,
        )

    if result.observed:
        print(
            "Observed:",
            result.observed,
        )

    if result.message:
        print(
            "Message:",
            result.message,
        )

    if result.evidence_path:
        print(
            "Failure screenshot:",
            result.evidence_path,
        )

    print(
        "Failure evidence saved under:",
        logger.directory,
    )


if __name__ == "__main__":
    asyncio.run(main())