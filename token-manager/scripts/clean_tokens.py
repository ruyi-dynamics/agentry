#!/usr/bin/env python3
"""Remove invalid/failed tokens from all config files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_config import (
    read_tokens_md, probe_token, mask_key, backup_file,
    read_openclaw, get_openclaw_providers, write_openclaw_provider,
    read_hermes_custom_providers, write_hermes_custom_provider,
    read_ccr_config, get_ccr_providers, write_ccr_provider,
    TOKENS_MD, OPENCLAW_JSON, HERMES_CONFIG, HERMES_ENV, CCR_CONFIG,
)


def main():
    parser = argparse.ArgumentParser(description="Remove failed tokens from all configs")
    parser.add_argument("--provider", help="Only consider specific provider")
    parser.add_argument("--from-json", help="Use prior test results from JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--confirm", action="store_true", help="Apply changes")
    args = parser.parse_args()

    # Get failed tokens
    if args.from_json:
        with open(args.from_json) as f:
            prior_results = json.load(f)
        failed = [r for r in prior_results if r.get("status") == "fail"]
    else:
        # Run live probe
        sections = read_tokens_md()
        failed = []
        for section in sections:
            if args.provider and args.provider.lower() not in section.provider_name.lower():
                continue
            for key_info in section.keys:
                result = probe_token(section.provider_name, key_info["value"], section.endpoint)
                if result["status"] == "fail":
                    failed.append({
                        "provider": section.provider_name,
                        "key": key_info["value"],
                        "key_label": key_info["label"],
                        "detail": result["detail"],
                    })

    if not failed:
        print("  No failed tokens found — all keys are valid or unreachable.")
        return

    if args.json:
        print(json.dumps(failed, indent=2))
        return

    # Show what would be removed
    print(f"\n  Found {len(failed)} failed token(s):")
    print(f"  {'='*60}")
    for f in failed:
        print(f"    {f['provider']}: {mask_key(f['key'])} — {f['detail']}")

    if not args.confirm:
        print(f"\n  Run with --confirm to remove these keys from all configs.")
        return

    # Backup all files
    for fpath in [TOKENS_MD, OPENCLAW_JSON, HERMES_CONFIG, HERMES_ENV, CCR_CONFIG]:
        backup_file(fpath)

    # Load configs
    oc = read_openclaw()
    oc_providers = get_openclaw_providers(oc)
    ccr = read_ccr_config()
    ccr_providers = {p["name"]: p for p in get_ccr_providers(ccr)}

    removed = []

    for fail in failed:
        pname = fail["provider"]
        key = fail["key"]

        # Remove from OpenClaw
        oc_entry = oc_providers.get(pname)
        if oc_entry and oc_entry.get("apiKey") == key:
            oc_entry["apiKey"] = ""
            write_openclaw_provider(OPENCLAW_JSON, pname, oc_entry)
            removed.append(f"openclaw.json: {pname}")

        # Remove from Hermes env
        from lib_config import read_hermes_env, write_hermes_env, env_var_name
        evar = env_var_name(pname)
        env = read_hermes_env()
        if env.get(evar) == key:
            write_hermes_env(HERMES_ENV, evar, "")
            removed.append(f"hermes .env: {evar}")

        # Remove from CCR
        ccr_entry = ccr_providers.get(pname)
        if ccr_entry and ccr_entry.get("api_key") == key:
            ccr_entry["api_key"] = ""
            write_ccr_provider(CCR_CONFIG, pname, ccr_entry)
            removed.append(f"CCR config.json: {pname}")

    print(f"\n  Removed {len(removed)} key reference(s):")
    for r in removed:
        print(f"    - {r}")


if __name__ == "__main__":
    main()
