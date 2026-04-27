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
hermes model            # interactive picker
# OR direct:
hermes config           # opens config.yaml; edit `model:` section
```

For parity with the OpenClaw default we configured (Tao Wei OpenAI), set primary to `openai/gpt-4o-mini` or `openai/o4-mini` (Hermes uses public OpenAI API model IDs, not OpenClaw's `gpt-5.4-mini` which is a ChatGPT-consumer-API name).

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
