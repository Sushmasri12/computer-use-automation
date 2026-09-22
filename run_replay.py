import asyncio
import uuid

from app.artifact.store import ArtifactStore
from app.observability.logger import RunLogger
from app.replay.engine import ReplayEngine
from app.safety.policy import SafetyPolicy
from app.surface.browser import BrowserSurface


CAPABILITY_NAME = "lookup_member_savings_balance"
CAPABILITY_VERSION = "1.0.0"

MEMBER_ID = "12345"


async def main():
    # Load the previously discovered capability artifact.
    store = ArtifactStore()

    artifact = store.load(
        capability_name=CAPABILITY_NAME,
        capability_version=CAPABILITY_VERSION,
    )

    # Create a unique replay evidence directory.
    run_id = f"replay-{uuid.uuid4().hex[:8]}"

    logger = RunLogger(
        run_id=run_id,
        run_type="replay",
    )

    # Replay uses the saved artifact directly.
    # No LLM client is created here.
    surface = BrowserSurface(
        headless=False
    )

    policy = SafetyPolicy()

    engine = ReplayEngine(
        surface=surface,
        policy=policy,
        logger=logger,
    )

    print("Starting deterministic replay...")
    print(
        f"Capability: "
        f"{artifact.capability_name} "
        f"v{artifact.capability_version}"
    )
    print(f"Member ID: {MEMBER_ID}")
    print()

    result = await engine.replay(
        artifact=artifact,
        inputs={
            "member_id": MEMBER_ID,
        },
    )

    print("Replay status:", result.status.value)

    if result.outputs:
        print("Outputs:", result.outputs)

    if result.business_outcome:
        print(
            "Business outcome:",
            result.business_outcome,
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
            "Failure evidence:",
            result.evidence_path,
        )

    print(
        "Replay evidence saved under:",
        logger.directory,
    )


if __name__ == "__main__":
    asyncio.run(main())