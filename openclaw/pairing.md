# /openclaw pairing — approve incoming user pairings

Goal: handle the per-user access-control gate that OpenClaw puts in front of every chat channel. Each new external user (Feishu account, Telegram user, Discord user, etc.) who DMs the bot first triggers a "pairing required" reply with a one-time code; the bot owner runs `pnpm openclaw pairing approve <channel> <code>` to whitelist them. This is a recurring operation, not a one-time setup.

## Why this exists

OpenClaw treats every external sender as untrusted by default. Without per-user approval, anyone who guessed your bot's handle could conscript the agent (cost, impersonation, data exfiltration). The pairing-code dance is a low-friction allowlist: owner approves once, that user can talk to the agent forever (until revoked).

## How it surfaces

The user's first message to the bot gets a reply like:

```
OpenClaw: access not configured.
Your Feishu user id: ou_8cdafea345e8d95b9b23bb1d6eddbd43
Pairing code: T3MQY2W3
Ask the bot owner to approve with:
openclaw pairing approve feishu T3MQY2W3
```

The Feishu user id (`ou_…`) is permanent; the pairing code is single-use and expires.

## Approve

```bash
cd ~/openclaw && pnpm openclaw --no-color pairing approve <channel> <code>
```

Examples:
- `pnpm openclaw pairing approve feishu T3MQY2W3`
- `pnpm openclaw pairing approve telegram <code>`
- `pnpm openclaw pairing approve discord <code>`

Confirm with:
```bash
pnpm openclaw --no-color pairing list --channel <channel>
```

`--channel` is **required** for `list` (the CLI errors with "Channel required" if omitted). After approve, `list` should show "No pending pairing requests".

## When the dispatch sub-command runs this

When the user invokes `/openclaw pairing <code>` or natural language ("approve feishu pairing T3MQY2W3", "let user X talk to the bot"):

1. Parse `<channel>` and `<code>` from the invocation. If channel is omitted but the code matches the format from a recent paste (`^[A-Z0-9]{6,12}$`) and recent context mentions Feishu/Telegram/Discord, infer it.
2. Run `pnpm openclaw --no-color pairing approve <channel> <code>`.
3. Verify with `pnpm openclaw --no-color pairing list --channel <channel>` — expect "No pending pairing requests".
4. Tell the user it's done; suggest they re-send a test message to the bot.

## Don't

- Don't auto-approve every code that appears in chat — the owner explicitly chose this gate. Always confirm the channel + code before running.
- Don't store pairing codes in the agentry repo or in `tokens.md` — they're single-use and don't need persistence.
- Don't try to pre-approve users by hand-editing a JSON file unless you know exactly which path stores the allowlist (it's not the same path as channel credentials). Use the `pairing approve` CLI.

## Revoke

If you need to remove access for a user later:

```bash
pnpm openclaw --no-color pairing revoke <channel> --user <ou_…>
# (Sub-command shape — confirm with `pnpm openclaw pairing --help`)
```
