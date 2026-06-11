# Example: `pipeline_demo` — Function chaining

Three-step sequential pipeline: input number → double it → add 10 → format as string. One
orchestrator + three activities. Ships with smoke-test stubs so it runs locally against the DTS
emulator without Azure.

## Run it

```bash
docker run -d --name dtsbox-emulator -p 8080:8080 mcr.microsoft.com/dts/dts-emulator:latest
cd examples/pipeline_demo
dtsbox worker > /tmp/dtsbox-worker.log 2>&1 &
sleep 5
dtsbox run process_pipeline --input '5'
# Wait a few seconds, then:
dtsbox logs <instance-id-printed-above> --json
```

## Expected output

```json
[
  {
    "step_1": {"stdout": "10", "sandbox_id": "local-smoke", "elapsed_seconds": 0.0},
    "step_2": {"stdout": "20", "sandbox_id": "local-smoke", "elapsed_seconds": 0.0},
    "step_3": {"stdout": "Final: 20", "sandbox_id": "local-smoke", "elapsed_seconds": 0.0}
  }
]
```

> ⚠️ `dtsbox logs <id>` without `--json` will show "1 activities" — that's the orchestrator's
> single return value, not the step count. Always use `--json` to see per-step output for chains.

## File map

- `orchestrators/process_pipeline.py` — chaining orchestrator (3 sequential `call_activity` yields)
- `activities/double_it.py` — step 1; first step receives raw workflow input
- `activities/add_ten.py` — step 2; later steps unwrap previous step's dict via `input_data["stdout"]`
- `activities/format_report.py` — step 3; emits a formatted string
- `dtsbox.yaml`, `Dockerfile`, `requirements.txt`, `worker.py` — produced by `dtsbox init`

## To run against real Azure sandboxes

Replace each activity's stub body with a real `run_sandbox_step` call (a commented template is at
the top of each file), then `dtsbox setup` + `dtsbox publish`.
