# /hermes status — read-only health snapshot

Goal: report Hermes's current state (model, providers, gateway, sessions) without mutating anything.

## Run

```bash
hermes status                # quick summary
hermes status --all          # all details, redacted (safe to share)
hermes status --deep         # deeper probes (slower; checks remote endpoints)
```

`--all` redacts secret values, so the output is safe to paste into a bug report or a chat. `--deep` adds latency checks and live provider probes — useful when debugging "why is the agent slow" or "is provider X reachable".

## What to report back

After running, summarize for the user:
- **Model**: primary model + provider, plus whether any auth is missing
- **Gateway**: running / stopped, and which channels (Telegram/Discord/etc.) are configured
- **Sessions**: count of recent sessions
- **Issues**: any ⚠ from `--deep` mode

## Don't

- Don't run `--deep` repeatedly — it hits live provider APIs and counts against quota.
- Don't paste raw `hermes status` output (without `--all`) into shared channels — secrets aren't redacted by default.
