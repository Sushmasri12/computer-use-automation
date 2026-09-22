from typing import Any, Dict

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.models.artifact import (
    ActionType,
    CapabilityArtifact,
    CapabilityStep,
    Locator,
    LocatorStrategy,
)
from app.models.replay import (
    FailureType,
    ReplayResult,
    ReplayStatus,
)
from app.observability.logger import RunLogger
from app.safety.policy import PolicyViolation, SafetyPolicy
from app.surface.browser import BrowserSurface


class ReplayEngine:
    def __init__(
        self,
        surface: BrowserSurface,
        policy: SafetyPolicy,
        logger: RunLogger,
    ):
        self.surface = surface
        self.policy = policy
        self.logger = logger

    async def replay(
        self,
        artifact: CapabilityArtifact,
        inputs: Dict[str, Any],
    ) -> ReplayResult:

        outputs: Dict[str, Any] = {}

        try:
            self._validate_inputs(artifact, inputs)

            self.policy.check_url(
                artifact.entry_point
            )

            self.logger.log(
                "replay_started",
                {
                    "capability":
                        artifact.capability_name,
                    "version":
                        artifact.capability_version,
                },
            )

            await self.surface.start()

            for step in artifact.steps:
                try:
                    await self._execute_with_retry(
                        step=step,
                        inputs=inputs,
                        outputs=outputs,
                    )

                    self.logger.log(
                        "step_completed",
                        {
                            "step_id": step.id,
                            "action":
                                step.action.value,
                        },
                    )

                    business_outcome = (
                        await self
                        ._detect_business_outcome()
                    )

                    if business_outcome:
                        self.logger.log(
                            "business_outcome",
                            {
                                "step_id": step.id,
                                "outcome":
                                    business_outcome,
                            },
                        )

                        return ReplayResult(
                            status=(
                                ReplayStatus
                                .BUSINESS_OUTCOME
                            ),
                            capability_name=(
                                artifact
                                .capability_name
                            ),
                            capability_version=(
                                artifact
                                .capability_version
                            ),
                            business_outcome=(
                                business_outcome
                            ),
                            message=business_outcome,
                        )

                except PlaywrightTimeoutError as exc:
                    return await self._failure(
                        artifact=artifact,
                        step=step,
                        failure_type=(
                            FailureType.TIMEOUT
                        ),
                        expected=step.description,
                        observed=str(exc),
                    )

                except PolicyViolation as exc:
                    return await self._failure(
                        artifact=artifact,
                        step=step,
                        failure_type=(
                            FailureType
                            .POLICY_VIOLATION
                        ),
                        expected=(
                            "Policy-approved action"
                        ),
                        observed=str(exc),
                    )

                except Exception as exc:
                    return await self._failure(
                        artifact=artifact,
                        step=step,
                        failure_type=(
                            FailureType.UNKNOWN
                        ),
                        expected=step.description,
                        observed=str(exc),
                    )

            checkpoint_ok = (
                await self._verify_checkpoint(
                    artifact
                )
            )

            if not checkpoint_ok:
                return await self._failure(
                    artifact=artifact,
                    step=None,
                    failure_type=(
                        FailureType
                        .CHECKPOINT_FAILED
                    ),
                    expected=(
                        artifact
                        .success_checkpoint
                        .description
                    ),
                    observed=(
                        await self
                        ._safe_visible_text()
                    ),
                )

            self.logger.log(
                "replay_completed",
                {
                    "status": "success",
                    "outputs": outputs,
                },
            )

            return ReplayResult(
                status=ReplayStatus.SUCCESS,
                capability_name=(
                    artifact.capability_name
                ),
                capability_version=(
                    artifact.capability_version
                ),
                outputs=outputs,
                message=(
                    "Replay completed successfully."
                ),
            )

        except ValueError as exc:
            return ReplayResult(
                status=ReplayStatus.FAILURE,
                capability_name=(
                    artifact.capability_name
                ),
                capability_version=(
                    artifact.capability_version
                ),
                failure_type=(
                    FailureType.VALIDATION_ERROR
                ),
                message=str(exc),
            )

        except PolicyViolation as exc:
            return ReplayResult(
                status=ReplayStatus.FAILURE,
                capability_name=(
                    artifact.capability_name
                ),
                capability_version=(
                    artifact.capability_version
                ),
                failure_type=(
                    FailureType.POLICY_VIOLATION
                ),
                message=str(exc),
            )

        finally:
            await self.surface.close()

    async def _execute_with_retry(
        self,
        step: CapabilityStep,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
    ) -> None:
        """
        Execute one deterministic step.

        A Playwright timeout is treated as a
        recoverable condition once. The same
        deterministic step is retried without
        asking an LLM for a new decision.
        """

        try:
            await self._execute_step(
                step,
                inputs,
                outputs,
            )

        except PlaywrightTimeoutError as exc:
            self.logger.log(
                "recoverable_condition_detected",
                {
                    "step_id": step.id,
                    "condition": "timeout",
                    "attempt": 1,
                    "error": str(exc),
                },
            )

            if self.surface.page is not None:
                await self.surface.page.wait_for_timeout(
                    1000
                )

            self.logger.log(
                "recovery_retry_started",
                {
                    "step_id": step.id,
                    "attempt": 2,
                },
            )

            try:
                await self._execute_step(
                    step,
                    inputs,
                    outputs,
                )

                self.logger.log(
                    "recovery_succeeded",
                    {
                        "step_id": step.id,
                        "attempt": 2,
                    },
                )

            except PlaywrightTimeoutError as retry_exc:
                self.logger.log(
                    "recovery_failed",
                    {
                        "step_id": step.id,
                        "attempt": 2,
                        "error": str(retry_exc),
                    },
                )

                raise retry_exc

    async def _execute_step(
        self,
        step: CapabilityStep,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
    ) -> None:

        self.policy.check_action(
            step.action,
            step.risk,
        )

        self.logger.log(
            "step_started",
            {
                "step_id": step.id,
                "action": step.action.value,
                "description":
                    step.description,
            },
        )

        if step.action == ActionType.NAVIGATE:
            if not step.value:
                raise ValueError(
                    "Navigate step requires a URL."
                )

            url = self._resolve_value(
                step.value,
                inputs,
            )

            self.policy.check_url(url)

            await self.surface.navigate(url)

        elif step.action == ActionType.TYPE:
            if step.locator is None:
                raise ValueError(
                    "Type step requires a locator."
                )

            value = self._resolve_value(
                step.value or "",
                inputs,
            )

            await self._fill(
                step.locator,
                value,
                step.timeout_ms,
            )

        elif step.action == ActionType.CLICK:
            if step.locator is None:
                raise ValueError(
                    "Click step requires a locator."
                )

            await self._click(
                step.locator,
                step.timeout_ms,
            )

        elif step.action == ActionType.EXTRACT:
            if step.locator is None:
                raise ValueError(
                    "Extract step requires a locator."
                )

            if not step.output_name:
                raise ValueError(
                    "Extract step requires "
                    "output_name."
                )

            value = await self._extract(
                step.locator,
                step.timeout_ms,
            )

            outputs[
                step.output_name
            ] = value

        elif step.action == ActionType.WAIT:
            if self.surface.page is None:
                raise RuntimeError(
                    "Browser page is not available."
                )

            await (
                self.surface.page
                .wait_for_timeout(
                    step.timeout_ms
                )
            )

        else:
            raise ValueError(
                f"Unsupported action: "
                f"{step.action}"
            )

    async def _fill(
        self,
        locator: Locator,
        value: str,
        timeout_ms: int,
    ) -> None:

        if self.surface.page is None:
            raise RuntimeError(
                "Browser page is not available."
            )

        if (
            locator.strategy
            == LocatorStrategy.LABEL
        ):
            await (
                self.surface.page
                .get_by_label(
                    locator.value
                )
                .fill(
                    value,
                    timeout=timeout_ms,
                )
            )

        elif (
            locator.strategy
            == LocatorStrategy.CSS
        ):
            await (
                self.surface.page
                .locator(locator.value)
                .fill(
                    value,
                    timeout=timeout_ms,
                )
            )

        else:
            raise ValueError(
                "Unsupported fill locator: "
                f"{locator.strategy.value}"
            )

    async def _click(
        self,
        locator: Locator,
        timeout_ms: int,
    ) -> None:

        if self.surface.page is None:
            raise RuntimeError(
                "Browser page is not available."
            )

        if (
            locator.strategy
            == LocatorStrategy.ROLE
        ):
            await (
                self.surface.page
                .get_by_role(
                    "button",
                    name=locator.value,
                )
                .click(
                    timeout=timeout_ms,
                )
            )

        elif (
            locator.strategy
            == LocatorStrategy.TEXT
        ):
            await (
                self.surface.page
                .get_by_text(
                    locator.value,
                    exact=True,
                )
                .click(
                    timeout=timeout_ms,
                )
            )

        elif (
            locator.strategy
            == LocatorStrategy.CSS
        ):
            await (
                self.surface.page
                .locator(locator.value)
                .click(
                    timeout=timeout_ms,
                )
            )

        else:
            raise ValueError(
                "Unsupported click locator: "
                f"{locator.strategy.value}"
            )

    async def _extract(
        self,
        locator: Locator,
        timeout_ms: int,
    ) -> str:

        if self.surface.page is None:
            raise RuntimeError(
                "Browser page is not available."
            )

        if (
            locator.strategy
            == LocatorStrategy.CSS
        ):
            value = await (
                self.surface.page
                .locator(locator.value)
                .inner_text(
                    timeout=timeout_ms,
                )
            )

        elif (
            locator.strategy
            == LocatorStrategy.TEXT
        ):
            value = await (
                self.surface.page
                .get_by_text(
                    locator.value,
                    exact=True,
                )
                .inner_text(
                    timeout=timeout_ms,
                )
            )

        else:
            raise ValueError(
                "Unsupported extract locator: "
                f"{locator.strategy.value}"
            )

        return value.strip()

    async def _verify_checkpoint(
        self,
        artifact: CapabilityArtifact,
    ) -> bool:

        checkpoint = (
            artifact.success_checkpoint
        )

        try:
            observed = await self._extract(
                checkpoint.locator,
                5000,
            )

            if (
                checkpoint.expected_text
                is None
            ):
                return bool(observed)

            return (
                checkpoint.expected_text
                in observed
            )

        except Exception:
            return False

    async def _detect_business_outcome(
        self,
    ) -> str | None:

        if self.surface.page is None:
            return None

        outcome = (
            self.surface.page.locator(
                "#business-outcome"
            )
        )

        if await outcome.count() == 0:
            return None

        text = (
            await outcome.inner_text(
                timeout=2000
            )
        ).strip()

        if text:
            return text

        return None

    async def _failure(
        self,
        artifact: CapabilityArtifact,
        step: CapabilityStep | None,
        failure_type: FailureType,
        expected: str,
        observed: str,
    ) -> ReplayResult:

        step_id = (
            step.id
            if step is not None
            else "checkpoint"
        )

        screenshot_path = (
            self.logger
            .failure_screenshot_path(
                step_id
            )
        )

        try:
            await self.surface.screenshot(
                screenshot_path
            )
        except Exception:
            screenshot_path = None

        self.logger.log(
            "replay_failed",
            {
                "step_id": step_id,
                "failure_type":
                    failure_type.value,
                "expected": expected,
                "observed": observed,
            },
        )

        return ReplayResult(
            status=ReplayStatus.FAILURE,
            capability_name=(
                artifact.capability_name
            ),
            capability_version=(
                artifact.capability_version
            ),
            failed_step_id=step_id,
            failure_type=failure_type,
            expected=expected,
            observed=observed,
            message=(
                "Deterministic replay failed."
            ),
            evidence_path=screenshot_path,
        )

    async def _safe_visible_text(
        self,
    ) -> str:

        try:
            state = (
                await self.surface.get_state()
            )

            return (
                state["visible_text"][:1000]
            )

        except Exception:
            return (
                "Unable to read current UI state."
            )

    @staticmethod
    def _resolve_value(
        value: str,
        inputs: Dict[str, Any],
    ) -> str:

        resolved = value

        for key, input_value in (
            inputs.items()
        ):
            resolved = resolved.replace(
                "{{" + key + "}}",
                str(input_value),
            )

        return resolved

    @staticmethod
    def _validate_inputs(
        artifact: CapabilityArtifact,
        inputs: Dict[str, Any],
    ) -> None:

        for parameter in artifact.inputs:
            if (
                parameter.required
                and parameter.name
                not in inputs
            ):
                raise ValueError(
                    "Missing required input: "
                    f"{parameter.name}"
                )