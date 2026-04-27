# /hermes claw-migrate — pull settings/memories/skills from OpenClaw

Goal: run Hermes's built-in OpenClaw migration to bring across model auth, memories, skills, and configuration that was set up in OpenClaw on this same Mac. **Use this once**, after Hermes is installed but before manually re-wiring providers — saves a lot of duplicate config work.

## Run

```bash
hermes backup --quick -l "before-claw-migrate"   # snapshot Hermes state first (skill convention)
hermes claw migrate --help                       # see flags first — recipe varies by version
hermes claw migrate                              # interactive; previews + asks per category
```

After migration, archive the old OpenClaw bits (their LaunchAgent, source dir, etc.) so they're not running side-by-side and competing for credentials:

```bash
hermes claw cleanup       # alias: hermes claw clean
```

`cleanup` does **not** delete OpenClaw — it archives the directories so a rollback is possible. To actually uninstall OpenClaw afterward, follow `~/agentry/openclaw/`'s reverse path (delete `~/.openclaw/`, `~/openclaw/`, `~/Library/LaunchAgents/ai.openclaw.gateway.plist`, `~/.local/bin` symlinks if any).

## What migrates and what doesn't (from upstream Hermes README — verify before relying on)

Likely migrated (paths Hermes knows about):
- Model auth profiles (the `auth-profiles.json` per-agent file)
- Memories / session history
- User-installed OpenClaw skills (under `~/.openclaw/skills/`)
- Channel credentials (Feishu, Telegram, Discord, etc.) where the schemas overlap

Likely **not** migrated:
- Custom `models.providers.<id>` entries we hand-wrote (DashScope, Volcengine) — Hermes's provider registry is different; re-register manually if needed
- OpenClaw plugin entries (`plugins.entries.<id>`) — Hermes uses a different plugin/toolset model
- Gateway tokens, device pairings (those are OpenClaw-internal auth, not portable)

## Don't

- Don't run migration against a partially-configured Hermes — always start with a fresh `~/.hermes/` state (or backup-then-clear) so the merge is unambiguous.
- Don't run `claw cleanup` until you've verified Hermes works end-to-end with the migrated config — once OpenClaw is archived, sending a Feishu message to test the OpenClaw bot won't work.
- Don't expect channel pairings to migrate verbatim — Hermes will need fresh per-user pairing approvals (the pairing-code dance) for each external user, since the pairing tokens are tied to OpenClaw's gateway identity.
