# /hermes pairing — approve / revoke per-user DM pairings

Goal: handle the per-user access-control gate that Hermes (like OpenClaw) puts in front of every chat channel. Each new external user who DMs the bot first triggers a "pairing required" reply with a one-time code; the bot owner runs `hermes pairing approve <code>` to whitelist them.

## Sub-commands

```bash
hermes pairing list                   # show pending + already-approved users
hermes pairing approve <code>         # whitelist by code
hermes pairing revoke <user>          # remove access (user id / handle)
hermes pairing clear-pending          # drop all pending codes (didn't approve any)
```

Hermes's `pairing` is **channel-agnostic** — same command works for Telegram / Discord / Slack / WhatsApp / Signal users. (OpenClaw required `--channel feishu` on `pairing list`; Hermes does not.) The pairing message the bot sends includes the user's channel-id so you know who you're approving.

## When the dispatch sub-command runs this

When the user invokes `/hermes pairing <code>` or natural language ("approve that hermes pairing", "let user X talk to the bot"):

1. Parse `<code>` from the invocation. If only `<channel> <code>` was provided (carried over from OpenClaw mental model), drop the channel — Hermes doesn't need it.
2. Run `hermes pairing approve <code>`.
3. Verify with `hermes pairing list` — expect the user's pending entry to be gone, and an "approved" entry present.
4. Tell the user it's done; suggest they re-send a test message.

## Don't

- Don't auto-approve every code that appears in chat — owner-decision gate.
- Don't store pairing codes in `tokens.md` or in the repo — single-use, no persistence value.
- Don't `revoke` a user without telling them; from their side it looks like the bot just stopped responding.
