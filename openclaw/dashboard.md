# /openclaw dashboard — open or report the Control UI URL

Goal: surface the local OpenClaw Control UI URL with the gateway token included, without blindly hand-copying secrets each time.

## Where the URL + token are stored

Persistent reference file (mode 600, outside any git repo):

```
~/.config/agentry/openclaw-dashboard.md
```

This file holds the current token-authenticated URL and the bare gateway token, plus regeneration commands. Read it first — if the token there still matches `~/openclaw/.env`'s `OPENCLAW_GATEWAY_TOKEN`, no refresh needed.

## How to print/refresh the URL

```bash
cd ~/openclaw && pnpm openclaw dashboard --no-open
```

This prints the base URL (`http://127.0.0.1:18789/`) and copies the **full token-bearing URL** to the macOS clipboard (`pbpaste` to read it back). The "#token=…" fragment is the gateway shared secret from `~/openclaw/.env` — same value across invocations until rotated.

To open the dashboard directly in the default browser:

```bash
cd ~/openclaw && pnpm openclaw dashboard
```

## After a token rotation

If the user runs `pnpm openclaw doctor --generate-gateway-token --non-interactive --yes`, the token in `~/openclaw/.env` rotates and the dashboard URL changes. Refresh `~/.config/agentry/openclaw-dashboard.md` by re-running `dashboard --no-open` and pasting the new URL into that file.

## Don't

- Don't commit the token-bearing URL to any git repo — `~/.config/agentry/` is the right home; do not copy into `~/agentry/`.
- Don't delete `~/openclaw/.env` — it holds the live `OPENCLAW_GATEWAY_TOKEN`. Even after a gateway restart, the token in there is what the dashboard URL uses.
- Don't print the full token-bearing URL inline in chat output unless the user asks for it; prefer pointing them at `pbpaste` or the storage file.
