# /hermes skills — install, manage, and reference local agentry skills inside Hermes

Goal: get Claude Code skills authored in `~/agentry/<name>/` to also load inside Hermes, so the same dispatcher logic that drives `/openclaw setup` from Claude Code can drive a scheduled `hermes cron` job that runs `/openclaw backup` at 3am.

## Two skill ecosystems on this machine

| System | Looks in | Source field shown |
|---|---|---|
| Claude Code | `~/.claude/skills/<name>/` | (n/a — see Skill tool) |
| Hermes | `~/.hermes/skills/<category>/<name>/` | `builtin` / `hub` / `local` |

Skills in `~/agentry/` can be **symlinked into both** so a single source of truth drives both runtimes. We already do this for Claude Code (`ln -s ~/agentry/openclaw ~/.claude/skills/openclaw`); same trick works for Hermes.

## File-format compatibility

The format is **the same**:
- A directory containing a `SKILL.md` with frontmatter `name`, `description`, plus body of trigger conditions + dispatch table.
- Optional sub-docs (`setup.md`, `doctor.md`, etc.) referenced from `SKILL.md`.

So no rewrite is needed — symlink and ship.

## Add a local skill

```bash
# Pick a category subdirectory (Hermes groups skills by category — see ~/.hermes/skills/ for existing ones)
ln -sf ~/agentry/openclaw ~/.hermes/skills/devops/openclaw

# Verify Hermes discovers it
hermes skills list | grep openclaw
# │ openclaw │ devops │ local │ local │

hermes skills list | tail -1
# 0 hub-installed, 74 builtin, 1 local
```

No restart needed — Hermes rescans the skills tree on each invocation.

If you want it under a different category, the existing ones are: `apple`, `autonomous-ai-agents`, `creative`, `data-science`, `devops`, `developer-tools`, `enterprise`, `entertainment`, `finance`, `food`, `gateway-tooling`, `health`, `lifestyle`, `media`, `messaging`, `office-productivity`, `personal`, `productivity-aids`, `science`, `social-media`, `software-development`, `system-admin`, `tools`, `travel`, `video-content`, `webhook-subscriptions`. Pick whichever is the closest semantic fit; Hermes treats them as organizational only.

## Schedule tasks with `hermes cron`

Once a skill is loaded, `hermes cron create` can attach it to scheduled prompts via `--skill <name>`:

```bash
# Schedule openclaw backup every morning at 3am (delivered to local log, no chat target)
hermes cron create '0 3 * * *' \
  'run /openclaw backup and log the resulting tarball path' \
  --skill openclaw --deliver local --name 'openclaw-daily-backup'

# Run openclaw doctor every Sunday at noon and post results to Feishu
hermes cron create '0 12 * * 0' \
  'run /openclaw doctor and summarize anything that is not green' \
  --skill openclaw --deliver feishu:<chat_id> --name 'openclaw-weekly-doctor'

# Quick interval syntax also works (every 6 hours)
hermes cron create 'every 6h' \
  'run /openclaw status and report the gateway pid + uptime' \
  --skill openclaw --deliver local

# Inspect / pause / resume / remove
hermes cron list
hermes cron pause openclaw-daily-backup
hermes cron resume openclaw-daily-backup
hermes cron remove openclaw-daily-backup
```

`--deliver` targets:
- `local` — write the agent's reply to `~/.hermes/sessions/`; nothing posts anywhere
- `origin` — reply back into the channel that created the job (n/a for cron)
- `telegram` / `discord` / `signal` — needs that channel wired
- `feishu:<chat_id>` — needs the Feishu channel wired in `~/.hermes/config.yaml` `channels.feishu` (we have it on OpenClaw, not yet on Hermes)

## Cron requires the gateway

`hermes cron` jobs only fire if the **gateway daemon is running** — it's the gateway that ticks the cron scheduler every 60 s. If `hermes cron list` shows your job but it never executes:

```bash
hermes gateway status   # → ✗ stopped means cron is not running
hermes gateway start    # if installed
hermes gateway install  # if not yet installed
```

See [`gateway.md`](gateway.md) for the install recipe. Foreground `hermes gateway run` also works for debugging — the cron tick is the same loop.

## Don't

- Don't add the symlink at the wrong category-level — `~/.hermes/skills/openclaw/` (no category) won't be discovered. Always nest under a category dir.
- Don't symlink with overlapping names — if you already have a hub-installed skill called `openclaw`, the local one wins (per `Source: local`) and the hub version becomes shadowed silently.
- Don't expect `hermes skills inspect <name>` to show the local skill — that command searches the registries (skills.sh, ClawHub) for installable variants, not local installs. Use `hermes skills list | grep <name>` or `cat ~/.hermes/skills/<category>/<name>/SKILL.md` to inspect a local skill.
- Don't put plaintext secrets inside skill files — they're loaded into the model's context every invocation. Skills should reference creds via env vars or files, not embed them.

## When the dispatch sub-command runs this

When the user invokes `/hermes skills <action>` or natural language ("install openclaw skill into hermes", "let hermes call openclaw", "schedule openclaw doctor"):

1. **Install local**: confirm the source path under `~/agentry/`, pick a category (default `devops`), `ln -s` it under `~/.hermes/skills/<category>/<name>/`, run `hermes skills list | grep <name>` to verify.
2. **Schedule task**: ask for the schedule (cron expression or interval), the prompt, and which skill to attach (`--skill`). Run `hermes cron create …`. Verify with `hermes cron list`. Remind the user the gateway must be running for jobs to fire.
3. **Remove**: `unlink ~/.hermes/skills/<category>/<name>/` for local skills; `hermes skills uninstall <name>` for hub-installed ones. Don't manipulate builtin skills — use `hermes skills config` to disable instead.
