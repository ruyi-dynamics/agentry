# /openclaw update — pull + rebuild

Goal: bring `~/openclaw` to latest `origin/main`, rebuild what's needed, verify health.

## Step 0: Backup first

Always run `backup.md`'s script before mutating. This snapshots `~/.openclaw/` to a tarball.

```bash
~/agentry/openclaw/scripts/backup.sh
```

If the backup fails, **stop**. Do not proceed to mutate state.

## Step 1: Verify clean working tree

```bash
cd ~/openclaw
git status -sb
```

If there are uncommitted changes, stop and ask the user: stash, commit, or abort? Don't decide unilaterally — local edits in `~/openclaw` may be intentional (the user may be developing OpenClaw itself).

## Step 2: Pull

```bash
cd ~/openclaw
git pull --rebase origin main
```

If rebase conflicts: stop and ask. Do not auto-resolve.

## Step 3: Reinstall deps

```bash
cd ~/openclaw
pnpm install
```

## Step 4: Conditional rebuild

Run `pnpm build` if any of these changed since the previous head: `package.json`, `pnpm-lock.yaml`, `src/**`, `extensions/**`, `tsconfig*.json`, or `tsdown.config.ts`. Cheap heuristic: just always rebuild after `git pull` — it's a few seconds on a no-op rebuild and the OpenClaw AGENTS.md says "Hard build gate: `pnpm build` before push if build output … can change."

```bash
cd ~/openclaw
pnpm build
```

## Step 5: Health check

```bash
cd ~/openclaw
pnpm openclaw doctor
```

Hand off to `doctor.md` for interpreting output.

## Step 6: Report

Summarize: previous rev → new rev (`git log -1 --format='%h %s'` before/after), what was rebuilt, doctor result.
