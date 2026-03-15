"""
Merge NewsAPI and GNews normalized CSVs into master Excel format.

Output conforms to SBB_Risk_Radar_Master_Source_Template_Normalization.xlsx schema.

Usage:
    python3 scripts/normalize/merge_master_source.py
"""

from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.utils.io import read_csv, write_csv

ROOT = Path(__file__).resolve().parents[2]
NEWSAPI_CSV = ROOT / "data" / "normalized" / "newsapi_sample_v0.csv"
GNEWS_CSV = ROOT / "data" / "normalized" / "gnews_sample_v0.csv"
OUTPUT_CSV = ROOT / "data" / "normalized" / "master" / "master_source_v0.csv"

# Column order matches SBB_Risk_Radar_Master_Source_Template_Normalization.xlsx.
MASTER_COLUMNS = [
    "record_id", "batch_id", "source_name", "source_group", "source_type",
    "record_granularity", "source_url", "document_url", "source_document_id",
    "title_raw", "summary_raw", "text_raw", "page_reference_raw",
    "published_at", "retrieved_at", "language", "country_hint", "author_or_org",
    "section_category", "file_format", "extraction_method", "access_status",
    "parse_status", "raw_storage_path", "normalized_storage_path",
    "text_length", "content_hash", "notes", "working_title",
    # Parallel German fields required by SBB template.
    "kurzbeschrieb", "quelle", "seitenangabe", "stichwoerter", "datum",
    "betroffene_konzernziele", "auswirkung", "zeithorizont",
    "geografische_relevanz", "primaer_betroffene_division",
    "sekundaer_betroffene_division", "trend", "kommentar",
    "dedup_cluster_id", "ai_confidence", "relevance_score_sbb", "pipeline_version",
]

BATCH_ID = "phase1_wk1"
PIPELINE_VERSION = "v0"

_PROVIDER_SOURCE_URL = {
    "newsapi": "https://newsapi.org/",
    "gnews": "https://gnews.io/",
}

_PROVIDER_RAW_PATH = {
    "newsapi": "data/raw/newsapi/",
    "gnews": "data/raw/gnews/",
}

_PROVIDER_NORMALIZED_PATH = {
    "newsapi": "data/normalized/newsapi_sample_v0.csv",
    "gnews": "data/normalized/gnews_sample_v0.csv",
}


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] if text else ""


def _to_master_row(
    *,
    record_id: str,
    provider: str,
    publisher_name: str,
    document_url: str,
    title_raw: str,
    summary_raw: str,
    text_raw: str,
    query: str,
    published_at: str,
    author_or_org: str,
    retrieved_at: str,
) -> dict[str, str]:
    h = _content_hash(text_raw)
    return {
        "record_id": record_id,
        "batch_id": BATCH_ID,
        "source_name": publisher_name or provider,
        "source_group": "api",
        "source_type": "article",
        "record_granularity": "item",
        "source_url": _PROVIDER_SOURCE_URL[provider],
        "document_url": document_url,
        "source_document_id": f"{provider}_{h}",
        "title_raw": title_raw,
        "summary_raw": summary_raw,
        "text_raw": text_raw,
        # query is stored as the page-level reference across all three columns.
        "page_reference_raw": query,
        "published_at": published_at,
        "retrieved_at": retrieved_at,
        "language": "en",
        "country_hint": "",
        "author_or_org": author_or_org,
        # section_category = query (best available category proxy from API output).
        "section_category": query,
        "file_format": "json",
        "extraction_method": "api",
        "access_status": "ok",
        "parse_status": "success",
        "raw_storage_path": _PROVIDER_RAW_PATH[provider],
        "normalized_storage_path": _PROVIDER_NORMALIZED_PATH[provider],
        "text_length": str(len(text_raw)),
        "content_hash": h,
        "notes": "",
        # German parallel fields required by SBB template.
        "working_title": title_raw,
        "kurzbeschrieb": summary_raw,
        "quelle": publisher_name or provider,
        "seitenangabe": "",
        # stichwoerter = query (closest equivalent to keywords from extraction).
        "stichwoerter": query,
        "datum": published_at,
        "betroffene_konzernziele": "",
        "auswirkung": "",
        "zeithorizont": "",
        "geografische_relevanz": "",
        "primaer_betroffene_division": "",
        "sekundaer_betroffene_division": "",
        "trend": "",
        "kommentar": "",
        "dedup_cluster_id": "",
        "ai_confidence": "",
        "relevance_score_sbb": "",
        "pipeline_version": PIPELINE_VERSION,
    }


def main() -> int:
    now = datetime.now(timezone.utc)
    retrieved_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    today = now.strftime("%Y%m%d")

    newsapi_rows = read_csv(NEWSAPI_CSV)
    gnews_rows = read_csv(GNEWS_CSV)

    master_rows: list[dict[str, str]] = []

    for i, r in enumerate(newsapi_rows, start=1):
        master_rows.append(_to_master_row(
            record_id=f"src_newsapi_{today}_{i:03d}",
            provider="newsapi",
            publisher_name=r.get("source_name", ""),
            document_url=r.get("url", ""),
            title_raw=r.get("title", ""),
            summary_raw=r.get("description", ""),
            text_raw=r.get("content", ""),
            query=r.get("query", ""),
            published_at=r.get("published_at", ""),
            author_or_org=r.get("author", ""),
            retrieved_at=retrieved_at,
        ))

    for i, r in enumerate(gnews_rows, start=1):
        # GNews normalized CSV has no author field; author_or_org is left empty.
        master_rows.append(_to_master_row(
            record_id=f"src_gnews_{today}_{i:03d}",
            provider="gnews",
            publisher_name=r.get("source_name", ""),
            document_url=r.get("url", ""),
            title_raw=r.get("title", ""),
            summary_raw=r.get("description", ""),
            text_raw=r.get("content", ""),
            query=r.get("query", ""),
            published_at=r.get("published_at", ""),
            author_or_org="",
            retrieved_at=retrieved_at,
        ))

    write_csv(master_rows, MASTER_COLUMNS, OUTPUT_CSV)
    print(f"Wrote {len(master_rows)} rows → {OUTPUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
