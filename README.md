# Computer-Use Automation System

A small computer-use automation system that discovers a workflow from a natural-language goal using an LLM, saves the discovered workflow as a reusable capability artifact, and later replays that capability deterministically without asking the LLM to decide the next action.

The project uses a local member-servicing web application as the target UI.

## What the System Demonstrates

The implementation demonstrates:

- LLM-driven UI discovery using an observe, decide, act loop
- Real browser interaction using Playwright
- Versioned and serializable capability artifacts
- Parameterized runtime inputs
- Deterministic replay without LLM decisions
- Stable locator strategies
- Success checkpoints
- Expected business outcomes
- Recoverable timeout handling with deterministic retry
- Structured hard failures with screenshots
- Host, route, and action allowlists
- Safe versus risky action policy
- Secret redaction in structured logs
- Human intervention in the same live browser session
- Structured evidence and execution logs

## Project Structure

```text
computer-use-automation/
├── app/
│   ├── agent/
│   │   ├── llm.py
│   │   └── discovery.py
│   ├── artifact/
│   │   ├── builder.py
│   │   └── store.py
│   ├── escalation/
│   │   └── intervention.py
│   ├── models/
│   │   ├── artifact.py
│   │   └── replay.py
│   ├── observability/
│   │   └── logger.py
│   ├── replay/
│   │   └── engine.py
│   ├── safety/
│   │   └── policy.py
│   └── surface/
│       └── browser.py
├── demo_app/
│   ├── app.py
│   └── templates/
├── artifacts/
├── evidence/
├── tests/
├── run_discovery.py
├── run_replay.py
├── run_recovery_demo.py
├── run_failure_demo.py
├── run_handoff.py
├── README.md
├── REPORT.md
├── requirements.txt
└── .env.example
```

## Setup

### 1. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Install the Playwright browser

```powershell
playwright install chromium
```

### 4. Configure the OpenAI API key

Create a `.env` file in the project root:

```text
OPENAI_API_KEY=your_api_key_here
```

The `.env` file is ignored by Git and must not be committed.

## Run the Demo Application

Start the local member-servicing portal:

```powershell
python -m demo_app.app
```

The application runs at:

```text
http://127.0.0.1:5000
```

Keep this terminal running while executing the automation examples.

The application contains synthetic test data only.

## LLM-Driven Discovery

In another terminal, activate the virtual environment and run:

```powershell
python run_discovery.py
```

The discovery agent receives a natural-language goal and interacts with the live browser UI.

Its loop is:

```text
observe -> decide -> act -> observe
```

The LLM receives the current UI state and selects the next action. Discovery is bounded by a maximum number of steps and does not contain a hard-coded workflow for completing the task.

A successful run produces a reusable capability artifact:

```text
artifacts/lookup_member_savings_balance_v1.0.0.json
```

The concrete discovery input is replaced with the runtime parameter:

```text
{{member_id}}
```

This allows the same capability to be reused for different member IDs.

## Deterministic Replay

Run:

```powershell
python run_replay.py
```

Replay loads the saved capability artifact and executes its ordered actions.

The replay engine does not ask an LLM what to do next.

It uses the artifact's:

- ordered steps
- locator strategies
- runtime parameters
- action types
- per-step timeouts
- expected outputs
- success checkpoint

A successful replay returns a structured result containing the extracted output.

## Business Outcomes

The replay engine distinguishes an expected business outcome from an automation failure.

For example, searching for a member that does not exist produces:

```text
status: business_outcome
business_outcome: Member not found.
```

This is not classified as a broken automation workflow.

## Recoverable Conditions

Run:

```powershell
python run_recovery_demo.py
```

This demo intentionally simulates one transient timeout.

The replay engine:

1. detects the recoverable timeout
2. records the condition
3. waits briefly
4. retries the same deterministic step once
5. continues if the retry succeeds

No LLM decision is introduced during recovery.

The evidence log records events such as:

```text
recoverable_condition_detected
recovery_retry_started
recovery_succeeded
```

## Hard Failure Demonstration

Run:

```powershell
python run_failure_demo.py
```

This demo intentionally uses a missing locator to simulate UI drift.

The replay engine retries the deterministic operation and then returns a structured hard failure when recovery does not succeed.

The result contains:

- failure type
- failed step
- expected state
- observed error
- screenshot path

The configured per-step timeout is enforced by the browser operations.

Failure evidence includes both a structured log and screenshot.

## Human Intervention

Run:

```powershell
python run_handoff.py
```

When intervention is requested, automation pauses while keeping the same browser session alive.

The operator can interact directly with that browser session and then return control to the automation.

The intervention evidence records:

- capability
- goal
- current step
- reason for intervention
- state before intervention
- screenshot
- operator note
- state after intervention
- return of control to automation

This preserves execution context rather than restarting the workflow in a new browser session.

## Safety

Safety controls are implemented in:

```text
app/safety/policy.py
```

The policy supports configurable:

- allowed hosts
- allowed routes
- allowed action types
- risky-action approval

By default, risky actions are blocked unless explicitly enabled.

The demo environment only allows the configured local member-servicing application.

## Sensitive Data and Secrets

Secrets are not stored in source control.

The OpenAI API key is loaded from `.env`, which is excluded by `.gitignore`.

Structured logging applies redaction to sensitive keys and secret-like values, including:

- passwords
- API keys
- access tokens
- refresh tokens
- authorization values
- credentials

The member records used by the demo application are synthetic test data.

The reusable artifact parameterizes the member identifier instead of storing the concrete discovery input.

## Evidence

Execution evidence is stored under:

```text
evidence/
```

The repository includes evidence for:

```text
evidence/
├── discovery/
├── failure/
├── handoff/
├── recovery/
├── replay/
└── example_capability.json
```

The evidence demonstrates:

- genuine LLM-driven discovery
- successful deterministic replay
- expected business outcome
- deterministic recovery
- hard failure with screenshot
- human intervention and return of control
- saved reusable capability artifact

## Tests

Run the complete test suite with:

```powershell
python -m pytest tests -v
```

The tests cover capability artifact structure and persistence, runtime parameterization, success checkpoints, host and route allowlisting, action safety, risky-action blocking, and secret redaction.

## Key Design Principle

The LLM is used during discovery to determine how to accomplish a goal against the live UI.

After discovery, the learned procedure is converted into a versioned capability artifact.

Replay then executes that artifact deterministically.

This separation keeps the discovery process flexible while making repeated execution predictable, observable, and easier to govern.