---
name: token-manager
description: |
  Manage API credentials across all agent config files (tokens.md, OpenClaw, Hermes, CCR).
  Add providers, probe validity, sync keys, discover models, benchmark latency, clean invalid keys,
  and visualize status in a dashboard.

  TRIGGER when: user asks to add/check/test/sync/clean/list API keys or tokens,
  manage provider credentials, check token validity, discover models, benchmark latency,
  or view token status dashboard. Also triggered by /token-doctor (backward compat).
---

# Skill: Token Manager

Manage API credentials across 5 config files from a single skill. Supersedes `/token-doctor`.

## Config Files

| File | Purpose |
|------|---------|
| `~/.config/agentry/tokens.md` | Master credential inventory |
| `~/.openclaw/openclaw.json` | OpenClaw `models.providers` |
| `~/.hermes/config.yaml` | Hermes `custom_providers` |
| `~/.hermes/.env` | Hermes env vars (`*_API_KEY`) |
| `~/.claude-code-router/config.json` | CCR `Providers` array |

## Dispatch

Parse `$ARGUMENTS` for a sub-command. If none matched, print this menu and stop.

| Sub-command | Description | Script |
|-------------|-------------|--------|
| `add` | Add a new provider to all configs | `scripts/add_provider.py` |
| `test` | Probe tokens + cross-file consistency | `scripts/test_tokens.py` |
| `list` | List tokens without probing | `scripts/test_tokens.py --no-probe` |
| `sync` | Propagate tokens.md active keys to agent configs | `scripts/sync_tokens.py` |
| `latency` | Benchmark model response times | `scripts/latency_test.py` |
| `clean` | Remove invalid keys | `scripts/clean_tokens.py` |
| `models` | Discover available models from API | `scripts/discover_models.py` |
| `discover` | Detect new models (API vs tokens.md) | `scripts/detect_new_models.py` |
| `dashboard` | Visual status dashboard | `scripts/dashboard.py` |

## Execution

```bash
SKILL_DIR="$(dirname "$(readlink -f ~/.claude/skills/token-manager/SKILL.md 2>/dev/null || echo ~/.claude/skills/token-manager/SKILL.md)")"
```

Run the matching script from `$SKILL_DIR/scripts/`. All scripts use Python 3 stdlib only.

## Sub-command Details

### `add` — Add a new provider

```bash
python3 "$SKILL_DIR/scripts/add_provider.py" <name> --url <base_url> --key <api_key>
# Optional: --api-type openai-completions --models "model1,model2" --no-discover --no-propagate
```

Flow:
1. Auto-detects API type from URL pattern
2. Discovers models via `GET /models` (unless `--no-discover`)
3. Shows preview of changes
4. With `--confirm`: backs up all 5 files, then updates them

**Always show the preview to the user and get confirmation before running with `--confirm`.**

### `test` — Probe tokens

```bash
python3 "$SKILL_DIR/scripts/test_tokens.py"              # probe all
python3 "$SKILL_DIR/scripts/test_tokens.py" --no-probe    # list only
python3 "$SKILL_DIR/scripts/test_tokens.py" --consistency # cross-file check
python3 "$SKILL_DIR/scripts/test_tokens.py" --service openai --json
```

Exit code: 0 if all ok/skipped/unreachable, 1 if any fail.

### `sync` — Propagate keys

```bash
python3 "$SKILL_DIR/scripts/sync_tokens.py" --dry-run     # preview
python3 "$SKILL_DIR/scripts/sync_tokens.py"               # apply
python3 "$SKILL_DIR/scripts/sync_tokens.py" --provider volcengine
```

### `latency` — Benchmark

```bash
python3 "$SKILL_DIR/scripts/latency_test.py" dashscope
python3 "$SKILL_DIR/scripts/latency_test.py" volcengine --models deepseek-v3.2,kimi-k2.6
python3 "$SKILL_DIR/scripts/latency_test.py" mimo --save  # save to dashboard cache
```

### `models` — Discover models

```bash
python3 "$SKILL_DIR/scripts/discover_models.py" volcengine --latest --compare
python3 "$SKILL_DIR/scripts/discover_models.py" --url https://api.example.com/v1 --key sk-xxx
```

### `discover` — Detect new models

```bash
python3 "$SKILL_DIR/scripts/detect_new_models.py"                        # all providers
python3 "$SKILL_DIR/scripts/detect_new_models.py" --provider volcengine   # one provider
python3 "$SKILL_DIR/scripts/detect_new_models.py" --save                  # save to cache
```

### `clean` — Remove invalid keys

```bash
python3 "$SKILL_DIR/scripts/clean_tokens.py" --dry-run     # preview
python3 "$SKILL_DIR/scripts/clean_tokens.py" --confirm     # apply
python3 "$SKILL_DIR/scripts/clean_tokens.py" --provider openai
```

### `dashboard` — Visual dashboard

```bash
python3 "$SKILL_DIR/scripts/dashboard.py" --refresh --open   # re-probe + open in browser
python3 "$SKILL_DIR/scripts/dashboard.py" --serve 8080       # start local server
python3 "$SKILL_DIR/scripts/dashboard.py"                     # generate from cached data
```

## Backward Compatibility

`/token-doctor test` and `/token-doctor list` redirect here. The old `token-doctor` SKILL.md has been updated to forward to this skill.
