# dtsbox-builder

A GitHub Copilot CLI skill that guides you through building a new
[`dtsbox`](https://github.com/nirmash/dts-sandbox-poc) project from scratch.

Pick a Durable Task pattern, answer 2-3 questions, get a working durable workflow with ephemeral
sandbox execution — locally testable and ready to deploy to Azure.

## What you get

When you type `/dtsbox-builder` in Copilot CLI, the skill:

1. Asks you which Durable Task pattern fits your use case (fan-out, chaining, or sub-orchestrations)
2. Asks 2-3 focused questions about what each step or branch does
3. Runs `dtsbox init <name>` to scaffold a new project
4. Uses `dtsbox add activity <name>` and `dtsbox add orchestrator <name> --pattern …` to
   generate the right templates, then customizes them with your answers
5. Walks you through testing it locally against the DTS emulator
6. Optionally walks you through deploying to Azure (always asks before any command that costs money)

You stay in control: the skill **never auto-commits** generated files, **never auto-installs**
dependencies, and **always prompts** before running Azure-billable commands.

## v1 scope

Three patterns supported now:
- **Fan-out / fan-in** — process N items in parallel
- **Function chaining** — sequential pipeline: step1 → step2 → step3
- **Sub-orchestrations** — parent workflow dispatches child workflows

Four patterns coming in v2:
- Async HTTP API, Monitor, Human interaction, Eternal (with native support)

## Prerequisites

Before invoking the skill, install:

- [`dtsbox`](https://github.com/nirmash/dts-sandbox-poc) — `pip install dtsbox`
- DTS local emulator — a Docker container (NOT a pip package):
  ```bash
  docker run -d --name dtsbox-emulator -p 8080:8080 mcr.microsoft.com/dts/dts-emulator:latest
  ```
  Requires Docker Desktop (macOS/Windows) or Docker Engine (Linux).
- [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli)
- Python 3.12+
- For full end-to-end runs (including sandbox execution): Azure CLI (`az`), an active subscription,
  and `az login` — `dtsbox.run_sandbox_step` always requires real Azure Container Apps
  SandboxGroups; there is no local sandbox runtime today. The skill offers a smoke-test path that
  stubs out sandbox calls so you can validate orchestration locally without Azure.

The skill checks these at the start and gives you clear install instructions if anything is missing.
It does **not** install anything for you.

## Install

This skill is distributed manually via `git clone` (no `gh skill install` required). Always pulls
the latest `main` — no version pinning.

```bash
mkdir -p ~/.copilot/skills
git clone https://github.com/nirmash/dtsbox-builder.git ~/.copilot/skills/dtsbox-builder
```

To update later:
```bash
cd ~/.copilot/skills/dtsbox-builder && git pull
```

## Use

Open a fresh directory where you want the new project to live, then launch Copilot CLI and type:

```
/dtsbox-builder
```

The skill takes it from there.

## Repo layout

```
dtsbox-builder/
├── SKILL.md                 # main playbook the LLM follows
├── README.md                # this file
├── reference/
│   ├── concepts.md          # DTS mental model the skill teaches on demand
│   ├── commands.md          # dtsbox CLI command reference
│   └── yaml-schema.md       # dtsbox.yaml schema reference
├── patterns/
│   ├── fan-out.md           # fan-out / fan-in playbook + code template
│   ├── chaining.md          # function chaining playbook + code template
│   └── sub-orchestrations.md  # sub-orchestrations playbook + code template
└── scripts/
    └── check-emulator.sh    # detect DTS emulator (installed? running?)
```

All content is markdown. Zero build step, zero Python dependencies for the skill itself (the
`dtsbox` CLI it invokes is a separate install).

## Contributing

This skill is intentionally minimal. The three v1 patterns cover ~80% of real-world workflow
shapes. To propose a new pattern:

1. Open an issue describing the use case and which existing pattern doesn't fit
2. Reference the corresponding `dtsbox` scaffolding (if it doesn't exist yet in the `dtsbox` CLI,
   that gets built first)
3. Submit a PR adding `patterns/<your-pattern>.md` following the existing playbook structure

## License

MIT — see [LICENSE](LICENSE).
