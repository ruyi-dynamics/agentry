---
name: token-doctor
description: |
  DEPRECATED — superseded by /token-manager.
  Probes credentials in ~/.config/agentry/tokens.md and reports validity.
  All requests are forwarded to /token-manager.
---

# Token Doctor (deprecated)

This skill has been superseded by **/token-manager** which adds: add, sync, latency, models, discover, dashboard.

All sub-commands still work — they are handled by token-manager:

| Sub-command | Forwarded to |
|-------------|-------------|
| `test` | `/token-manager test` |
| `list` | `/token-manager list` |

Use `/token-manager` for the full feature set.
