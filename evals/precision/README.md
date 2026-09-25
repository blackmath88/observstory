# Precision study data

Report: [docs/development/precision-report.md](../../docs/development/precision-report.md).

| File | What it is |
|---|---|
| `git_study.py` | Git-only collection (`collect`, `stacks`) and line-level measurement (`measure`) |
| `run.py` | API-mode equivalent, for a rerun with a token |
| `analyze.py` | Pair-level breakdown by noise category and patch class |
| `sample.py` | Fixed-seed stratified sample for manual labelling |
| `data/*.observations.json` | Observation bundles for the six repos (collected 2026-09-25, with stacks inferred) |
| `data/stage0-v1-overlap-counts.json` | Overlap counts from the merged v1 model on the same observations |
| `data/measurements-a-base-aware.json`, `data/breakdown-a-base-aware.json` | Stage A: base-aware overlap only (137 signals, 5,903 pairs) |
| `data/measurements.json`, `data/breakdown.json` | Stage B: stale work excluded (59 signals, 1,095 pairs); the pool the sample was drawn from |
| `data/sample.json`, `data/labels.json` | 85 sampled pairs and their labels with rationales |
| `data/final-signals.json`, `data/final-labels.json` | The 27 final signals and their labels |
| `data/ablation.json` | Final model with individual changes switched off |
