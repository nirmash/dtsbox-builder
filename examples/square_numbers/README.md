# Example: `square_numbers` — Fan-out / fan-in

Squares each integer in an input list, in parallel. One orchestrator + one activity. Ships with
a smoke-test stub so it runs locally against the DTS emulator without Azure.

## Run it

```bash
docker run -d --name dtsbox-emulator -p 8080:8080 mcr.microsoft.com/dts/dts-emulator:latest
cd examples/square_numbers
dtsbox worker > /tmp/dtsbox-worker.log 2>&1 &
sleep 5
dtsbox run square_all --input '[3,5,7]'
# Wait a few seconds, then:
dtsbox logs <instance-id-printed-above>
```

## Expected output

```
─── Activity 1 [exit 0] (0.0s) ───
9

─── Activity 2 [exit 0] (0.0s) ───
25

─── Activity 3 [exit 0] (0.0s) ───
49

Status: COMPLETED (3 activities)
```

## File map

- `orchestrators/square_all.py` — fan-out orchestrator (deterministic)
- `activities/square_one.py` — **smoke-test stub**; real version is shown in comments
- `dtsbox.yaml`, `Dockerfile`, `requirements.txt`, `worker.py` — produced by `dtsbox init`

## To run against real Azure sandboxes

Replace the body of `activities/square_one.py` with the commented `run_sandbox_step` version, then:

```bash
dtsbox setup        # ~10 min, ~$50/month idle
dtsbox publish
dtsbox run square_all --input '[3,5,7]'
```
