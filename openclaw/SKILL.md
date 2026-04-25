---
name: openclaw
description: Use when the user wants to install, update, check, repair, snapshot, or report on OpenClaw on this Mac, OR invokes `/openclaw …`. Sub-commands: setup, update, doctor, status, backup. Source at `~/openclaw`; user state at `~/.openclaw/`.
---

# OpenClaw lifecycle

Umbrella skill for managing the OpenClaw productive coding agent on this host.

## Dispatch

Parse the sub-command from the invocation:
- If invoked with `args` (e.g. via slash command `$ARGUMENTS`), the first whitespace-delimited token is the sub-command.
- Otherwise infer from the user's request: install/setup → `setup`; pull/upgrade/refresh → `update`; check/diagnose/health → `doctor`; show/snapshot/report → `status`; snapshot config/save state → `backup`.

Then **Read the matching sub-doc and follow it**:

| Sub | File |
|---|---|
| `setup`   | `setup.md`   |
| `update`  | `update.md`  |
| `doctor`  | `doctor.md`  |
| `status`  | `status.md`  |
| `backup`  | `backup.md`  |

If the sub-command is missing or unrecognized, print this menu and stop:

```
/openclaw <sub>
  setup    First-time host install (pnpm install + build, bootstrap ~/.openclaw)
  update   Pull latest source, rebuild, run doctor (auto-backups first)
  doctor   Run openclaw doctor and interpret the output
  status   Read-only health snapshot (no mutations)
  backup   Tarball ~/.openclaw/ to ~/.openclaw/backups/
```

## Conventions for all sub-docs

- **Host-only path.** Source lives at `~/openclaw`; user state at `~/.openclaw/`. Don't propose Docker hosting (see project memory on host-vs-Docker).
- **Confirm before mutating.** Show the planned actions and ask before executing anything that writes outside `~/.openclaw/backups/`.
- **Auto-backup before mutation.** Any sub-doc that writes to `~/.openclaw/` runs `backup.md`'s script first.
- **Defer to OpenClaw's own commands.** Use `pnpm openclaw …` and `openclaw doctor`. Do not reimplement what OpenClaw already does.
