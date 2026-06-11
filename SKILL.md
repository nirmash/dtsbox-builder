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
```

**Do NOT auto-detect or auto-install dtsbox.** If `dtsbox --version` fails, tell the user:
> The `dtsbox` CLI isn't on your PATH. Install it with `pip install dtsbox`, then re-run me.

For the local emulator, run `scripts/check-emulator.sh` from this skill's directory (if available).
If the emulator isn't installed, instruct the user:
> The DTS local emulator isn't running. Install it with `pip install <emulator-package>` and start
> it before we test locally. We can still scaffold the project without it.

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

This is the main code-generation step. The pattern playbook tells you the exact files to write
and the exact template to fill in. **The user's answers from Step 3 fill in the variable parts.**

For example, in a fan-out for "fetch a URL and extract text":
- Write `orchestrators/url_processor.py` based on the fan-out template
- Write `activities/fetch_and_extract.py` filling in the user's command and files
- Delete the default `orchestrators/example_fan_out.py` and `activities/example_activity.py`
  (or rename them if the user wants to keep them as reference)

As you write each file, **explain in one sentence what it does**. Don't lecture — narrate.

### Step 8 — Wire up `dtsbox.yaml`

Open `dtsbox.yaml`. If the user picked the default Python 3.12 source, no edits needed. Otherwise,
add the new source per `reference/yaml-schema.md`. If the user mentioned external dependencies
(e.g. "store in blob storage"), add the relevant packages to `requirements.txt`.

### Step 9 — Local test (always prompt)

Say:
> Ready to test locally? I'll start the worker in one terminal and run the workflow in another.
> This requires the DTS emulator to be running (run `scripts/check-emulator.sh` if you're unsure).
> Proceed? [yes/no]

If yes, run:

```bash
# Terminal 1 (background process)
dtsbox worker
```

Wait a few seconds for the worker to register, then in another shell run:

```bash
dtsbox run <orchestrator_name> --input '<json-payload>'
```

Construct the input from the user's Step 3 answers. For fan-out, that's a list. For chaining, an
object. For sub-orchestrations, the parent's payload.

### Step 10 — Explain results

When the workflow completes, show the output and explain what happened in 4 sentences:
> The orchestrator scheduled N activities. DTS dispatched each to the worker, which booted a fresh
> sandbox per activity, ran your command, captured stdout, and deleted the sandbox. Results came
> back as a list of `{stdout, sandbox_id, elapsed_seconds}` dicts. You can re-query the run with
> `dtsbox logs <instance-id>`.

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
