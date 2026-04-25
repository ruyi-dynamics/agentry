# agentry

Workspace for authoring [Claude Code](https://claude.com/claude-code) **skills that manage the productive-coding-agent stack** on a single Mac — install/update agents themselves (OpenClaw, future Hermes) and the supporting infrastructure they share (e.g. credentials).

Each skill is self-contained and portable enough to drop into `~/.claude/skills/<name>/` once stable.

## Shipped skills

| Skill | Sub-commands | Purpose |
|---|---|---|
| [`openclaw/`](openclaw/) | `setup`, `update`, `doctor`, `status`, `backup` | Install, update, diagnose, snapshot OpenClaw at `~/openclaw` |
| [`token-doctor/`](token-doctor/) | `test`, `list` | Probe credentials in `~/.config/agentry/tokens.md` and report which still work (read-only) |

Invoke from Claude Code via slash command — `/openclaw doctor`, `/token-doctor test` — or natural language ("check my tokens", "update openclaw").

## Layout

```
agentry/
  CLAUDE.md             # conventions for Claude Code working in this repo
  <skill-name>/
    SKILL.md            # frontmatter (name, description) + dispatch table
    <sub>.md            # one sub-doc per sub-command
    scripts/            # optional helper scripts
  plans/                # dated implementation design notes (reference)
```

Both shipped skills follow the same dispatch pattern: `SKILL.md` parses a sub-command from `$ARGUMENTS` (or infers it from natural language) and reads the matching sub-doc. See [`CLAUDE.md`](CLAUDE.md) for full conventions.

## Installing a skill locally

Symlink the skill directory into your Claude Code skills folder:

```bash
ln -s ~/agentry/openclaw ~/.claude/skills/openclaw
ln -s ~/agentry/token-doctor ~/.claude/skills/token-doctor
```

Restart Claude Code (or open a new session) to pick up the skill.

## Out-of-repo state

These paths are referenced by skills but **not** stored in this repo:

- `~/openclaw/` — OpenClaw source checkout (managed by the `openclaw` skill, not vendored here)
- `~/.openclaw/` — OpenClaw user config & state; auto-backed-up before any mutating sub-command
- `~/.config/agentry/tokens.md` — credential inventory probed by `token-doctor`

## Adding a new skill

1. Create `<agent-or-utility>/SKILL.md` with frontmatter (`name`, `description` — the description is what the harness matches against, so be specific about triggers).
2. Use the umbrella + sub-doc pattern if the skill has more than one mode.
3. Reference any external install paths; don't vendor source into this repo.
4. If the skill writes to user config, back up first and log what changed.

See [`CLAUDE.md`](CLAUDE.md) for the full set of conventions.
