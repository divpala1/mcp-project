"""Quick test for the agent /chat endpoint."""
from __future__ import annotations

import json
import sys
import textwrap

import httpx

URL   = "http://127.0.0.1:8002/agent/chat"
TOKEN = "tok_alice"
PROMPT = "Hello! What tools do you have available?"

DIVIDER = "─" * 60

def render(event: dict) -> None:
    etype = event.get("type")

    if etype == "token":
        print(event.get("text", ""), end="", flush=True)

    elif etype == "tool_start":
        print(f"\n\n[tool call]  {event.get('name')}")
        args = event.get("args")
        if args:
            print(textwrap.indent(json.dumps(args, indent=2), "  "))

    elif etype == "tool_end":
        print(f"[tool result] {event.get('name')}")
        out = event.get("output")
        if out:
            text = json.dumps(out, indent=2) if not isinstance(out, str) else out
            print(textwrap.indent(textwrap.shorten(text, width=400, placeholder=" …"), "  "))

    elif etype == "error":
        print(f"\n[error]  {event.get('message')}", file=sys.stderr)

    elif etype == "end":
        print(f"\n\n{DIVIDER}")
        print("done")


print(DIVIDER)
print(f"prompt : {PROMPT}")
print(f"token  : {TOKEN}")
print(DIVIDER + "\n")

with httpx.stream(
    "POST",
    URL,
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={"prompt": PROMPT},
    timeout=120,
) as r:
    if r.status_code != 200:
        print(f"HTTP {r.status_code}")
        print(r.read().decode())
        sys.exit(1)

    for line in r.iter_lines():
        if line.startswith("data:"):
            payload = line[len("data:"):].strip()
            try:
                render(json.loads(payload))
            except json.JSONDecodeError:
                print(f"[unparseable] {payload}")

