#!/usr/bin/env python3.11
"""Web search using SearXNG (self-hosted) or DuckDuckGo fallback."""

import sys
import json
import argparse
import os
import urllib.request
import urllib.parse

SEARXNG_URL = "http://localhost:8888"

# Set SOCKS5 proxy (Clash default) for DuckDuckGo fallback
PROXY = "socks5://127.0.0.1:7897"
os.environ.setdefault("all_proxy", PROXY)
os.environ.setdefault("http_proxy", PROXY)
os.environ.setdefault("https_proxy", PROXY)


def search_searxng(query: str, max_results: int = 10, lang: str = "auto",
                   engines: str = "") -> list[dict]:
    """Search using local SearXNG instance."""
    params = {
        "q": query,
        "format": "json",
        "language": lang,
        "pageno": 1,
    }
    if engines:
        params["engines"] = engines

    url = f"{SEARXNG_URL}/search?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})

    # Bypass proxy for local SearXNG
    proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_handler)
    with opener.open(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    results = []
    for r in data.get("results", [])[:max_results]:
        results.append({
            "title": r.get("title", ""),
            "href": r.get("url", ""),
            "body": r.get("content", ""),
            "engine": r.get("engine", ""),
        })
    return results


def search_ddg(query: str, max_results: int = 10, region: str = "wt-wt") -> list[dict]:
    """Search DuckDuckGo as fallback."""
    from ddgs import DDGS
    results = DDGS().text(query, max_results=max_results, region=region)
    return results


def search(query: str, max_results: int = 10, backend: str = "searxng",
           lang: str = "auto", region: str = "wt-wt", engines: str = "") -> list[dict]:
    """Search with specified backend."""
    if backend == "searxng":
        try:
            return search_searxng(query, max_results, lang, engines)
        except Exception as e:
            print(f"SearXNG failed ({e}), falling back to DDG", file=sys.stderr)
            return search_ddg(query, max_results, region)
    elif backend == "ddg":
        return search_ddg(query, max_results, region)
    else:
        # auto: try SearXNG first, fallback to DDG
        try:
            return search_searxng(query, max_results, lang, engines)
        except Exception:
            return search_ddg(query, max_results, region)


def main():
    parser = argparse.ArgumentParser(description="Web search")
    parser.add_argument("query", help="Search query")
    parser.add_argument("-n", "--max-results", type=int, default=10, help="Max results")
    parser.add_argument("-b", "--backend", default="searxng",
                       choices=["searxng", "ddg", "auto"],
                       help="Search backend")
    parser.add_argument("-l", "--lang", default="auto", help="Language")
    parser.add_argument("-r", "--region", default="wt-wt", help="Region (for DDG)")
    parser.add_argument("-e", "--engines", default="",
                       help="SearXNG engines (comma-separated, e.g. 'google,bing')")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    results = search(args.query, args.max_results, args.backend, args.lang,
                     args.region, args.engines)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            href = r.get("href", "")
            body = r.get("body", "")
            engine = r.get("engine", "")
            print(f"{i}. {title}")
            print(f"   {href}")
            if engine:
                print(f"   [{engine}]")
            if body:
                print(f"   {body}")
            print()


if __name__ == "__main__":
    main()
