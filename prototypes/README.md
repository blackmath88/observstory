# Prototypes (DEVELOP phase)

All three directions read the same snapshots, derived from `fixtures/observations/demo-t*.json`.

| Direction | Build | Output |
|---|---|---|
| Radar | `python3 prototypes/radar/build.py` | `radar/demo-t{0..3}.html` |
| Timeline | `python3 prototypes/timeline/build.py` | `timeline/index.html`, `timeline/timeline.json` |
| Agent surface | `python3 prototypes/agent-surface/build.py` | `agent-surface/examples/*.json`, plus `mcp-tools.json` (the contract) |

Comparison and selection: [`docs/development/concept-comparison.md`](../docs/development/concept-comparison.md).
