import json
from typing import Any, Dict

from openai import OpenAI


class LLMClient:
    def __init__(self, model: str = "gpt-5-mini"):
        self.client = OpenAI()
        self.model = model

    def decide(
        self,
        goal: str,
        state: Dict[str, Any],
        history: list[Dict[str, Any]],
    ) -> Dict[str, Any]:

        system_prompt = """
You are controlling a browser to accomplish a user goal.

You operate in an observe -> decide -> act loop.

You may choose exactly one action at a time.

Allowed actions:
- fill
- click
- extract
- done
- stuck

Return ONLY valid JSON.

For fill:
{
  "action": "fill",
  "label": "visible form label",
  "value": "value to enter",
  "reason": "short explanation"
}

For click:
{
  "action": "click",
  "role": "button",
  "name": "visible button name",
  "reason": "short explanation"
}

For extract:
{
  "action": "extract",
  "selector": "CSS selector",
  "output_name": "name for extracted value",
  "reason": "short explanation"
}

When extracting a value:
- Inspect current_state.elements first.
- Prefer a specific visible element ID as the CSS selector.
- If an element has id "savings-balance", use "#savings-balance".
- Never use "body" when a more specific element is available.
- Extract only the value needed to satisfy the goal.
- Do not extract the same information more than once.
- Use a clear output name such as "savings_balance".
- After the required value has been extracted successfully, choose "done".
- Never invent a selector that is not supported by current_state.elements.

For done:
{
  "action": "done",
  "reason": "why the goal is complete"
}

For stuck:
{
  "action": "stuck",
  "reason": "why safe progress cannot continue"
}

Do not navigate to another domain.
Do not perform risky or irreversible actions.
Do not invent information that is not visible in the current state.
"""

        user_prompt = {
            "goal": goal,
            "current_state": state,
            "previous_actions": history,
        }

        response = self.client.responses.create(
            model=self.model,
            instructions=system_prompt,
            input=json.dumps(user_prompt),
        )

        text = response.output_text.strip()

        if text.startswith("```"):
            text = text.strip("`")

            if text.startswith("json"):
                text = text[4:].strip()

        try:
            decision = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"LLM returned invalid JSON: {text}"
            ) from exc

        if "action" not in decision:
            raise ValueError(
                "LLM decision does not contain an action."
            )

        return decision