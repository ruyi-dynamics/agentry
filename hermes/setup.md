# /hermes setup — first-time install + first-run config

Goal: get `hermes` callable on this Mac with at least one model provider authenticated, so the agent can answer prompts.

```
1. Preflight  →  2. Install (curl|bash, with VPN-routing fallback)
              →  3. Verify CLI on PATH
              →  4. Configure model auth (interactive or .env-based)
              →  5. Health check (doctor)
```

---

## 1. Preflight

```bash
which uv      # nice to have — installer will fetch if missing (curl|sh from astral.sh)
which python3 # must be 3.11+
which git     # must exist
which brew    # nice to have — installer uses brew for ripgrep/ffmpeg if missing
```

None of these are user-invasive (Hermes doesn't need root). If `uv` is missing, the installer fetches it from `https://astral.sh/uv/install.sh` — that's a second `curl|sh` call. Mention it before running.

## 2. Install

The canonical recipe from the upstream README:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash -s -- --skip-setup
```

`--skip-setup` is **strongly recommended** — without it, the installer drops into the interactive setup wizard at the end, which hangs in non-TTY contexts (same lesson as OpenClaw doctor). Run setup separately in step 4.

**Where it puts things** (macOS user mode):
- Code: `~/.hermes/hermes-agent` (git clone of the repo)
- State + config: `~/.hermes/{config.yaml, .env, sessions/, logs/, memories/, hooks/, skills/, cron/, pairing/}`
- CLI: symlink at `~/.local/bin/hermes` → `~/.hermes/hermes-agent/venv/bin/hermes`
- Bundled skills: 74 of them auto-installed at `~/.hermes/skills/` (Hermes has its own skill ecosystem, separate from Claude Code skills)

### VPN-routing trap (this machine specifically)

The installer's git-clone step **fails on this Mac** if Easy Connect VPN + ClashVerge TUN mode are running together — git over HTTPS to GitHub gets mid-stream-canceled (`RPC failed; curl 92 HTTP/2 stream … was not closed cleanly`) because TUN intercepts and rewrites traffic to GitHub. The installer also tries SSH first but doesn't pick up `~/.ssh/config`'s custom `IdentityFile`, so SSH attempt fails too.

**Workaround** — pre-clone via SSH using our key, then re-run the installer (it detects the existing clone and switches to update mode at line ~800 of `install.sh`):

```bash
mkdir -p ~/.hermes
git clone --depth 1 git@github.com:NousResearch/hermes-agent.git ~/.hermes/hermes-agent
# Now re-run the installer; it'll skip the clone and go to dependency install
bash /tmp/hermes-install.sh --skip-setup    # if you already downloaded it
# OR
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash -s -- --skip-setup
```

`pnpm`/`uv` dependency install over HTTPS to PyPI/registry seems to survive the TUN routing fine — it's specifically the GitHub clone phase that gets killed.

## 3. Verify

```bash
which hermes                    # /Users/xuhao/.local/bin/hermes
hermes version                  # → "Hermes Agent v…  Up to date"
hermes status                   # → list of components (most ⚠ until step 4)
```

If `which hermes` returns empty, source `~/.zshrc` (the installer adds `~/.local/bin` to PATH but only for new shells). On this machine that's already done — both login and interactive zsh see it.

## 4. Configure model auth

Two paths, depending on whether the user wants the interactive wizard or just to wire keys from `~/.config/agentry/tokens.md`.

### A. Interactive (first-time, user-driven)

```bash
hermes setup model      # only the model section
hermes setup            # full wizard (model + tts + terminal + gateway + tools + agent)
```

The wizard is TUI — only run from a real terminal, never from a Claude Code Bash call.

### B. Non-interactive (`.env`-driven, repeatable)

Hermes reads provider keys from `~/.hermes/.env`. The file is created by the installer with all known env-var names commented out, ready to fill. Source the verified-working set from `~/.config/agentry/tokens.md` and uncomment the matching lines:

| `~/.hermes/.env` key | tokens.md source | Notes |
|---|---|---|
| `OPENAI_API_KEY` | § 1.1 (Tao Wei key — currently active in OpenClaw) | Public OpenAI API. Standard `gpt-4o-mini` / `o4-mini` etc. |
| `OPENROUTER_API_KEY` | § 1.3 | Catch-all routing |
| `GEMINI_API_KEY` | § 1.2 (the doctor-✓ one, `AIzaSyCD3…`) | Note: env-var name is `GEMINI_API_KEY` not `GOOGLE_API_KEY` for Hermes |
| `ANTHROPIC_API_KEY` | § 1.5 — **DISABLED for this account, do not use** | Skip; Hermes will silently fail on Claude calls |
| `WANDB_API_KEY` | § 7.2 | For `rl` toolset |
| `GITHUB_TOKEN` | none — generate a fine-grained PAT for higher Skills Hub rate limit | Optional; without it Hermes Hub is capped at 60 req/hr |

Then either restart any running `hermes gateway` or just re-launch `hermes`.

### Set the default model

```bash
hermes model                           # interactive picker
hermes config set model.default <id>   # direct set
# OR open editor:
hermes config edit
```

**Heads-up: comments in `config.yaml` are unpreservable through any Hermes write.** The file ships with ~46 KB of inline documentation comments (~826 of them), but `hermes config set`, `hermes claw migrate`, and any hand-edit-via-PyYAML all serialize the YAML and strip every comment in the process. After your first write, `config.yaml` shrinks from ~50 KB to ~4–5 KB. This is by design (Hermes uses PyYAML's `safe_dump`); restore from the snapshot at `~/.hermes/state-snapshots/<initial>/config.yaml` is the only recovery, but it'll be wiped on the next write again. Don't waste time fighting it — accept the loss; the upstream README and `hermes config show --help` describe each option.

For parity with the OpenClaw default we configured (Tao Wei OpenAI), candidates:
- `openai/gpt-4o-mini` via OpenRouter — universally cheap, ~$0.15/1M
- `dashscope/qwen3-coder-plus` via the DashScope coding plan — flat-rate subscription, effectively free per call (this is the current default on this machine, set 2026-04-27)
- `openai/o4-mini` for reasoning tasks

### Custom providers (DashScope, Volcengine, etc.)

Hermes exposes non-bundled providers via `custom_providers[]` in `config.yaml`:

```yaml
custom_providers:
  - name: dashscope
    base_url: https://coding.dashscope.aliyuncs.com/v1
    api_key: ""                          # leave empty; Hermes reads <NAME>_API_KEY from .env
    api_mode: chat_completions           # also: anthropic_messages
  - name: volcengine
    base_url: https://ark.cn-beijing.volces.com/api/coding/v1
    api_key: ""
    api_mode: chat_completions
```

Then put the key as `DASHSCOPE_API_KEY=sk-sp-…` (or `VOLCENGINE_API_KEY=…`) in `~/.hermes/.env`. Hermes routes by name prefix: `model.default = dashscope/qwen3-coder-plus` matches `custom_providers[name=dashscope]`.

The cleanest way to populate these is `hermes claw migrate --preset full --migrate-secrets --yes` (see `claw-migrate.md`) — it auto-imports DashScope + Volcengine + Qwen Portal from a previously-configured OpenClaw install.

### Doctor false positives to ignore

After wiring the above, `hermes doctor` may report:

- **`✗ Anthropic API (invalid API key)`** — expected if your Anthropic account has direct-API support disabled. The key is kept in tokens.md for reference only; route Claude-style traffic through OpenRouter (`anthropic/claude-…` model IDs) instead.
- **`✗ Alibaba/DashScope (invalid API key)`** — false positive. Doctor probes the standard-tier `dashscope.aliyuncs.com` endpoint which rejects `sk-sp-…` **coding-plan** keys. The key works against the coding-plan endpoint (`coding.dashscope.aliyuncs.com/v1`) which is what `custom_providers[dashscope]` targets. Verify with: `curl -H "Authorization: Bearer sk-sp-…" https://coding.dashscope.aliyuncs.com/v1/chat/completions -d '{"model":"qwen3-coder-plus","messages":[{"role":"user","content":"ping"}]}'` — should return 200.

## 5. Health check

```bash
hermes doctor           # baseline list (1 issue: setup wizard not run)
hermes doctor --fix     # auto-fix what it can
hermes status --deep    # deeper probe
```

Items still ⚠ after auth wiring are usually **optional toolsets** — `discord` (no bot token), `homeassistant` (no Home Assistant on this Mac), `image_gen` (no model with image gen wired), `web` (no Exa/Tavily/etc.), `vision` (no vision model wired). Leave them ⚠ unless the user asks for that toolset.

## Idempotency

Re-running setup on a healthy install:
- preflight: passes
- installer: switches to update mode (git pull + uv sync); fast
- step 3 (verify): no-op
- step 4: no-op if `.env` keys already set + model selected
- doctor: green except for opt-in toolsets

## Don't

- Don't run the installer **without** `--skip-setup` from a non-TTY context — the wizard hangs.
- Don't put provider keys in `~/.zprofile` or `~/.zshrc` for Hermes — `hermes gateway` (when daemonized later) won't see them. Use `~/.hermes/.env` (Hermes loads it explicitly via dotenv).
- Don't edit `~/.hermes/hermes-agent/` source files — they get clobbered on `hermes update` (which runs `git stash; git pull`).
- Don't enable `--insecure` on `hermes dashboard` — exposes API keys on the LAN. The default 127.0.0.1 bind is correct.
