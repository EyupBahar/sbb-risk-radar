"""
Fetch secondary API sample responses (Newsdata, Mediastack) and save raw JSON.

Each source runs independently — a missing key or HTTP error skips that source
and saves an error JSON, so the other source still completes.

Usage:
    NEWSDATA_API_KEY="<key>" python3 scripts/extractors/extract_secondary_samples.py --query "rail safety"
    MEDIASTACK_ACCESS_KEY="<key>" python3 scripts/extractors/extract_secondary_samples.py --query "rail safety"
    NEWSDATA_API_KEY="<key>" MEDIASTACK_ACCESS_KEY="<key>" \
        python3 scripts/extractors/extract_secondary_samples.py --query "rail safety"
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.utils.http import fetch_json
from scripts.utils.io import write_json

NEWSDATA_URL = "https://newsdata.io/api/1/news"
MEDIASTACK_URL = "http://api.mediastack.com/v1/news"  # free tier requires HTTP


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch secondary API sample responses.")
    parser.add_argument("--query", default="rail safety", help="Query keyword.")
    parser.add_argument("--insecure-skip-tls-verify", action="store_true", help="Disable TLS verification.")
    return parser.parse_args()


def _fetch_source(name: str, url: str, out_path: Path, insecure: bool) -> bool:
    """Fetch one source, save result or error JSON. Returns True on success."""
    try:
        payload = fetch_json(url, insecure_skip_tls_verify=insecure)
        write_json(payload, out_path)
        print(f"[{name}] saved → {out_path.name}")
        return True
    except RuntimeError as exc:
        error_payload = {"status": "error", "source": name, "message": str(exc), "url": url}
        write_json(error_payload, out_path)
        print(f"[{name}] skipped — {exc} (saved error record)")
        return False


def main() -> int:
    args = _parse_args()

    newsdata_key = os.getenv("NEWSDATA_API_KEY", "")
    mediastack_key = os.getenv("MEDIASTACK_ACCESS_KEY", "")

    root = Path(__file__).resolve().parents[2]
    out_dir = root / "data" / "raw" / "secondary"

    results: list[bool] = []

    if newsdata_key:
        url = f"{NEWSDATA_URL}?{urlencode({'apikey': newsdata_key, 'q': args.query})}"
        results.append(_fetch_source("newsdata", url, out_dir / "newsdata_sample_response.json", args.insecure_skip_tls_verify))
    else:
        print("[newsdata] skipped — NEWSDATA_API_KEY not set")

    if mediastack_key:
        url = f"{MEDIASTACK_URL}?{urlencode({'access_key': mediastack_key, 'keywords': args.query})}"
        results.append(_fetch_source("mediastack", url, out_dir / "mediastack_sample_response.json", args.insecure_skip_tls_verify))
    else:
        print("[mediastack] skipped — MEDIASTACK_ACCESS_KEY not set")

    if not newsdata_key and not mediastack_key:
        raise SystemExit("No API keys provided. Set NEWSDATA_API_KEY and/or MEDIASTACK_ACCESS_KEY.")

    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
