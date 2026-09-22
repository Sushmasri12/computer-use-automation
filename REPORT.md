# Computer-Use Automation System Report

## 1. Architecture

The system separates LLM-driven discovery from deterministic execution.

During discovery, the user provides a natural-language goal such as looking up a member and reading the current savings balance. The discovery agent observes the live browser state, sends that state and the goal to the LLM, receives one structured action, executes that action through the browser surface, and observes the resulting state again.

The discovery loop follows:

```text
observe -> decide -> act -> observe
```

The loop is bounded by a maximum number of steps so the agent cannot continue indefinitely.

`BrowserSurface` provides the UI interaction boundary and uses Playwright for real browser interaction. The LLM does not receive a hard-coded sequence for the task. It chooses actions from the current UI state.

After successful discovery, `ArtifactBuilder` converts the recorded actions into a reusable capability artifact. Concrete discovery inputs are replaced with runtime parameters such as `{{member_id}}`.

Replay is intentionally separate. `ReplayEngine` loads the saved artifact and executes the recorded actions in order without asking an LLM to decide what to do next.

Supporting components provide safety policy enforcement, structured evidence logging, artifact persistence, failure classification, and human intervention.

The local Flask member-servicing portal is a synthetic target application used to demonstrate the architecture without accessing a real financial system.

## 2. Artifact schema

Capabilities are represented using typed Pydantic models and serialized as JSON.

Each `CapabilityArtifact` contains:

- schema version
- capability name and version
- description
- target application
- entry point
- typed input definitions
- typed output definitions
- ordered capability steps
- success checkpoint
- metadata

Each step records an action type, description, locator when required, optional value, optional output name, risk level, and timeout.

Supported actions include navigation, typing, clicking, extraction, and waiting.

Locator strategies include role, label, visible text, and CSS. The discovered member lookup uses semantic label and role targeting for interaction and a stable element ID for balance extraction.

The concrete member identifier used during discovery is converted to:

```text
{{member_id}}
```

This allows the artifact to be reused with different runtime inputs instead of encoding one test case.

The artifact also contains a success checkpoint that verifies that the expected Member Details page was reached.

Artifacts are versioned and stored as JSON so they can be inspected, persisted, reviewed, and replayed later.

## 3. Determinism & error handling

Replay does not use the LLM for action selection.

The replay engine reads the artifact and executes the same ordered procedure with supplied runtime inputs. This makes repeated execution easier to reason about and audit.

Each browser operation respects the timeout configured on its capability step.

The replay result distinguishes three major outcomes.

A successful execution returns `success` and the extracted outputs.

An expected application result, such as a member not existing, returns `business_outcome`. This is intentionally different from an automation failure because the UI may have worked correctly even though the requested business object was not found.

Recoverable Playwright timeouts are retried once. The same deterministic step is retried without asking the LLM for another decision. Recovery events are written to the evidence log.

If the retry also fails, replay returns a structured hard failure containing the failure type, failed step, expected behavior, observed error, and screenshot evidence.

A final success checkpoint provides an additional validation that the expected UI state was reached.

The included failure demonstration intentionally changes the extraction locator to simulate UI drift. This produces a bounded timeout and failure screenshot instead of silently returning incorrect data.

## 4. Heterogeneity & multi-tenant

The current implementation targets a web application through Playwright, but UI interaction is isolated behind the surface layer.

For a legacy web application, another browser-based adapter could use accessibility roles, labels, DOM selectors, screenshots, or other targeting techniques while preserving the same higher-level capability model.

For a desktop application, the browser surface could be replaced with a desktop surface backed by an accessibility tree or desktop automation framework. The discovery and replay layers would continue to work against the same conceptual operations: observe state, locate a target, perform an action, and validate the result.

For multi-tenant use, I would keep the reusable capability definition separate from tenant-specific configuration. Tenant configuration could provide allowed targets, authentication context, locator overrides, and application-specific settings.

Artifacts would remain versioned. A tenant or application version could be associated with a known capability version or locator configuration.

UI drift should not silently cause the replay system to invoke an LLM and continue unpredictably. Locator failures and checkpoint failures should surface as explicit replay failures. Discovery can then be run again to produce a candidate updated capability that can be reviewed and promoted as a new version.

This approach keeps common workflow semantics reusable while allowing controlled adaptation to different application surfaces and tenants.

## 5. Escalation & handoff

The project includes a human-intervention path for situations where automation becomes blocked or requires operator assistance.

When intervention is requested, the system records the capability, goal, current step, reason for escalation, current browser state, and screenshot.

Automation then pauses while keeping the same live browser session open.

The human operator can interact directly with that existing browser session. The workflow is not restarted in a separate browser or reconstructed from scratch.

After the operator completes the required action, the operator returns control to the automation. The system records the operator note and post-intervention state so the handoff is represented in the execution evidence.

This preserves context across the machine-to-human and human-to-machine transition.

The current operator interface is intentionally minimal and terminal-based because the assessment prioritizes real control transfer over UI polish.

## 6. Safety

The safety policy provides configurable allowlists for hosts, routes, and action types.

The demonstration environment permits only the configured local member-servicing application. Navigation to an unapproved host, unsupported URL scheme, or unapproved route is rejected by policy.

Capability steps also include a risk classification. Safe actions can execute normally, while risky actions are blocked by default unless risky execution is explicitly enabled.

The OpenAI API key is loaded from `.env`. The `.env` file is excluded from source control.

Structured logging applies redaction to common secret fields and secret-like text, including passwords, API keys, tokens, authorization values, secrets, and credentials.

The member data in the local demonstration application is synthetic.

The reusable capability parameterizes the member identifier rather than persisting the concrete discovery input in the final artifact.

The included tests exercise host and route restrictions, action policy, risky-action blocking, artifact parameterization, artifact persistence, checkpoints, and secret redaction.

## 7. Cuts

The implementation intentionally focuses on the smallest complete system that demonstrates the required architecture.

I did not build a production-grade operator dashboard. Human intervention uses a terminal prompt while preserving the same live browser session.

I did not implement desktop automation. Instead, the surface abstraction provides the design seam where a desktop adapter could be added.

I did not implement a full multi-tenant artifact registry or automatic capability migration system. The design uses versioned artifacts and describes how tenant-specific configuration and locator overrides could be layered on top.

I also did not implement advanced self-healing that invokes an LLM during replay. This was intentional because replay is designed to remain deterministic. When bounded deterministic recovery fails, the system produces explicit evidence or transfers control to a human rather than silently changing the learned procedure.

The result is a small system that demonstrates LLM-driven discovery, reusable capability learning, deterministic replay, explicit error semantics, safety controls, evidence collection, and real human handoff without adding unnecessary infrastructure.