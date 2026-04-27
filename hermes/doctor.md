# /hermes doctor — run + interpret

Goal: surface Hermes's own diagnostics and translate common ⚠ patterns into next-step suggestions.

## Run

```bash
hermes doctor             # baseline
hermes doctor --fix       # auto-fix what's possible (creates missing dirs, etc.)
```

`hermes doctor` is non-interactive by default — no TUI, safe to call from a Bash tool. Returns a list of `✓` / `⚠` lines per toolset and per subsystem.

## Interpret common patterns

| Pattern in output | Likely cause | Suggested next step |
|---|---|---|
| `⚠ <toolset> (missing X_API_KEY)` | provider env var not set | add the matching key to `~/.hermes/.env`; restart `hermes`. See `setup.md` § 4.B for the tokens.md → .env mapping |
| `⚠ <toolset> (system dependency not met)` | optional native binary missing (e.g. `homeassistant`, `image_gen`, `vision`, `messaging`) | only fix if the user wants that toolset; otherwise leave ⚠ |
| `⚠ Skills Hub directory not initialized` | first-run state | `hermes skills list` triggers init, then re-doctor |
| `⚠ No GITHUB_TOKEN (60 req/hr rate limit)` | Skills Hub rate-limited | optional — generate a fine-grained PAT (read-only public, no scopes), put as `GITHUB_TOKEN=…` in `~/.hermes/.env` |
| `Run 'hermes setup' to configure …` | wizard hasn't been run | run `hermes setup model` (model section only) — see `setup.md` § 4 for non-interactive .env path |

## Don't

- Don't run `hermes doctor --fix` blindly when the only ⚠ is "run setup" — `--fix` doesn't run the wizard, it just creates missing dirs. Run `hermes setup model` (or wire `.env` keys directly) instead.
- Don't conflate the `messaging` ⚠ with a broken gateway — that warning is about libraries needed for **outgoing channel messages**, not the gateway daemon itself. `hermes status --deep` is more precise about gateway health.

## Report

Summarize: doctor's overall verdict, items it auto-fixed, items needing user action. Highlight anything that would block the agent from making model calls (missing primary-model auth, no .env at all) ahead of optional toolsets.
