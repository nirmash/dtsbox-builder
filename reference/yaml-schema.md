# `dtsbox.yaml` Schema Reference

The single config file that drives every dtsbox project. The skill reads this when customizing
sources, schedules, or the azure block.

## Minimal default (what `dtsbox init` writes)

```yaml
sources:
  python-3.12:
    type: code
    image: python-3.12
    timeout_seconds: 300
cleanup:
  grace_minutes: 5
```

## Full schema

```yaml
sources:
  <source-name>:                    # lookup key used in dtsbox.run_sandbox_step(source=...)
    type: code | image | snapshot
    image: <public-image-name>      # required when type=code (e.g. "python-3.12")
    disk_id: <azure-resource-id>    # required when type=image
    snapshot_id: <azure-resource-id># required when type=snapshot
    timeout_seconds: <int>          # per-sandbox exec timeout (default 300)

cleanup:
  grace_minutes: 5                  # GC orphaned sandboxes older than N minutes

workflows:                          # optional — declare eternal workflows
  <workflow-name>:
    eternal: true                   # auto-start as a singleton on worker boot
    orchestrator: <module.fn>       # required for eternals; orch must call continue_as_new

schedules:                          # optional — install with `dtsbox schedules install`
  <schedule-name>:
    workflow: <workflow-name>
    cron: "*/10 * * * *"            # croniter syntax
    input: { ... }                  # JSON-serializable input

azure:                              # populated by `dtsbox setup` — do not edit by hand
  subscription: ""
  resource_group: ""
  acr: ""
  aca_environment: ""
  aca_app: ""
  sandbox_group: ""
  dts_endpoint: ""
  taskhub: ""
  region: ""
  identity: ""
  storage_account: ""
  code_share: dtsbox-code
```

## When the skill edits this file

### Adding a custom Python image
```yaml
sources:
  python-3.11:
    type: code
    image: python-3.11
    timeout_seconds: 300
```

### Adding a private disk image
```yaml
sources:
  my-prebaked:
    type: image
    disk_id: /subscriptions/<sub>/resourceGroups/<rg>/sandboxGroups/<sg>/diskImages/<id>
    timeout_seconds: 600
```

### Adding a recurring schedule
```yaml
schedules:
  nightly-batch:
    workflow: example_fan_out
    cron: "0 2 * * *"               # 2am daily
    input: [1, 2, 3]
```

## Rules the skill enforces

- Never edit the `azure:` block manually — `dtsbox setup` writes it.
- Every source name used in `run_sandbox_step(source=...)` must exist under `sources:`.
- `eternal: true` workflows require `continue_as_new(...)` in the orchestrator.
- `cleanup.grace_minutes` must be > 0; default is fine for most projects.
