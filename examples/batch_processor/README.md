# batch_processor — sub-orchestrations pattern (verified)

Demonstrates the **sub-orchestrations** pattern: a parent orchestrator dispatches one child
orchestrator per group, each child does its own fan-out, and the parent aggregates child returns.

## Shape

```
batch_processor (parent)
├── square_group (child #0001) → fan-out over numbers[0]
├── square_group (child #0002) → fan-out over numbers[1]
└── square_group (child #0003) → fan-out over numbers[2]
```

## Files

| Path | Purpose |
|---|---|
| `orchestrators/batch_processor.py` | Parent + child orchestrators (both defined here for clarity) |
| `activities/square_one.py` | The leaf activity that squares a single number (smoke-stub by default) |

The activity ships with the local smoke-stub as live code. The real `dtsbox.run_sandbox_step`
version is commented inline — uncomment it after `dtsbox setup`.

## Run locally (Docker emulator, zero Azure)

```bash
# 1. Start the emulator
docker run -d --name dtsbox-emulator -p 8080:8080 mcr.microsoft.com/dts/dts-emulator:latest

# 2. Install deps and start the worker
pip install -r requirements.txt
dtsbox worker &

# 3. Run the parent — three groups of numbers
INSTANCE=$(dtsbox run batch_processor --input '[[1,2,3],[4,5],[6,7,8,9]]' | tail -1)

# 4. Inspect (must use --json — see "Gotcha" below)
dtsbox logs "$INSTANCE" --json
```

**Expected output:**

```json
[
  {"group_id": 0, "results": [1, 4, 9]},
  {"group_id": 1, "results": [16, 25]},
  {"group_id": 2, "results": [36, 49, 64, 81]}
]
```

## Drilling into a child

Child instance IDs follow the pattern `<parent-id>:0001`, `:0002`, `:0003`. Inspect any child:

```bash
dtsbox logs "<parent-id>:0001" --json
# → [1, 4, 9]   ← the first child's squared results
```

## Gotcha: default `dtsbox logs` shows `(empty)`

The default (non-JSON) view of `dtsbox logs <parent-id>` reads child returns as "activities" and
expects each to have a `stdout` key. Children here return `{"group_id": ..., "results": ...}` —
no `stdout` — so the default view shows:

```
─── Activity 1 [exit 0] (0.0s) ───
(empty)
...
```

That does NOT mean the children failed. Always use `--json` for sub-orchestration parents.
