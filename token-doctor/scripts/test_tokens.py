#!/usr/bin/env python3
"""token-doctor: probe credentials in ~/.config/agentry/tokens.md.

Reads the markdown file, extracts every backticked candidate value, classifies
each by prefix or section context, runs a minimal live probe per service, and
prints a per-service report. Tokens that can't be tested via plain HTTP (OAuth,
paired AK/SK, unknown APIs) are reported as skipped with a reason.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

DEFAULT_TOKENS_FILE = Path.home() / ".config" / "agentry" / "tokens.md"
TIMEOUT = 8


@dataclass
class Token:
    service: str
    label: str
    value: str
    section: str
    note: str = ""

    @property
    def masked(self) -> str:
        v = self.value
        if len(v) <= 16:
            return v
        return f"{v[:8]}…{v[-4:]}"


@dataclass
class ProbeResult:
    token: Token
    status: str  # "ok", "fail", "skip", "unreachable", "transient"
    detail: str = ""
    http_code: Optional[int] = None


# ── parsing ────────────────────────────────────────────────────────────────

# Find ## headings + the table block under each.
SECTION_RE = re.compile(r"^## ([^\n]+)$", re.MULTILINE)


def parse_tokens(md_path: Path) -> list[Token]:
    md = md_path.read_text()
    tokens: list[Token] = []
    sections = list(SECTION_RE.finditer(md))
    for i, m in enumerate(sections):
        section = m.group(1).strip()
        start = m.end()
        end = sections[i + 1].start() if i + 1 < len(sections) else len(md)
        body = md[start:end]

        for line in body.splitlines():
            for cell in extract_backticked(line):
                tok = classify(cell, section, line)
                if tok:
                    tokens.append(tok)
    # Dedupe by (service, value)
    seen: set[tuple[str, str]] = set()
    uniq: list[Token] = []
    for t in tokens:
        key = (t.service, t.value)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(t)
    return uniq


def extract_backticked(line: str) -> list[str]:
    return [m.group(1) for m in re.finditer(r"`([^`]+)`", line)]


def classify(value: str, section: str, line: str) -> Optional[Token]:
    v = value.strip()
    s = section.lower()

    # Skip obvious non-tokens
    if v.startswith(("http://", "https://")) and "@" not in v:
        return None
    if " " in v and not v.startswith("BBDC-"):
        return None
    if v in ("…", "...", "<key>", "<token>", "<AK>", "<SK>"):
        return None
    # Truncation markers — incomplete values
    if "..." in v or "…" in v:
        return None
    # Plain prefix labels masquerading as tokens (heading text, format examples)
    if len(v) < 20:
        return None
    # Common documentation placeholders
    if any(p in v for p in ("xxxx", "xxxxxx", "your-key", "your_key", "YOUR_")):
        return None

    # Context note: parenthetical at start of line (Markdown row) — used as a label hint
    # Remove pipe-table junk:
    note = ""
    cells = [c.strip() for c in line.split("|") if c.strip()]
    if cells:
        # Heuristic: first non-tokeny cell is the label
        for c in cells:
            if "`" not in c and c not in ("---", ""):
                note = c
                break

    # Prefix-based classification (most reliable)
    if v.startswith("sk-ant-api0"):
        return Token("Anthropic", "api_key", v, section, note)
    if v.startswith("sk-ant-oat0"):
        return Token("Anthropic", "oauth_oat01", v, section, note)
    if v.startswith("sk-ant-sid0"):
        return Token("Anthropic", "oauth_sid", v, section, note)
    if v.startswith("sk-or-v1-"):
        return Token("OpenRouter", "api_key", v, section, note)
    if v.startswith("sk-proj-"):
        return Token("OpenAI", "api_key_proj", v, section, note)
    if v.startswith("AIzaSy"):
        return Token("Gemini", "api_key", v, section, note)
    if v.startswith("hf_"):
        return Token("HuggingFace", "api_key", v, section, note)
    if v.startswith("wandb_v"):
        return Token("WandB", "api_key", v, section, note)
    if v.startswith("BBDC-"):
        return Token("Bitbucket", "personal_access_token", v, section, note)
    if v.startswith("AKLT"):
        return Token("Volcano", "access_key", v, section, note)
    if v.startswith("BSA") and re.fullmatch(r"BSA[A-Za-z0-9_\-]{20,}", v):
        return Token("Brave Search", "api_key", v, section, note)
    if v.startswith("sk-sp-") and re.fullmatch(r"sk-sp-[a-f0-9]{32,}", v):
        return Token("DashScope (Aliyun)", "api_key", v, section, note)
    if v.startswith("xoxb-") or v.startswith("xoxp-"):
        return Token("Slack", "bot_or_user_token" if v.startswith("xoxb-") else "user_token", v, section, note)
    if v.startswith("ghp_") or v.startswith("gho_") or v.startswith("ghs_") or v.startswith("ghu_"):
        return Token("GitHub", "pat", v, section, note)
    if v.startswith("cli_a") and re.fullmatch(r"cli_a[a-f0-9]{16}", v):
        return Token("Feishu", "app_id", v, section, note)
    if v.startswith("pi_3") or v.startswith("pi_4"):
        # Lebohub / Stripe-shape — section disambiguates
        if "lebohub" in s:
            return Token("Lebohub", "api_key", v, section, note)
        return Token("Stripe-shape", "api_key", v, section, note)
    # Bare sk-XXXX (relay-shape, e.g. bitexingai)
    if v.startswith("sk-") and re.fullmatch(r"sk-[A-Za-z0-9_\-]{20,}", v):
        # Section context determines this
        if "bitexingai" in s or "relay" in s:
            return Token("OpenAI-compat-relay", "api_key", v, section, note)
        if "anthropic" in s:
            return Token("Anthropic-compat-relay", "api_key", v, section, note)
        return Token("Unknown sk- shape", "api_key", v, section, note)

    # Hex-only patterns: 32-hex / 40-hex — disambiguate by section
    if re.fullmatch(r"[a-f0-9]{32}", v):
        if "fish" in s:
            return Token("FishAudio", "api_key", v, section, note)
        if "gitee" in s:
            return Token("Gitee", "personal_access_token", v, section, note)
        return None  # Too generic in unknown section
    if re.fullmatch(r"[a-f0-9]{40}", v):
        if "deepgram" in s:
            return Token("DeepGram", "api_key", v, section, note)
        return None

    # Atlassian Jira / similar base64-shape (section determines)
    if "jira" in s and re.fullmatch(r"[A-Za-z0-9+/=]{30,}", v):
        return Token("Jira", "api_token", v, section, note)
    # Volcano SK is base64-shape
    if "volcano" in s and v.endswith("=") and len(v) > 50:
        return Token("Volcano", "secret_key", v, section, note)

    return None


# ── probes ─────────────────────────────────────────────────────────────────


def http_probe(method: str, url: str, headers: dict, body: Optional[bytes] = None,
               timeout: int = TIMEOUT) -> tuple[Optional[int], str]:
    """Return (http_code, short_detail). Code is None on connection error."""
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, "ok"
    except urllib.error.HTTPError as e:
        # Read first ~200 bytes of error body for context
        try:
            body_snip = e.read(200).decode(errors="replace")
        except Exception:
            body_snip = ""
        return e.code, body_snip[:120].replace("\n", " ")
    except (urllib.error.URLError, socket.timeout, ConnectionError, OSError) as e:
        return None, str(e)[:120]


def probe_anthropic_api(t: Token) -> ProbeResult:
    code, detail = http_probe(
        "GET",
        "https://api.anthropic.com/v1/models",
        {"x-api-key": t.value, "anthropic-version": "2023-06-01"},
    )
    if code is None:
        return ProbeResult(t, "unreachable", detail)
    if code == 200:
        return ProbeResult(t, "ok", "/v1/models 200", code)
    if code in (401, 403):
        return ProbeResult(t, "fail", f"unauthorized: {detail}", code)
    return ProbeResult(t, "transient", f"{code}: {detail}", code)


def probe_openai(t: Token, base: str = "https://api.openai.com/v1") -> ProbeResult:
    code, detail = http_probe(
        "GET", f"{base}/models", {"Authorization": f"Bearer {t.value}"}
    )
    if code is None:
        return ProbeResult(t, "unreachable", detail)
    if code == 200:
        return ProbeResult(t, "ok", f"{base}/models 200", code)
    if code in (401, 403):
        return ProbeResult(t, "fail", f"unauthorized: {detail}", code)
    return ProbeResult(t, "transient", f"{code}: {detail}", code)


def probe_openrouter(t: Token) -> ProbeResult:
    code, detail = http_probe(
        "GET", "https://openrouter.ai/api/v1/models",
        {"Authorization": f"Bearer {t.value}"},
    )
    if code is None:
        return ProbeResult(t, "unreachable", detail)
    if code == 200:
        return ProbeResult(t, "ok", "/api/v1/models 200", code)
    if code in (401, 403):
        return ProbeResult(t, "fail", f"unauthorized: {detail}", code)
    return ProbeResult(t, "transient", f"{code}: {detail}", code)


def probe_gemini(t: Token) -> ProbeResult:
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={t.value}"
    code, detail = http_probe("GET", url, {})
    if code is None:
        return ProbeResult(t, "unreachable", detail)
    if code == 200:
        return ProbeResult(t, "ok", "/v1beta/models 200", code)
    if code in (400, 401, 403):
        return ProbeResult(t, "fail", f"rejected: {detail}", code)
    return ProbeResult(t, "transient", f"{code}: {detail}", code)


def probe_huggingface(t: Token) -> ProbeResult:
    code, detail = http_probe(
        "GET", "https://huggingface.co/api/whoami-v2",
        {"Authorization": f"Bearer {t.value}"},
    )
    if code is None:
        return ProbeResult(t, "unreachable", detail)
    if code == 200:
        return ProbeResult(t, "ok", "/api/whoami-v2 200", code)
    if code in (401, 403):
        return ProbeResult(t, "fail", f"unauthorized: {detail}", code)
    return ProbeResult(t, "transient", f"{code}: {detail}", code)


def probe_wandb(t: Token) -> ProbeResult:
    body = json.dumps({"query": "{ viewer { username } }"}).encode()
    code, detail = http_probe(
        "POST", "https://api.wandb.ai/graphql",
        {"Authorization": f"Bearer {t.value}", "Content-Type": "application/json"},
        body=body,
    )
    if code is None:
        return ProbeResult(t, "unreachable", detail)
    if code == 200 and "errors" not in detail.lower():
        return ProbeResult(t, "ok", "graphql viewer 200", code)
    if code in (401, 403) or "authentication" in detail.lower():
        return ProbeResult(t, "fail", f"unauthorized: {detail}", code)
    return ProbeResult(t, "transient", f"{code}: {detail}", code)


def probe_bitbucket(t: Token) -> ProbeResult:
    # Internal — needs VPN. application-properties is the cheapest authenticated GET.
    code, detail = http_probe(
        "GET", "https://bitbucket.imotion.ai:7990/rest/api/1.0/application-properties",
        {"Authorization": f"Bearer {t.value}"},
        timeout=6,
    )
    if code is None:
        return ProbeResult(t, "unreachable", f"VPN/network: {detail}")
    if code == 200:
        return ProbeResult(t, "ok", "/rest/api/1.0/application-properties 200", code)
    if code in (401, 403):
        return ProbeResult(t, "fail", f"unauthorized: {detail}", code)
    return ProbeResult(t, "transient", f"{code}: {detail}", code)


def probe_gitee(t: Token) -> ProbeResult:
    # Internal Gitee
    code, detail = http_probe(
        "GET", f"https://gitee-test.imotion.ai/api/v1/user?access_token={t.value}",
        {}, timeout=6,
    )
    if code is None:
        return ProbeResult(t, "unreachable", f"VPN/network: {detail}")
    if code == 200:
        return ProbeResult(t, "ok", "/api/v1/user 200", code)
    if code in (401, 403):
        return ProbeResult(t, "fail", f"unauthorized: {detail}", code)
    return ProbeResult(t, "transient", f"{code}: {detail}", code)


def probe_deepgram(t: Token) -> ProbeResult:
    code, detail = http_probe(
        "GET", "https://api.deepgram.com/v1/projects",
        {"Authorization": f"Token {t.value}"},
    )
    if code is None:
        return ProbeResult(t, "unreachable", detail)
    if code == 200:
        return ProbeResult(t, "ok", "/v1/projects 200", code)
    if code in (401, 403):
        return ProbeResult(t, "fail", f"unauthorized: {detail}", code)
    return ProbeResult(t, "transient", f"{code}: {detail}", code)


def probe_fishaudio(t: Token) -> ProbeResult:
    # Try the wallet endpoint first; falls back to /model
    for path in ("/wallet/self/api-credit", "/model"):
        code, detail = http_probe(
            "GET", f"https://api.fish.audio{path}",
            {"Authorization": f"Bearer {t.value}"},
        )
        if code == 200:
            return ProbeResult(t, "ok", f"{path} 200", code)
        if code in (401, 403):
            return ProbeResult(t, "fail", f"unauthorized: {detail}", code)
    return ProbeResult(t, "transient", f"{code}: {detail}", code)


def probe_brave(t: Token) -> ProbeResult:
    code, detail = http_probe(
        "GET", "https://api.search.brave.com/res/v1/web/search?q=test",
        {"X-Subscription-Token": t.value, "Accept": "application/json"},
    )
    if code is None:
        return ProbeResult(t, "unreachable", detail)
    if code == 200:
        return ProbeResult(t, "ok", "/res/v1/web/search 200", code)
    if code in (401, 403, 422):
        return ProbeResult(t, "fail", f"rejected: {detail}", code)
    return ProbeResult(t, "transient", f"{code}: {detail}", code)


def probe_dashscope(t: Token) -> ProbeResult:
    # Aliyun's Anthropic-compat endpoint expects x-api-key + minimal /v1/messages
    body = json.dumps({
        "model": "qwen-coder-plus",
        "max_tokens": 1,
        "messages": [{"role": "user", "content": "hi"}],
    }).encode()
    code, detail = http_probe(
        "POST", "https://coding.dashscope.aliyuncs.com/apps/anthropic/v1/messages",
        {"x-api-key": t.value, "anthropic-version": "2023-06-01",
         "content-type": "application/json"},
        body=body,
    )
    if code is None:
        return ProbeResult(t, "unreachable", detail)
    if code in (200, 400):
        # 400 with valid auth means the request shape was rejected but key is fine
        return ProbeResult(t, "ok", f"reachable ({code}); auth accepted", code)
    if code in (401, 403):
        return ProbeResult(t, "fail", f"unauthorized: {detail}", code)
    return ProbeResult(t, "transient", f"{code}: {detail}", code)


def probe_jira(t: Token) -> ProbeResult:
    # Internal Jira; PATs typically are sent as Bearer
    code, detail = http_probe(
        "GET", "https://jira.imotion.ai/rest/api/2/myself",
        {"Authorization": f"Bearer {t.value}"},
        timeout=6,
    )
    if code is None:
        return ProbeResult(t, "unreachable", f"VPN/network: {detail}")
    if code == 200:
        return ProbeResult(t, "ok", "/rest/api/2/myself 200", code)
    if code in (401, 403):
        return ProbeResult(t, "fail", f"unauthorized: {detail}", code)
    return ProbeResult(t, "transient", f"{code}: {detail}", code)


def probe_skip(t: Token, reason: str) -> ProbeResult:
    return ProbeResult(t, "skip", reason)


def probe_token(t: Token) -> ProbeResult:
    svc = t.service
    if svc == "Anthropic":
        if t.label == "api_key":
            return probe_anthropic_api(t)
        if t.label.startswith("oauth"):
            return probe_skip(t, "OAuth/session token — test via Claude Code or `claude --resume`")
    if svc == "OpenAI":
        return probe_openai(t)
    if svc == "OpenRouter":
        return probe_openrouter(t)
    if svc == "Gemini":
        return probe_gemini(t)
    if svc == "HuggingFace":
        return probe_huggingface(t)
    if svc == "WandB":
        return probe_wandb(t)
    if svc == "Bitbucket":
        return probe_bitbucket(t)
    if svc == "Gitee":
        return probe_gitee(t)
    if svc == "Jira":
        return probe_jira(t)
    if svc == "DeepGram":
        return probe_deepgram(t)
    if svc == "FishAudio":
        return probe_fishaudio(t)
    if svc == "Brave Search":
        return probe_brave(t)
    if svc == "DashScope (Aliyun)":
        return probe_dashscope(t)
    if svc == "Volcano":
        return probe_skip(t, "AK/SK pair — needs `tosutil` with both halves; test out of band")
    if svc == "Feishu":
        return probe_skip(t, "appId is not a credential by itself; verify `lark-cli auth status`")
    if svc == "Lebohub":
        return probe_skip(t, "no public probe endpoint known for Lebohub")
    if svc == "Stripe-shape":
        return probe_skip(t, "ambiguous Stripe-shape token; needs explicit endpoint")
    if svc == "OpenAI-compat-relay":
        # Try OpenAI-shape /models against the known relay base
        # Wiki labels bitexingai with base = https://bitexingai.com/v1
        return probe_openai(t, base="https://bitexingai.com/v1")
    if svc == "Anthropic-compat-relay":
        # Wiki has ANTHROPIC_BASE_URL=https://claudecode.aikeji.vip; try /v1/models there
        code, detail = http_probe(
            "GET", "https://claudecode.aikeji.vip/v1/models",
            {"x-api-key": t.value, "anthropic-version": "2023-06-01"},
        )
        if code is None:
            return ProbeResult(t, "unreachable", detail)
        if code == 200:
            return ProbeResult(t, "ok", "relay /v1/models 200", code)
        if code in (401, 403):
            return ProbeResult(t, "fail", f"unauthorized: {detail}", code)
        return ProbeResult(t, "transient", f"{code}: {detail}", code)
    if svc == "GitHub":
        code, detail = http_probe(
            "GET", "https://api.github.com/user",
            {"Authorization": f"Bearer {t.value}"},
        )
        if code is None:
            return ProbeResult(t, "unreachable", detail)
        if code == 200:
            return ProbeResult(t, "ok", "/user 200", code)
        if code in (401, 403):
            return ProbeResult(t, "fail", f"unauthorized: {detail}", code)
        return ProbeResult(t, "transient", f"{code}: {detail}", code)
    if svc == "Slack":
        code, detail = http_probe(
            "GET", "https://slack.com/api/auth.test",
            {"Authorization": f"Bearer {t.value}"},
        )
        if code is None:
            return ProbeResult(t, "unreachable", detail)
        # Slack always returns 200; check body
        if code == 200 and '"ok":true' in detail:
            return ProbeResult(t, "ok", "auth.test ok=true", code)
        return ProbeResult(t, "fail", f"slack: {detail}", code)
    return probe_skip(t, "no probe handler implemented")


# ── output ─────────────────────────────────────────────────────────────────

ICON = {"ok": "✓", "fail": "✗", "skip": "⚠", "unreachable": "⊘", "transient": "?"}


def render_report(results: list[ProbeResult]) -> None:
    by_svc: dict[str, list[ProbeResult]] = {}
    for r in results:
        by_svc.setdefault(r.token.service, []).append(r)

    summary = {"ok": 0, "fail": 0, "skip": 0, "unreachable": 0, "transient": 0}
    for r in results:
        summary[r.status] = summary.get(r.status, 0) + 1

    print(f"\n  totals: ok={summary['ok']} fail={summary['fail']} "
          f"skip={summary['skip']} unreachable={summary['unreachable']} "
          f"transient={summary['transient']}\n")
    for svc in sorted(by_svc):
        items = by_svc[svc]
        print(f"=== {svc} ({len(items)}) ===")
        for r in items:
            t = r.token
            line = f"  {ICON[r.status]} [{t.label}] {t.masked}"
            if t.note and t.note not in (t.value, "Type", "Token", "Value", "Project"):
                line += f"  ({t.note[:48]})"
            print(line)
            if r.detail and r.status != "ok":
                print(f"      {r.detail[:160]}")
        print()


def render_list(tokens: list[Token]) -> None:
    by_svc: dict[str, list[Token]] = {}
    for t in tokens:
        by_svc.setdefault(t.service, []).append(t)
    print(f"\n  {len(tokens)} tokens across {len(by_svc)} services\n")
    for svc in sorted(by_svc):
        items = by_svc[svc]
        print(f"=== {svc} ({len(items)}) ===")
        for t in items:
            line = f"  [{t.label}] {t.masked}"
            if t.note and t.note not in (t.value, "Type", "Token", "Value", "Project"):
                line += f"  ({t.note[:60]})"
            print(line)
        print()


# ── main ───────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tokens-file", type=Path, default=DEFAULT_TOKENS_FILE)
    ap.add_argument("--no-probe", action="store_true",
                    help="parse + list only, no network")
    ap.add_argument("--service", help="filter to a single service name (case-insensitive)")
    ap.add_argument("--json", action="store_true",
                    help="emit JSON instead of human report")
    ap.add_argument("--workers", type=int, default=8,
                    help="parallel probe workers (default 8)")
    args = ap.parse_args()

    if not args.tokens_file.exists():
        print(f"tokens file not found: {args.tokens_file}", file=sys.stderr)
        return 2

    tokens = parse_tokens(args.tokens_file)
    if args.service:
        tokens = [t for t in tokens
                  if args.service.lower() in t.service.lower()]

    if args.no_probe:
        if args.json:
            print(json.dumps([asdict(t) for t in tokens], ensure_ascii=False, indent=2))
        else:
            render_list(tokens)
        return 0

    results: list[ProbeResult] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(probe_token, t) for t in tokens]
        for f in as_completed(futures):
            results.append(f.result())

    # Stable sort: by service then by label
    results.sort(key=lambda r: (r.token.service, r.token.label, r.token.value))

    if args.json:
        print(json.dumps(
            [{"token": asdict(r.token), "status": r.status,
              "detail": r.detail, "http_code": r.http_code}
             for r in results], ensure_ascii=False, indent=2))
        return 0

    render_report(results)

    # Exit code: 0 if all ok or all skipped/unreachable; 1 if any fail.
    if any(r.status == "fail" for r in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
