"""
Fetch secondary API sample responses (Newsdata, Mediastack) and save raw JSON.

Exits with an error if a required key is missing. HTTP errors are raised
(consistent with the other extractors) so failures are visible immediately.

Usage:
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
MEDIASTACK_URL = "https://api.mediastack.com/v1/news"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch secondary API sample responses.")
    parser.add_argument("--query", default="rail safety", help="Query keyword.")
    parser.add_argument("--insecure-skip-tls-verify", action="store_true", help="Disable TLS verification.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    newsdata_key = os.getenv("NEWSDATA_API_KEY", "")
    mediastack_key = os.getenv("MEDIASTACK_ACCESS_KEY", "")

    if not newsdata_key:
        raise SystemExit("Missing NEWSDATA_API_KEY.")
    if not mediastack_key:
        raise SystemExit("Missing MEDIASTACK_ACCESS_KEY.")

    root = Path(__file__).resolve().parents[2]
    out_dir = root / "data" / "raw" / "secondary"

    newsdata_url = f"{NEWSDATA_URL}?{urlencode({'apikey': newsdata_key, 'q': args.query})}"
    mediastack_url = f"{MEDIASTACK_URL}?{urlencode({'access_key': mediastack_key, 'keywords': args.query})}"

    newsdata_payload = fetch_json(newsdata_url, insecure_skip_tls_verify=args.insecure_skip_tls_verify)
    write_json(newsdata_payload, out_dir / "newsdata_sample_response.json")

    mediastack_payload = fetch_json(mediastack_url, insecure_skip_tls_verify=args.insecure_skip_tls_verify)
    write_json(mediastack_payload, out_dir / "mediastack_sample_response.json")

    print(f"Saved secondary samples → {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
