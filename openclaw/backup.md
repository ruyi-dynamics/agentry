# /openclaw backup — snapshot user state

Goal: produce a timestamped tarball of `~/.openclaw/` user state to `~/.openclaw/backups/`.

## Run

```bash
~/agentry/openclaw/scripts/backup.sh
```

The script:
1. Creates `~/.openclaw/backups/` if missing.
2. Tarballs these paths (exists-checked individually): `~/.openclaw/openclaw.json`, `~/.openclaw/agents/`, `~/.openclaw/credentials/`, `~/.openclaw/identity/`, `~/.openclaw/cron/`, `~/.openclaw/devices/`.
3. Output filename: `~/.openclaw/backups/openclaw-YYYY-MM-DDTHHMMSS.tar.gz`.
4. Prints final size and SHA-256.
5. Prunes older-than-30-day backups (configurable via `OPENCLAW_BACKUP_RETAIN_DAYS` env var).

Excluded by default (large, regenerable, or not user state): `~/.openclaw/logs/`, `~/.openclaw/workspace/`, `~/.openclaw/canvas/`, `~/.openclaw/completions/`, `*.bak*`.

## Report

After the script exits, summarize: tarball path, size, file count inside the archive, and what was pruned. If any path was missing (e.g. fresh install with no `agents/` yet), note it but don't fail.

## When to run

- Manually before any operation that mutates `~/.openclaw/` and isn't already covered by `update.md`.
- Automatically called by `update.md` step 0.
- Before any user-driven cleanup or migration.
