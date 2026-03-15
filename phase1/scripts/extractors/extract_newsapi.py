"""
Extract sample articles from NewsAPI and generate:
1) Raw JSON files under data/raw/newsapi/
2) Normalized CSV at data/normalized/newsapi_sample_v0.csv
3) Profiling note at data/profiling/newsapi_profile.md

Usage:
    NEWSAPI_KEY="<key>" python3 scripts/extractors/extract_newsapi.py \
      --query "rail safety" --query "infrastructure risk"
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.utils.http import fetch_json
from scripts.utils.io import slugify, write_csv, write_json

NEWSAPI_URL = "https://newsapi.org/v2/everything"
DEFAULT_QUERIES = ["rail safety", "infrastructure risk"]
DEFAULT_PAGE_SIZE = 10

NORMALIZED_FIELDS = [
    "source_name", "author", "title", "description",
    "url", "published_at", "query", "content",
]


def _extract(
    *,
    api_key: str,
    query: str,
    page_size: int,
    insecure_skip_tls_verify: bool,
) -> dict[str, Any]:
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "page": 1,
        "apiKey": api_key,
    }
    payload = fetch_json(
        f"{NEWSAPI_URL}?{urlencode(params)}",
        insecure_skip_tls_verify=insecure_skip_tls_verify,
    )
    if payload.get("status") != "ok":
        raise RuntimeError(f"NewsAPI returned non-ok response: {payload}")
    return payload


def _normalize(article: dict[str, Any], query: str) -> dict[str, str]:
    source = article.get("source") or {}
    return {
        "source_name": str(source.get("name") or ""),
        "author": str(article.get("author") or ""),
        "title": str(article.get("title") or ""),
        "description": str(article.get("description") or ""),
        "url": str(article.get("url") or ""),
        "published_at": str(article.get("publishedAt") or ""),
        "query": query,
        "content": str(article.get("content") or ""),
    }


def _write_profile(
    *,
    output_path: Path,
    api_call_count: int,
    query_stats: list[tuple[str, int]],
    total_rows: int,
    status: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    lines = [
        "# NewsAPI Profiling Note",
        "",
        f"- Run timestamp (UTC): {now_iso}",
        f"- API calls executed: {api_call_count}",
        f"- Total normalized rows: {total_rows}",
        f"- Run status: {status}",
        "",
        "## Query-level counts",
        "",
        *[f"- `{q}`: {n} article(s)" for q, n in query_stats],
        "",
        "## Rate limit observations",
        "",
        "- Free/developer plans may return HTTP 429 when rate limit is exceeded.",
        "- Implement retry/backoff for larger extraction runs.",
        "",
        "## Data quality notes",
        "",
        "- Duplicate headlines may appear across closely related queries.",
        "- `author` and `content` can be null/empty depending on publisher.",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract sample data from NewsAPI.")
    parser.add_argument("--api-key", default=os.getenv("NEWSAPI_KEY", ""), help="NewsAPI key.")
    parser.add_argument("--query", action="append", dest="queries", help="Query term (repeatable).")
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE, help="Results per query (1-100).")
    parser.add_argument("--min-articles", type=int, default=5, help="Minimum expected rows.")
    parser.add_argument("--insecure-skip-tls-verify", action="store_true", help="Disable TLS verification.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if not args.api_key:
        raise SystemExit("Missing API key. Set NEWSAPI_KEY or pass --api-key.")

    queries = args.queries or DEFAULT_QUERIES
    page_size = max(1, min(args.page_size, 100))

    root = Path(__file__).resolve().parents[2]
    raw_dir = root / "data" / "raw" / "newsapi"
    csv_path = root / "data" / "normalized" / "newsapi_sample_v0.csv"
    profile_path = root / "data" / "profiling" / "newsapi_profile.md"

    rows: list[dict[str, str]] = []
    query_stats: list[tuple[str, int]] = []

    # Capture run timestamp once before the loop.
    run_ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    for query in queries:
        payload = _extract(
            api_key=args.api_key,
            query=query,
            page_size=page_size,
            insecure_skip_tls_verify=args.insecure_skip_tls_verify,
        )
        raw_path = raw_dir / f"newsapi_{slugify(query)}_{run_ts}.json"
        write_json(payload, raw_path)

        articles = payload.get("articles", [])
        query_stats.append((query, len(articles)))
        rows.extend(_normalize(a, query) for a in articles)

    write_csv(rows, NORMALIZED_FIELDS, csv_path)
    status = "success" if len(rows) >= args.min_articles else "insufficient_rows"
    _write_profile(
        output_path=profile_path,
        api_call_count=len(queries),
        query_stats=query_stats,
        total_rows=len(rows),
        status=status,
    )

    if len(rows) < args.min_articles:
        raise SystemExit(f"Only {len(rows)} rows extracted, expected at least {args.min_articles}.")

    print(f"Saved {len(rows)} rows → {csv_path}")
    print(f"Raw JSON → {raw_dir}")
    print(f"Profiling → {profile_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
