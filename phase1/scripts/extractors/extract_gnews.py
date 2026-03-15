"""
Extract sample articles from GNews and generate:
1) Raw JSON files under data/raw/gnews/
2) Normalized CSV at data/normalized/gnews_sample_v0.csv
3) Profiling note at data/profiling/gnews_profile.md

Usage:
    GNEWS_API_KEY="<key>" python3 scripts/extractors/extract_gnews.py \
      --query "rail safety" --query "infrastructure risk"
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import ssl
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


GNEWS_SEARCH_URL = "https://gnews.io/api/v4/search"
DEFAULT_QUERIES = ["rail safety", "infrastructure risk"]
DEFAULT_MAX_RESULTS = 10
REQUEST_TIMEOUT_SECONDS = 30


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "query"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _extract_articles(
    *,
    api_key: str,
    query: str,
    max_results: int,
    insecure_skip_tls_verify: bool = False,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "q": query,
        "lang": "en",
        "max": max_results,
        "sortby": "publishedAt",
        "apikey": api_key,
    }
    url = f"{GNEWS_SEARCH_URL}?{urlencode(params)}"
    ssl_context = None
    if insecure_skip_tls_verify:
        ssl_context = ssl._create_unverified_context()

    try:
        with urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS, context=ssl_context) as response:
            status_code = getattr(response, "status", 200)
            if status_code >= 400:
                raise RuntimeError(f"GNews request failed with HTTP {status_code}")
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 401:
            raise RuntimeError(
                "GNews returned 401 Unauthorized. Check GNEWS_API_KEY value."
            ) from exc
        if exc.code == 403:
            raise RuntimeError(
                "GNews returned 403 Forbidden. Plan/quota/permissions may block this request."
            ) from exc
        if exc.code == 429:
            raise RuntimeError(
                "GNews returned 429 Too Many Requests. You hit rate limits/quota."
            ) from exc
        raise RuntimeError(f"GNews HTTP error: {exc.code}") from exc
    except URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, ssl.SSLCertVerificationError):
            raise RuntimeError(
                "TLS certificate verification failed. Retry with "
                "--insecure-skip-tls-verify as a temporary workaround."
            ) from exc
        raise RuntimeError(f"Failed to call GNews over HTTPS: {reason or exc}") from exc

    if "articles" not in payload:
        raise RuntimeError(f"Unexpected GNews response shape: {payload}")
    return payload


def _normalize_article(article: dict[str, Any], query: str) -> dict[str, str]:
    source = article.get("source") or {}
    return {
        "source_name": str(source.get("name") or ""),
        "title": str(article.get("title") or ""),
        "description": str(article.get("description") or ""),
        "content": str(article.get("content") or ""),
        "url": str(article.get("url") or ""),
        "image": str(article.get("image") or ""),
        "published_at": str(article.get("publishedAt") or ""),
        "query": query,
    }


def _write_raw_json(payload: dict[str, Any], output_path: Path) -> None:
    _ensure_parent(output_path)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _write_normalized_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    _ensure_parent(output_path)
    fieldnames = [
        "source_name",
        "title",
        "description",
        "content",
        "url",
        "image",
        "published_at",
        "query",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_profile_markdown(
    *,
    output_path: Path,
    api_call_count: int,
    query_stats: list[tuple[str, int]],
    total_rows: int,
    status: str,
) -> None:
    _ensure_parent(output_path)
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    lines = [
        "# GNews Profiling Note",
        "",
        f"- Run timestamp (UTC): {now_iso}",
        f"- API calls executed: {api_call_count}",
        f"- Total normalized rows: {total_rows}",
        f"- Run status: {status}",
        "",
        "## Query-level counts",
        "",
    ]
    for query, count in query_stats:
        lines.append(f"- `{query}`: {count} article(s)")
    lines += [
        "",
        "## Comparison comments vs NewsAPI",
        "",
        "- GNews may return fewer metadata fields than NewsAPI (for example, no author in many cases).",
        "- GNews uses `max` for result size and `apikey` parameter name, while NewsAPI uses `pageSize` and `apiKey`.",
        "- Rate limit/plan behavior differs by provider and should be monitored separately.",
        "",
        "## Rate limit observations",
        "",
        "- Handle `429` with retry/backoff for larger extraction runs.",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract sample data from GNews.")
    parser.add_argument(
        "--api-key",
        default=os.getenv("GNEWS_API_KEY", ""),
        help="GNews API key. Defaults to GNEWS_API_KEY env var.",
    )
    parser.add_argument(
        "--query",
        action="append",
        dest="queries",
        help="Query term. Can be passed multiple times. Defaults to two built-in queries.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=DEFAULT_MAX_RESULTS,
        help="Maximum results per query (1-100).",
    )
    parser.add_argument(
        "--min-articles",
        type=int,
        default=5,
        help="Fail if fewer than this many normalized rows are collected.",
    )
    parser.add_argument(
        "--insecure-skip-tls-verify",
        action="store_true",
        help="Disable TLS certificate verification temporarily (not recommended for production).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.api_key:
        raise SystemExit("Missing API key. Set GNEWS_API_KEY or pass --api-key.")

    queries = args.queries or DEFAULT_QUERIES
    max_results = max(1, min(args.max_results, 100))

    root = Path(__file__).resolve().parents[2]
    raw_dir = root / "data" / "raw" / "gnews"
    normalized_csv_path = root / "data" / "normalized" / "gnews_sample_v0.csv"
    profile_md_path = root / "data" / "profiling" / "gnews_profile.md"

    rows: list[dict[str, str]] = []
    query_stats: list[tuple[str, int]] = []
    api_call_count = 0

    for query in queries:
        payload = _extract_articles(
            api_key=args.api_key,
            query=query,
            max_results=max_results,
            insecure_skip_tls_verify=args.insecure_skip_tls_verify,
        )
        api_call_count += 1

        timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        raw_path = raw_dir / f"gnews_{_slugify(query)}_{timestamp}.json"
        _write_raw_json(payload, raw_path)

        articles = payload.get("articles", [])
        query_stats.append((query, len(articles)))
        for article in articles:
            rows.append(_normalize_article(article, query))

    _write_normalized_csv(rows, normalized_csv_path)

    status = "success" if len(rows) >= args.min_articles else "insufficient_rows"
    _write_profile_markdown(
        output_path=profile_md_path,
        api_call_count=api_call_count,
        query_stats=query_stats,
        total_rows=len(rows),
        status=status,
    )

    if len(rows) < args.min_articles:
        raise SystemExit(
            f"Only {len(rows)} rows extracted, expected at least {args.min_articles}."
        )

    print(f"Saved {len(rows)} normalized rows to {normalized_csv_path}")
    print(f"Raw JSON files are available under {raw_dir}")
    print(f"Profiling note saved to {profile_md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
