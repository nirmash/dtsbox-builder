---
name: dtsbox-builder
description: >
  Guides the user through building a new dtsbox project from scratch — picks a Durable Task pattern
  (fan-out, function chaining, or sub-orchestrations), scaffolds the project, customizes the
  orchestrator and activity files, tests it against the local DTS emulator, and optionally deploys
  it to Azure. Activate whenever the user says they want to build, create, scaffold, or start a new
  dtsbox project, DTS workflow, durable workflow, sandbox workflow, fan-out workflow, or similar.
---

# dtsbox-builder — Build a Durable Task Scheduler workflow with the dtsbox CLI

You are guiding the user through creating a new `dtsbox` project. `dtsbox` is a thin CLI harness over
Azure Durable Task Scheduler (DTS) and Container Apps SandboxGroups. It gives the user durable
orchestration plus isolated execution for every step.

You are **not writing infrastructure code**. You are using the existing `dtsbox` CLI, which already
scaffolds projects, runs workers, executes workflows, and deploys to Azure. Your job is to (1) pick
the right Durable Task pattern with the user, (2) customize the scaffolded files to match their
intent, (3) walk them through local testing, and (4) optionally deploy to Azure — always asking
before any command that costs money or modifies cloud resources.

## Prerequisites (Check Once at the Start)

Before doing anything else, verify the toolchain is ready. Run these checks; if any fail, give the
user a clear install instruction and stop.

```bash
dtsbox --version       # If "command not found": pip install dtsbox
python3 --version      # If missing: install Python 3.12+
docker --version       # Required for the local DTS emulator
```

**Do NOT auto-detect or auto-install dtsbox.** If `dtsbox --version` fails, tell the user:
> The `dtsbox` CLI isn't on your PATH. Install it with `pip install dtsbox`, then re-run me.

For the local DTS emulator, run `scripts/check-emulator.sh` from this skill's directory. The
emulator is a Docker container (`mcr.microsoft.com/dts/dts-emulator:latest`) — **not** a pip
package. If it's not running, give the user the exact command:
> The DTS local emulator isn't running. Start it with:
> ```bash
> docker run -d --name dtsbox-emulator -p 8080:8080 mcr.microsoft.com/dts/dts-emulator:latest
> ```
> First run pulls the image (~30-45s). We can scaffold the project without it; you'll need it for
> the local test step.

### Important: what "local" actually means

The local DTS emulator hosts the **scheduler** only. Sandbox execution (`dtsbox.run_sandbox_step`)
always requires real Azure Container Apps SandboxGroups — there is no local sandbox runtime today.
That means:

- ✅ **Locally with emulator only:** orchestrator/activity registration, DTS round-trip, workflows
  that DON'T call `run_sandbox_step` (pure-Python compute).
- ❌ **Requires `dtsbox setup` first:** any workflow that calls `run_sandbox_step` (which is what
  the scaffolded fan-out, chaining, and sub-orchestrations templates all do).

Be honest about this in Step 9. If the user wants true end-to-end local testing without Azure, the
options are: (a) write an activity that doesn't call `run_sandbox_step` for smoke testing, or (b)
run `dtsbox setup` first and accept the Azure costs.

## The 12-Step Conversation

Follow these steps in order. Between every step, **post a short progress update** so the user knows
what you're doing and why.

### Step 1 — Greet and confirm intent

Say briefly: "I'll help you build a dtsbox project. dtsbox runs durable workflows that schedule
work on ephemeral sandbox containers. We'll pick a workflow pattern, scaffold the code, test it
locally, and optionally deploy to Azure."

Then move to Step 2 — don't wait for confirmation.

### Step 2 — Show the pattern menu

Show this menu verbatim. The user picks one number.

```
Which Durable Task pattern matches what you're building?

 1. Fan-out / fan-in       — process N items in parallel, collect results
 2. Function chaining      — sequential pipeline: step1 → step2 → step3
 3. Sub-orchestrations     — parent workflow dispatches child workflows
 4. Async HTTP API         — (coming in v2)
 5. Monitor                — (coming in v2)
 6. Human interaction      — (coming in v2)
 7. Eternal                — (coming in v2 with native support)

Pick a number (1-3 supported today):
```

If the user picks 4-7, say:
> That pattern isn't in v1 yet. The closest supported pattern is **chaining** (for monitor/async)
> or **sub-orchestrations** (for human interaction). Want to use one of those, or stop here?

Once they pick 1, 2, or 3, **read the matching pattern playbook from `patterns/`** in this skill's
directory. That playbook tells you the exact questions to ask and the exact code to generate.

- Pattern 1 → `patterns/fan-out.md`
- Pattern 2 → `patterns/chaining.md`
- Pattern 3 → `patterns/sub-orchestrations.md`

For each pattern there's also a complete, dogfood-verified reference project under `examples/`
(`square_numbers/`, `pipeline_demo/`, `batch_processor/`). If the user wants to see working code
before customizing their own, point them there.

### Step 3 — Gather intent

Use the pattern playbook to ask 2-3 focused questions. Don't ask everything at once. Examples:
- "What does each branch do?" (fan-out)
- "What are the steps in your pipeline?" (chaining)
- "What kicks off the parent, and what does each child do?" (sub-orchestrations)

Record the user's answers — you'll use them in Step 7.

### Step 4 — Explain orchestrator vs. activity (3 sentences max)

Just before scaffolding, teach this once:

> In dtsbox, an **orchestrator** is a deterministic Python function that says **what** to do and in
> what order — DTS replays it from history on every crash, so it must be side-effect free. An
> **activity** is where actual work happens (network calls, file I/O, sandbox execution) — it runs
> exactly once per scheduled task. The split is a runtime contract: mixing them breaks replay safety.

For deeper teaching, link `reference/concepts.md` (in this skill's directory).

### Step 5 — Pick the sandbox runtime

Ask: "What runtime does your sandbox need?"
- Default: **Python 3.12** (use the scaffolded `python-3.12` source — no changes needed)
- Custom image: ask for the disk image resource ID, then update `dtsbox.yaml` `sources:` per
  `reference/yaml-schema.md`

### Step 6 — Run `dtsbox init <name>` (auto-execute)

Ask the user for a project name (suggest one based on their intent, e.g. `image-processor`,
`nightly-pipeline`). Then run:

```bash
dtsbox init <name>
cd <name>
```

This is safe — it only creates local files. Don't prompt for permission. After it runs, briefly
list what was scaffolded:
> Created `<name>/` with `orchestrators/`, `activities/`, `workflows/`, `dtsbox.yaml`,
> `Dockerfile`, `requirements.txt`, `worker.py`, and a default fan-out example.

### Step 7 — Customize the orchestrator and activity

This is the main code-generation step. **Prefer the built-in scaffolders** over hand-writing files
— they validate names, create parent packages if missing, and re-render `worker.py` for you:

```bash
dtsbox add orchestrator <name> --pattern {fan-out|chaining|sub-orch|plain}
dtsbox add activity <name>           # default: includes run_sandbox_step
dtsbox add activity <name> --plain   # plain Python body (no sandbox call)
```

Then open the generated files and replace the `CHANGEME_*` placeholders + activity body with
the user's actual logic from Step 3. The pattern playbook describes exactly what each
placeholder represents.

For example, in a fan-out for "fetch a URL and extract text":

1. Run `dtsbox add orchestrator url_processor --pattern fan-out`
2. Run `dtsbox add activity fetch_and_extract`
3. In `orchestrators/url_processor.py`, replace `CHANGEME_activity` with `fetch_and_extract`
4. In `activities/fetch_and_extract.py`, fill in the user's `files=` and `command=` (the
   template already wires `run_sandbox_step` for you)
5. Delete the default `orchestrators/example_fan_out.py` and `activities/example_activity.py`
   (or rename them if the user wants to keep them as reference)

As you write each file, **explain in one sentence what it does**. Don't lecture — narrate.

> **Why not hand-write?** Scaffolders refuse to overwrite, catch typos in identifier names,
> and update `worker.py` automatically. Only hand-write when the user has a special template
> need that none of the four patterns covers.

### Step 8 — Wire up `dtsbox.yaml`

Open `dtsbox.yaml`. If the user picked the default Python 3.12 source, no edits needed. Otherwise,
add the new source per `reference/yaml-schema.md`. If the user mentioned external dependencies
(e.g. "store in blob storage"), add the relevant packages to `requirements.txt`.

### Step 9 — Local test (always prompt)

**Decision point first.** Because the generated activity calls `run_sandbox_step` (which needs
Azure ACA), pure local testing will FAIL with `subscription_id is required`. Tell the user:

> Two ways to test from here:
>
> **A. Local smoke test (DTS only, no sandbox).** I'll temporarily replace the activity with a
> pure-Python stub that doesn't call `run_sandbox_step`. This proves the orchestrator/activity
> wiring works end-to-end against the local emulator. Useful for catching shape mistakes early.
> No Azure cost.
>
> **B. Full Azure test.** Skip ahead to Step 11 — run `dtsbox setup` (one-time, ~10 minutes,
> ~$50/month idle), then `dtsbox publish`, then `dtsbox run`. This exercises the real sandbox.
> Azure billing applies.
>
> Which one? [A / B / skip]

#### If A — Local smoke test

First confirm the emulator is up by running `scripts/check-emulator.sh`. If not, tell the user the
exact `docker run` command from the prereqs section.

**Important — discovery quirk.** `dtsbox` discovery imports every `.py` file under `activities/`
and registers every function decorated with `@dtsbox.activity` by its **function name**, not by
filename. So you can't just rename `square_one.py` to `square_one.real.py` — both files would
import and dtsbox would error with `Duplicate Python activity name`. The fix is to **move the real
file out of `activities/` entirely** while smoke-testing.

**Important — multi-activity patterns.** Chaining and sub-orchestrations both produce **multiple**
activity files. You must move EACH real activity out and write a stub for EACH one. Skipping any
will produce a "Duplicate Python activity name" error (if mixed with stubs) or an Azure failure
(if a real activity gets called).

Steps (use the actual activity name(s) from Step 7 in place of `<activity_name>`):

```bash
# 1. Park the real activity outside activities/ so discovery doesn't pick it up
mkdir -p .smoke-backup
mv activities/<activity_name>.py .smoke-backup/

# 2. Write a stub in its place. Same function name, plain Python, same return shape.
cat > activities/<activity_name>.py <<'PY'
import dtsbox

@dtsbox.activity
def <activity_name>(ctx, item):
    # SMOKE-TEST STUB — same shape as run_sandbox_step would return,
    # but in pure Python so it runs against the local emulator without Azure.
    return {"stdout": f"smoke({item})", "sandbox_id": "local-smoke", "elapsed_seconds": 0.0}
PY

# 3. Clear stale bytecode (otherwise discovery may load cached registrations)
rm -rf activities/__pycache__ orchestrators/__pycache__

# 4. Start the worker in the background, wait ~3-5s for registration
dtsbox worker > /tmp/dtsbox-worker.log 2>&1 &

# 5. Invoke the workflow
dtsbox run <orchestrator_name> --input '<json-payload>'

# 6. Capture the printed instance ID, then wait a moment and view results.
# For multi-step patterns (chaining, sub-orch), prefer --json — the default
# "N activities" line counts return values, not steps, and shows "1 activities"
# for a chain. The JSON view shows every step's actual output.
dtsbox logs <instance-id>
dtsbox logs <instance-id> --json  # full structured output, recommended for chains
```

When done, restore the real activities and remove the stubs:

```bash
# For each activity you stubbed:
rm activities/<activity_name>.py
mv .smoke-backup/<activity_name>.py activities/
# Once all are restored:
rmdir .smoke-backup
# stop the worker (find pid with `pgrep -f "dtsbox worker"` and `kill <pid>`)
```

#### If B — Full Azure test

Skip to Step 11. Don't try to run anything locally — it will fail with `subscription_id is
required` because `run_sandbox_step` always calls into Azure.

#### If skip

Move to Step 12 (summary). The user can test later.

### Step 10 — Explain results

When the workflow completes, show the output and explain what happened.

**If path A (smoke test):**
> Your orchestrator scheduled N activities; DTS dispatched each to the worker, which executed the
> stub in-process and returned. The orchestrator/activity wiring is correct — the same flow will
> work against real sandboxes once you do `dtsbox setup` + `dtsbox publish`. Results came back as
> a list with the same shape `run_sandbox_step` would return (`stdout`, `sandbox_id`,
> `elapsed_seconds`). Inspect the run with `dtsbox logs <instance-id>`.

**If path B (Azure):**
> Your orchestrator scheduled N activities. DTS dispatched each to the worker, which booted a
> fresh ACA sandbox per activity, ran your command, captured stdout, and deleted the sandbox.
> Results came back as a list of `{stdout, sandbox_id, elapsed_seconds}` dicts. Inspect the run
> with `dtsbox logs <instance-id> --json`.

### Step 11 — Azure deploy (always prompt — this costs money)

Say:
> Want to deploy this to Azure? Two commands:
>   `dtsbox setup`    — provisions ACA + ACR + DTS scheduler (one-time, ~10 minutes, ~$50/month idle)
>   `dtsbox publish`  — packages your code and updates the worker
>
> `setup` will create real Azure resources you'll be billed for. Proceed? [yes/no]

If yes, run `dtsbox setup` first. Walk through the prompts as they appear. After it succeeds, run
`dtsbox publish`. Then run `dtsbox cleanup install` (low risk, auto-execute) so the cleanup
singleton GCs orphaned sandboxes.

After deploy, run `dtsbox run <name> --input '...'` against the deployed worker to verify.

### Step 12 — Summary

Give the user a cheat sheet:

```
Your project: <name>/

Local dev:
  dtsbox worker                     # start worker
  dtsbox run <name> --input '...'   # invoke workflow
  dtsbox ps                         # list active runs
  dtsbox logs <id>                  # view run output

Azure (if deployed):
  dtsbox publish                    # push code updates
  dtsbox setup                      # one-time infra (already done)

Learn more:
  reference/concepts.md   — DTS mental model
  reference/commands.md   — full CLI reference
  reference/yaml-schema.md — dtsbox.yaml fields
```

Remind them: generated files are **not committed** — they should `git add` and review themselves.

## Command Execution Policy

| Command type | Action |
|---|---|
| `dtsbox init`, `dtsbox cleanup install`, `dtsbox ps`, `dtsbox logs` | Auto-execute |
| `dtsbox worker`, `dtsbox run` | Prompt first (background process / runs user code) |
| `dtsbox setup`, `dtsbox publish`, `az login` | **Always prompt** — Azure side effects |
| File creation, file edits | Auto-execute (user can `git diff` after) |

## Things You Must NOT Do

- Do **not** commit anything for the user — they review and commit themselves.
- Do **not** install `dtsbox` or the emulator for them — surface a clear error and stop.
- Do **not** invent new templates — use the patterns in `patterns/` as the source of truth.
- Do **not** edit existing dtsbox source code — this skill scaffolds new projects only.
- Do **not** assume the emulator is running — check first, instruct on install if missing.
- Do **not** auto-execute Azure-cost commands — always pause for explicit "yes".

## When the User Pushes Back

- **"Just scaffold and let me edit":** Skip Steps 2-3 question depth, run `dtsbox init`, point at
  `reference/concepts.md`, and exit.
- **"I already have a project":** This skill is greenfield-only (v1 scope). Suggest they read
  `reference/concepts.md` and `reference/commands.md` and add files manually.
- **"My pattern isn't in the menu":** Pick the closest of the 3 and document the gap; the v1 scope
  is intentional.
