#!/usr/bin/env python3
"""Sync active keys from tokens.md to all agent config files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_config import (
    read_tokens_md, get_registry, env_var_name, backup_file,
    read_openclaw, get_openclaw_providers, write_openclaw_provider,
    read_hermes_custom_providers, write_hermes_custom_provider,
    read_hermes_env, write_hermes_env,
    read_ccr_config, get_ccr_providers, write_ccr_provider,
    TOKENS_MD, OPENCLAW_JSON, HERMES_CONFIG, HERMES_ENV, CCR_CONFIG,
)


def main():
    parser = argparse.ArgumentParser(description="Sync active keys from tokens.md to agent configs")
    parser.add_argument("--provider", help="Sync specific provider only")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    sections = read_tokens_md()
    if not sections:
        print("Error: Could not parse tokens.md", file=sys.stderr)
        sys.exit(1)

    # Load current configs
    oc = read_openclaw()
    oc_providers = get_openclaw_providers(oc)
    hermes_providers = read_hermes_custom_providers()
    hermes_env = read_hermes_env()
    ccr = read_ccr_config()
    ccr_providers = {p["name"]: p for p in get_ccr_providers(ccr)}

    changes = []

    for section in sections:
        if args.provider and args.provider.lower() not in section.provider_name.lower():
            continue
        if not section.active_key:
            continue

        pname = section.provider_name
        active_key = section.active_key

        # OpenClaw
        oc_entry = oc_providers.get(pname)
        if oc_entry and oc_entry.get("apiKey") != active_key:
            changes.append({
                "provider": pname, "file": "openclaw.json",
                "old": oc_entry.get("apiKey", ""), "new": active_key,
            })
            if not args.dry_run:
                oc_entry["apiKey"] = active_key
                write_openclaw_provider(OPENCLAW_JSON, pname, oc_entry)

        # Hermes config
        for hp in hermes_providers:
            if hp.get("name") == pname and hp.get("api_key") != active_key:
                changes.append({
                    "provider": pname, "file": "hermes config.yaml",
                    "old": hp.get("api_key", ""), "new": active_key,
                })
                if not args.dry_run:
                    write_hermes_custom_provider(
                        HERMES_CONFIG, pname,
                        hp.get("base_url", ""),
                        active_key,
                        hp.get("api_mode", "chat_completions"),
                    )

        # Hermes env
        evar = env_var_name(pname)
        env_val = hermes_env.get(evar)
        if env_val and env_val != active_key:
            changes.append({
                "provider": pname, "file": "hermes .env",
                "old": env_val, "new": active_key,
            })
            if not args.dry_run:
                write_hermes_env(HERMES_ENV, evar, active_key)

        # CCR
        ccr_entry = ccr_providers.get(pname)
        if ccr_entry and ccr_entry.get("api_key") != active_key:
            changes.append({
                "provider": pname, "file": "CCR config.json",
                "old": ccr_entry.get("api_key", ""), "new": active_key,
            })
            if not args.dry_run:
                ccr_entry["api_key"] = active_key
                write_ccr_provider(CCR_CONFIG, pname, ccr_entry)

    if args.json:
        print(json.dumps(changes, indent=2))
    elif changes:
        mode = "Would sync" if args.dry_run else "Synced"
        print(f"\n  {mode} {len(changes)} key(s):")
        for c in changes:
            old_masked = c["old"][:8] + "..." + c["old"][-4:] if len(c["old"]) > 12 else c["old"]
            new_masked = c["new"][:8] + "..." + c["new"][-4:] if len(c["new"]) > 12 else c["new"]
            marker = "DRY-RUN" if args.dry_run else "DONE"
            print(f"    [{marker}] {c['provider']} → {c['file']}: {old_masked} → {new_masked}")
        if args.dry_run:
            print(f"\n  Run without --dry-run to apply.")
        print()
    else:
        print("  All keys are in sync — nothing to do.")


if __name__ == "__main__":
    main()
