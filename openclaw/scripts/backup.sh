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
