# /openclaw status — read-only snapshot

Goal: one-screen health snapshot of OpenClaw on this host. **Never mutates anything.**

## Run

```bash
~/agentry/openclaw/scripts/status.sh
```

The script prints a structured report covering:

- **Source repo**: path, current commit, branch, ahead/behind `origin/main`, dirty?
- **Build state**: `node_modules` present? package count; last `pnpm install` mtime; last `pnpm build` artifacts mtime.
- **User config**: `~/.openclaw/openclaw.json` exists + mtime; `~/.openclaw/agents/` count; presence of `credentials/`, `identity/`.
- **Update notifier**: `~/.openclaw/update-check.json` last check timestamp + last available version.
- **Docker state**: daemon running? any local images named `*openclaw*`?
- **Global binary**: any `openclaw` on `PATH`? (expected: no — this is a source install).

## Report

Read the script's output and present it as a Markdown table or bullet list. Highlight anything actionable in **bold**:
- node_modules absent → suggest `/openclaw setup`
- repo behind origin/main → suggest `/openclaw update`
- update-check older than 30 days → noted, not actionable
- doctor not run recently → suggest `/openclaw doctor`

Do not run `pnpm openclaw doctor` from status; doctor is a separate sub-command.
