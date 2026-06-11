# Pattern Playbook: Sub-orchestrations

A parent orchestrator dispatches one or more child orchestrators. Each child is itself a full
durable workflow with its own history, retry, and replay semantics.

## When this fits

- "For each customer, run the full onboarding workflow"
- "I have a complex pipeline that's getting unreadable — break it into sub-flows"
- "Different customers need different workflow shapes — parent picks the right child"

## Questions to ask (Step 3)

1. **"What kicks off the parent orchestrator?"** — Determines the parent's input shape. Example: "a
   list of customer IDs", "a single batch ID".
2. **"What does each child orchestrator do?"** — One concrete description per child. The child
   itself can be a fan-out or a chain — get enough detail to know its internal pattern.
3. **"Are children different shapes, or all the same?"** — If all the same, you generate one child
   orchestrator and the parent dispatches N copies. If different, you generate one orchestrator per
   child shape.

## Code to generate (Step 7)

Replace the default fan-out files with:
- One parent orchestrator
- One or more child orchestrators
- One activity per child step (children typically follow fan-out or chaining internally)

### `orchestrators/<parent_name>.py` — fan-out parent

```python
"""Parent orchestrator: dispatches N child orchestrators, collects their results.

Deterministic — DTS replays this from history on every crash. Each child sub-orchestration runs
as its own durable workflow with independent history and retry.
"""
import dtsbox
from durabletask import task


@dtsbox.orchestrator
def <parent_name>(ctx, items: list):
    # Schedule one child orchestrator per item. Each child is a full durable workflow.
    child_tasks = [
        ctx.call_sub_orchestrator("<child_name>", input=item)
        for item in items
    ]

    # Wait for all children to complete. Each child's return value becomes one entry.
    child_results = yield task.when_all(child_tasks)

    return {
        "children_completed": len(child_results),
        "results": child_results,
    }
```

### `orchestrators/<child_name>.py` — child (example: a small fan-out)

```python
"""Child orchestrator: a self-contained durable workflow invoked by a parent.

Receives a single input from the parent, returns a single result back.
"""
import dtsbox
from durabletask import task


@dtsbox.orchestrator
def <child_name>(ctx, input_item):
    # The child does its own work — here, a small fan-out over derived items.
    sub_items = [f"{input_item}-{i}" for i in range(3)]
    tasks = [ctx.call_activity("<child_activity>", input=s) for s in sub_items]
    results = yield task.when_all(tasks)
    return {"parent_input": input_item, "branch_results": results}
```

### `activities/<child_activity>.py`

```python
"""Activity used by child orchestrator(s). Side effects allowed; runs once per scheduled task."""
import dtsbox
from durabletask import task


# Local smoke stub — runs against the Docker emulator with zero Azure setup.
# Return shape MUST match run_sandbox_step's output so swapping to Azure is a 1-line change.
@dtsbox.activity
def <child_activity>(ctx: task.ActivityContext, item) -> dict:
    result = f"processed:{item}"
    return {"stdout": result, "sandbox_id": "local-smoke", "elapsed_seconds": 0.0}


# Real Azure version (uncomment after `dtsbox setup` + comment out the stub above):
# @dtsbox.activity
# def <child_activity>(ctx: task.ActivityContext, item):
#     return dtsbox.run_sandbox_step(
#         ctx,
#         source="python-3.12",
#         files={"/tmp/work.py": f"print({item!r})"},
#         command="python3 /tmp/work.py",
#         workflow="<child_name>",
#     )
```

> **Multi-activity / multi-orchestrator note**: every `@dtsbox.activity` and every
> `@dtsbox.orchestrator` in the project runs through the worker. If any activity touches
> `run_sandbox_step` without Azure configured, the orchestration will fail on that step.
> Smoke-stub every activity for local testing, then swap to the Azure path together.

## The key API: `ctx.call_sub_orchestrator(...)`

This is the only new thing in this pattern. It schedules a child orchestration as a separate
durable workflow. The child:

- Has its own instance ID, history, and retry counter
- Can be invoked independently with `dtsbox run <child_name> --input '...'` for testing
- Runs on the same worker pool (no separate infra)
- Returns its final value to the parent like any other yielded task

You can also call children sequentially (no `when_all`) for a chain-of-children pattern.

## Why this pattern matters

This is the architectural unlock that lets you compose workflows. Without sub-orchestrations, a
complex pipeline lives as one giant orchestrator function. With sub-orchestrations, you build
small focused workflows and compose them — each piece is independently testable, and each child's
history is bounded.

## Sample input (Step 9)

Test the child alone first:

```bash
dtsbox run <child_name> --input '"customer-001"'
```

Then test the parent:

```bash
dtsbox run <parent_name> --input '["customer-001", "customer-002", "customer-003"]'
```

## What to explain in Step 10

> Your parent orchestrator scheduled 3 child sub-orchestrations via
> `ctx.call_sub_orchestrator(...)`. Each child got its own instance ID and ran as a fully
> independent durable workflow — own history, own retries, own replay. The parent collected each
> child's return value and aggregated them.
>
> **Inspecting children**: child instance IDs follow the pattern `<parent-id>:0001`, `:0002`, etc.
> Drill into any child with `dtsbox logs <parent-id>:0001 --json`. Note that `dtsbox ps` only
> shows ACTIVE instances — once a child completes, it disappears from `ps` but its logs remain
> accessible by ID.
>
> **Default logs view caveat**: `dtsbox logs <parent-id>` (without `--json`) shows the parent's
> child-orchestrator returns as "activities". If your children return dicts that don't have a
> `stdout` key, the default view will display `(empty)` for each — that does NOT mean they failed.
> Always use `--json` for sub-orchestration parents to see the real return values.

## Worked smoke-test example

A verified end-to-end example lives at `examples/batch_processor/` in this repo. Parent dispatches
one child per group; each child fan-outs over its group's numbers and squares them. Run with the
Docker emulator:

```bash
cd examples/batch_processor
dtsbox worker &
dtsbox run batch_processor --input '[[1,2,3],[4,5],[6,7,8,9]]'
dtsbox logs <instance-id> --json
# → [{"group_id": 0, "results": [1,4,9]}, {"group_id": 1, "results": [16,25]}, ...]
```

## Edge cases to mention

- Child fails → parent's `task.when_all` raises and the parent fails. Each child's history is
  preserved — you can retry just the failing child independently.
- Want to handle child failures without failing the parent? Wrap `call_sub_orchestrator` in a try
  inside the parent (yield-then-catch pattern from the Durable Task SDK).
- Mixed child shapes? Define multiple child orchestrators and dispatch the right one based on the
  parent's input.
- Don't nest too deep — 2 levels (parent → child) is the sweet spot. Deeper nesting hurts
  observability.
