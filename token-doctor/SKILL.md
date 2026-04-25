---
name: token-doctor
description: Use when the user wants to test which credentials in `~/.config/agentry/tokens.md` are still valid (or invokes `/token-doctor …`). Sub-commands: test, list. Probes each token against its provider's API and reports ✓ valid / ✗ invalid / ⚠ skipped.
---

# token-doctor

Probes the credentials inventory at `~/.config/agentry/tokens.md` and reports which still work.

## Dispatch

Parse the sub-command from the invocation. If invoked with `args` (slash command), the first whitespace-delimited token is the sub-command. Otherwise infer from the user's request: test/probe/check/validate → `test`; show/inventory/list → `list`.

| Sub | File / behavior |
|---|---|
| `test` (default) | Run `scripts/test_tokens.py` — probes each known token, prints a per-service report. |
| `list` | Run `scripts/test_tokens.py --no-probe` — parses tokens.md and lists what's known without making any network calls. |

If the sub-command is missing or unrecognized, print this menu and stop:

```
/token-doctor <sub>
  test    Probe each credential and report ✓/✗/⚠ (default)
  list    Parse tokens.md and list known credentials without probing
```

## Conventions

- **Read-only.** This skill never modifies `tokens.md`. If a token is invalid, the user decides whether to rotate.
- **Network-conditional.** Internal hosts (`bitbucket.imotion.ai`, `gitee-test.imotion.ai`, `jira.imotion.ai`) require Easy Connect VPN; they're tested but failures with `unreachable` are expected when the VPN is down — don't conflate with token invalidity.
- **OAuth tokens skipped.** `sk-ant-oat01-…` (Claude Code OAuth), `sk-ant-sid…` (web sessions) cannot be probed via standard API calls; the script marks them ⚠ and notes how to test them out-of-band.
- **No retries.** A 5xx is reported as transient; the user re-runs if needed.
- **No caching.** Each invocation hits live endpoints — that's the point.

## How to invoke from inside this skill

```bash
python3 ~/agentry/token-doctor/scripts/test_tokens.py            # full probe
python3 ~/agentry/token-doctor/scripts/test_tokens.py --no-probe # list only
python3 ~/agentry/token-doctor/scripts/test_tokens.py --service openai   # filter
python3 ~/agentry/token-doctor/scripts/test_tokens.py --json     # structured output
```

After the script returns, summarize the user-facing report. Highlight anything actionable in **bold** (e.g. `**3 OpenAI keys revoked — rotate or remove from tokens.md**`).
