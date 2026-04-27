# /hermes update — pull latest + reinstall deps

Goal: bring `~/.hermes/hermes-agent` to the upstream HEAD and re-sync Python dependencies.

## Run

```bash
hermes backup --quick               # auto-snapshot first (skill convention)
hermes update                       # git pull + uv sync inside ~/.hermes/hermes-agent
hermes doctor                       # verify
```

`hermes update` is built-in — does `git stash` (if local mods) → `git pull` → `uv sync` → restores stash. Idempotent on a healthy install (no-op if HEAD is already at origin/main).

## VPN-routing trap

Same trap as `setup.md` § 2 — `git pull` over HTTPS to GitHub fails when Easy Connect VPN + ClashVerge TUN are running. Symptom: `RPC failed; curl 92 HTTP/2 stream … was not closed cleanly`.

**Fix in place** (one-time, persistent across updates): set the repo's remote to SSH so all subsequent fetches use our `~/.ssh/config`'s id_ed25519_github:

```bash
cd ~/.hermes/hermes-agent
git remote set-url origin git@github.com:NousResearch/hermes-agent.git
git remote -v   # confirm origin is now ssh
```

After that, `hermes update` works through the VPN without intervention.

## Don't

- Don't pass `--gateway` unless you're driving update from inside a running gateway IPC context. The flag exists for `/update` from the chat UI.
- Don't `git pull` directly without `hermes update` — you'd skip the `uv sync`, leaving dep state stale.
