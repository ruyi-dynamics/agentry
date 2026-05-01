#!/usr/bin/env python3
"""Discover available models from a provider's /models endpoint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_config import (
    read_tokens_md, discover_models, filter_latest_models,
    get_registry, read_status_cache, write_status_cache,
)


def find_provider(name: str) -> dict | None:
    """Find provider info from tokens.md."""
    for section in read_tokens_md():
        if name.lower() in section.provider_name.lower():
            return {
                "name": section.provider_name,
                "endpoint": section.endpoint,
                "key": section.active_key,
                "registered_models": section.model_ids,
            }
    return None


def main():
    parser = argparse.ArgumentParser(description="Discover models from a provider")
    parser.add_argument("provider", help="Provider name (from tokens.md)")
    parser.add_argument("--url", help="Override base URL")
    parser.add_argument("--key", help="Override API key")
    parser.add_argument("--latest", action="store_true", help="Filter to latest versions only")
    parser.add_argument("--prefix", help="Filter by model name prefix")
    parser.add_argument("--compare", action="store_true", help="Compare with tokens.md registered models")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--save", action="store_true", help="Save to status cache")
    args = parser.parse_args()

    # Find provider
    prov = find_provider(args.provider)
    if not prov and not (args.url and args.key):
        print(f"Error: Provider '{args.provider}' not found in tokens.md and no --url/--key given", file=sys.stderr)
        sys.exit(1)

    base_url = args.url or (prov["endpoint"] if prov else "")
    api_key = args.key or (prov["key"] if prov else "")

    if not base_url or not api_key:
        print("Error: Need both URL and key", file=sys.stderr)
        sys.exit(1)

    # Discover
    print(f"Discovering models from {base_url}...", file=sys.stderr)
    models = discover_models(base_url, api_key)

    if not models:
        print("No models found or endpoint unreachable", file=sys.stderr)
        sys.exit(1)

    # Filter
    if args.latest:
        models = filter_latest_models(models)
    if args.prefix:
        models = [m for m in models if m.startswith(args.prefix)]

    models.sort()

    if args.json:
        output = {"provider": args.provider, "models": models, "total": len(models)}
        if args.compare and prov:
            registered = set(prov.get("registered_models", []))
            api_set = set(models)
            output["new_in_api"] = sorted(api_set - registered)
            output["removed_from_api"] = sorted(registered - api_set)
            output["registered_count"] = len(registered)
        print(json.dumps(output, indent=2))
    else:
        print(f"\n  {args.provider} — {len(models)} models")
        print(f"  {'='*50}")
        for m in models:
            marker = ""
            if args.compare and prov:
                registered = set(prov.get("registered_models", []))
                if m not in registered:
                    marker = " \033[32mNEW\033[0m"
            print(f"    {m}{marker}")

        if args.compare and prov:
            registered = set(prov.get("registered_models", []))
            api_set = set(models)
            new_models = sorted(api_set - registered)
            removed = sorted(registered - api_set)
            if new_models:
                print(f"\n  \033[32m{len(new_models)} new models available\033[0m")
            if removed:
                print(f"  \033[31m{len(removed)} registered models no longer in API\033[0m")
        print()

    if args.save:
        cache = read_status_cache()
        cache.setdefault("models", {})[args.provider] = {
            "models": models,
            "count": len(models),
        }
        if args.compare and prov:
            registered = set(prov.get("registered_models", []))
            api_set = set(models)
            cache["models"][args.provider]["new_in_api"] = sorted(api_set - registered)
            cache["models"][args.provider]["registered_count"] = len(registered)
        write_status_cache(cache)


if __name__ == "__main__":
    main()
