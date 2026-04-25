# /openclaw setup — first-time host install + first-run configuration

Goal: get `~/openclaw` runnable as a productive coding agent on this Mac, with a working default model and credentials wired in.

A complete fresh setup runs six phases. Don't skip any — running install/build alone leaves the agent with the bundled `qwen-portal/coder-model` default, which has no auth on a fresh machine.

```
1. Preflight  →  2. Install/build  →  3. Configure agent defaults
                                      →  4. Register model providers
                                      →  5. Set credentials
                                      →  6. Health check (doctor)
```

---

## 1. Preflight (read-only checks)

Run each, fail fast on first miss:

```bash
node --version            # must be >= 22.x
pnpm --version            # must exist
git --version             # must exist
test -d ~/openclaw && echo "source: present" || echo "source: MISSING"
test -f ~/openclaw/package.json && echo "manifest: present" || echo "manifest: MISSING"
```

If any required item is missing, **stop and report**, then ask the user how they want to install it. Don't auto-install Node/pnpm/git — those are user-level decisions.

If pnpm is missing: recommend **`brew install pnpm`** (cleanest on this Mac if Homebrew is already there) over `npm i -g pnpm` (pollutes the brew-managed Node prefix) or the standalone installer (adds shell init lines).

If `~/openclaw` is missing, ask the user where to clone it (default: `~/openclaw`) before running `git clone https://github.com/openclaw/openclaw.git ~/openclaw`. Confirm before cloning.

## 2. Install + build

Show the plan, confirm, then run:

```bash
cd ~/openclaw
pnpm install     # ~3-5 minutes on first run; ~1278 packages
pnpm build       # required after fresh install; emits dist/
pnpm ui:build    # control-ui assets — without this, doctor warns and the dashboard 404s
```

`pnpm ui:build` is **not** part of `pnpm build` and is easy to forget — doctor will flag it as "Control UI assets are missing." Run it as part of setup so the dashboard works on first try.

`pnpm install` may pull a few warnings (e.g. `@discordjs/opus` ignored build script) — those are optional and safe to skip with `pnpm approve-builds` later if any of those features are wanted.

## 3. Configure agent defaults

After build, the agent (`main`) inherits whatever defaults shipped in OpenClaw — currently `qwen-portal/coder-model` with `/home/node/.openclaw/workspace`. Both are wrong for a fresh macOS host. Inspect and fix:

```bash
cd ~/openclaw
pnpm openclaw --no-color config get agents
```

What to fix:

| Field | Default (broken) | Fix to |
|---|---|---|
| `agents.defaults.model.primary` | `qwen-portal/coder-model` (no auth) | a model with working auth, e.g. `google/gemini-3-pro-preview` once Gemini key is set, or `anthropic/claude-…` once Anthropic registered |
| `agents.defaults.workspace` | `/home/node/.openclaw/workspace` (Docker path) | `~/.openclaw/workspace` (host path) — `mkdir -p` first if missing |
| `agents.defaults.model.fallbacks` | may include providers without auth | `pnpm openclaw models fallbacks remove <id>` for each broken one |

Apply with the CLI (it backs up `openclaw.json` automatically):

```bash
pnpm openclaw config set agents.defaults.model.primary google/gemini-3-pro-preview
pnpm openclaw config set agents.defaults.workspace "$HOME/.openclaw/workspace"
pnpm openclaw models fallbacks remove qwen-portal/vision-model    # example
mkdir -p ~/.openclaw/workspace
```

After every `config set`, the CLI prints **"Restart the gateway to apply"** — defer the restart until step 5 (one restart covers all changes).

## 4. Register callable model providers

For most providers you do **not** need to write `models.providers` entries — bundled plugins under `~/openclaw/extensions/<id>/openclaw.plugin.json` claim model-id prefixes (e.g. anthropic claims `claude-*`, openai claims `gpt-*`/`o1`/`o3`/`o4`, google claims gemini IDs) and **auto-discover** their model catalogs once an `auth-profiles.json` entry exists for that provider (next step). Adding the auth profile is enough; the model becomes callable immediately.

The CLI even **strips** custom `models.providers` entries you write by hand for plugin-covered providers (the next `pnpm openclaw config set` or gateway restart re-normalizes openclaw.json against the schema and drops them). Do not fight this — for openai / anthropic / openrouter / google, skip step 4 entirely and rely on plugin auto-discovery.

`models.providers` edits *do* survive for providers without a bundled plugin — e.g. **DashScope** (Aliyun's Anthropic-compatible coding gateway), **bitexingai** (3rd-party OpenAI-compatible relay), self-hosted Ollama, etc. Use this section only for those.

Shape (each is a key under `models.providers`):

| Provider key | baseUrl | api | Notes |
|---|---|---|---|
| `dashscope` | `https://coding.dashscope.aliyuncs.com/apps/anthropic` | `anthropic` | Aliyun's Anthropic-compatible coding gateway. No bundled plugin, so this is the only path. `pnpm openclaw models list` will show "Auth: -" / "missing" tag — that's cosmetic; runtime calls still attempt and the fallback chain catches if they fail. |
| `bitexingai` (or any name) | `https://bitexingai.com/v1/chat/completions` | `openai-completions` | Generic 3rd-party OpenAI-compatible relays go here. |
| `ollama` | `http://127.0.0.1:11434` | `ollama` | Self-hosted local. |

Each provider entry needs a `models[]` array with the model IDs you want callable. Minimal model entry:

```json
{ "id": "<provider-model-id>", "name": "<display-name>",
  "input": ["text", "image"], "contextWindow": 200000, "maxTokens": 16384,
  "reasoning": true,
  "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 } }
```

Set the agent default + fallback chain via CLI (each writes `openclaw.json.bak`):

```bash
pnpm openclaw --no-color config set agents.defaults.model.primary openai/gpt-5.4-mini
pnpm openclaw --no-color models fallbacks clear
for m in dashscope/claude-sonnet-4-5 anthropic/claude-sonnet-4-6 google/gemini-3-pro-preview openai/gpt-4o-mini openrouter/openai/gpt-4o-mini; do
  pnpm openclaw --no-color models fallbacks add "$m"
done
```

Order the fallback chain by what should be tried first on the primary's failure — usually a different provider (cross-provider fallbacks beat same-provider, since most outages are provider-wide).

**Note on the bundled `codex` provider:** OpenClaw ships a `codex` provider entry pointing at `chatgpt.com/backend-api/v1` for `gpt-5.x` ChatGPT-consumer-API models. That endpoint needs **OpenAI's browser OAuth**, not `sk-proj-…` keys. If you have `sk-proj-…` keys and want to call any `gpt-*` model (including `gpt-5.4-mini`), the openai plugin's auto-discovery against `auth-profiles.json` covers it — no need to register under either `codex` or a custom `openai` provider entry.

## 5. Set credentials

The gateway runs as a **macOS LaunchAgent**, which **does not inherit `~/.zprofile` / `~/.zshrc` / `~/.profile` env vars**. Exporting `ANTHROPIC_API_KEY` in your shell init reaches `pnpm openclaw …` from a terminal but never reaches the daemon. The reliable path is `auth-profiles.json`.

Source of verified credentials: **`~/.config/agentry/tokens.md`** (mode 600, outside any git repo). If it exists, use only ✓-working entries from it. If it doesn't, surface that and ask which keys to use.

Auth profile shape (per provider):

```json
{
  "version": 1,
  "profiles": {
    "anthropic:default": { "type": "api_key", "provider": "anthropic",  "key": "sk-ant-…" },
    "openai:default":    { "type": "api_key", "provider": "openai",     "key": "sk-proj-…" },
    "openrouter:default":{ "type": "api_key", "provider": "openrouter", "key": "sk-or-v1-…" },
    "google:default":    { "type": "api_key", "provider": "google",     "key": "AIzaSy…" }
  },
  "usageStats": {}
}
```

Provider IDs are stable: `anthropic`, `openai`, `openrouter`, `google`. All four are bundled plugins enabled by default — adding the auth profile is enough; no plugin install needed. Provider names are documented in each plugin's `~/openclaw/extensions/<id>/openclaw.plugin.json` (look for `"providers"`).

Steps:

```bash
# 1. Backup first (skill convention: any write to ~/.openclaw is auto-backed-up)
cp ~/.openclaw/agents/main/agent/auth-profiles.json \
   ~/.openclaw/agents/main/agent/auth-profiles.json.bak.$(date +%Y%m%d-%H%M%S)

# 2. Edit the file directly (no CLI command exists for adding profiles)

# 3. Lock down perms
chmod 600 ~/.openclaw/agents/main/agent/auth-profiles.json

# 4. Reset usageStats for any profile whose key changed
#    (otherwise an old cooldownUntil from the dead key suppresses the new one)
```

When replacing a key in place: clear that profile's `usageStats` entry too — `errorCount` and `cooldownUntil` from the dead key will block the new one until the cooldown expires.

Brave Search is set under `plugins.entries.brave.config.webSearch.apiKey`, not in `auth-profiles.json` — doctor's auto-migration handles moving any legacy `tools.web.search.apiKey` there.

## 6. Apply + health check

Restart the gateway so it re-reads config + credentials, then run doctor:

```bash
launchctl kickstart -k gui/$UID/ai.openclaw.gateway
cd ~/openclaw
pnpm openclaw --no-color doctor --non-interactive --yes
```

**Always pass `--non-interactive --yes`** — without them doctor renders a TUI prompt that hangs forever in a non-TTY context. See `doctor.md` for the full set of quirks.

Defer to `doctor.md` for interpreting the output. A green run shows: 0 errors, 0 pending device approvals, plugins loaded, default model has working auth.

## Migrating from a prior install (especially Docker)

If `~/.openclaw/` already exists from a previous install — *especially a Docker-based one* — the device-pair table and identity files will be stale and trigger a "device metadata change pending approval" loop on every CLI call. The `openclaw devices clear` CLI command itself can't run because it requires gateway approval first (chicken-and-egg).

Fix (only when the loop appears):

```bash
# 1. Backup full state
bash ~/agentry/openclaw/scripts/backup.sh

# 2. Stop gateway
launchctl bootout gui/$UID/ai.openclaw.gateway

# 3. Move device + identity state aside (don't delete — keep for forensics)
TS=$(date +%Y%m%d-%H%M%S)
mv ~/.openclaw/devices  ~/.openclaw/_old-devices.$TS
mv ~/.openclaw/identity ~/.openclaw/_old-identity.$TS

# 4. Restart gateway (creates fresh device + identity dirs on first pair)
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/ai.openclaw.gateway.plist

# 5. Trigger re-pair with any CLI call
cd ~/openclaw && pnpm openclaw --no-color devices list
# Should show 1 paired device, 0 pending. The CLI auto-pairs on first call.
```

Other Docker-era leftovers to look for and clean:
- Workspace path `/home/node/.openclaw/workspace` in `agents.defaults.workspace` (fix in step 3 above).
- Devices with IPs `192.168.65.x` (Docker bridge gateway) — `pnpm openclaw devices revoke <fingerprint>`.
- Orphaned session JSONLs under `/home/node/.openclaw/agents/main/sessions/` — `pnpm openclaw sessions cleanup --enforce --fix-missing` prunes the index entries.

## Idempotency

Re-running `setup` on a healthy install:
- preflight: passes
- `pnpm install` / `pnpm build` / `pnpm ui:build`: incremental, fast
- step 3 (config get → fix): no-op if defaults are already correct
- step 4 (model providers): no-op if `models.providers` already lists what you want
- step 5 (auth profiles): no-op if profiles match tokens.md
- doctor: green
