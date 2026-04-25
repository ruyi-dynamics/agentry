# /openclaw doctor — run + interpret

Goal: surface OpenClaw's own diagnostics and translate common failure patterns into next-step suggestions.

## Run

```bash
cd ~/openclaw
pnpm openclaw --no-color doctor --non-interactive --yes
```

Three flags that you almost always want:
- **`--non-interactive --yes`** — without these, doctor pops a TUI confirm prompt (`┌ OpenClaw doctor` boxes) and hangs forever when stdin is `/dev/null` or a non-TTY.
- **`--no-color`** — strips ANSI so output stays readable when piped or saved.

To apply repairs in the same run, add `--fix` (alias `--repair`). To include service-level scans, add `--deep`. To rotate the gateway shared secret, add `--generate-gateway-token`.

If `pnpm openclaw doctor` itself fails to start (e.g. missing `node_modules`), the issue is install state, not config — recommend running `/openclaw setup` first.

## Quirks worth knowing

- **Apparent hang during `--fix`** — some plugins ship with bundled-runtime deps that get installed on first repair. `web-readability` alone takes ~28s to download `@mozilla/readability` + `linkedom`. Wait for it; don't kill the process unless `ps` shows 0% CPU and no I/O for 60s+.
- **Don't pipe doctor through `tail`** — `tail -80` only flushes when stdin closes, so a doctor process that's blocked on a TUI prompt will look indistinguishable from one doing real work. Redirect to a file (`> /tmp/d.log`) and `tail` the file separately if you want progressive output.
- **`config set` always says "Restart the gateway to apply"** — batch multiple sets, then restart once: `launchctl kickstart -k gui/$UID/ai.openclaw.gateway`.

## Interpret common patterns

OpenClaw's doctor output is the source of truth. The patterns below are hints for follow-up only.

| Pattern in output | Likely cause | Suggested next step |
|---|---|---|
| `node_modules` missing or stale | install never run / pnpm-lock changed | `/openclaw setup` (or just `cd ~/openclaw && pnpm install`) |
| `Control UI assets are missing. Run: pnpm ui:build` | UI bundle never built | `cd ~/openclaw && pnpm ui:build` (one-shot, ~1s) |
| Auth profile expired / unauthorized | model provider creds rotated | edit `~/.openclaw/agents/<id>/agent/auth-profiles.json`; clear that profile's `usageStats` entry too (cooldown carries over otherwise); restart gateway |
| Channel/provider creds missing | `~/.openclaw/credentials/` incomplete | check which channel is failing, add cred file |
| Gateway not running / port in use | mac gateway daemon down or other process holds port | `launchctl kickstart -k gui/$UID/ai.openclaw.gateway` (preferred over `openclaw gateway restart` when running as a LaunchAgent) |
| `device metadata change pending approval (requestId: …)` repeating | stale device pairing from prior install (esp. Docker → host migration); every CLI call generates a new requestId, can't approve | follow the migration steps in `setup.md` § "Migrating from a prior install" — move `~/.openclaw/devices/` and `~/.openclaw/identity/` aside, restart gateway, let CLI re-pair on next call |
| `/home/node/.openclaw/...` paths in config or session refs | Docker-era path leak | edit `agents.defaults.workspace` to a host path; `sessions cleanup --enforce --fix-missing` prunes orphan session index entries |
| Stale plugin reference like `qwen-portal-auth: plugin not found` | legacy `plugins.entries` entry from older OpenClaw | doctor's `--fix` removes it automatically |
| Stale `update-check.json` | update notifier hasn't refreshed | `/openclaw update` |
| Config-format warnings about retired keys | legacy config from older OpenClaw | doctor's own `--fix` handles common migrations (e.g. `tools.web.search.apiKey` → `plugins.entries.brave.config.webSearch.apiKey`) |

## LaunchAgent env-var gotcha

The gateway is a macOS LaunchAgent (`~/Library/LaunchAgents/ai.openclaw.gateway.plist`). LaunchAgents **do not load shell init files** — `~/.zprofile`, `~/.zshrc`, `~/.profile` are never sourced for them. So:

- `export ANTHROPIC_API_KEY=…` in `.zprofile` works for `pnpm openclaw …` from your terminal.
- That same key is **invisible to the gateway daemon**.

Configure provider credentials in `~/.openclaw/agents/<id>/agent/auth-profiles.json` (the gateway reads it directly), or — if you really need env vars — add them to the plist's `EnvironmentVariables` key (and re-bootstrap with `launchctl bootout` + `launchctl bootstrap`).

## Don't

- Don't edit `~/.openclaw/openclaw.json` by hand to silence a warning. Use doctor's `--fix` or `pnpm openclaw config set <key> <value>` (each `config set` writes a `.bak`).
- Don't delete `~/.openclaw/agents/` or `credentials/` to "reset" — back up first via `~/agentry/openclaw/scripts/backup.sh`.
- Don't run `node_modules` removals as a fix without backing up first.
- Don't try to break a device-approval loop by repeatedly running `devices approve` — every CLI call generates a new requestId before the approve can land. Use the migration steps in `setup.md`.

## Report

Summarize: doctor's overall verdict, items it auto-repaired, items needing user action. Highlight anything that would block the agent from making model calls (missing auth, broken default model, broken gateway) ahead of cosmetic items (stale session refs, channel notices).
