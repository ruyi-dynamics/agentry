# /hermes gateway — manage the messaging + cron daemon

Goal: manage the Hermes Gateway service, which is the **daemon process** that hosts messaging-platform integrations (Feishu, Telegram, Discord, Slack, WhatsApp, Signal) and runs scheduled cron jobs. **Does not host the web dashboard** — that's a separate command (see `dashboard.md`).

## Mental model

The gateway is conceptually identical to OpenClaw's gateway: a long-running Python daemon that:
- holds open WebSocket / webhook connections to each enabled messaging platform
- routes incoming messages → the agent → response → back to the platform
- ticks the cron scheduler every 60s for any `hermes cron` jobs
- caches model auth, plugin state, etc. so each invocation is fast

It does **not**:
- bind any HTTP port unless a messaging platform explicitly needs one (e.g. webhook receiver)
- serve the dashboard at `:9119` (foreground command — see `dashboard.md`)
- accept ad-hoc CLI prompts (use `hermes` / `hermes chat` instead)

## Sub-commands

```bash
hermes gateway run                       # foreground; dies on Ctrl+C
hermes gateway install                   # installs LaunchAgent at ~/Library/LaunchAgents/ai.hermes.gateway.plist
hermes gateway start                     # start the installed LaunchAgent
hermes gateway stop                      # stop the running LaunchAgent (without uninstalling)
hermes gateway status                    # ✓ running / ✗ stopped + recent errors
hermes gateway uninstall                 # remove the LaunchAgent (also removes from boot)
hermes gateway install --force           # reinstall over an existing plist
sudo hermes gateway install --system     # macOS doesn't really do system-level for this; prefer user-level
```

## When to install vs run foreground

- **Install** when you want messaging channels (Feishu/Telegram/etc.) to keep responding even after you close your terminal or reboot. This is the normal production setup.
- **Run foreground** for debugging — log lines stream to stdout, easier to see what's happening when wiring a new channel.

## Verify

```bash
hermes gateway status
# ✓ running, manager: launchd, pid: <N>

ps -p <pid> -o pid,etime,command   # confirm process tree
tail -f ~/.hermes/logs/gateway.log # watch live activity
```

The gateway log will show one line per message received + one per cron tick. If you wired a Feishu account, the log shows `Connected to Feishu (WebSocket)` on startup.

## What runs even with no messaging platforms

Even with zero channels enabled, the gateway daemon stays up to:
- run cron jobs (`hermes cron list` / `hermes cron add`)
- serve as the IPC target for `hermes update --gateway` (used by the in-chat `/update` command)
- pre-warm plugin discovery + model auth so the next chat invocation is faster

The startup log will say `No messaging platforms enabled. Gateway will continue running for cron job execution.` — that's fine, it's not an error.

## When the dispatch sub-command runs this

If the user invokes `/hermes gateway` or natural language ("start the hermes gateway", "is the hermes daemon running?", "install hermes as a service"):

1. Detect intent: **install** (set up service), **start** / **stop** (toggle), **status** (read-only check), **uninstall** (remove).
2. For mutating commands, confirm with the user first if no explicit `--yes` or equivalent was given.
3. Run the matching `hermes gateway <sub>` and surface the output.
4. For status, also `tail -10 ~/.hermes/logs/gateway.log` to surface any recent errors that the bare `status` command might omit.

## Don't

- Don't install the gateway hoping it'll make the dashboard reachable — it won't. They're separate processes (see `dashboard.md`'s persistence section).
- Don't run `hermes gateway run` foreground from a Bash tool call — it's an infinite loop and will hang the tool until timeout. Use `install` + `start` for non-interactive setups.
- Don't expect the gateway to serve `hermes -z` one-shot prompts — those are CLI-only invocations of the agent, not gateway-routed.
