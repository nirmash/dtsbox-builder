# Examples — verified end-to-end

Three reference projects, identical to what `/dtsbox-builder` would generate for these patterns.
All ship with **smoke-test stubs** so they run locally against the DTS emulator (Docker) without
Azure. Each example was actually executed before being checked in.

| Example | Pattern | What it does |
|---|---|---|
| [`square_numbers/`](square_numbers/) | Fan-out / fan-in | Squares each integer in a list, in parallel |
| [`pipeline_demo/`](pipeline_demo/) | Function chaining | `n → double → +10 → "Final: <n>"` |
| [`batch_processor/`](batch_processor/) | Sub-orchestrations | Parent dispatches one child per group; each child fan-outs and squares its numbers |

## How to run an example locally (no Azure required)

```bash
# 1. Start the DTS emulator (Docker)
docker run -d --name dtsbox-emulator -p 8080:8080 mcr.microsoft.com/dts/dts-emulator:latest

# 2. From inside the example directory
cd examples/square_numbers     # or pipeline_demo / batch_processor

# 3. Start the worker in the background
dtsbox worker > /tmp/dtsbox-worker.log 2>&1 &

# 4. Invoke (see each example's README for the exact --input)
dtsbox run square_all --input '[3,5,7]'                          # square_numbers
dtsbox run process_pipeline --input '5'                          # pipeline_demo
dtsbox run batch_processor --input '[[1,2,3],[4,5],[6,7,8,9]]'   # batch_processor

# 5. View the per-step output as JSON
dtsbox logs <instance-id-printed-above> --json

# 6. Stop the worker and emulator when done
pgrep -f "dtsbox worker" | head -1 | xargs kill
docker rm -f dtsbox-emulator
```

## How these differ from what `dtsbox init` creates

The default `dtsbox init` scaffold writes activities that call `dtsbox.run_sandbox_step(...)`,
which requires real Azure ACA SandboxGroups (no local sandbox runtime exists today). These
examples replace that call with a **smoke-test stub** that returns the same dict shape
(`{stdout, sandbox_id, elapsed_seconds}`) in pure Python, so the orchestration flow can be
exercised against the local DTS emulator without any Azure cost.

To turn an example into a real Azure project, swap each stub for the real `run_sandbox_step`
version shown as a comment at the top of each activity file, then run `dtsbox setup` +
`dtsbox publish`.
