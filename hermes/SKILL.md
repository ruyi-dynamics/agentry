---
name: hermes
description: Use when the user wants to install, update, check, repair, snapshot, or report on Hermes Agent (NousResearch) on this Mac, OR invokes `/hermes …`. Sub-commands: setup, update, doctor, status, backup, dashboard, pairing, claw-migrate. Code at `~/.hermes/hermes-agent`; user state at `~/.hermes/`.
---

# Hermes Agent lifecycle

Umbrella skill for managing the [Hermes Agent](https://github.com/NousResearch/hermes-agent) on this host. Hermes is a Python-based AI agent framework from NousResearch with both interactive CLI (`hermes`) and a messaging gateway daemon for Telegram/Discord/Slack/WhatsApp/Signal.

## Dispatch

Parse the sub-command from the invocation:
- If invoked with `args` (slash command), the first whitespace-delimited token is the sub-command.
- Otherwise infer from the user's request: install/setup → `setup`; pull/upgrade/refresh → `update`; check/diagnose/health → `doctor`; show/snapshot/report → `status`; snapshot config/save state → `backup`; dashboard/web/url → `dashboard`; gateway/daemon/messaging service/install service → `gateway`; approve/pairing/whitelist user → `pairing`; install local skill / cron / schedule → `skills`; migrate/import openclaw → `claw-migrate`.

Then **Read the matching sub-doc and follow it**:

| Sub | File |
|---|---|
| `setup`         | `setup.md`         |
| `update`        | `update.md`        |
| `doctor`        | `doctor.md`        |
| `status`        | `status.md`        |
| `backup`        | `backup.md`        |
| `dashboard`     | `dashboard.md`     |
| `gateway`       | `gateway.md`       |
| `pairing`       | `pairing.md`       |
| `skills`        | `skills.md`        |
| `claw-migrate`  | `claw-migrate.md`  |

If the sub-command is missing or unrecognized, print this menu and stop:

```
/hermes <sub>
  setup         First-time install + interactive (or non-interactive) config
  update        hermes update — git pull + reinstall deps
  doctor        hermes doctor (--fix optional) and interpret output
  status        Read-only health snapshot (hermes status [--all|--deep])
  backup        hermes backup [--quick] — zip of ~/.hermes/ (excludes hermes-agent/)
  dashboard     Open the Hermes web dashboard (foreground command, port 9119)
  gateway       Manage the messaging + cron daemon (install/start/stop/status)
  pairing       Approve/revoke per-user DM pairing codes
  skills        Install local agentry skills into Hermes; schedule via cron
  claw-migrate  hermes claw migrate — pull settings/memory/skills from OpenClaw
```

## Conventions for all sub-docs

- **Host-only path.** Code lives at `~/.hermes/hermes-agent` (cloned by the installer); user state at `~/.hermes/`. Don't propose Docker hosting (project memory: agents conflict with Docker).
- **Confirm before mutating.** Show the planned actions and ask before executing anything that writes outside `~/.hermes/` snapshots.
- **Auto-backup before mutation.** Any sub-doc that writes to `~/.hermes/` runs `hermes backup --quick` first (Hermes's built-in zip; we don't need a custom script).
- **Defer to Hermes's own commands.** Use `hermes <sub>` directly. Almost every operation has a built-in (`update`, `doctor`, `backup`, `status`, `dashboard`, `pairing`) — this skill is mostly orchestration + gotcha capture, not reimplementation.
- **Non-interactive friendly.** `hermes setup --non-interactive` and `hermes doctor --fix` exist; prefer them in non-TTY contexts to avoid TUI hangs (see OpenClaw's same lesson in `~/agentry/openclaw/doctor.md`).
- **PATH note.** The installer symlinks the CLI to `~/.local/bin/hermes`. That dir is already on PATH on this machine. If `which hermes` returns empty in a fresh shell, `source ~/.zshrc` or use the absolute path.
