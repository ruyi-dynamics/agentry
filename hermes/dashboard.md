# /hermes dashboard — open or report the web dashboard URL

Goal: launch (or just print) the local Hermes web dashboard for managing config, API keys, sessions, and skills in a browser.

## Critical: dashboard ≠ gateway

These are **two separate things**, easy to conflate:

| Process | Purpose | Persistence | Binds 9119? |
|---|---|---|---|
| `hermes dashboard` | Web UI for config/sessions/skills | **Foreground-only** — dies when terminal closes | ✓ |
| `hermes gateway run` (or LaunchAgent) | Daemon for messaging platforms (Feishu/Telegram/Discord) + cron jobs | Reboot-persistent (when installed via `hermes gateway install`) | ✗ — only binds when a messaging platform needs it |

**The gateway does not host the dashboard.** Installing `hermes gateway install` does NOT make `:9119` reachable. They're different commands serving different purposes.

## Run the dashboard

```bash
hermes dashboard                # opens browser at http://127.0.0.1:9119/
hermes dashboard --no-open      # binds the port but doesn't launch a browser
hermes dashboard --port 9120    # alternate port
hermes dashboard --tui          # also exposes the in-browser Chat tab (PTY/WS)
```

The dashboard binds **127.0.0.1:9119** by default (different port from OpenClaw's 18789, no conflict — both can run side-by-side).

**Startup takes ~5 seconds** — don't curl the port immediately and assume it failed. The Python imports + Hermes plugin discovery take a few seconds before the HTTP server actually binds.

## Persistence options

Hermes ships **no daemonized dashboard** — `hermes dashboard` is foreground-only by design. To keep `:9119` reachable beyond the lifetime of a single terminal, pick one:

### Option A: backgrounded shell (survives shell exit, dies on reboot)

```bash
nohup hermes dashboard --no-open >> ~/.hermes/logs/dashboard.log 2>&1 &
disown
```

After this, the process's parent reparents to `init` (PPID=1), and it survives closing the terminal. `kill <pid>` to stop. Doesn't survive macOS logout / reboot.

### Option B: macOS LaunchAgent (reboot-persistent)

Hermes does not ship a plist for this — write one at `~/Library/LaunchAgents/ai.hermes.dashboard.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>ai.hermes.dashboard</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/<USER>/.local/bin/hermes</string>
    <string>dashboard</string>
    <string>--no-open</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/Users/<USER>/.hermes/logs/dashboard.log</string>
  <key>StandardErrorPath</key><string>/Users/<USER>/.hermes/logs/dashboard.error.log</string>
  <key>WorkingDirectory</key><string>/Users/<USER>/.hermes</string>
</dict>
</plist>
```

Then:

```bash
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/ai.hermes.dashboard.plist
launchctl print gui/$UID/ai.hermes.dashboard | grep -E 'state|pid|exit'
```

Reverse with `launchctl bootout gui/$UID/ai.hermes.dashboard && rm ~/Library/LaunchAgents/ai.hermes.dashboard.plist`.

### Option C: tmux/screen session

If you live in tmux already: `tmux new -d -s hermes-dash 'hermes dashboard --no-open'`. Lighter than a LaunchAgent, easier to inspect (`tmux a -t hermes-dash`), still dies on reboot.

## Persistent reference

The dashboard URL has **no token in the URL** — Hermes auths via the local-bind assumption. So unlike OpenClaw, there's no `#token=…` fragment to capture; just `http://127.0.0.1:9119/`. If you wrote a persistence file (like `~/.config/agentry/openclaw-dashboard.md`), it would be a one-liner. Skip the persist-file unless explicitly asked.

## Don't

- **Never** pass `--insecure` — that flag binds to non-localhost, exposing the dashboard (and your API keys) to any host that can reach this Mac. Hermes prints a warning when you try; honor it.
- Don't conflate `hermes gateway` with the dashboard. The gateway is for messaging/cron; install it for chat-channel daemonization, not for dashboard persistence.
- Don't run two dashboards on the same port — `--port` to disambiguate.
- Don't change the bind host to `0.0.0.0` even via env var; same security reason.
