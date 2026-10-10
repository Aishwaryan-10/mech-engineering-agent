import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI
from tools import TOOLS

load_dotenv()  # reads your .env file

client = OpenAI(
    api_key=os.environ["LLM_API_KEY"],
    base_url=os.environ.get("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
)
MODEL = os.environ.get("LLM_MODEL", "openai/gpt-oss-120b")
MAX_STEPS = 6   # safety limit so the agent can't loop forever


def build_system_prompt() -> str:
    tool_text = "\n".join(f"- {name}: {desc}" for name, (_, desc) in TOOLS.items())
    return f"""You are a Mechanical Engineering Assistant Agent.
You solve the user's goal step by step using tools when needed.

Available tools:
{tool_text}

You MUST reply with ONLY one JSON object, in one of two forms:

1) To use a tool:
{{"thought": "why I need this tool", "action": "tool_name", "action_input": {{...}}}}

2) When you have enough information to answer:
{{"thought": "I have the answer", "final_answer": "your answer to the user"}}

Rules:
- Every reply MUST contain either "action" (a real tool name from the list) or "final_answer". Never leave action empty or null.
- For ANY calculation or unit conversion you MUST call a tool and wait for its Observation. Never compute numbers yourself.
- Use one tool per step.
- After each Observation, either call the next tool or give the final_answer using the tool results exactly.

Example for "convert 5 MPa to psi":
{{"thought": "I must convert units with the tool", "action": "unit_convert", "action_input": {{"value": 5, "from_unit": "MPa", "to_unit": "psi"}}}}"""


def parse_json(text: str) -> dict:
    """Pull a JSON object out of the model's reply."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found")
    return json.loads(match.group(0))


def call_llm(messages):
    """Ask the model. 'low' reasoning effort keeps replies fast and avoids empty output."""
    try:
        r = client.chat.completions.create(
            model=MODEL, messages=messages, temperature=0,
            extra_body={"reasoning_effort": "low"},
        )
    except Exception:
        r = client.chat.completions.create(
            model=MODEL, messages=messages, temperature=0,
        )
    return r.choices[0].message.content or ""


def run_agent(goal: str, history: list) -> str:
    messages = [{"role": "system", "content": build_system_prompt()}]
    messages += history
    messages.append({"role": "user", "content": goal})

    step = 0
    attempts = 0
    used_tool = False
    nudged = False

    while step < MAX_STEPS and attempts < MAX_STEPS * 3:
        attempts += 1
        reply = call_llm(messages)

        # 1. Must be valid JSON
        try:
            data = parse_json(reply)
        except Exception:
            print("   (invalid JSON, retrying...)")
            messages.append({"role": "assistant", "content": reply or "(empty)"})
            messages.append({"role": "user",
                             "content": "Invalid format. Reply with ONLY one valid JSON object."})
            continue

        # 2. Final answer
        if "final_answer" in data:
            # Guard: numbers in the goal but no tool used -> ask once to use a tool
            if not used_tool and not nudged and any(c.isdigit() for c in goal):
                nudged = True
                print("   (answer given without using a tool, asking agent to use one...)")
                messages.append({"role": "assistant", "content": reply})
                messages.append({"role": "user", "content":
                    "You did not use a tool. Do not calculate yourself. "
                    "Call the correct tool first using an 'action'."})
                continue
            step += 1
            print(f"\n--- Step {step} ---")
            print("Thought:", data.get("thought", ""))
            history.append({"role": "user", "content": goal})
            history.append({"role": "assistant", "content": data["final_answer"]})
            return data["final_answer"]

        # 3. Tool call: must name an action
        tool_name = data.get("action")
        if not tool_name:
            print("   (no action given, retrying...)")
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content":
                "Your reply had no action. Reply with a JSON object containing "
                "'action' and 'action_input', or 'final_answer'."})
            continue

        step += 1
        tool_input = data.get("action_input", {}) or {}
        print(f"\n--- Step {step} ---")
        print("Thought:", data.get("thought", ""))
        print("Action :", tool_name, tool_input)

        if tool_name in TOOLS:
            try:
                observation = TOOLS[tool_name][0](**tool_input)
                used_tool = True
            except Exception as e:
                observation = f"Tool error: {e}"
        else:
            observation = f"Unknown tool '{tool_name}'. Available: {list(TOOLS)}"

        print("Observation:", observation)
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": f"Observation: {observation}"})

    return "Stopped: reached the maximum number of steps."


if __name__ == "__main__":
    print("Mechanical Engineering Agent (type 'exit' to quit)")
    history = []   # short-term memory across questions
    while True:
        goal = input("\nYou: ").strip()
        if goal.lower() in ("exit", "quit"):
            break
        print("\nAgent:", run_agent(goal, history))