"""
Fetch secondary API sample responses and save raw JSON files.

Usage:
    NEWSDATA_API_KEY="<key_or_placeholder>" MEDIASTACK_ACCESS_KEY="<key_or_placeholder>" \
    python3 scripts/extractors/extract_secondary_samples.py --query "rail"
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


NEWSDATA_URL = "https://newsdata.io/api/1/news"
MEDIASTACK_URL = "https://api.mediastack.com/v1/news"


def fetch_json(url: str, insecure_skip_tls_verify: bool) -> dict:
    context = None
    if insecure_skip_tls_verify:
        context = ssl._create_unverified_context()
    try:
        with urlopen(url, timeout=30, context=context) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw_error_body": raw}
        return {
            "status": "error",
            "http_status": exc.code,
            "url": url,
            "provider_response": payload,
        }
    except URLError as exc:
        return {
            "status": "error",
            "url": url,
            "message": f"Network error: {exc.reason}",
        }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch secondary API sample responses.")
    parser.add_argument("--query", default="rail safety", help="Query keyword")
    parser.add_argument(
        "--insecure-skip-tls-verify",
        action="store_true",
        help="Disable TLS verification temporarily if local cert chain is broken.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    newsdata_key = os.getenv("NEWSDATA_API_KEY", "INVALID_KEY")
    mediastack_key = os.getenv("MEDIASTACK_ACCESS_KEY", "INVALID_KEY")

    root = Path(__file__).resolve().parents[2]
    out_dir = root / "data" / "raw" / "secondary"

    newsdata_url = f"{NEWSDATA_URL}?{urlencode({'apikey': newsdata_key, 'q': args.query})}"
    mediastack_url = f"{MEDIASTACK_URL}?{urlencode({'access_key': mediastack_key, 'keywords': args.query})}"

    newsdata_payload = fetch_json(newsdata_url, args.insecure_skip_tls_verify)
    mediastack_payload = fetch_json(mediastack_url, args.insecure_skip_tls_verify)

    write_json(out_dir / "newsdata_sample_response.json", newsdata_payload)
    write_json(out_dir / "mediastack_sample_response.json", mediastack_payload)

    print(f"Saved: {out_dir / 'newsdata_sample_response.json'}")
    print(f"Saved: {out_dir / 'mediastack_sample_response.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
