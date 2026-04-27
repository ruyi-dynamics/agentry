# /hermes dashboard — open or report the web dashboard URL

Goal: launch (or just print) the local Hermes web dashboard for managing config, API keys, and sessions in a browser.

## Run

```bash
hermes dashboard                # opens browser at http://127.0.0.1:9119/
hermes dashboard --no-open      # prints the URL but doesn't launch a browser
hermes dashboard --port 9120    # alternate port
hermes dashboard --tui          # also exposes the in-browser Chat tab (PTY/WS)
```

The dashboard binds to **127.0.0.1:9119** by default (different port from OpenClaw's 18789, no conflict — both can run side-by-side).

## Persistent reference

Unlike OpenClaw, Hermes's dashboard **does not** require a token in the URL — it auths via the local-bind assumption. So there's no `#token=…` fragment to capture; the URL is just `http://127.0.0.1:9119/`.

If you need to persist this for the user (for parity with `~/.config/agentry/openclaw-dashboard.md`), the file would be much shorter — just the URL. Skip the persist unless explicitly asked.

## Don't

- **Never** pass `--insecure` — that flag binds to non-localhost, exposing the dashboard (and your API keys) to any host that can reach this Mac. Hermes prints a warning when you try; honor it.
- Don't run two dashboards on the same port — `--port` to disambiguate.
- Don't change the bind host to `0.0.0.0` even via env var; same security reason.
