# /openclaw feishu-bootstrap — wire a freshly-created Feishu app

Goal: take a Feishu app that the user just created in the Developer Console and finish the OpenClaw side end-to-end — credential wiring, scope request, gateway restart, and channel probe — in one command. Replaces the manual recipe in `setup.md` § 5b for the case where the app already exists.

## What this does (and does not) cover

| Step | Where | Who does it |
|---|---|---|
| Create the app | https://open.feishu.cn/app | **User, in browser** (Feishu API requires an existing self-managed app) |
| Enable bot capability | App → 应用功能 → 机器人 | **User, in browser** |
| Enable WebSocket events | App → 事件与回调 → WebSocket | **User, in browser** |
| Install + publish version | App → 版本管理与发布 | **User, in browser** |
| Validate appId/appSecret | API call to `tenant_access_token/internal` | **This script** |
| Apply scopes | API `POST /applications/{app_id}/scope_request` | **This script** (org admin still approves) |
| Write `channels.feishu.accounts.<id>` | `~/.openclaw/openclaw.json` | **This script** (with backup) |
| Restart gateway | `launchctl kickstart` | **This script** |
| Probe channel | `pnpm openclaw channels status --deep --probe` | **This script** |
| Approve user pairings | `pnpm openclaw pairing approve feishu <code>` | **`/openclaw pairing` sub-command** (recurring per-user) |

## Inputs to ask for

When the user invokes this sub-command, collect (in order; ask for each that wasn't provided):

1. **`--app-id`** — required. Format `cli_…` (16 chars after the prefix). Comes from app's 凭证与基础信息 page.
2. **`--app-secret`** — required. Comes from same page.
3. **`--account-id`** — optional. Default `default`. Use a different value (e.g. `work`, `personal`) if you're wiring a second account on the same OpenClaw install.
4. **`--name`** — optional. Display name shown in `channels list`. Default = same as account-id.
5. **`--domain`** — optional. `feishu` (default, China) or `lark` (international).
6. **`--no-scopes`** — flag. Skip the scope-request API call. Use if the user already pasted `feishu-scopes.json` into the Developer Console UI (`API 权限` → `权限 JSON 导入`).

If the user has only said something like "bootstrap feishu", ask for appId + appSecret first; defaults cover the rest.

## Run

```bash
python3 ~/.claude/skills/openclaw/scripts/feishu-bootstrap.py \
  --app-id cli_… \
  --app-secret … \
  [--account-id work] [--name "work bot"] [--domain feishu|lark] [--no-scopes]
```

The script:
1. Validates the appId+appSecret by calling `tenant_access_token/internal`. If Feishu rejects (code != 0), it stops with the actual response body — that's almost always either a typo in the secret, the secret being rotated in the console without re-copying, or the wrong app id.
2. Applies scopes (unless `--no-scopes`). The org admin still has to approve the scope request from the Developer Console (`应用审核` page) before the scopes take effect.
3. Backs up `~/.openclaw/openclaw.json` to `~/.openclaw/openclaw.json.bak.<ts>` (UTC timestamp), then writes `channels.feishu.accounts.<account-id>` and enables the plugin + channel.
4. `launchctl kickstart`s the gateway LaunchAgent so the new config is picked up.
5. Probes via `channels status --deep --probe` and reports the verdict.

Idempotency: re-running with the same args is a no-op for the JSON edit (the script compares the desired account block against what's there and skips the write if identical).

## Interpret the verdict

| Probe says | Meaning | Next step |
|---|---|---|
| `Feishu <name>: enabled, configured, running, works` | All green — bot can send + receive | Ask the user to DM the bot to trigger the first pairing-code dance |
| `enabled, configured, stopped, error:…` | Auth worked, channel can't open WS connection | Check Feishu org allows WebSocket events; check the gateway has outbound network |
| `enabled, not configured` | Credentials at the wrong path or missing | Should not happen via this script — re-run; if it persists, check `python3 -c "import json; print(json.load(open('~/.openclaw/openclaw.json'.replace('~', '$HOME')))['channels']['feishu']['accounts'])"` |
| `disabled` | Plugin or channel `enabled: false` | The script sets both to true; if you see this, something else flipped them back (other tooling, doctor --fix) |

## Don't

- Don't run this before the app version is published in the console — scopes won't take effect even if the API accepts the scope_request.
- Don't pass the **app secret** on a shared shell history. Prefer pasting interactively or via a file (`--app-secret "$(cat secret.txt)"`).
- Don't use this to rotate an *existing* account's secret — the script writes the secret in plaintext into openclaw.json which is fine, but the old secret stays in the `.bak.<ts>` backup. If you're rotating because of a leak, also delete the backup file after confirming the new config works.

## What this skill writes vs leaves alone

Writes:
- `plugins.entries.feishu.enabled = true`
- `channels.feishu.enabled = true`
- `channels.feishu.accounts.<account-id>` = `{enabled, name, appId, appSecret, domain, connectionMode: "websocket", streaming: true}`
- `~/.openclaw/openclaw.json.bak.<ts>` (backup)

Leaves alone:
- All other `channels.feishu.accounts.*` (multi-account-safe)
- All non-feishu channels
- Models, agents, plugins, gateway config — unchanged
- `tokens.md` — does NOT auto-update; the user should run `/openclaw status` or manually add the new app to `~/.config/agentry/tokens.md` § 10
