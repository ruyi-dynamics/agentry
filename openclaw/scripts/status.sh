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
  ahead_behind=$(git rev-list --left-right --count origin/main...HEAD 2>/dev/null || printf '?\t?')
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
  kv last_check     "$(grep -oE '"lastCheckedAt"[[:space:]]*:[[:space:]]*"[^"]*"' "$USERDIR/update-check.json" | sed -E 's/.*"([^"]*)"$/\1/')"
  kv last_available "$(grep -oE '"lastAvailableVersion"[[:space:]]*:[[:space:]]*"[^"]*"' "$USERDIR/update-check.json" | sed -E 's/.*"([^"]*)"$/\1/')"
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
