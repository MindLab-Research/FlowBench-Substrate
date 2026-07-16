# Running FlowBench with an LLM Agent

FlowBench's public split is answer-free. It is intended for task inspection,
agent integration, smoke tests, and reproducible harness development. It is not
an official public-answer leaderboard split.

## What to Give the Agent

For each task, give the agent:

- one record from `data/test.jsonl`
- the callable tools from `tools/flowbench_tools.py`
- the tool signatures and descriptions in `TOOLS`
- the required `answer_format`

Do not give the agent gold answers, oracle solutions, verifier expected files,
or model transcripts from previous runs. They are intentionally not included in
this release.

The data source is the tool module. There is no CSV file, database dump, or
network service to fetch. Importing `tools/flowbench_tools.py` builds the same
synthetic customers, products, orders, returns, tickets, inventory, FX rates, and
SLA policies on every machine.

Because the public deterministic tools are shipped with the public task records,
the public package is not a secure fixed-answer leaderboard package. A solver
that imports the tools can recompute answers. Use it for transparent
reproducibility, harness integration, and smoke tests; use a private evaluator
or a freshly salted held-out split for official scoring.

## Non-Harbor Harness Contract

A fair public harness should:

1. Start a fresh task context unless you are explicitly studying persistence.
2. Load `tools/flowbench_tools.py`.
3. Expose only the functions listed in `TOOLS` as callable tools.
4. Ask the agent to solve the task by calling those tools.
5. Record the final answer as a string.

Do not expose the imported module object, function `__globals__`, source text,
generated data tables, local filesystem, or network access as part of the
agent-visible interface. For code/REPL agents, pass scrubbed callable wrappers
or provider tool schemas rather than raw module objects.

The public split has no labels, so this produces predictions for inspection or
private scoring. A useful prediction file format is JSONL:

```json
{"task_id": "example_task_id", "answer": "<model-output>", "model": "your-model-name"}
```

Minimal host-side adapter skeleton:

```python
import importlib.util
import json


def load_flowbench_tools(path="tools/flowbench_tools.py"):
    spec = importlib.util.spec_from_file_location("flowbench_tools", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    tool_specs = []
    tool_fns = {}
    for name, (signature, description, fn) in module.TOOLS.items():
        tool_specs.append({
            "name": name,
            "signature": signature,
            "description": description,
        })
        tool_fns[name] = fn
    return tool_specs, tool_fns


tool_specs, tool_fns = load_flowbench_tools()

with open("data/test.jsonl") as fin, open("predictions.jsonl", "w") as fout:
    for line in fin:
        task = json.loads(line)
        answer = run_agent(task=task, tool_specs=tool_specs, tool_fns=tool_fns)
        fout.write(json.dumps({
            "task_id": task["task_id"],
            "answer": str(answer).strip(),
            "model": "your-model-name",
        }) + "\n")
```

`run_agent` is your agent adapter. The `tool_fns` mapping above is for
host-side dispatch. Do not pass that mapping, the imported module, or raw
function objects directly to an agent-visible REPL. Raw Python functions expose
attributes such as `__globals__`, which can reveal implementation details and
generated tables. For a function-calling agent, convert `tool_specs` to your
provider's tool schema and dispatch calls to `tool_fns` outside the model-visible
context. For a code/REPL agent, expose sandboxed adapters or RPC-backed
functions that execute through the same `tool_fns` dispatcher without exposing
the module object, source text, globals, or data tables. For a command-style
agent, expose a thin command wrapper around the same dispatcher. The underlying
tools should be identical across substrates.

## Prompt Template

Use a prompt that is explicit about the output contract:

```text
You are solving one FlowBench task.
Use only the provided FlowBench tools to compute the answer.
Return the final answer only, with no explanation.
The required answer format is: {answer_format}

Task:
{instruction}

Available tools:
{tool_signatures_and_descriptions}
```

## Example Tool Plan

For a `breached_ticket_revenue` task, the agent should compose the public tools:

```python
orders = get_orders(region, category, month_start, month_end)
tickets = tickets_for_orders(orders, "high") + tickets_for_orders(orders, "critical")
breached = [tid for tid in tickets if sla_breached(tid, 24, 120)]
at_risk_orders = sorted({ticket_order_id(tid) for tid in breached})
answer = sum_values([net_revenue_usd(oid) for oid in at_risk_orders])
```

This illustrates where the data comes from: every intermediate value is produced
by the deterministic tool implementation.

## Harbor Smoke Pack

The `harbor/` directory is a Harbor-compatible public task pack. From a release
root that contains `harbor/`, run:

```bash
harbor run -p harbor -a <agent> -l 1
```

This is a smoke run. The public Harbor verifier checks only that the agent wrote
an output with the required shape. It does not contain private expected answers
and must not be reported as official benchmark scoring.

## Reporting Results

When reporting public FlowBench runs, include:

- model name and provider
- agent framework and action substrate
- prompt and tool exposure policy
- turn, token, and timeout limits
- whether the run used the public split, a private evaluator, or a generated
  held-out split

Do not claim official FlowBench scores from this public repository alone. The
public files deliberately exclude gold labels so fixed-answer submissions cannot
game the benchmark.

For paper, leaderboard, or cross-model claims, freeze the prompt and tool
adapter before scoring, avoid task-id-specific lookup logic, and evaluate with
private labels or a freshly generated held-out split. Public-only numbers should
be described as integration or smoke-test results.
