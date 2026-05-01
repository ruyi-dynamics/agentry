#!/usr/bin/env python3
"""Benchmark response latency for provider models."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_config import read_tokens_md, discover_models, filter_latest_models


def test_model_latency(base_url: str, api_key: str, model_id: str,
                       prompt: str = "Say hello in one word.",
                       max_tokens: int = 32, timeout: int = 30) -> dict:
    """Test latency for a single model. Returns timing info."""
    url = base_url.rstrip("/") + "/chat/completions"
    payload = json.dumps({
        "model": model_id,
        "max_tokens": max_tokens,
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    })

    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode())
        t1 = time.monotonic()
        usage = body.get("usage", {})
        output = body["choices"][0]["message"]["content"][:60].replace("\n", " ").strip()
        return {
            "model": model_id,
            "status": "ok",
            "latency_s": round(t1 - t0, 2),
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "output": output,
            "error": "",
        }
    except urllib.error.HTTPError as e:
        t1 = time.monotonic()
        return {
            "model": model_id, "status": "error", "latency_s": round(t1 - t0, 2),
            "prompt_tokens": 0, "completion_tokens": 0, "output": "",
            "error": f"HTTP {e.code}",
        }
    except Exception as e:
        t1 = time.monotonic()
        return {
            "model": model_id, "status": "error", "latency_s": round(t1 - t0, 2),
            "prompt_tokens": 0, "completion_tokens": 0, "output": "",
            "error": str(e)[:60],
        }


def main():
    parser = argparse.ArgumentParser(description="Test model latency")
    parser.add_argument("provider", help="Provider name (from tokens.md)")
    parser.add_argument("--models", help="Comma-separated model IDs to test")
    parser.add_argument("--url", help="Override base URL")
    parser.add_argument("--key", help="Override API key")
    parser.add_argument("--prompt", default="Say hello in one word.", help="Test prompt")
    parser.add_argument("--max-tokens", type=int, default=32, help="Max tokens")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--save", action="store_true", help="Save to status cache")
    args = parser.parse_args()

    # Find provider
    section = None
    for s in read_tokens_md():
        if args.provider.lower() in s.provider_name.lower():
            section = s
            break

    if not section and not (args.url and args.key):
        print(f"Error: Provider '{args.provider}' not found in tokens.md", file=sys.stderr)
        sys.exit(1)

    base_url = args.url or (section.endpoint if section else "")
    api_key = args.key or (section.active_key if section else "")

    if not base_url or not api_key:
        print("Error: Need both URL and key", file=sys.stderr)
        sys.exit(1)

    # Determine models to test
    if args.models:
        model_list = [m.strip() for m in args.models.split(",")]
    elif section and section.model_ids:
        model_list = section.model_ids
    else:
        print("  Discovering models...", file=sys.stderr)
        all_models = discover_models(base_url, api_key)
        model_list = filter_latest_models(all_models) if all_models else []

    if not model_list:
        print("Error: No models to test", file=sys.stderr)
        sys.exit(1)

    # Run tests
    print(f"  Testing {len(model_list)} models on {args.provider}...", file=sys.stderr)
    results = []
    for i, model in enumerate(model_list):
        print(f"  [{i+1}/{len(model_list)}] {model}...", file=sys.stderr, end="\r")
        result = test_model_latency(base_url, api_key, model, args.prompt, args.max_tokens)
        results.append(result)
    print(file=sys.stderr)

    # Sort by latency
    results.sort(key=lambda r: r["latency_s"])

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"\n  {args.provider} — Latency Results")
        print(f"  {'='*85}")
        print(f"  {'Model':<30} {'Time':>7} {'pTok':>5} {'cTok':>5}  {'Output'}")
        print(f"  {'-'*85}")
        for r in results:
            if r["status"] == "error":
                print(f"  {r['model']:<30} {r['latency_s']:>6.2f}s  ERROR  {r['error']}")
            else:
                print(f"  {r['model']:<30} {r['latency_s']:>6.2f}s  {r['prompt_tokens']:>4}  {r['completion_tokens']:>4}  {r['output']}")

        # Stats
        ok = [r for r in results if r["status"] == "ok"]
        if ok:
            print(f"\n  Fastest: {ok[0]['model']} ({ok[0]['latency_s']:.2f}s)")
            print(f"  Slowest: {ok[-1]['model']} ({ok[-1]['latency_s']:.2f}s)")
            avg = sum(r["latency_s"] for r in ok) / len(ok)
            print(f"  Average: {avg:.2f}s")
        print()

    if args.save:
        from lib_config import read_status_cache, write_status_cache
        cache = read_status_cache()
        cache.setdefault("latency", {})[args.provider] = results
        write_status_cache(cache)


if __name__ == "__main__":
    main()
