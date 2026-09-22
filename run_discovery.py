import asyncio
import os
import uuid

from dotenv import load_dotenv

from app.agent.discovery import DiscoveryAgent
from app.agent.llm import LLMClient
from app.artifact.builder import ArtifactBuilder
from app.artifact.store import ArtifactStore
from app.observability.logger import RunLogger
from app.safety.policy import SafetyPolicy
from app.surface.browser import BrowserSurface


TARGET_URL = "http://127.0.0.1:5000"
MEMBER_ID = "12345"

GOAL = (
    f"Look up member {MEMBER_ID} and read "
    "their current savings balance."
)


async def main():
    load_dotenv(override=True)

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is missing. "
            "Add it to the .env file."
        )

    run_id = f"discovery-{uuid.uuid4().hex[:8]}"

    logger = RunLogger(
        run_id=run_id,
        run_type="discovery",
    )

    surface = BrowserSurface(
        headless=False
    )

    policy = SafetyPolicy()

    llm = LLMClient()

    agent = DiscoveryAgent(
        surface=surface,
        llm=llm,
        policy=policy,
        logger=logger,
        max_steps=10,
    )

    print("Starting LLM discovery...")
    print(f"Goal: {GOAL}")
    print()

    result = await agent.run(
        goal=GOAL,
        target_url=TARGET_URL,
    )

    print("Discovery status:", result["status"])

    if result["status"] != "success":
        print(
            "Discovery did not complete successfully."
        )
        print(result)
        return

    builder = ArtifactBuilder()

    artifact = builder.build_member_lookup(
        discovery_result=result,
        member_id_used=MEMBER_ID,
    )

    store = ArtifactStore()

    artifact_path = store.save(
        artifact
    )

    print()
    print("Discovery completed successfully.")
    print("Outputs:", result["outputs"])
    print(
        "Artifact saved to:",
        artifact_path,
    )
    print(
        "Evidence saved under:",
        logger.directory,
    )


if __name__ == "__main__":
    asyncio.run(main())