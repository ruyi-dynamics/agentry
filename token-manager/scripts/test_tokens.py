#!/usr/bin/env python3
"""Probe all tokens in tokens.md and check cross-file consistency."""

from __future__ import annotations
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Add parent scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from lib_config import (
    read_tokens_md, check_consistency, probe_token,
    read_status_cache, write_status_cache, TOKENS_MD,
)

STATUS_ICONS = {
    "ok": "\033[32m✓\033[0m",
    "fail": "\033[31m✗\033[0m",
    "skip": "\033[33m⊘\033[0m",
    "unreachable": "\033[33m⚠\033[0m",
    "transient": "\033[35m?\033[0m",
}


def mask_key(key: str) -> str:
    """Mask a key showing first 8 and last 4 chars."""
    if len(key) <= 16:
        return key[:4] + "..." + key[-4:]
    return key[:8] + "..." + key[-4:]


def run_probe(sections, service_filter=None, workers=8):
    """Probe all tokens and return results."""
    results = []
    tasks = []

    for section in sections:
        if not section.keys:
            continue
        if service_filter and service_filter.lower() not in section.provider_name.lower():
            continue
        for key_info in section.keys:
            tasks.append((section.provider_name, section.endpoint, key_info))

    def probe_one(args):
        provider, endpoint, key_info = args
        result = probe_token(provider, key_info["value"], url=endpoint)
        return {
            "provider": provider,
            "key_label": key_info["label"],
            "key_masked": mask_key(key_info["value"]),
            "active": key_info["active"],
            **result,
        }

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(probe_one, tasks))

    return results


def run_consistency(service_filter=None):
    """Check cross-file consistency."""
    results = check_consistency()
    if service_filter:
        results = [r for r in results if service_filter.lower() in r["provider"].lower()]
    return results


def print_probe_report(results):
    """Print human-readable probe results."""
    by_provider = {}
    for r in results:
        by_provider.setdefault(r["provider"], []).append(r)

    print(f"\n{'='*70}")
    print(f"  Token Probe Report — {len(results)} tokens across {len(by_provider)} providers")
    print(f"{'='*70}\n")

    for provider, items in sorted(by_provider.items()):
        print(f"  {provider}")
        for item in items:
            icon = STATUS_ICONS.get(item["status"], "?")
            active_mark = " ★" if item.get("active") else ""
            lat = f" {item['latency_ms']:.0f}ms" if item.get("latency_ms") else ""
            print(f"    {icon} {item['key_masked']}{active_mark}  {item['detail']}{lat}")
        print()


def print_consistency_report(results):
    """Print human-readable consistency results."""
    CONS_ICONS = {
        "match": "\033[32m✓\033[0m",
        "mismatch": "\033[31m✗\033[0m",
        "not_propagated": "\033[33m⊘\033[0m",
    }

    print(f"\n{'='*70}")
    print(f"  Cross-File Consistency Report — {len(results)} providers")
    print(f"{'='*70}\n")
    print(f"  {'Provider':<20} {'Status':<15} {'OpenClaw':<10} {'Hermes':<10} {'CCR':<10}")
    print(f"  {'-'*65}")

    for r in results:
        icon = CONS_ICONS.get(r["status"], "?")
        oc = "✓" if r["openclaw_key"] == r["tokens_md_key"] else ("✗" if r["openclaw_key"] else "-")
        hm = "✓" if r["hermes_config_key"] == r["tokens_md_key"] else ("✗" if r["hermes_config_key"] else "-")
        cc = "✓" if r["ccr_key"] == r["tokens_md_key"] else ("✗" if r["ccr_key"] else "-")
        print(f"  {r['provider']:<20} {icon} {r['status']:<13} {oc:<10} {hm:<10} {cc:<10}")

    print()


def main():
    parser = argparse.ArgumentParser(description="Probe tokens and check consistency")
    parser.add_argument("--no-probe", action="store_true", help="Skip network probes")
    parser.add_argument("--consistency", action="store_true", help="Run consistency check only")
    parser.add_argument("--service", help="Filter by service name")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--workers", type=int, default=8, help="Concurrent probe workers")
    parser.add_argument("--save", action="store_true", help="Save results to status cache")
    args = parser.parse_args()

    sections = read_tokens_md()
    if not sections:
        print("Error: Could not parse tokens.md", file=sys.stderr)
        sys.exit(1)

    output = {}

    if args.consistency:
        cons = run_consistency(args.service)
        if args.json:
            print(json.dumps(cons, indent=2))
        else:
            print_consistency_report(cons)
        output["consistency"] = cons

    if not args.no_probe:
        probes = run_probe(sections, args.service, args.workers)
        if args.json:
            print(json.dumps(probes, indent=2))
        else:
            print_probe_report(probes)

        fails = [p for p in probes if p["status"] == "fail"]
        if fails:
            sys.exit(1)
        output["probes"] = probes

    if args.save:
        cache = read_status_cache()
        if "probes" in output:
            cache["probe_results"] = output["probes"]
        if "consistency" in output:
            cache["consistency_results"] = output["consistency"]
        write_status_cache(cache)


if __name__ == "__main__":
    main()
