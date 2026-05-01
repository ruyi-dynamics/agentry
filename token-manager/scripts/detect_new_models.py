#!/usr/bin/env python3
"""Detect new models by comparing API endpoint vs tokens.md registered models."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_config import (
    read_tokens_md, discover_models, filter_latest_models,
    read_status_cache, write_status_cache,
)


def main():
    parser = argparse.ArgumentParser(description="Detect new models across providers")
    parser.add_argument("--provider", help="Check specific provider only")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--save", action="store_true", help="Save to status cache")
    args = parser.parse_args()

    sections = read_tokens_md()
    if not sections:
        print("Error: Could not parse tokens.md", file=sys.stderr)
        sys.exit(1)

    results = []

    for section in sections:
        if args.provider and args.provider.lower() not in section.provider_name.lower():
            continue
        if not section.endpoint or not section.active_key:
            continue
        if not section.model_ids:
            continue

        # Discover from API
        try:
            api_models = discover_models(section.endpoint, section.active_key)
        except Exception:
            continue

        if not api_models:
            continue

        registered = set(section.model_ids)
        api_set = set(api_models)
        new_models = sorted(api_set - registered)
        removed = sorted(registered - api_set)
        latest_new = filter_latest_models(new_models)

        results.append({
            "provider": section.provider_name,
            "registered_count": len(registered),
            "api_count": len(api_models),
            "new_count": len(new_models),
            "new_models": new_models,
            "latest_new": latest_new,
            "removed_count": len(removed),
            "removed_models": removed,
        })

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        has_changes = False
        for r in results:
            if r["new_count"] > 0 or r["removed_count"] > 0:
                has_changes = True
                print(f"\n  {r['provider']} ({r['registered_count']} registered / {r['api_count']} in API)")
                if r["new_count"] > 0:
                    print(f"    \033[32m+ {r['new_count']} new models\033[0m")
                    for m in r["latest_new"][:10]:
                        print(f"      + {m}")
                    if len(r["latest_new"]) > 10:
                        print(f"      ... and {len(r['latest_new'])-10} more")
                if r["removed_count"] > 0:
                    print(f"    \033[31m- {r['removed_count']} removed from API\033[0m")
                    for m in r["removed_models"][:5]:
                        print(f"      - {m}")

        if not has_changes:
            print("\n  All providers up to date — no new models detected.\n")

    if args.save:
        cache = read_status_cache()
        cache["discover_results"] = results
        write_status_cache(cache)


if __name__ == "__main__":
    main()
