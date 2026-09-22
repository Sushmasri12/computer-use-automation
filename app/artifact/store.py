import json
from pathlib import Path

from app.models.artifact import CapabilityArtifact


class ArtifactStore:
    def __init__(self, directory: str = "artifacts"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, artifact: CapabilityArtifact) -> Path:
        filename = (
            f"{artifact.capability_name}"
            f"_v{artifact.capability_version}.json"
        )

        path = self.directory / filename

        with path.open("w", encoding="utf-8") as file:
            json.dump(
                artifact.model_dump(mode="json"),
                file,
                indent=2,
            )

        return path

    def load(
        self,
        capability_name: str,
        capability_version: str,
    ) -> CapabilityArtifact:

        filename = (
            f"{capability_name}"
            f"_v{capability_version}.json"
        )

        path = self.directory / filename

        if not path.exists():
            raise FileNotFoundError(
                f"Capability artifact not found: {path}"
            )

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return CapabilityArtifact.model_validate(data)