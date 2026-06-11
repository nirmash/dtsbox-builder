# dtsbox CLI Reference (for the skill)

Quick reference for every `dtsbox` command the skill invokes.

## Project lifecycle

### `dtsbox init <name>`
Scaffolds a new project directory with `orchestrators/`, `activities/`, `workflows/`,
`dtsbox.yaml`, `Dockerfile`, `requirements.txt`, `worker.py`, and a default fan-out example.
- Safe to auto-execute.
- Fails if `<name>` already exists.

### `dtsbox worker`
Starts the DTS worker in the current project. Auto-discovers `orchestrators/` and `activities/`.
- Local default: connects to `http://localhost:8080`, taskhub `default` (the emulator).
- Azure: reads `azure.dts_endpoint` and `azure.taskhub` from `dtsbox.yaml`.
- Long-running — start in a separate terminal or as a background process.
- **Prompt the user before starting.**

### `dtsbox run <workflow_name> --input '<json>'`
Invokes a workflow once. `<workflow_name>` is either a YAML workflow name or a Python orchestrator
function name (auto-discovered from `orchestrators/`).
- `--input` accepts JSON. Examples: `'[1,2,3]'`, `'{"url": "https://x"}'`, `'{}'`.
- Optional `--cron '*/10 * * * *'` schedules a recurring run instead of one-shot.
- **Prompt the user before running** (it runs their code).

### `dtsbox ps`
Lists active workflow instances. Safe to auto-execute.

### `dtsbox logs <instance-id> [--json]`
Shows captured output for a completed or running workflow. Safe to auto-execute.

## Cleanup singleton

### `dtsbox cleanup install`
Installs the eternal cleanup orchestrator on the DTS scheduler. Idempotent.
- Safe to auto-execute (low risk).
- Should always be run once after `dtsbox setup` + `dtsbox publish`.

## Azure deployment

### `dtsbox setup`
Provisions Azure infrastructure: ACR, ACA environment, ACA app, SandboxGroup, DTS scheduler, role
assignments. One-time per project. Takes ~10 minutes.
- **ALWAYS PROMPT.** This creates billable Azure resources.
- Requires `az login` first.
- Populates the `azure:` block in `dtsbox.yaml`.

### `dtsbox publish`
Packages the current project, uploads to the Azure Files volume, and updates the worker. Re-run
after every code change.
- **ALWAYS PROMPT.** Modifies the running Azure deployment.

### `dtsbox teardown`
Deletes all Azure resources created by `dtsbox setup`.
- **ALWAYS PROMPT.** Destructive. Confirm the project name back to the user.

## Schedules and eternals

### `dtsbox schedules install`
Installs all `schedules:` declared in `dtsbox.yaml` as DTS scheduled triggers.
- Prompt before running (creates DTS resources).

### `dtsbox schedules list`
Lists declared schedules and their runtime status. Safe to auto-execute.

### `dtsbox eternal install <workflow>`
Installs a named eternal orchestrator as a singleton. The orchestrator must call
`ctx.continue_as_new(...)` or history grows unbounded.
- Prompt before running.

## Flags common to most commands

- `--project PATH` / `-p PATH` — point at a project root other than the cwd.
- `--input JSON` / `-i JSON` — only for `run`.
