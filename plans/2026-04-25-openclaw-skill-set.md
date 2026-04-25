# OpenClaw Skill Set — Implementation Plan

**Goal:** Ship an umbrella `openclaw` skill at `~/agentry/openclaw/` with sub-commands `setup`, `update`, `doctor`, `status`, `backup`, invokable via natural language or `/openclaw <sub>`.

**Architecture:** Progressive-disclosure skill. `SKILL.md` is a thin router with frontmatter; sub-docs (`setup.md`, `update.md`, …) loaded on demand. Two helper bash scripts under `scripts/` for the operations that benefit from real shell logic (status snapshot, backup tarball). Slash command at `~/.claude/commands/openclaw.md` dispatches to the skill via `$ARGUMENTS`. Authored in `~/agentry/`, installed via symlink to `~/.claude/skills/openclaw/` so edits flow live.

**Tech stack:** bash (POSIX-ish), markdown with YAML frontmatter, symlinks. Host-only install path (no Docker).

**Verification model:** This is doc + shell authoring; no test suite. Each task's verification step is either a syntax check (`bash -n`), running the script in a safe read-only mode, or reading the file back. No git commits between tasks (agentry isn't a git repo yet). User reviews end-to-end at the smoke-test task.

---

## File structure

```
~/agentry/openclaw/
  SKILL.md           # router; frontmatter + dispatch logic
  setup.md           # host install procedure
  update.md          # git pull + rebuild
  doctor.md          # run openclaw doctor + interpret
  status.md          # invoke scripts/status.sh + interpret
  backup.md          # invoke scripts/backup.sh
  scripts/
    status.sh        # read-only snapshot
    backup.sh        # tarball ~/.openclaw/

~/.claude/commands/openclaw.md    # slash-command dispatcher

~/.claude/skills/openclaw         # symlink → ~/agentry/openclaw
```

---

## Task 1: Scaffold directories

**Files:**
- Create: `~/agentry/openclaw/`
- Create: `~/agentry/openclaw/scripts/`

- [ ] **Step 1: Create directories**

```bash
mkdir -p ~/agentry/openclaw/scripts
```

- [ ] **Step 2: Verify**

```bash
ls -la ~/agentry/openclaw/
```
Expected: directory exists with `scripts/` subdirectory.

---

## Task 2: Write SKILL.md router

**Files:**
- Create: `~/agentry/openclaw/SKILL.md`

The router reads args (passed via Skill tool's `args`, or parsed from the user message), and instructs Claude to load the matching sub-doc with the Read tool. Unknown/empty args → print menu.

- [ ] **Step 1: Write file**

Content:

````markdown
---
name: openclaw
description: Use when the user wants to install, update, check, repair, snapshot, or report on OpenClaw on this Mac, OR invokes `/openclaw …`. Sub-commands: setup, update, doctor, status, backup. Source at `~/openclaw`; user state at `~/.openclaw/`.
---

# OpenClaw lifecycle

Umbrella skill for managing the OpenClaw productive coding agent on this host.

## Dispatch

Parse the sub-command from the invocation:
- If invoked with `args` (e.g. via slash command `$ARGUMENTS`), the first whitespace-delimited token is the sub-command.
- Otherwise infer from the user's request: install/setup → `setup`; pull/upgrade/refresh → `update`; check/diagnose/health → `doctor`; show/snapshot/report → `status`; snapshot config/save state → `backup`.

Then **Read the matching sub-doc and follow it**:

| Sub | File |
|---|---|
| `setup`   | `setup.md`   |
| `update`  | `update.md`  |
| `doctor`  | `doctor.md`  |
| `status`  | `status.md`  |
| `backup`  | `backup.md`  |

If the sub-command is missing or unrecognized, print this menu and stop:

```
/openclaw <sub>
  setup    First-time host install (pnpm install + build, bootstrap ~/.openclaw)
  update   Pull latest source, rebuild, run doctor (auto-backups first)
  doctor   Run openclaw doctor and interpret the output
  status   Read-only health snapshot (no mutations)
  backup   Tarball ~/.openclaw/ to ~/.openclaw/backups/
```

## Conventions for all sub-docs

- **Host-only path.** Source lives at `~/openclaw`; user state at `~/.openclaw/`. Don't propose Docker hosting (see project memory on host-vs-Docker).
- **Confirm before mutating.** Show the planned actions and ask before executing anything that writes outside `~/.openclaw/backups/`.
- **Auto-backup before mutation.** Any sub-doc that writes to `~/.openclaw/` runs `backup.md`'s script first.
- **Defer to OpenClaw's own commands.** Use `pnpm openclaw …` and `openclaw doctor`. Do not reimplement what OpenClaw already does.
````

- [ ] **Step 2: Verify**

```bash
head -3 ~/agentry/openclaw/SKILL.md
```
Expected: shows YAML frontmatter delimiter `---` and `name: openclaw`.

---

## Task 3: Write setup.md

**Files:**
- Create: `~/agentry/openclaw/setup.md`

- [ ] **Step 1: Write file**

````markdown
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
````

- [ ] **Step 2: Verify**

```bash
test -f ~/agentry/openclaw/setup.md && wc -l ~/agentry/openclaw/setup.md
```
Expected: file exists, ~40 lines.

---

## Task 4: Write update.md

**Files:**
- Create: `~/agentry/openclaw/update.md`

- [ ] **Step 1: Write file**

````markdown
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
````

- [ ] **Step 2: Verify**

```bash
test -f ~/agentry/openclaw/update.md
```

---

## Task 5: Write doctor.md

**Files:**
- Create: `~/agentry/openclaw/doctor.md`

- [ ] **Step 1: Write file**

````markdown
# /openclaw doctor — run + interpret

Goal: surface OpenClaw's own diagnostics and translate common failure patterns into next-step suggestions.

## Run

```bash
cd ~/openclaw
pnpm openclaw doctor
```

If `pnpm openclaw doctor` itself fails to start (e.g. missing `node_modules`), the issue is install state, not config — recommend running `/openclaw setup` first.

## Interpret common patterns

OpenClaw's doctor output is the source of truth. The patterns below are hints for follow-up only.

| Pattern in output | Likely cause | Suggested next step |
|---|---|---|
| `node_modules` missing or stale | install never run / pnpm-lock changed | `/openclaw setup` (or just `cd ~/openclaw && pnpm install`) |
| Auth profile expired / unauthorized | model provider creds rotated | edit `~/.openclaw/agents/<id>/agent/auth-profiles.json`; re-run doctor |
| Channel/provider creds missing | `~/.openclaw/credentials/` incomplete | check which channel is failing, add cred file |
| Gateway not running / port in use | mac gateway daemon down or other process holds port | `openclaw gateway restart --deep` (run from app or CLI; never ad-hoc tmux per OpenClaw AGENTS.md) |
| Stale `update-check.json` | update notifier hasn't refreshed | `/openclaw update` |
| Config-format warnings about retired keys | legacy config from older OpenClaw | doctor's own auto-repair path; let it fix and re-run |

## Don't

- Don't edit `~/.openclaw/openclaw.json` by hand to silence a warning. Use doctor's repair path or `/openclaw update`.
- Don't delete `~/.openclaw/agents/` or `credentials/` to "reset" — back up first.
- Don't run `node_modules` removals as a fix without backing up first.

## Report

Summarize: doctor's overall verdict, items it auto-repaired, items needing user action.
````

- [ ] **Step 2: Verify**

```bash
test -f ~/agentry/openclaw/doctor.md
```

---

## Task 6: Write status.md

**Files:**
- Create: `~/agentry/openclaw/status.md`

- [ ] **Step 1: Write file**

````markdown
# /openclaw status — read-only snapshot

Goal: one-screen health snapshot of OpenClaw on this host. **Never mutates anything.**

## Run

```bash
~/agentry/openclaw/scripts/status.sh
```

The script prints a structured report covering:

- **Source repo**: path, current commit, branch, ahead/behind `origin/main`, dirty?
- **Build state**: `node_modules` present? package count; last `pnpm install` mtime; last `pnpm build` artifacts mtime.
- **User config**: `~/.openclaw/openclaw.json` exists + mtime; `~/.openclaw/agents/` count; presence of `credentials/`, `identity/`.
- **Update notifier**: `~/.openclaw/update-check.json` last check timestamp + last available version.
- **Docker state**: daemon running? any local images named `*openclaw*`?
- **Global binary**: any `openclaw` on `PATH`? (expected: no — this is a source install).

## Report

Read the script's output and present it as a Markdown table or bullet list. Highlight anything actionable in **bold**:
- node_modules absent → suggest `/openclaw setup`
- repo behind origin/main → suggest `/openclaw update`
- update-check older than 30 days → noted, not actionable
- doctor not run recently → suggest `/openclaw doctor`

Do not run `pnpm openclaw doctor` from status; doctor is a separate sub-command.
````

- [ ] **Step 2: Verify**

```bash
test -f ~/agentry/openclaw/status.md
```

---

## Task 7: Write backup.md

**Files:**
- Create: `~/agentry/openclaw/backup.md`

- [ ] **Step 1: Write file**

````markdown
# /openclaw backup — snapshot user state

Goal: produce a timestamped tarball of `~/.openclaw/` user state to `~/.openclaw/backups/`.

## Run

```bash
~/agentry/openclaw/scripts/backup.sh
```

The script:
1. Creates `~/.openclaw/backups/` if missing.
2. Tarballs these paths (exists-checked individually): `~/.openclaw/openclaw.json`, `~/.openclaw/agents/`, `~/.openclaw/credentials/`, `~/.openclaw/identity/`, `~/.openclaw/cron/`, `~/.openclaw/devices/`.
3. Output filename: `~/.openclaw/backups/openclaw-YYYY-MM-DDTHHMMSS.tar.gz`.
4. Prints final size and SHA-256.
5. Prunes older-than-30-day backups (configurable via `OPENCLAW_BACKUP_RETAIN_DAYS` env var).

Excluded by default (large, regenerable, or not user state): `~/.openclaw/logs/`, `~/.openclaw/workspace/`, `~/.openclaw/canvas/`, `~/.openclaw/completions/`, `*.bak*`.

## Report

After the script exits, summarize: tarball path, size, file count inside the archive, and what was pruned. If any path was missing (e.g. fresh install with no `agents/` yet), note it but don't fail.

## When to run

- Manually before any operation that mutates `~/.openclaw/` and isn't already covered by `update.md`.
- Automatically called by `update.md` step 0.
- Before any user-driven cleanup or migration.
````

- [ ] **Step 2: Verify**

```bash
test -f ~/agentry/openclaw/backup.md
```

---

## Task 8: Write scripts/status.sh

**Files:**
- Create: `~/agentry/openclaw/scripts/status.sh`

- [ ] **Step 1: Write file**

```bash
#!/usr/bin/env bash
# Read-only OpenClaw host status snapshot. No mutations.
set -uo pipefail

SRC="${OPENCLAW_SRC:-$HOME/openclaw}"
USERDIR="${OPENCLAW_HOME:-$HOME/.openclaw}"

heading() { printf '\n=== %s ===\n' "$1"; }
kv()      { printf '  %-22s %s\n' "$1" "$2"; }

heading "Source repo"
if [[ -d "$SRC/.git" ]]; then
  cd "$SRC"
  kv path "$SRC"
  kv version "$(grep -E '"version"' package.json 2>/dev/null | head -1 | sed -E 's/.*"version": "([^"]+)".*/\1/')"
  kv head    "$(git log -1 --format='%h %ai %s' 2>/dev/null)"
  kv branch  "$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
  ahead_behind=$(git rev-list --left-right --count origin/main...HEAD 2>/dev/null || echo "?\t?")
  kv ahead/behind "$(printf '%s' "$ahead_behind" | awk '{print "behind "$1", ahead "$2}')"
  dirty=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  kv dirty   "$dirty file(s)"
  cd - >/dev/null
else
  kv path "MISSING ($SRC)"
fi

heading "Build state"
if [[ -d "$SRC/node_modules" ]]; then
  pkgs=$(ls "$SRC/node_modules" 2>/dev/null | wc -l | tr -d ' ')
  kv node_modules "present ($pkgs entries)"
  kv installed_at "$(stat -f '%Sm' "$SRC/node_modules" 2>/dev/null)"
else
  kv node_modules "ABSENT — run /openclaw setup"
fi

heading "User state ($USERDIR)"
if [[ -d "$USERDIR" ]]; then
  kv path "$USERDIR"
  if [[ -f "$USERDIR/openclaw.json" ]]; then
    kv config_mtime "$(stat -f '%Sm' "$USERDIR/openclaw.json")"
  else
    kv config "MISSING openclaw.json"
  fi
  for sub in agents credentials identity cron devices; do
    if [[ -d "$USERDIR/$sub" ]]; then
      n=$(find "$USERDIR/$sub" -maxdepth 1 -mindepth 1 2>/dev/null | wc -l | tr -d ' ')
      kv "$sub/" "$n entries"
    else
      kv "$sub/" "absent"
    fi
  done
  bak_count=$(ls "$USERDIR"/openclaw.json.bak* 2>/dev/null | wc -l | tr -d ' ')
  kv config_backups "$bak_count .bak files"
  if [[ -d "$USERDIR/backups" ]]; then
    kv tar_backups "$(ls "$USERDIR/backups"/*.tar.gz 2>/dev/null | wc -l | tr -d ' ') tarball(s)"
  fi
else
  kv path "MISSING — first run will bootstrap"
fi

heading "Update notifier"
if [[ -f "$USERDIR/update-check.json" ]]; then
  kv last_check     "$(grep -o '"lastCheckedAt":"[^"]*"' "$USERDIR/update-check.json" | sed 's/.*:"//;s/"//')"
  kv last_available "$(grep -o '"lastAvailableVersion":"[^"]*"' "$USERDIR/update-check.json" | sed 's/.*:"//;s/"//')"
fi

heading "Docker"
if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    kv daemon "running"
    imgs=$(docker images --format '{{.Repository}}:{{.Tag}}' 2>/dev/null | grep -i claw || true)
    kv openclaw_images "${imgs:-none}"
  else
    kv daemon "installed but not running"
  fi
else
  kv daemon "docker CLI not installed"
fi

heading "Global binary"
if command -v openclaw >/dev/null 2>&1; then
  kv on_PATH "$(command -v openclaw) (unexpected — this is a source install)"
else
  kv on_PATH "not on PATH (expected for source install; use 'pnpm openclaw …')"
fi

echo
```

- [ ] **Step 2: Make executable**

```bash
chmod +x ~/agentry/openclaw/scripts/status.sh
```

- [ ] **Step 3: Syntax check**

```bash
bash -n ~/agentry/openclaw/scripts/status.sh && echo OK
```
Expected: `OK`.

- [ ] **Step 4: Smoke run**

```bash
~/agentry/openclaw/scripts/status.sh
```
Expected: prints sections without errors. Acceptable for some fields to show "MISSING" or "ABSENT" — that's the script reporting reality.

---

## Task 9: Write scripts/backup.sh

**Files:**
- Create: `~/agentry/openclaw/scripts/backup.sh`

- [ ] **Step 1: Write file**

```bash
#!/usr/bin/env bash
# Snapshot ~/.openclaw/ user state to a timestamped tarball.
set -euo pipefail

USERDIR="${OPENCLAW_HOME:-$HOME/.openclaw}"
RETAIN_DAYS="${OPENCLAW_BACKUP_RETAIN_DAYS:-30}"
BACKUP_DIR="$USERDIR/backups"

if [[ ! -d "$USERDIR" ]]; then
  echo "no $USERDIR — nothing to back up" >&2
  exit 0
fi

mkdir -p "$BACKUP_DIR"

stamp=$(date -u +%Y-%m-%dT%H%M%SZ)
out="$BACKUP_DIR/openclaw-$stamp.tar.gz"

# Build include list, skipping missing paths so partial installs don't fail.
includes=()
for p in openclaw.json agents credentials identity cron devices; do
  [[ -e "$USERDIR/$p" ]] && includes+=("$p")
done

if [[ ${#includes[@]} -eq 0 ]]; then
  echo "no backup-able state under $USERDIR yet" >&2
  exit 0
fi

tar -czf "$out" -C "$USERDIR" "${includes[@]}"

size=$(du -h "$out" | awk '{print $1}')
sha=$(shasum -a 256 "$out" | awk '{print $1}')
count=$(tar -tzf "$out" | wc -l | tr -d ' ')

echo "backup: $out"
echo "  size:   $size"
echo "  sha256: $sha"
echo "  files:  $count"
echo "  paths:  ${includes[*]}"

# Prune older than RETAIN_DAYS.
pruned=0
while IFS= read -r -d '' f; do
  rm -f "$f" && pruned=$((pruned+1))
done < <(find "$BACKUP_DIR" -maxdepth 1 -name 'openclaw-*.tar.gz' -mtime +"$RETAIN_DAYS" -print0 2>/dev/null || true)
echo "  pruned: $pruned older than ${RETAIN_DAYS}d"
```

- [ ] **Step 2: Make executable**

```bash
chmod +x ~/agentry/openclaw/scripts/backup.sh
```

- [ ] **Step 3: Syntax check**

```bash
bash -n ~/agentry/openclaw/scripts/backup.sh && echo OK
```
Expected: `OK`.

- [ ] **Step 4: Smoke run**

```bash
~/agentry/openclaw/scripts/backup.sh
```
Expected: prints `backup: …openclaw-…tar.gz`, size in MB-range (config + agents + creds), pruned `0` (first run).

- [ ] **Step 5: Verify tarball**

```bash
ls -lh ~/.openclaw/backups/ | head -3
tar -tzf "$(ls -t ~/.openclaw/backups/openclaw-*.tar.gz | head -1)" | head -10
```
Expected: tarball exists, contains `openclaw.json`, `agents/`, etc.

---

## Task 10: Slash command

**Files:**
- Create: `~/.claude/commands/openclaw.md`

- [ ] **Step 1: Write file**

````markdown
---
description: Manage the OpenClaw productive coding agent on this host. Usage: /openclaw <setup|update|doctor|status|backup>
argument-hint: <setup|update|doctor|status|backup>
---

Invoke the `openclaw` skill with these arguments: `$ARGUMENTS`

If `$ARGUMENTS` is empty, show the sub-command menu and stop.
````

- [ ] **Step 2: Verify**

```bash
test -f ~/.claude/commands/openclaw.md && head -5 ~/.claude/commands/openclaw.md
```

---

## Task 11: Symlink into ~/.claude/skills/

**Files:**
- Create: `~/.claude/skills/openclaw` (symlink → `~/agentry/openclaw`)

- [ ] **Step 1: Pre-check no collision**

```bash
ls -ld ~/.claude/skills/openclaw 2>/dev/null && echo "EXISTS — investigate" || echo "free to create"
```
Expected: `free to create`. If it exists already, stop and ask the user before overwriting.

- [ ] **Step 2: Create symlink**

```bash
ln -s ~/agentry/openclaw ~/.claude/skills/openclaw
```

- [ ] **Step 3: Verify**

```bash
readlink ~/.claude/skills/openclaw
ls ~/.claude/skills/openclaw/
```
Expected: readlink prints `/Users/xuhao/agentry/openclaw`; ls shows `SKILL.md`, sub-docs, `scripts/`.

---

## Task 12: Update agentry/CLAUDE.md

**Files:**
- Modify: `~/agentry/CLAUDE.md`

Replace the "currently empty" line and add a section describing what shipped.

- [ ] **Step 1: Edit**

In the **Purpose** section, change "This directory is currently empty. New work starts by creating a skill per target agent." to:

> Currently shipped: `openclaw/` (umbrella skill — sub-commands setup/update/doctor/status/backup). Next: Hermes, when its install location and CLI surface are known.

In the **OpenClaw — `~/openclaw`** section, add at the top:

> Managed by the `openclaw` skill (this workspace) — invoke via `/openclaw <sub>` or natural language ("set up openclaw", "update openclaw", etc.).

- [ ] **Step 2: Verify**

```bash
grep -n "Currently shipped" ~/agentry/CLAUDE.md
grep -n "Managed by the .openclaw. skill" ~/agentry/CLAUDE.md
```

---

## Task 13: End-to-end smoke test

- [ ] **Step 1: Skill loads**

Confirm by listing files reachable through the symlink:

```bash
ls -la ~/.claude/skills/openclaw/
cat ~/.claude/skills/openclaw/SKILL.md | head -5
```
Expected: frontmatter visible.

- [ ] **Step 2: status sub-command (read-only)**

```bash
~/.claude/skills/openclaw/scripts/status.sh
```
Expected: structured report. None of the values causes the script to error.

- [ ] **Step 3: backup sub-command**

```bash
~/.claude/skills/openclaw/scripts/backup.sh
```
Expected: tarball created at `~/.openclaw/backups/openclaw-…tar.gz`.

- [ ] **Step 4: Slash command sanity**

(Manual — next session, type `/openclaw status` and confirm the skill activates and dispatches.)

---

## Self-review checklist

- ✅ Spec coverage: setup, update, doctor, status, backup — all have a sub-doc + (where useful) a script. Slash command + symlink + CLAUDE.md update covered. Memories already saved.
- ✅ No placeholders.
- ✅ Type/name consistency: every file referenced from SKILL.md is created in tasks 3–7. Scripts referenced from status.md/backup.md are created in tasks 8–9.
- ✅ Out-of-scope items (run, gateway, auth, logs, Docker, Hermes) explicitly parked in design.
