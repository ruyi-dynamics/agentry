#!/usr/bin/env python3
"""
feishu-bootstrap — wire a freshly-created Feishu app into OpenClaw.

Prereqs (must be done in the Feishu Developer Console, can't be skipped):
  1. App created at https://open.feishu.cn/app
  2. Bot capability enabled (应用功能 → 机器人)
  3. Event subscriptions enabled, transport = WebSocket
  4. App installed/approved in the org
  5. App version published (without publish, scopes don't take effect)

This script does the rest:
  - Validates the appId/appSecret against open.feishu.cn (must return code:0)
  - Optionally POSTs the scope request from feishu-scopes.json (idempotent)
  - Backs up ~/.openclaw/openclaw.json, then writes the credentials at
    channels.feishu.accounts.<id> (the runtime path; plugins.entries.feishu.config.*
    is silently ignored — see the channel-config trap in setup.md)
  - Restarts the gateway LaunchAgent
  - Probes the channel and prints the verdict

Idempotent: re-running with the same args is a no-op for the JSON edit.

Usage:
  feishu-bootstrap.py --app-id cli_… --app-secret …
  feishu-bootstrap.py --app-id cli_… --app-secret … --account-id work --name 'work bot'
  feishu-bootstrap.py --app-id cli_… --app-secret … --no-scopes  # skip scope POST

Environment:
  OPENCLAW_HOME (default: ~/openclaw) — source checkout root
  OPENCLAW_STATE_DIR (default: ~/.openclaw) — user state root
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SCOPES_PATH = SCRIPT_DIR.parent / "feishu-scopes.json"
HOME = Path.home()
OPENCLAW_STATE = Path(os.environ.get("OPENCLAW_STATE_DIR", HOME / ".openclaw"))
CONFIG_PATH = OPENCLAW_STATE / "openclaw.json"


def http_post(url, body, headers=None):
    headers = {"Content-Type": "application/json", **(headers or {})}
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"_status": e.code, "_body": e.read().decode("utf-8", "replace")}
    except Exception as e:
        return {"_error": str(e)}


def validate_creds(app_id, app_secret):
    r = http_post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        {"app_id": app_id, "app_secret": app_secret},
    )
    if r.get("code") == 0 and r.get("tenant_access_token"):
        return r["tenant_access_token"]
    raise SystemExit(f"Feishu credentials rejected by open.feishu.cn: {r}")


def apply_scopes(app_id, tenant_token):
    if not SCOPES_PATH.exists():
        print(f"  ! {SCOPES_PATH} not found — skipping scope request", file=sys.stderr)
        return
    scopes = json.loads(SCOPES_PATH.read_text()).get("scopes", {})
    if not scopes:
        print("  ! scope file has no scopes key — skipping", file=sys.stderr)
        return
    url = f"https://open.feishu.cn/open-apis/application/v6/applications/{app_id}/scope_request"
    r = http_post(url, {"scopes": scopes}, headers={"Authorization": f"Bearer {tenant_token}"})
    if r.get("code") == 0:
        n_t, n_u = len(scopes.get("tenant", [])), len(scopes.get("user", []))
        print(f"  ✓ scope request submitted: {n_t} tenant + {n_u} user scopes (org admin must still approve in console)")
    else:
        print(f"  ! scope_request response: {r} (continuing — you can re-paste in console)", file=sys.stderr)


def write_config(app_id, app_secret, account_id, name, domain):
    if not CONFIG_PATH.exists():
        raise SystemExit(f"{CONFIG_PATH} not found — run /openclaw setup first")

    current = json.loads(CONFIG_PATH.read_text())
    plugins = current.setdefault("plugins", {}).setdefault("entries", {})
    plugins.setdefault("feishu", {})["enabled"] = True

    channels = current.setdefault("channels", {}).setdefault("feishu", {})
    channels["enabled"] = True
    accounts = channels.setdefault("accounts", {})

    desired = {
        "enabled": True,
        "name": name,
        "appId": app_id,
        "appSecret": app_secret,
        "domain": domain,
        "connectionMode": "websocket",
        "streaming": True,
    }

    if accounts.get(account_id) == desired:
        print(f"  · channels.feishu.accounts.{account_id} already matches — no JSON write needed")
        return False  # no change

    # Backup before mutation
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    backup = CONFIG_PATH.with_suffix(f".json.bak.{ts}")
    shutil.copy2(CONFIG_PATH, backup)
    print(f"  · backup: {backup}")

    accounts[account_id] = desired
    CONFIG_PATH.write_text(json.dumps(current, indent=2) + "\n")
    os.chmod(CONFIG_PATH, 0o600)
    print(f"  ✓ wrote channels.feishu.accounts.{account_id} = (appId={app_id}, mode=websocket)")
    return True


def restart_gateway():
    uid = os.getuid()
    subprocess.run(["launchctl", "kickstart", "-k", f"gui/{uid}/ai.openclaw.gateway"],
                   check=False, capture_output=True)
    print("  · gateway restarted (LaunchAgent kickstart)")
    time.sleep(4)


def probe_channel(account_id):
    openclaw_home = Path(os.environ.get("OPENCLAW_HOME", HOME / "openclaw"))
    cmd = ["pnpm", "openclaw", "--no-color", "channels", "status", "--deep", "--probe"]
    try:
        out = subprocess.run(cmd, cwd=openclaw_home, capture_output=True, text=True, timeout=30)
        line = next((l for l in out.stdout.splitlines() if "Feishu" in l and account_id in l), None)
        if line is None:
            line = next((l for l in out.stdout.splitlines() if "Feishu" in l), "(no Feishu line in status output)")
        print(f"  · status: {line.strip().lstrip('-').strip()}")
        if "works" in line:
            return True
        if "not configured" in line:
            print("  ! channel says not configured — verify scopes are approved in console + app version is published")
        return False
    except Exception as e:
        print(f"  ! probe failed: {e}", file=sys.stderr)
        return False


def main():
    ap = argparse.ArgumentParser(prog="feishu-bootstrap", description=__doc__.split("\n", 2)[1])
    ap.add_argument("--app-id", required=True, help="Feishu app id (cli_…)")
    ap.add_argument("--app-secret", required=True, help="Feishu app secret")
    ap.add_argument("--account-id", default="default", help="Account id under channels.feishu.accounts (default: default)")
    ap.add_argument("--name", default=None, help="Display name (default: <account-id>)")
    ap.add_argument("--domain", default="feishu", choices=["feishu", "lark"], help="Feishu vs Lark deployment (default: feishu)")
    ap.add_argument("--no-scopes", action="store_true", help="Skip POSTing scope request (use if scopes already pasted in console)")
    args = ap.parse_args()

    name = args.name or args.account_id

    print(f"feishu-bootstrap ({args.app_id}, account={args.account_id}, domain={args.domain})")

    print("[1/4] validating credentials against open.feishu.cn …")
    tenant_token = validate_creds(args.app_id, args.app_secret)
    print(f"  ✓ tenant_access_token issued: {tenant_token[:8]}…")

    if args.no_scopes:
        print("[2/4] scope application skipped (--no-scopes)")
    else:
        print(f"[2/4] applying scopes from {SCOPES_PATH.name} …")
        apply_scopes(args.app_id, tenant_token)

    print(f"[3/4] writing credentials into {CONFIG_PATH} …")
    write_config(args.app_id, args.app_secret, args.account_id, name, args.domain)

    print("[4/4] restarting gateway and probing …")
    restart_gateway()
    ok = probe_channel(args.account_id)

    if ok:
        print("\nDone. The Feishu channel is configured and running.")
        print("Next: any new Feishu user who DMs the bot will get a pairing code.")
        print("Approve with: /openclaw pairing <code>  (or pnpm openclaw pairing approve feishu <code>)")
    else:
        print("\nDone, but the channel is not yet 'works'. Common causes:")
        print("  - Scope request still pending org-admin approval (Developer Console → 应用审核)")
        print("  - App version not published")
        print("  - Bot capability not enabled (应用功能 → 机器人)")
        print("Re-run after fixing each; the script is idempotent.")


if __name__ == "__main__":
    main()
