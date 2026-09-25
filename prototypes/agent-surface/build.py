#!/usr/bin/env python3
"""Direction 3 prototype: Agent Coordination Surface.

Plays a coding agent's pre-flight questions against the demo snapshot at t2 (overlap live)
and writes each request/response pair to examples/. The MCP tool definitions in
mcp-tools.json map 1:1 onto these queries.

  python3 prototypes/agent-surface/build.py
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from observstory import config, query  # noqa: E402
from observstory.derive import derive, parse_time  # noqa: E402

HERE = pathlib.Path(__file__).parent
SESSION = [
    ("01-changes-since", "What changed since my last run?", "changes_since", {"since": "2026-09-21T15:00:00Z"}),
    ("02-work-near", "What is active around src/conversation?", "work_near", {"paths": ["src/conversation"]}),
    ("03-proposed-task", "What overlaps my proposed task (edit store.py, add export.py)?", "work_near",
     {"paths": ["src/conversation/store.py", "src/conversation/export.py"]}),
    ("04-open-loops", "What open loops exist?", "open_loops", {}),
    ("05-handoff", "What is ready for handoff?", "handoff", {}),
]


def main():
    obs = json.loads((ROOT / "fixtures/observations/demo-t2.json").read_text())
    snap = derive(obs, config.normalise(None), parse_time(obs["fetched_at"]))
    out = HERE / "examples"
    out.mkdir(exist_ok=True)
    for name, question, fn, args in SESSION:
        response = getattr(query, fn)(snap, *args.values())
        request = {"tool": f"observstory.{fn}", "arguments": args}
        (out / f"{name}.json").write_text(json.dumps({"agent_question": question, "request": request,
                                                      "response": response}, indent=2) + "\n")
        print(name, "->", fn)


if __name__ == "__main__":
    main()
