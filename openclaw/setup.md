# /openclaw setup — first-time host install

Goal: get `~/openclaw` runnable as a productive coding agent on this Mac.

## Preflight (read-only checks)

Run each, fail fast on first miss:

```bash
node --version            # must be >= 22.x
pnpm --version            # must exist (corepack enable if missing)
git --version             # must exist
test -d ~/openclaw && echo "source: present" || echo "source: MISSING"
test -f ~/openclaw/package.json && echo "manifest: present" || echo "manifest: MISSING"
```

If any required item is missing, **stop and report**. Don't auto-install Node/pnpm/git — those are user-level decisions.

If `~/openclaw` is missing, ask the user where to clone it (default: `~/openclaw`) before running `git clone https://github.com/openclaw/openclaw.git ~/openclaw`. Confirm before cloning.

## Install

Show the plan, confirm, then run:

```bash
cd ~/openclaw
pnpm install
pnpm build
```

Notes:
- `pnpm install` may take several minutes; run in foreground and surface progress.
- `pnpm build` is required if any "build output, packaging, lazy/module boundaries, or published surfaces" can change (per OpenClaw's AGENTS.md). On a fresh install this is always true.

## First-time user state bootstrap

If `~/.openclaw/` doesn't exist yet, OpenClaw will create it on first run. Don't pre-create it manually.

If `~/.openclaw/openclaw.json` exists from a previous install, leave it alone.

## Finish with health check

Defer to `doctor.md` for interpreting the output:

```bash
cd ~/openclaw
pnpm openclaw doctor
```

Idempotency: re-running `setup` on a healthy install should be a no-op (`pnpm install` is incremental, `pnpm build` re-emits, doctor reports green).
