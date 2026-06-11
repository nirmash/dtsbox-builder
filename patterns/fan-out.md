# Pattern Playbook: Fan-out / Fan-in

Process N items in parallel, collect results.

## When this fits

- "Process every image in this folder"
- "Run this analysis on each of these 1000 URLs"
- "Validate each record in this batch"

## Questions to ask (Step 3)

1. **"What are the items you want to process?"** — Determines the input shape (a list).
   Example: "URLs", "image filenames", "user IDs".
2. **"What does each branch do?"** — Determines the per-item activity. Get a concrete description
   you can turn into a sandbox command. Example: "download the URL and extract the title tag".
3. **"How should results be aggregated?"** — Default: return all results as a list. Ask only if the
   user wants something specific like "sum them" or "filter failures".

## Code to generate (Step 7)

Replace the default `orchestrators/example_fan_out.py` and `activities/example_activity.py` with
files named after the user's intent. Suggest names like `process_urls` / `fetch_url_title` or
`analyze_images` / `analyze_one_image`.

### `orchestrators/<orchestrator_name>.py`

```python
"""Fan-out orchestrator: schedules one activity per input item, collects results.

Deterministic — DTS replays this function from history on any crash or restart.
Never call time.now(), random(), or do I/O here; use activities for side effects.
"""
import dtsbox
from durabletask import task


@dtsbox.orchestrator
def <orchestrator_name>(ctx, items: list):
    # Schedule one activity task per item. No work runs yet — these are declarations.
    tasks = [ctx.call_activity("<activity_name>", input=item) for item in items]

    # Checkpoint: orchestrator suspends. DTS dispatches all tasks. On resume, results is populated.
    results = yield task.when_all(tasks)

    # Aggregate branch outputs into the final result.
    return {"processed": len(results), "results": results}
```

### `activities/<activity_name>.py`

```python
"""Fan-out activity: runs one sandbox step per item received from the orchestrator.

Runs exactly once per scheduled task — no replay. Side effects allowed.
"""
import dtsbox


@dtsbox.activity
def <activity_name>(ctx, item):
    return dtsbox.run_sandbox_step(
        ctx,
        source="python-3.12",
        files={"/tmp/work.py": <USER_GENERATED_PYTHON_FOR_ONE_ITEM>},
        command="python3 /tmp/work.py",
        workflow="<orchestrator_name>",
    )
```

## Filling in the template

`<USER_GENERATED_PYTHON_FOR_ONE_ITEM>` should be a Python f-string or template that uses `item` to
parameterize the per-branch work.

### Example fills

| User intent | files content |
|---|---|
| "square each integer" | `f"print({item} * {item})"` |
| "fetch URL and print title" | `f"import urllib.request, re; html = urllib.request.urlopen('{item}').read().decode(); print(re.search(r'<title>(.+?)</title>', html).group(1))"` |
| "echo each string" | `f"print({item!r})"` |

For anything non-trivial, write the code as a multi-line Python string. If it uses third-party
packages, add them to `requirements.txt` AND to a `pip install` line inside the sandbox command
(sandboxes start with stdlib only by default).

Example with pip install:
```python
command="pip install -q requests && python3 /tmp/work.py"
```

## Sample input to test with (Step 9)

For the orchestrator above, run:

```bash
dtsbox run <orchestrator_name> --input '[<sample-item-1>, <sample-item-2>, <sample-item-3>]'
```

Pick 2-3 small sample items based on the user's data. For `[1]*100` they get 100 parallel
sandboxes — fine for testing scale.

## What to explain in Step 10

After the run completes, point out:
> Your orchestrator scheduled N activities via `task.when_all(...)`. DTS dispatched each to the
> worker, which booted N fresh sandboxes (one per item), ran your command, captured stdout, and
> deleted each sandbox. `results` is a list of `{stdout, sandbox_id, elapsed_seconds}` dicts — one
> per item, in input order. Check `dtsbox logs <instance-id> --json` for full per-sandbox detail.

## Edge cases to mention

- `[]` as input → `task.when_all([])` resolves immediately to `[]`. Zero sandboxes, completes fast.
- `[1] * 100` → 100 parallel branches. DTS queues all; workers drain by replica count.
- An activity that throws → that branch fails; `task.when_all` raises and the orchestration fails.
  Use `try/except` inside the activity if you want to record failures and continue.
