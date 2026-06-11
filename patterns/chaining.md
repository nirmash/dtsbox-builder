# Pattern Playbook: Function Chaining

Sequential pipeline — step1 produces an output, step2 consumes it, step3 consumes step2's output, etc.

## When this fits

- "Download a file, then transform it, then upload the result"
- "Fetch user record → enrich with external data → write to database"
- "Build → test → deploy"

## Questions to ask (Step 3)

1. **"What are the steps in your pipeline, in order?"** — Get a list of step names. Example:
   "download", "transform", "upload".
2. **"What does each step do?"** — One concrete description per step that you can turn into a
   sandbox command.
3. **"What does each step pass to the next?"** — The output shape of step N is the input shape of
   step N+1. Default: pass each step's `stdout` (a string) forward. If the user needs structured
   data, the step should print JSON.

## Code to generate (Step 7)

Replace the default fan-out files with:
- One orchestrator file
- One activity file per step

Suggest naming the orchestrator after the pipeline (`process_pipeline`, `nightly_etl`) and each
activity after its step (`download_file`, `transform_data`, `upload_result`).

### `orchestrators/<orchestrator_name>.py`

```python
"""Chaining orchestrator: each step's output feeds the next.

Deterministic — DTS replays this from history on every crash. Each step's result is recorded
in history, so on resume completed steps return cached values and only the next pending step runs.
"""
import dtsbox


@dtsbox.orchestrator
def <orchestrator_name>(ctx, payload):
    # Step 1 — receives the initial workflow payload
    result_1 = yield ctx.call_activity("<step_1_activity>", input=payload)

    # Step 2 — receives step 1's output
    result_2 = yield ctx.call_activity("<step_2_activity>", input=result_1)

    # Step 3 — receives step 2's output (extend or shorten as needed)
    result_3 = yield ctx.call_activity("<step_3_activity>", input=result_2)

    return {
        "step_1": result_1,
        "step_2": result_2,
        "step_3": result_3,
    }
```

### `activities/<step_N_activity>.py` (one per step)

```python
"""Pipeline step: runs once per orchestrator invocation. Side effects allowed."""
import dtsbox


@dtsbox.activity
def <step_N_activity>(ctx, input_data):
    return dtsbox.run_sandbox_step(
        ctx,
        source="python-3.12",
        files={"/tmp/work.py": <PYTHON_CODE_FOR_THIS_STEP>},
        command="python3 /tmp/work.py",
        workflow="<orchestrator_name>",
    )
```

## Filling in each step's code

The step's Python code receives `input_data` implicitly via its `files` body — you parameterize the
file contents with the input value at template-render time. Common pattern: serialize input as JSON
inside the file, then the script parses and processes it.

### Example: download → transform → upload

**`activities/download_file.py`** (input: a URL string)
```python
files={"/tmp/work.py": f"""
import urllib.request, json
data = urllib.request.urlopen({input_data!r}).read().decode()
print(json.dumps({{'content': data, 'length': len(data)}}))
"""},
```

**`activities/transform_data.py`** (input: the dict from download_file)
```python
files={"/tmp/work.py": f"""
import json
payload = json.loads({json.dumps(input_data['stdout'])!r})
# transform here
print(json.dumps({{'transformed': payload['content'].upper()}}))
"""},
```

Note: the previous step's output comes back as the full `run_sandbox_step` dict, so the next step
unwraps via `input_data['stdout']` (the captured stdout).

## Sample input (Step 9)

For a 3-step pipeline starting with a URL:

```bash
dtsbox run <orchestrator_name> --input '"https://example.com"'
```

For a JSON-shaped initial payload:

```bash
dtsbox run <orchestrator_name> --input '{"url": "https://example.com", "format": "json"}'
```

## What to explain in Step 10

> Your orchestrator ran 3 sequential activities. Each one's output was passed as input to the next.
> Because the orchestrator is deterministic and replayed from history, if the worker had crashed
> between step 2 and step 3, DTS would resume at step 3 — steps 1 and 2 would return cached results
> from history. That's the durability guarantee in action.

## Edge cases to mention

- A step that throws → the orchestration fails at that step. Steps before it stay completed in
  history; if you retry the instance, they replay from cache.
- Need conditional branching? Use a regular Python `if` on a previous step's result — that's
  deterministic.
- Need to skip a step based on input? Same — use `if` in the orchestrator before calling the
  activity.
- Very long pipelines (>10 steps)? Consider sub-orchestrations (separate pattern) to keep each
  orchestrator readable.
