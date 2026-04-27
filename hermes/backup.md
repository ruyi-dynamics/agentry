# /hermes backup — snapshot ~/.hermes/

Goal: zip up `~/.hermes/` (config, .env, sessions, memories, hooks, skills, cron — but **not** the `hermes-agent` source checkout) so state can be restored or moved to another machine.

## Run

```bash
hermes backup                                  # full snapshot to ~/hermes-backup-<ts>.zip
hermes backup --quick                          # only critical state files (config, state.db, .env, auth, cron) — fast
hermes backup -o ~/.hermes/backups/snap.zip    # explicit output path
hermes backup --quick -l "before-update"       # labeled quick snapshot
```

Recommended: run `--quick -l "before-<thing>"` automatically before any mutating sub-command in this skill (the convention from `openclaw/backup.md`'s auto-backup-before-mutation rule).

## Restore

```bash
hermes import ~/path/to/hermes-backup-<ts>.zip
```

Restores into `~/.hermes/`. If `~/.hermes/` exists, Hermes will refuse to overwrite — move it aside (`mv ~/.hermes ~/.hermes.<ts>`) before restoring.

## What's NOT in the backup

- `~/.hermes/hermes-agent/` (the code checkout) — re-cloned by `hermes update` or the installer, no value in backing it up
- `~/.hermes/audio_cache/`, `~/.hermes/image_cache/` — regenerable
- `~/.hermes/logs/` — historical, not state

If the user wants those too, recommend a plain `tar -czf` of the whole `~/.hermes/` tree.

## Don't

- Don't copy `~/.hermes/.env` into git or anywhere shared — it's plaintext API keys.
- Don't run `hermes import` over a live install without backing the live `~/.hermes/` up first.
