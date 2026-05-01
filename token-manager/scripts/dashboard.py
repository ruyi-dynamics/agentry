#!/usr/bin/env python3
"""Generate an HTML dashboard for token status visualization."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import webbrowser
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_config import (
    read_tokens_md, read_status_cache, write_status_cache,
    check_consistency, DASHBOARD_HTML, STATUS_JSON,
)


def generate_html(cache: dict) -> str:
    """Generate self-contained HTML dashboard."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    probes = cache.get("probe_results", [])
    consistency = cache.get("consistency_results", [])
    models_data = cache.get("models", {})
    latency_data = cache.get("latency", {})
    discover_data = cache.get("discover_results", [])

    # Build provider cards
    provider_cards = ""
    status_colors = {
        "ok": "#22c55e", "fail": "#ef4444", "unreachable": "#f59e0b",
        "skip": "#6b7280", "transient": "#a855f7",
    }
    cons_colors = {"match": "#22c55e", "mismatch": "#ef4444", "not_propagated": "#f59e0b"}

    # Group probes by provider
    probe_by_provider = {}
    for p in probes:
        probe_by_provider.setdefault(p["provider"], []).append(p)

    # Get all providers (skip non-AI services / tool servers)
    skip_providers = {"ssh", "bitbucket", "jira", "qwen-portal", "feishu-(lark", "feishu",
                      "wandb", "huggingface", "brave"}
    all_providers = set()
    for p in probes:
        if p["provider"] not in skip_providers:
            all_providers.add(p["provider"])
    for c in consistency:
        if c["provider"] not in skip_providers:
            all_providers.add(c["provider"])

    for pname in sorted(all_providers):
        prov_probes = probe_by_provider.get(pname, [])
        cons = next((c for c in consistency if c["provider"] == pname), None)
        model_info = models_data.get(pname, {})
        lat_info = latency_data.get(pname, [])
        disc = next((d for d in discover_data if d.get("provider") == pname), None)

        # Determine overall status
        if prov_probes:
            statuses = [p["status"] for p in prov_probes]
            if "ok" in statuses:
                overall = "ok"
            elif "fail" in statuses:
                overall = "fail"
            elif "unreachable" in statuses:
                overall = "unreachable"
            else:
                overall = "skip"
        else:
            overall = "skip"

        color = status_colors.get(overall, "#6b7280")
        cons_status = cons["status"] if cons else "unknown"
        cons_color = cons_colors.get(cons_status, "#6b7280")

        # Active key display
        active_key = ""
        for p in prov_probes:
            if p.get("active"):
                active_key = p.get("key_masked", "")
                break
        if not active_key and prov_probes:
            active_key = prov_probes[0].get("key_masked", "")

        # Model count
        model_count = model_info.get("count", 0)
        new_count = 0
        if model_info.get("new_in_api"):
            new_count = len(model_info["new_in_api"])
        if disc and disc.get("new_count"):
            new_count = disc["new_count"]

        # Latency
        lat_display = ""
        if lat_info:
            ok_lat = [l for l in lat_info if l.get("status") == "ok"]
            if ok_lat:
                avg_lat = sum(l["latency_s"] for l in ok_lat) / len(ok_lat)
                lat_display = f"{avg_lat:.1f}s avg"

        # Cards
        new_badge = f'<span class="badge new">+{new_count} new</span>' if new_count else ""
        lat_badge = f'<span class="badge latency">{lat_display}</span>' if lat_display else ""
        model_badge = f'<span class="badge models">{model_count} models</span>' if model_count else ""

        provider_cards += f"""
        <div class="card" style="border-left: 4px solid {color}">
            <div class="card-header">
                <span class="provider-name">{pname}</span>
                <span class="status-dot" style="background:{color}" title="{overall}"></span>
            </div>
            <div class="card-body">
                <div class="key">{active_key or '—'}</div>
                <div class="consistency" style="color:{cons_color}">
                    Consistency: {cons_status}
                </div>
                <div class="badges">
                    {model_badge}{new_badge}{lat_badge}
                </div>
            </div>
        </div>"""

    # Build consistency matrix
    cons_matrix = ""
    if consistency:
        file_names = ["openclaw", "hermes_config", "hermes_env", "ccr"]
        file_labels = ["OpenClaw", "Hermes Config", "Hermes .env", "CCR"]
        cons_matrix = """
        <h2>Cross-File Consistency</h2>
        <table class="cons-table">
            <tr><th>Provider</th><th>Status</th>"""
        for fl in file_labels:
            cons_matrix += f"<th>{fl}</th>"
        cons_matrix += "</tr>"

        for c in consistency:
            cons_matrix += f'<tr><td>{c["provider"]}</td>'
            sc = cons_colors.get(c["status"], "#6b7280")
            cons_matrix += f'<td style="color:{sc}">{c["status"]}</td>'
            for fn in file_names:
                k = c.get(f"{fn}_key")
                tk = c.get("tokens_md_key")
                if k and tk and k == tk:
                    cons_matrix += '<td class="match">✓</td>'
                elif k and tk and k != tk:
                    cons_matrix += '<td class="mismatch">✗</td>'
                elif not k:
                    cons_matrix += '<td class="missing">—</td>'
                else:
                    cons_matrix += '<td class="missing">?</td>'
            cons_matrix += "</tr>"
        cons_matrix += "</table>"

    # Build latency chart (simple bar chart)
    lat_chart = ""
    all_lat = []
    for prov, lats in latency_data.items():
        for l in lats:
            if l.get("status") == "ok":
                all_lat.append({"model": f"{prov}/{l['model']}", "latency": l["latency_s"]})
    if all_lat:
        all_lat.sort(key=lambda x: x["latency"])
        max_lat = max(l["latency"] for l in all_lat) if all_lat else 1
        lat_chart = '<h2>Latency Benchmark</h2><div class="lat-chart">'
        for l in all_lat[:30]:
            pct = (l["latency"] / max_lat) * 100
            color = "#22c55e" if l["latency"] < 3 else "#f59e0b" if l["latency"] < 10 else "#ef4444"
            lat_chart += f"""
            <div class="lat-row">
                <span class="lat-label">{l['model']}</span>
                <div class="lat-bar-bg"><div class="lat-bar" style="width:{pct}%;background:{color}"></div></div>
                <span class="lat-val">{l['latency']:.2f}s</span>
            </div>"""
        lat_chart += "</div>"

    # New models alert
    new_alert = ""
    total_new = sum(d.get("new_count", 0) for d in discover_data)
    if total_new > 0:
        new_alert = f'<div class="alert">🔔 {total_new} new models detected across providers. Run <code>/token-manager discover</code> for details.</div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Token Manager Dashboard</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
           background: #0f172a; color: #e2e8f0; padding: 24px; }}
    h1 {{ font-size: 24px; margin-bottom: 8px; color: #f8fafc; }}
    h2 {{ font-size: 18px; margin: 24px 0 12px; color: #94a3b8; }}
    .subtitle {{ color: #64748b; font-size: 14px; margin-bottom: 24px; }}
    .alert {{ background: #1e3a5f; border: 1px solid #3b82f6; border-radius: 8px;
              padding: 12px 16px; margin-bottom: 20px; font-size: 14px; }}
    .alert code {{ background: #1e293b; padding: 2px 6px; border-radius: 4px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }}
    .card {{ background: #1e293b; border-radius: 8px; padding: 16px; }}
    .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
    .provider-name {{ font-weight: 600; font-size: 16px; }}
    .status-dot {{ width: 12px; height: 12px; border-radius: 50%; }}
    .key {{ font-family: monospace; font-size: 12px; color: #94a3b8; margin-bottom: 8px; }}
    .consistency {{ font-size: 12px; margin-bottom: 8px; }}
    .badges {{ display: flex; gap: 6px; flex-wrap: wrap; }}
    .badge {{ font-size: 11px; padding: 2px 8px; border-radius: 12px; background: #334155; }}
    .badge.new {{ background: #166534; color: #86efac; }}
    .badge.latency {{ background: #1e3a5f; color: #93c5fd; }}
    .badge.models {{ background: #312e81; color: #a5b4fc; }}
    .cons-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    .cons-table th, .cons-table td {{ padding: 8px 12px; text-align: center; border-bottom: 1px solid #334155; }}
    .cons-table th {{ color: #94a3b8; font-weight: 500; }}
    .cons-table td:first-child {{ text-align: left; font-weight: 500; }}
    .match {{ color: #22c55e; }}
    .mismatch {{ color: #ef4444; }}
    .missing {{ color: #475569; }}
    .lat-chart {{ display: flex; flex-direction: column; gap: 6px; }}
    .lat-row {{ display: flex; align-items: center; gap: 8px; }}
    .lat-label {{ width: 240px; font-size: 12px; font-family: monospace; text-align: right;
                  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .lat-bar-bg {{ flex: 1; height: 18px; background: #1e293b; border-radius: 4px; overflow: hidden; }}
    .lat-bar {{ height: 100%; border-radius: 4px; transition: width 0.3s; }}
    .lat-val {{ width: 50px; font-size: 12px; font-family: monospace; text-align: right; }}
</style>
</head>
<body>
    <h1>Token Manager Dashboard</h1>
    <p class="subtitle">Last updated: {now}</p>
    {new_alert}
    <h2>Provider Status</h2>
    <div class="grid">{provider_cards}</div>
    {cons_matrix}
    {lat_chart}
</body>
</html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="Generate token status dashboard")
    parser.add_argument("--open", action="store_true", help="Open in browser")
    parser.add_argument("--serve", type=int, metavar="PORT", help="Start local HTTP server on port")
    parser.add_argument("--refresh", action="store_true", help="Re-run all probes before generating")
    args = parser.parse_args()

    cache = read_status_cache()

    if args.refresh:
        print("  Running probes... (this may take a minute)", file=sys.stderr)
        # Run test probe
        try:
            result = subprocess.run(
                [sys.executable, str(Path(__file__).parent / "test_tokens.py"), "--json", "--save"],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode <= 1:  # 1 = some fails, still valid
                try:
                    cache["probe_results"] = json.loads(result.stdout)
                except json.JSONDecodeError:
                    pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Run model discovery + latency for known providers
        for section in read_tokens_md():
            if section.endpoint and section.active_key and section.model_ids:
                # Discover models
                try:
                    r = subprocess.run(
                        [sys.executable, str(Path(__file__).parent / "discover_models.py"),
                         section.provider_name, "--compare", "--json", "--save"],
                        capture_output=True, text=True, timeout=30,
                    )
                    if r.returncode == 0:
                        data = json.loads(r.stdout)
                        cache.setdefault("models", {})[section.provider_name] = {
                            "models": data.get("models", []),
                            "count": data.get("total", 0),
                            "new_in_api": data.get("new_in_api", []),
                            "registered_count": data.get("registered_count", 0),
                        }
                except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                    pass

                # Latency test (limit to first 5 models to keep it fast)
                models_to_test = ",".join(section.model_ids[:5])
                try:
                    r = subprocess.run(
                        [sys.executable, str(Path(__file__).parent / "latency_test.py"),
                         section.provider_name, "--models", models_to_test, "--json", "--save"],
                        capture_output=True, text=True, timeout=120,
                    )
                    if r.returncode == 0:
                        lat_data = json.loads(r.stdout)
                        cache.setdefault("latency", {})[section.provider_name] = lat_data
                except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                    pass

        write_status_cache(cache)
        cache = read_status_cache()

    # Generate HTML
    html = generate_html(cache)
    DASHBOARD_HTML.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_HTML.write_text(html)
    print(f"  Dashboard written to: {DASHBOARD_HTML}")

    if args.serve:
        os.chdir(str(DASHBOARD_HTML.parent))
        server = HTTPServer(("127.0.0.1", args.serve), SimpleHTTPRequestHandler)
        print(f"  Serving at http://127.0.0.1:{args.serve}/token-dashboard.html")
        print(f"  Press Ctrl+C to stop.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    elif args.open:
        webbrowser.open(f"file://{DASHBOARD_HTML}")


if __name__ == "__main__":
    main()
