# /openclaw doctor — run + interpret

Goal: surface OpenClaw's own diagnostics and translate common failure patterns into next-step suggestions.

## Run

```bash
cd ~/openclaw
pnpm openclaw doctor
```

If `pnpm openclaw doctor` itself fails to start (e.g. missing `node_modules`), the issue is install state, not config — recommend running `/openclaw setup` first.

## Interpret common patterns

OpenClaw's doctor output is the source of truth. The patterns below are hints for follow-up only.

| Pattern in output | Likely cause | Suggested next step |
|---|---|---|
| `node_modules` missing or stale | install never run / pnpm-lock changed | `/openclaw setup` (or just `cd ~/openclaw && pnpm install`) |
| Auth profile expired / unauthorized | model provider creds rotated | edit `~/.openclaw/agents/<id>/agent/auth-profiles.json`; re-run doctor |
| Channel/provider creds missing | `~/.openclaw/credentials/` incomplete | check which channel is failing, add cred file |
| Gateway not running / port in use | mac gateway daemon down or other process holds port | `openclaw gateway restart --deep` (run from app or CLI; never ad-hoc tmux per OpenClaw AGENTS.md) |
| Stale `update-check.json` | update notifier hasn't refreshed | `/openclaw update` |
| Config-format warnings about retired keys | legacy config from older OpenClaw | doctor's own auto-repair path; let it fix and re-run |

## Don't

- Don't edit `~/.openclaw/openclaw.json` by hand to silence a warning. Use doctor's repair path or `/openclaw update`.
- Don't delete `~/.openclaw/agents/` or `credentials/` to "reset" — back up first.
- Don't run `node_modules` removals as a fix without backing up first.

## Report

Summarize: doctor's overall verdict, items it auto-repaired, items needing user action.
