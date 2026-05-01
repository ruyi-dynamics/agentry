#!/usr/bin/env python3
"""Add a new provider to all 5 config files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_config import (
    TOKENS_MD, OPENCLAW_JSON, HERMES_CONFIG, HERMES_ENV, CCR_CONFIG,
    detect_api_type_url, probe_api_type, discover_models, filter_latest_models,
    env_var_name, get_registry, backup_file,
    add_tokens_md_section, update_tokens_md_key,
    write_openclaw_provider, write_hermes_custom_provider,
    write_hermes_env, write_ccr_provider,
    read_tokens_md,
)


def make_model_obj(model_id: str, api_type: str) -> dict:
    """Create a model object for openclaw.json."""
    name = model_id.replace("-", " ").replace("_", " ").title()
    return {
        "id": model_id,
        "name": name,
        "input": ["text"],
        "reasoning": "think" in model_id.lower() or "r1" in model_id.lower(),
        "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
        "contextWindow": 128000,
        "maxTokens": 8192,
    }


def main():
    parser = argparse.ArgumentParser(description="Add a new provider to all configs")
    parser.add_argument("name", help="Provider name (e.g., mimo, volcengine)")
    parser.add_argument("--url", required=True, help="API base URL")
    parser.add_argument("--key", required=True, help="API key")
    parser.add_argument("--api-type", help="Override API type detection")
    parser.add_argument("--models", help="Comma-separated model list (skip discovery)")
    parser.add_argument("--no-discover", action="store_true", help="Skip model discovery")
    parser.add_argument("--no-propagate", action="store_true", help="Only update tokens.md")
    parser.add_argument("--confirm", action="store_true", help="Actually write changes")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    provider_name = args.name.lower().replace(" ", "-")

    # Step 1: Detect API type
    api_type = args.api_type
    if not api_type:
        api_type = detect_api_type_url(args.url)
        print(f"  Auto-detected API type: {api_type}", file=sys.stderr)

    # Step 2: Discover models
    model_ids = []
    if args.models:
        model_ids = [m.strip() for m in args.models.split(",")]
    elif not args.no_discover:
        print(f"  Discovering models from {args.url}...", file=sys.stderr)
        raw_models = discover_models(args.url, args.key)
        if raw_models:
            model_ids = filter_latest_models(raw_models)
            print(f"  Found {len(raw_models)} models, {len(model_ids)} after latest filter", file=sys.stderr)

    # Step 3: Build preview
    env_var = env_var_name(provider_name)
    reg = get_registry(provider_name) or {}
    ccr_transformer = reg.get("ccr_transformer", "openai")
    ccr_suffix = reg.get("ccr_url_suffix", "/chat/completions")
    ccr_url = args.url.rstrip("/") + ccr_suffix

    preview = {
        "provider": provider_name,
        "api_type": api_type,
        "endpoint": args.url,
        "env_var": env_var,
        "models_count": len(model_ids),
        "models": model_ids[:10],
        "files_to_update": ["tokens.md", "openclaw.json", "hermes config.yaml", "hermes .env", "CCR config.json"],
    }

    if args.json:
        print(json.dumps(preview, indent=2))

    if not args.confirm:
        print(f"\n  Preview — would add provider '{provider_name}':")
        print(f"  {'='*50}")
        print(f"  API type:   {api_type}")
        print(f"  Endpoint:   {args.url}")
        print(f"  Env var:    {env_var}")
        print(f"  Models:     {len(model_ids)}")
        if model_ids:
            for m in model_ids[:8]:
                print(f"    - {m}")
            if len(model_ids) > 8:
                print(f"    ... and {len(model_ids)-8} more")
        print(f"\n  Files to update: tokens.md, openclaw.json, hermes config.yaml, hermes .env, CCR config.json")
        print(f"\n  Run with --confirm to apply changes.\n")
        return

    # Step 4: Backup all files
    for f in [TOKENS_MD, OPENCLAW_JSON, HERMES_CONFIG, HERMES_ENV, CCR_CONFIG]:
        bak = backup_file(f)
        if bak:
            print(f"  Backed up: {bak}", file=sys.stderr)

    # Step 5: Check if provider already exists in tokens.md
    existing_sections = read_tokens_md()
    provider_exists = any(provider_name in s.provider_name.lower() for s in existing_sections)

    if provider_exists:
        update_tokens_md_key(TOKENS_MD, provider_name, args.key)
        print(f"  Updated tokens.md key for {provider_name}", file=sys.stderr)
    else:
        add_tokens_md_section(TOKENS_MD, provider_name, args.url, api_type, model_ids, args.key)
        print(f"  Added {provider_name} section to tokens.md", file=sys.stderr)

    if args.no_propagate:
        print("Done (tokens.md only)")
        return

    # Step 6: OpenClaw
    oc_models = [make_model_obj(m, api_type) for m in model_ids]
    oc_entry = {
        "baseUrl": args.url,
        "apiKey": args.key,
        "api": api_type,
        "models": oc_models,
    }
    write_openclaw_provider(OPENCLAW_JSON, provider_name, oc_entry)
    print(f"  Updated openclaw.json ({len(oc_models)} models)", file=sys.stderr)

    # Step 7: Hermes config
    hermes_url = args.url
    hermes_mode = reg.get("hermes_api_mode", "chat_completions")
    if hermes_mode:
        write_hermes_custom_provider(HERMES_CONFIG, provider_name, hermes_url, args.key, hermes_mode)
        print(f"  Updated hermes config.yaml", file=sys.stderr)

    # Step 8: Hermes .env
    write_hermes_env(HERMES_ENV, env_var, args.key)
    print(f"  Updated hermes .env ({env_var})", file=sys.stderr)

    # Step 9: CCR
    ccr_entry = {
        "name": provider_name,
        "api_base_url": ccr_url,
        "api_key": args.key,
        "models": model_ids,
        "transformer": {"use": [ccr_transformer]},
    }
    write_ccr_provider(CCR_CONFIG, provider_name, ccr_entry)
    print(f"  Updated CCR config.json", file=sys.stderr)

    print(f"\nDone — provider '{provider_name}' added to all 5 config files.")
    print(f"  Models: {len(model_ids)} | API type: {api_type}")


if __name__ == "__main__":
    main()
