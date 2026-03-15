"""
Merge NewsAPI and GNews normalized CSVs into master Excel format.

Output conforms to SBB_Risk_Radar_Master_Source_Template_Normalization.xlsx schema.

Usage:
    python3 scripts/normalize/merge_master_source.py
"""

from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NEWSAPI_CSV = ROOT / "data" / "normalized" / "newsapi_sample_v0.csv"
GNEWS_CSV = ROOT / "data" / "normalized" / "gnews_sample_v0.csv"
OUTPUT_CSV = ROOT / "data" / "normalized" / "master" / "master_source_v0.csv"

MASTER_COLUMNS = [
    "record_id",
    "batch_id",
    "source_name",
    "source_group",
    "source_type",
    "record_granularity",
    "source_url",
    "document_url",
    "source_document_id",
    "title_raw",
    "summary_raw",
    "text_raw",
    "page_reference_raw",
    "published_at",
    "retrieved_at",
    "language",
    "country_hint",
    "author_or_org",
    "section_category",
    "file_format",
    "extraction_method",
    "access_status",
    "parse_status",
    "raw_storage_path",
    "normalized_storage_path",
    "text_length",
    "content_hash",
    "notes",
    "working_title",
    "kurzbeschrieb",
    "quelle",
    "seitenangabe",
    "stichwoerter",
    "datum",
    "betroffene_konzernziele",
    "auswirkung",
    "zeithorizont",
    "geografische_relevanz",
    "primaer_betroffene_division",
    "sekundaer_betroffene_division",
    "trend",
    "kommentar",
    "dedup_cluster_id",
    "ai_confidence",
    "relevance_score_sbb",
    "pipeline_version",
]

BATCH_ID = "phase1_wk1"
PIPELINE_VERSION = "v0"
RETRIEVED_AT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash_content(text: str) -> str:
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
    page_ref: str,
    published_at: str,
    author_or_org: str,
    raw_storage_path: str,
    normalized_storage_path: str,
) -> dict[str, str]:
    text_len = str(len(text_raw)) if text_raw else "0"
    content_hash = _hash_content(text_raw)
    source_url = "https://newsapi.org/" if provider == "newsapi" else "https://gnews.io/"
    return {
        "record_id": record_id,
        "batch_id": BATCH_ID,
        "source_name": publisher_name or provider,
        "source_group": "api",
        "source_type": "article",
        "record_granularity": "item",
        "source_url": source_url,
        "document_url": document_url or "",
        "source_document_id": f"{provider}_{content_hash}",
        "title_raw": title_raw or "",
        "summary_raw": summary_raw or "",
        "text_raw": text_raw or "",
        "page_reference_raw": page_ref or "",
        "published_at": published_at or "",
        "retrieved_at": RETRIEVED_AT,
        "language": "en",
        "country_hint": "",
        "author_or_org": author_or_org or "",
        "section_category": page_ref or "",
        "file_format": "json",
        "extraction_method": "api",
        "access_status": "ok",
        "parse_status": "success",
        "raw_storage_path": raw_storage_path or "",
        "normalized_storage_path": normalized_storage_path or "",
        "text_length": text_len,
        "content_hash": content_hash,
        "notes": "",
        "working_title": title_raw or "",
        "kurzbeschrieb": summary_raw or "",
        "quelle": publisher_name or provider,
        "seitenangabe": "",
        "stichwoerter": page_ref or "",
        "datum": published_at or "",
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


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    rows: list[dict[str, str]] = []
    newsapi_data = _read_csv(NEWSAPI_CSV)
    gnews_data = _read_csv(GNEWS_CSV)

    for i, r in enumerate(newsapi_data, start=1):
        record_id = f"src_newsapi_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{i:03d}"
        master = _to_master_row(
            record_id=record_id,
            provider="newsapi",
            publisher_name=r.get("source_name", ""),
            document_url=r.get("url", ""),
            title_raw=r.get("title", ""),
            summary_raw=r.get("description", ""),
            text_raw=r.get("content", ""),
            page_ref=r.get("query", ""),
            published_at=r.get("published_at", ""),
            author_or_org=r.get("author", ""),
            raw_storage_path="data/raw/newsapi/",
            normalized_storage_path="data/normalized/newsapi_sample_v0.csv",
        )
        rows.append(master)

    for i, r in enumerate(gnews_data, start=1):
        record_id = f"src_gnews_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{i:03d}"
        master = _to_master_row(
            record_id=record_id,
            provider="gnews",
            publisher_name=r.get("source_name", ""),
            document_url=r.get("url", ""),
            title_raw=r.get("title", ""),
            summary_raw=r.get("description", ""),
            text_raw=r.get("content", ""),
            page_ref=r.get("query", ""),
            published_at=r.get("published_at", ""),
            author_or_org="",
            raw_storage_path="data/raw/gnews/",
            normalized_storage_path="data/normalized/gnews_sample_v0.csv",
        )
        rows.append(master)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MASTER_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
