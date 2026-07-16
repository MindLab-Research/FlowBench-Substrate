# FlowBench Public Release

This is the answer-free public task package. It is suitable for inspecting
tasks, integrating agents, and launching Harbor containers with a smoke
verifier. It is not the official scoring package.

Scope note: this package is a business-operations tool-composition benchmark. It
is unrelated to prior workflow-guided planning or workflow-generation benchmarks
that also use the FlowBench name.

Files intentionally excluded from this public package:
- fixed gold labels
- Harbor oracle solutions
- strict verifier expected files
- model result logs and generated transcripts

Official-style or private benchmark scores should be computed with the private
evaluator pack or a freshly generated held-out split. Publishing fixed labels
for the official split would make hard-coded benchmark submissions possible.

Repeated prompt or adapter tuning on `data/test.jsonl` can overfit to the
released task surface.

For public runs, freeze prompts and adapters before scoring and reject
task-id-specific lookup logic. Public Harbor results are smoke-test results,
not official FlowBench scores.

Data source:
- There is no separate CSV, database dump, or network service. The public
  task records are in `data/test.jsonl`; the data tables are generated
  deterministically inside `tools/flowbench_tools.py` and each Harbor task's
  `/app/flowbench_tools.py` using SHA-256 keyed generators. Importing the
  tool file builds the same synthetic customers, products, orders, returns,
  tickets, inventory, FX rates, and SLA policies on every machine.

Public scoring boundary:
- Because the public deterministic tools are shipped with the public task
  records, anyone can recompute answers locally. This package is therefore
  not a secure fixed-answer leaderboard package. Use it for transparent
  reproducibility, harness integration, and smoke tests; use a private
  evaluator or freshly salted held-out split for official scoring.

Task note:
- The `currency_lookup` family is a depth-1 diagnostic. It intentionally
  repeats the four region currency facts across task ids as a tool-wiring
  sanity check; do not treat those repeated diagnostic items as a
  leaderboard difficulty signal.

See `RUN.md` for the public agent-evaluation contract, prediction format,
and Harbor smoke-run instructions.

Harbor smoke run, replacing `<agent>` with the Harbor agent to evaluate:

```bash
harbor run -p harbor -a <agent> -l 1
```
