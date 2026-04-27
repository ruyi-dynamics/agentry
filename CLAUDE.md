# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

`agentry/` is a workspace for authoring **skills that manage the productive-coding-agent stack on this PC** — install/update agents themselves (OpenClaw, future Hermes) and the supporting infrastructure they share (e.g. credentials). Each skill is self-contained and portable enough to drop into `~/.claude/skills/` once stable.

Currently shipped:
- `openclaw/` — umbrella skill, sub-commands `setup / update / doctor / status / backup / dashboard / pairing / feishu-bootstrap`, invoked via `/openclaw <sub>` or natural language.
- `hermes/` — umbrella skill, sub-commands `setup / update / doctor / status / backup / dashboard / pairing / claw-migrate`, invoked via `/hermes <sub>` or natural language.
- `token-doctor/` — umbrella skill, sub-commands `test / list`, probes credentials in `~/.config/agentry/tokens.md` and reports validity. Read-only; never mutates the inventory.

`plans/` holds dated implementation plans (e.g. `2026-04-25-openclaw-skill-set.md`) — design notes that predate or accompany skill changes. Not loaded by the harness; reference material for humans and future sessions.

## Skill layout convention

Match the convention already used under `~/.claude/skills/`:

```
agentry/
  <agent-name>/
    SKILL.md          # frontmatter: name, description; body: when-to-trigger + steps
    scripts/          # optional: install/update shell or node scripts
    evals/            # optional
```

`SKILL.md` frontmatter must include `name` and `description` (the description is what the harness matches against to decide when to load the skill — be specific about triggers, e.g. "Use when the user asks to install/update OpenClaw"). Cross-reference: existing skill examples at `~/.claude/skills/ci-error-analyzer/SKILL.md`, `~/.claude/skills/imdataset-sync/SKILL.md`.

Once a skill is ready, it can be:
- copied/symlinked into `~/.claude/skills/<name>/` to use locally, or
- pushed to Bitbucket via the `skill-sync-bitbucket` skill (each skill lives in its own repo under the COMMON_SKILL project).

## Skill dispatch pattern

Both shipped skills use the same shape: a top-level `SKILL.md` parses a sub-command from `$ARGUMENTS` (or infers it from natural language) and reads a matching sub-doc (`setup.md`, `doctor.md`, etc.) for the actual steps. When adding a new sub-command, create a new sub-doc and add it to the dispatch table in `SKILL.md` — don't inline the steps in `SKILL.md`. Unknown/missing sub-commands print the menu and stop.

## Target agents

### OpenClaw — `~/openclaw`

Managed by the `openclaw` skill in this workspace — invoke via `/openclaw <sub>` or natural language ("set up openclaw", "update openclaw", etc.). The skill is symlinked to `~/.claude/skills/openclaw`.

Full source checkout, not installed via brew/npm. Treat `~/openclaw` as the source of truth when writing the install/update skill:

- Repo root rules and architecture: `~/openclaw/AGENTS.md` (`CLAUDE.md` is a symlink to it).
- Top-level CLI entry: `~/openclaw/openclaw.mjs`; pnpm workspace; runtime is **Node 22+**, must keep Bun paths working too.
- Install: `pnpm install` from repo root. Run via `pnpm openclaw …` or `pnpm dev`. Build via `pnpm build`.
- User config / state lives outside the repo at `~/.openclaw/` (`agents/`, `credentials/`, `workspace/`, `openclaw.json`, etc.). Backups like `openclaw.json.bak*` exist — preserve them on update.
- Channel/provider creds: `~/.openclaw/credentials/`. Model auth profiles: `~/.openclaw/agents/<agentId>/agent/auth-profiles.json`. Env keys live in `~/.profile`. Do not commit any of these.
- For doctor/repair flows, OpenClaw exposes `openclaw doctor`. Prefer it over hand-editing config when an update skill needs to reconcile state.
- Plugins live in `~/openclaw/extensions/<id>/`; skills bundled with OpenClaw live in `~/openclaw/skills/`. These are *internal* to OpenClaw — an `agentry` skill should not edit them, only invoke OpenClaw's own CLI.

### Hermes — `~/.hermes/` (installed 2026-04-26)

Managed by the `hermes` skill in this workspace — invoke via `/hermes <sub>` or natural language ("set up hermes", "update hermes", etc.). The skill is symlinked to `~/.claude/skills/hermes`.

NousResearch's Python-based agent framework. Installed via `curl|bash` (not git clone like OpenClaw):

- **Installer entry**: `https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh` → uses `uv` for Python deps. Always pass `--skip-setup` from a non-TTY context (interactive wizard hangs otherwise).
- **Code lives at**: `~/.hermes/hermes-agent/` (cloned by installer, kept current by `hermes update`).
- **State + config at**: `~/.hermes/{config.yaml, .env, sessions/, logs/, memories/, hooks/, skills/, cron/, pairing/}`. The `.env` is plaintext provider keys — load via dotenv, NOT shell init (gateway daemon doesn't see `~/.zprofile`).
- **CLI binary**: symlink at `~/.local/bin/hermes` (already on PATH).
- **Update**: `hermes update` (built-in: `git stash; git pull; uv sync`).
- **Backup**: `hermes backup [--quick]` (built-in zip; excludes the `hermes-agent/` source dir).
- **Migration from OpenClaw**: `hermes claw migrate` (see `hermes/claw-migrate.md`).

**VPN-routing trap on this Mac**: the installer's git clone over HTTPS gets mid-stream-canceled when Easy Connect VPN + ClashVerge TUN are running together (we saw the same on `git push`). Workaround: pre-clone via SSH (`git clone git@github.com:NousResearch/hermes-agent.git ~/.hermes/hermes-agent`) before re-running the installer; the installer detects the existing clone and switches to update mode. After install, persist the SSH remote so `hermes update` keeps working through the VPN: `cd ~/.hermes/hermes-agent && git remote set-url origin git@github.com:NousResearch/hermes-agent.git`.

Hermes has **its own internal skill ecosystem** at `~/.hermes/skills/` (74 bundled, separate from Claude Code's `~/.claude/skills/`). An agentry skill should not edit those directly — invoke `hermes skills …` if needed.

## Working in this directory

- Each skill (agent or utility) gets its own subdirectory; do not collapse multiple into a single skill.
- Don't copy OpenClaw/Hermes source into this repo — reference their canonical install path. Skills here orchestrate; they don't vendor.
- When a skill writes to user config (e.g. `~/.openclaw/`), it must back up first and clearly log what it changed. `token-doctor` is read-only by design — preserve that.
- This workspace is **not a git repository** at the time of writing. Don't run git commands against it; if version control is needed for a sub-skill being promoted to `~/.claude/skills/`, use the `skill-sync-bitbucket` skill (each skill lives in its own repo under the COMMON_SKILL project).
