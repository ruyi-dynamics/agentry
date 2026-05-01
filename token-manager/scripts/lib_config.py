#!/usr/bin/env python3
"""Shared library for token-manager: read/write 5 config files, backup, registry, API detection."""

from __future__ import annotations
import json
import os
import re
import shutil
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any

# ─── Paths ───────────────────────────────────────────────────────────────────

TOKENS_MD = Path.home() / ".config" / "agentry" / "tokens.md"
OPENCLAW_JSON = Path.home() / ".openclaw" / "openclaw.json"
HERMES_CONFIG = Path.home() / ".hermes" / "config.yaml"
HERMES_ENV = Path.home() / ".hermes" / ".env"
CCR_CONFIG = Path.home() / ".claude-code-router" / "config.json"
STATUS_JSON = Path.home() / ".config" / "agentry" / "token-status.json"
DASHBOARD_HTML = Path.home() / ".config" / "agentry" / "token-dashboard.html"

# ─── Provider Registry ───────────────────────────────────────────────────────

PROVIDER_REGISTRY: dict[str, dict[str, Any]] = {
    "openai": {
        "env_var": "OPENAI_API_KEY",
        "default_base_url": "https://api.openai.com/v1",
        "api_type": "openai-completions",
        "hermes_api_mode": "chat_completions",
        "ccr_transformer": "openai",
        "ccr_url_suffix": "/chat/completions",
        "probe_url_suffix": "/models",
    },
    "anthropic": {
        "env_var": "ANTHROPIC_API_KEY",
        "default_base_url": "https://api.anthropic.com",
        "api_type": "anthropic-messages",
        "hermes_api_mode": None,
        "ccr_transformer": "Anthropic",
        "ccr_url_suffix": "/v1/messages",
        "probe_url_suffix": "/v1/models",
    },
    "openrouter": {
        "env_var": "OPENROUTER_API_KEY",
        "default_base_url": "https://openrouter.ai/api/v1",
        "api_type": "openai-completions",
        "hermes_api_mode": "chat_completions",
        "ccr_transformer": "openrouter",
        "ccr_url_suffix": "/chat/completions",
        "probe_url_suffix": "/models",
    },
    "gemini": {
        "env_vars": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "default_base_url": "https://generativelanguage.googleapis.com/v1beta",
        "api_type": "google-generative-ai",
        "hermes_api_mode": "chat_completions",
        "ccr_transformer": "gemini",
        "ccr_url_suffix": "/models",
        "probe_url_suffix": "/models",
    },
    "dashscope": {
        "env_var": "DASHSCOPE_API_KEY",
        "default_base_url": "https://coding.dashscope.aliyuncs.com/v1",
        "api_type": "openai-completions",
        "hermes_api_mode": "chat_completions",
        "ccr_transformer": "openai",
        "ccr_url_suffix": "/chat/completions",
        "probe_url_suffix": "/chat/completions",
        "probe_method": "POST",
        "alt_base_urls": ["https://coding.dashscope.aliyuncs.com/apps/anthropic"],
    },
    "volcengine": {
        "env_var": "VOLCENGINE_API_KEY",
        "default_base_url": "https://ark.cn-beijing.volces.com/api/coding/v3",
        "api_type": "openai-completions",
        "hermes_api_mode": "chat_completions",
        "ccr_transformer": "openai",
        "ccr_url_suffix": "/chat/completions",
        "probe_url_suffix": "/models",
    },
    "mimo": {
        "env_var": "MIMO_API_KEY",
        "default_base_url": "https://token-plan-cn.xiaomimimo.com/v1",
        "api_type": "openai-completions",
        "hermes_api_mode": "chat_completions",
        "ccr_transformer": "openai",
        "ccr_url_suffix": "/chat/completions",
        "probe_url_suffix": "/models",
    },
    "bitexingai": {
        "env_var": "BITEXINGAI_API_KEY",
        "default_base_url": "https://bitexingai.com/v1",
        "api_type": "openai-completions",
        "hermes_api_mode": "chat_completions",
        "ccr_transformer": "openai",
        "ccr_url_suffix": "/chat/completions",
        "probe_url_suffix": "/models",
    },
    "deepgram": {
        "env_var": "DEEPGRAM_API_KEY",
        "default_base_url": "https://api.deepgram.com",
        "api_type": "rest-api",
        "probe_url_suffix": "/v1/projects",
    },
    "fishaudio": {
        "env_var": "FISH_AUDIO_API_KEY",
        "default_base_url": "https://api.fish.audio",
        "api_type": "rest-api",
        "probe_url_suffix": "/v1/tts",
        "probe_method": "POST",
    },
    "brave": {
        "env_var": "BRAVE_SEARCH_API_KEY",
        "default_base_url": "https://api.search.brave.com",
        "api_type": "rest-api",
        "probe_url_suffix": "/res/v1/web/search?q=test&count=1",
    },
    "huggingface": {
        "env_var": "HF_TOKEN",
        "default_base_url": "https://huggingface.co",
        "api_type": "rest-api",
        "probe_url_suffix": "/api/whoami-v2",
    },
    "wandb": {
        "env_var": "WANDB_API_KEY",
        "default_base_url": "https://api.wandb.ai",
        "api_type": "rest-api",
        "probe_url_suffix": "/graphql",
    },
}


def get_registry(name: str) -> dict[str, Any] | None:
    """Look up provider in registry (case-insensitive)."""
    return PROVIDER_REGISTRY.get(name.lower())


def env_var_name(provider_name: str) -> str:
    """Get the env var name for a provider."""
    reg = get_registry(provider_name)
    if reg:
        v = reg.get("env_var")
        if v:
            return v
        ev = reg.get("env_vars")
        if ev:
            return ev[0]
    return f"{provider_name.upper()}_API_KEY"


# ─── Backup ──────────────────────────────────────────────────────────────────

def backup_file(path: Path) -> Path | None:
    """Create a timestamped backup. Returns backup path or None if file doesn't exist."""
    if not path.exists():
        return None
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = path.with_suffix(path.suffix + f".bak.{ts}")
    shutil.copy2(path, bak)
    return bak


# ─── tokens.md Reader ───────────────────────────────────────────────────────

class TokenSection:
    """A parsed section from tokens.md."""
    def __init__(self, heading: str, level: int, body: str):
        self.heading = heading
        self.level = level
        self.body = body
        self.provider_name = ""
        self.endpoint = ""
        self.api_enum = ""
        self.model_ids: list[str] = []
        self.keys: list[dict[str, str]] = []  # [{label, value, active}]
        self._parse()

    def _parse(self):
        # Extract provider name from heading (strip section number, keep spaces for readability)
        m = re.match(r'(?:\d+\.\d+\s+)?(.+?)(?:\s*—.*)?$', self.heading)
        if m:
            self.provider_name = m.group(1).strip().lower().replace(' ', '-').replace('&', '-')

        # Normalize to config-file-compatible names
        name_map = {
            "openai-(gpt)": "openai",
            "google-gemini": "gemini",
            "bitexingai-(3rd-party-openai-compatible-relay)": "bitexingai",
            "anthropic-(claude)": "anthropic",
            "mimo-(xiaomi)": "mimo",
            "aliyun-dashscope-coding-plan": "dashscope",
            "volcengine-(bytedance)-coding-plan": "volcengine",
            "qwen-portal-(tongyi-/-aliyun)": "qwen-portal",
            "deepgram": "deepgram",
            "fish-audio": "fishaudio",
            "brave-search": "brave",
            "atlassian-bitbucket-server-(`bitbucket.imotion.ai`)": "bitbucket",
            "atlassian-jira-(`jira.imotion.ai`-or-similar)": "jira",
            "huggingface": "huggingface",
            "weights---biases": "wandb",
            "ssh-servers": "ssh",
        }
        self.provider_name = name_map.get(self.provider_name, self.provider_name)

        # Extract endpoint — try bullet format first, then table format
        m = re.search(r'\*\*Endpoint\*\*:\s*`([^`]+)`', self.body)
        if m:
            self.endpoint = m.group(1)
        else:
            # Table format: look for URLs in table rows with "★ active" or first URL
            active_urls = re.findall(r'\*\*.*?★\s*active.*?\*\*.*?`([^`]+https?://[^`]+)`', self.body)
            if active_urls:
                self.endpoint = active_urls[0]
            else:
                # First URL in a table row
                table_urls = re.findall(r'\|\s*`?(https?://[^`\s|]+)', self.body)
                if table_urls:
                    self.endpoint = table_urls[0]

        # Extract API enum
        m = re.search(r'`api`\s*enum.*?:\s*`([^`]+)`', self.body)
        if m:
            self.api_enum = m.group(1)

        # Extract model IDs from "Supported model IDs" line
        m = re.search(r'\*\*Supported model IDs?\*\*.*?:\s*(.+?)(?:\n\n|\n#|\Z)', self.body, re.DOTALL)
        if m:
            raw = m.group(1)
            ids = re.findall(r'`([^`]+)`', raw)
            # Filter to valid model IDs: lowercase, digits, hyphens, dots; no paths/config/env vars
            self.model_ids = [
                mid for mid in ids
                if not mid.startswith('http')
                and not mid.startswith('~')
                and not mid.startswith('*')
                and '/' not in mid
                and '[' not in mid
                and not mid.isupper()  # Skip env vars like VOLCENGINE_API_KEY
                and len(mid) > 2  # Skip short strings like v3
                and not re.search(r'\.\w+\.', mid)  # Skip config paths like models.providers.volcengine
                and re.match(r'^[a-z0-9][a-z0-9._-]*$', mid)  # Valid model ID pattern
            ]

        # Extract keys from markdown tables
        for row_match in re.finditer(r'\|(.+)\|', self.body):
            cells = [c.strip() for c in row_match.group(1).split('|')]
            if len(cells) >= 2:
                for cell in cells:
                    key_match = re.search(r'`([a-zA-Z0-9_-]{20,})`', cell)
                    if key_match:
                        key_val = key_match.group(1)
                        # Skip if it looks like a URL, example, or error message
                        if key_val.startswith('http'):
                            continue
                        # Skip strings containing common error words
                        if re.search(r'(?i)(error|invalid|failed|missing|exception|authn)', key_val):
                            continue
                        is_active = '★' in row_match.group(0) or 'active' in row_match.group(0).lower()
                        # Determine label from first cell
                        label = cells[0].strip().rstrip('*').strip()
                        self.keys.append({"label": label, "value": key_val, "active": is_active})
                        break

    @property
    def active_key(self) -> str | None:
        """Return the active key, or the first key if none marked active."""
        for k in self.keys:
            if k["active"]:
                return k["value"]
        return self.keys[0]["value"] if self.keys else None


def read_tokens_md(path: Path = TOKENS_MD) -> list[TokenSection]:
    """Parse tokens.md into sections."""
    if not path.exists():
        return []
    text = path.read_text()
    sections = []
    # Split by ## headings (level 2) — these are the provider sections
    parts = re.split(r'^(#{2,3}\s+.+)$', text, flags=re.MULTILINE)
    current_heading = None
    current_level = 0
    for part in parts:
        hm = re.match(r'^(#{2,3})\s+(.+)$', part)
        if hm:
            current_heading = hm.group(2).strip()
            current_level = len(hm.group(1))
        elif current_heading:
            sections.append(TokenSection(current_heading, current_level, part))
            current_heading = None
    return sections


# ─── tokens.md Writer ───────────────────────────────────────────────────────

def update_tokens_md_key(path: Path, provider_name: str, new_key: str, label: str = ""):
    """Add or update a key in tokens.md for a provider section. Marks new key as ★ active."""
    backup_file(path)
    text = path.read_text()

    # Find the section for this provider
    pattern = re.compile(
        rf'(##\s+\d+\.\d+\s+.*{re.escape(provider_name)}.*\n)',
        re.IGNORECASE
    )
    m = pattern.search(text)
    if not m:
        # Try matching by name in heading
        for section in read_tokens_md(path):
            if provider_name.lower() in section.provider_name.lower():
                m = re.search(rf'(##\s+.*{re.escape(section.heading)}.*\n)', text)
                break

    if not m:
        print(f"Warning: No section found for '{provider_name}' in tokens.md")
        return False

    section_start = m.start()
    # Find the end of this section (next ## or end of file)
    next_section = re.search(r'\n##\s+\d+\.', text[m.end():])
    section_end = m.end() + next_section.start() if next_section else len(text)

    section_text = text[section_start:section_end]

    # Remove active marker from existing keys
    section_text = re.sub(r'★\s*active', '', section_text)

    # Check if key already exists
    if new_key in section_text:
        # Just mark it as active
        section_text = section_text.replace(f'`{new_key}`', f'`{new_key}` ★ active')
    else:
        # Add new key row to the table — find the last table row
        table_end = section_text.rfind('|')
        if table_end > 0:
            new_row = f"\n| {label or 'New key'} | `{new_key}` | ★ active |"
            section_text = section_text[:table_end+1] + new_row + section_text[table_end+1:]

    text = text[:section_start] + section_text + text[section_end:]
    path.write_text(text)
    return True


def add_tokens_md_section(path: Path, provider_name: str, endpoint: str,
                          api_enum: str, model_ids: list[str], key: str,
                          section_type: str = "LLM"):
    """Add a new provider section to tokens.md."""
    backup_file(path)
    text = path.read_text()

    # Determine section number
    existing = read_tokens_md(path)
    max_num = 0
    for s in existing:
        m = re.match(r'(\d+)\.', s.heading)
        if m:
            max_num = max(max_num, int(m.group(1)))
    new_num = max_num + 1

    models_str = ", ".join(f"`{m}`" for m in model_ids[:10])
    if len(model_ids) > 10:
        models_str += f" (+{len(model_ids)-10} more)"

    section = f"""
## {new_num}. {provider_name.title()}

- **Endpoint**: `{endpoint}`
- **API type**: `{api_enum}`
- **Plugin**: none → register under `models.providers.{provider_name}`
- **Supported model IDs**: {models_str}

| Type | Value |
|---|---|
| API key ★ active | `{key}` |
"""
    text = text.rstrip() + "\n" + section
    path.write_text(text)


# ─── OpenClaw JSON Reader/Writer ─────────────────────────────────────────────

def read_openclaw(path: Path = OPENCLAW_JSON) -> dict:
    """Read openclaw.json."""
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def get_openclaw_providers(openclaw: dict) -> dict[str, dict]:
    """Extract models.providers from openclaw config."""
    return openclaw.get("models", {}).get("providers", {})


def write_openclaw_provider(path: Path, provider_id: str, provider_entry: dict):
    """Add or update a provider in openclaw.json models.providers."""
    backup_file(path)
    data = json.loads(path.read_text()) if path.exists() else {}
    if "models" not in data:
        data["models"] = {}
    if "providers" not in data["models"]:
        data["models"]["providers"] = {}
    data["models"]["providers"][provider_id] = provider_entry
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


# ─── Hermes Config YAML Reader/Writer ───────────────────────────────────────

def read_hermes_custom_providers(path: Path = HERMES_CONFIG) -> list[dict]:
    """Parse custom_providers from hermes config.yaml (line-based, no PyYAML)."""
    if not path.exists():
        return []
    lines = path.read_text().splitlines()
    providers = []
    in_cp = False
    current = {}
    for line in lines:
        stripped = line.strip()
        if stripped == "custom_providers:":
            in_cp = True
            continue
        if in_cp:
            if stripped.startswith("- name:"):
                if current:
                    providers.append(current)
                current = {"name": stripped.split(":", 1)[1].strip()}
            elif stripped.startswith("name:") and not current.get("name"):
                current["name"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("base_url:"):
                current["base_url"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("api_key:"):
                val = stripped.split(":", 1)[1].strip().strip("'\"")
                current["api_key"] = val
            elif stripped.startswith("api_mode:"):
                current["api_mode"] = stripped.split(":", 1)[1].strip()
            elif stripped and not stripped.startswith("-") and not stripped.startswith("#"):
                # End of custom_providers block (new top-level key)
                if current:
                    providers.append(current)
                    current = {}
                in_cp = False
    if current:
        providers.append(current)
    return providers


def write_hermes_custom_provider(path: Path, provider_name: str,
                                  base_url: str, api_key: str,
                                  api_mode: str = "chat_completions"):
    """Add or update a custom_providers entry in hermes config.yaml."""
    backup_file(path)
    lines = path.read_text().splitlines()

    # Find custom_providers: line
    cp_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "custom_providers:":
            cp_idx = i
            break

    if cp_idx is None:
        # Append at end
        lines.extend([
            "custom_providers:",
            f"- name: {provider_name}",
            f"  base_url: {base_url}",
            f"  api_key: '{api_key}'",
            f"  api_mode: {api_mode}",
        ])
    else:
        # Find the entry for this provider
        entry_start = None
        entry_end = None
        for i in range(cp_idx + 1, len(lines)):
            stripped = lines[i].strip()
            if stripped.startswith("- name:"):
                name_val = stripped.split(":", 1)[1].strip()
                if name_val == provider_name:
                    entry_start = i
                elif entry_start is not None:
                    entry_end = i
                    break
            elif stripped and not stripped.startswith(" ") and not stripped.startswith("-"):
                if entry_start is not None:
                    entry_end = i
                break

        new_block = [
            f"- name: {provider_name}",
            f"  base_url: {base_url}",
            f"  api_key: '{api_key}'",
            f"  api_mode: {api_mode}",
        ]

        if entry_start is not None:
            if entry_end is None:
                entry_end = len(lines)
            lines[entry_start:entry_end] = new_block
        else:
            # Append after the last entry
            insert_at = cp_idx + 1
            for i in range(cp_idx + 1, len(lines)):
                if lines[i].strip().startswith("- name:") or lines[i].strip().startswith("name:"):
                    # Find end of this entry
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip().startswith("- name:") or \
                           (lines[j].strip() and not lines[j].startswith(" ")):
                            insert_at = j
                            break
                    else:
                        insert_at = len(lines)
            # Actually, just append at the end of the block
            # Find the last line that's part of custom_providers
            last_cp_line = cp_idx
            for i in range(cp_idx + 1, len(lines)):
                s = lines[i].strip()
                if s.startswith("- name:") or s.startswith("name:") or \
                   s.startswith("base_url:") or s.startswith("api_key:") or \
                   s.startswith("api_mode:") or s == "" or s.startswith("'"):
                    last_cp_line = i
                elif s and not s.startswith(" ") and not s.startswith("-"):
                    break
                elif s.startswith("- ") and not s.startswith("- name:"):
                    break
            for i, new_line in enumerate(new_block):
                lines.insert(last_cp_line + 1 + i, new_line)

    path.write_text("\n".join(lines) + "\n")


# ─── Hermes .env Reader/Writer ───────────────────────────────────────────────

def read_hermes_env(path: Path = HERMES_ENV) -> dict[str, str]:
    """Parse hermes .env into key-value dict."""
    if not path.exists():
        return {}
    env = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip("'\"")
    return env


def write_hermes_env(path: Path, env_var: str, value: str):
    """Add or update an env var in hermes .env."""
    backup_file(path)
    lines = path.read_text().splitlines() if path.exists() else []
    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{env_var}="):
            lines[i] = f"{env_var}={value}"
            found = True
            break
    if not found:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(f"{env_var}={value}")
    path.write_text("\n".join(lines) + "\n")


# ─── CCR Config JSON Reader/Writer ──────────────────────────────────────────

def read_ccr_config(path: Path = CCR_CONFIG) -> dict:
    """Read claude-code-router config.json."""
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def get_ccr_providers(ccr: dict) -> list[dict]:
    """Extract Providers array from CCR config."""
    return ccr.get("Providers", [])


def write_ccr_provider(path: Path, provider_name: str, provider_entry: dict):
    """Add or update a provider in CCR config.json Providers array."""
    backup_file(path)
    data = json.loads(path.read_text()) if path.exists() else {}
    if "Providers" not in data:
        data["Providers"] = []
    # Find existing
    for i, p in enumerate(data["Providers"]):
        if p.get("name") == provider_name:
            data["Providers"][i] = provider_entry
            break
    else:
        data["Providers"].append(provider_entry)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


# ─── API Type Detection ─────────────────────────────────────────────────────

def detect_api_type_url(base_url: str) -> str:
    """Detect API type from URL pattern (no network)."""
    url = base_url.lower()
    if "anthropic" in url or "/apps/anthropic" in url:
        return "anthropic-messages"
    if "openrouter" in url:
        return "openai-completions"
    if "google" in url or "generativelanguage" in url:
        return "google-generative-ai"
    if "openai" in url:
        return "openai-completions"
    # Default: assume OpenAI-compatible
    return "openai-completions"


def probe_api_type(base_url: str, api_key: str, timeout: int = 10) -> str:
    """Probe the API to detect type. Returns 'openai-completions' or 'anthropic-messages'."""
    # Try OpenAI-style GET /models
    for suffix in ["/models", "/v1/models"]:
        url = base_url.rstrip("/")
        if not url.endswith("/models"):
            url += suffix
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode())
                if "data" in body:
                    return "openai-completions"
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError):
            pass

    # Try Anthropic-style
    url = base_url.rstrip("/") + "/v1/messages"
    req = urllib.request.Request(url, headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return "anthropic-messages"
    except urllib.error.HTTPError as e:
        if e.code == 400:  # Bad request = endpoint exists
            return "anthropic-messages"
    except (urllib.error.URLError, OSError):
        pass

    return detect_api_type_url(base_url)


# ─── Model Discovery ─────────────────────────────────────────────────────────

def discover_models(base_url: str, api_key: str, timeout: int = 15) -> list[str]:
    """Probe GET /models to discover available model IDs."""
    url = base_url.rstrip("/")
    if not url.endswith("/models"):
        url += "/models"

    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    })

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError) as e:
        print(f"Error probing {url}: {e}", file=__import__('sys').stderr)
        return []

    # OpenAI format: {"data": [{"id": "..."}]}
    if "data" in body and isinstance(body["data"], list):
        return [m["id"] for m in body["data"] if "id" in m]

    # Google format: {"models": [{"name": "..."}]}
    if "models" in body and isinstance(body["models"], list):
        names = []
        for m in body["models"]:
            name = m.get("name", "")
            # Google uses "models/" prefix
            names.append(name.removeprefix("models/"))
        return names

    return []


def filter_latest_models(model_ids: list[str]) -> list[str]:
    """Filter to keep only the latest version of each model family."""
    # Group by base name (strip date suffixes)
    date_pattern = re.compile(r'-\d{6,8}$')
    families: dict[str, list[str]] = {}
    no_date: list[str] = []

    for mid in model_ids:
        m = date_pattern.search(mid)
        if m:
            base = mid[:m.start()]
            families.setdefault(base, []).append(mid)
        else:
            no_date.append(mid)

    result = list(no_date)
    for base, variants in families.items():
        # Keep the one with the latest date suffix
        variants.sort(reverse=True)
        result.append(variants[0])

    return sorted(result)


# ─── Consistency Check ───────────────────────────────────────────────────────

def check_consistency() -> list[dict]:
    """Compare active keys across all 5 config files.
    Returns list of {provider, tokens_md_key, openclaw_key, hermes_key, hermes_env_key, ccr_key, status}.
    """
    sections = read_tokens_md()
    oc = read_openclaw()
    oc_providers = get_openclaw_providers(oc)
    hermes_providers = read_hermes_custom_providers()
    hermes_env = read_hermes_env()
    ccr = read_ccr_config()
    ccr_providers = {p["name"]: p for p in get_ccr_providers(ccr)}

    results = []
    for section in sections:
        if not section.keys:
            continue
        pname = section.provider_name
        tm_key = section.active_key

        # OpenClaw
        oc_key = None
        oc_entry = oc_providers.get(pname)
        if oc_entry:
            oc_key = oc_entry.get("apiKey", "")

        # Hermes config
        hm_key = None
        for hp in hermes_providers:
            if hp.get("name") == pname:
                hm_key = hp.get("api_key", "")
                break

        # Hermes env
        he_key = None
        evar = env_var_name(pname)
        he_key = hermes_env.get(evar)

        # CCR
        ccr_key = None
        ccr_entry = ccr_providers.get(pname)
        if ccr_entry:
            ccr_key = ccr_entry.get("api_key", "")

        # Determine status
        keys = {
            "openclaw": oc_key,
            "hermes_config": hm_key,
            "hermes_env": he_key,
            "ccr": ccr_key,
        }
        mismatches = []
        for file_name, k in keys.items():
            if k and tm_key and k != tm_key:
                mismatches.append(file_name)
            elif not k and tm_key:
                mismatches.append(f"{file_name}(missing)")

        status = "match" if not mismatches else "mismatch"
        if all(v is None for v in keys.values()):
            status = "not_propagated"

        results.append({
            "provider": pname,
            "tokens_md_key": tm_key,
            "openclaw_key": oc_key,
            "hermes_config_key": hm_key,
            "hermes_env_key": he_key,
            "ccr_key": ccr_key,
            "status": status,
            "mismatches": mismatches,
        })

    return results


# ─── Probe Token ─────────────────────────────────────────────────────────────

def probe_token(service: str, key: str, url: str = "", timeout: int = 10) -> dict:
    """Probe a single token. Returns {status, detail, latency_ms}."""
    reg = get_registry(service)
    if not reg:
        # Unknown provider — try a generic probe with the URL as-is
        if not url:
            return {"status": "skip", "detail": f"Unknown service: {service}", "latency_ms": 0}
        reg = {"api_type": "openai-completions", "probe_url_suffix": "/models"}

    # Some providers can't be probed with a single key
    if reg.get("skip_probe"):
        return {"status": "skip", "detail": "Multi-credential auth (not probeable)", "latency_ms": 0}

    # Build probe URL: use provided URL + suffix, or registry default + suffix
    suffix = reg.get("probe_url_suffix", "/models")

    # Special case: dashscope has both Anthropic and OpenAI endpoints; prefer OpenAI for probing
    if service.lower() == "dashscope" and "anthropic" in (url or "").lower():
        url = "https://coding.dashscope.aliyuncs.com/v1"

    if url:
        # If the provided URL already ends with the suffix, use as-is
        if url.rstrip("/").endswith(suffix.rstrip("/")):
            probe_url = url
        else:
            probe_url = url.rstrip("/") + suffix
    else:
        probe_url = (reg.get("default_base_url", "") + suffix)

    if not probe_url:
        return {"status": "skip", "detail": "No probe URL", "latency_ms": 0}

    # Build auth headers based on API type
    api_type = reg.get("api_type", "")
    if api_type == "anthropic-messages":
        headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "Accept": "application/json"}
    elif api_type == "google-generative-ai":
        # Gemini uses ?key= query param, not Bearer
        sep = "&" if "?" in probe_url else "?"
        probe_url = probe_url + sep + f"key={key}"
        headers = {"Accept": "application/json"}
    elif service.lower() == "brave":
        headers = {"X-Subscription-Token": key, "Accept": "application/json"}
    elif service.lower() == "deepgram":
        headers = {"Authorization": f"Token {key}", "Accept": "application/json"}
    else:
        headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}

    t0 = datetime.now()
    probe_method = reg.get("probe_method", "GET")
    try:
        if probe_method == "POST":
            # POST with minimal body for APIs that don't support GET
            probe_body = json.dumps({"model": "test", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1}).encode()
            headers["Content-Type"] = "application/json"
            req = urllib.request.Request(probe_url, data=probe_body, headers=headers, method="POST")
        else:
            req = urllib.request.Request(probe_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            latency = (datetime.now() - t0).total_seconds() * 1000
            return {"status": "ok", "detail": f"HTTP {resp.status}", "latency_ms": latency}
    except urllib.error.HTTPError as e:
        latency = (datetime.now() - t0).total_seconds() * 1000
        if e.code in (401, 403):
            return {"status": "fail", "detail": f"HTTP {e.code}", "latency_ms": latency}
        elif e.code == 400:
            # Some APIs return 400 for valid auth with wrong request shape
            # Check if it's an auth error disguised as 400
            try:
                err_body = e.read().decode()[:200]
                if "auth" in err_body.lower() or "key" in err_body.lower() or "token" in err_body.lower():
                    return {"status": "fail", "detail": f"HTTP {e.code} (auth)", "latency_ms": latency}
            except Exception:
                pass
            return {"status": "ok", "detail": f"HTTP {e.code} (auth OK)", "latency_ms": latency}
        elif e.code == 404:
            # Some APIs don't have /models — try base URL as fallback
            try:
                base = url or reg.get("default_base_url", "")
                req2 = urllib.request.Request(base, headers=headers)
                with urllib.request.urlopen(req2, timeout=timeout) as resp2:
                    latency2 = (datetime.now() - t0).total_seconds() * 1000
                    return {"status": "ok", "detail": f"HTTP {resp2.status} (base)", "latency_ms": latency2}
            except urllib.error.HTTPError as e2:
                if e2.code in (400, 401, 403):
                    # 400/401/403 means server is up, just auth/shape issue
                    latency2 = (datetime.now() - t0).total_seconds() * 1000
                    return {"status": "ok", "detail": f"HTTP {e2.code} (base)", "latency_ms": latency2}
            except Exception:
                pass
        elif e.code >= 500:
            return {"status": "transient", "detail": f"HTTP {e.code}", "latency_ms": latency}
        return {"status": "fail", "detail": f"HTTP {e.code}", "latency_ms": latency}
    except urllib.error.URLError as e:
        latency = (datetime.now() - t0).total_seconds() * 1000
        return {"status": "unreachable", "detail": str(e.reason)[:60], "latency_ms": latency}
    except OSError as e:
        latency = (datetime.now() - t0).total_seconds() * 1000
        return {"status": "unreachable", "detail": str(e)[:60], "latency_ms": latency}


# ─── Status JSON (cached results for dashboard) ─────────────────────────────

def read_status_cache() -> dict:
    """Read cached status from token-status.json."""
    if STATUS_JSON.exists():
        return json.loads(STATUS_JSON.read_text())
    return {}


def write_status_cache(data: dict):
    """Write status cache to token-status.json."""
    STATUS_JSON.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = datetime.now().isoformat()
    STATUS_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
