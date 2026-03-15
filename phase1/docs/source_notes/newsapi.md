# Source Note - NewsAPI

## Source identification

- Source name: NewsAPI
- Base endpoint used: `https://newsapi.org/v2/everything`
- Access type: API key based authentication
- Script: `scripts/extractors/extract_newsapi.py`

## Access and authentication

- Auth method: `apiKey` query parameter (`NEWSAPI_KEY` environment variable).
- Expected failure modes:
  - `401` for invalid/missing API key
  - `429` when rate limit is exceeded

## Test queries executed

The extractor is configured to run at least 1-2 queries; defaults are:

- `rail safety`
- `infrastructure risk`

Queries can be customized with repeated `--query` arguments.

## Output artifacts

- Raw JSON files: `data/raw/newsapi/newsapi_<query>_<timestamp>.json`
- Normalized CSV: `data/normalized/newsapi_sample_v0.csv`
- Profiling note: `data/profiling/newsapi_profile.md`

## Normalization schema (v0)

Columns written to normalized CSV:

1. `source_name`
2. `author`
3. `title`
4. `description`
5. `url`
6. `published_at`
7. `query`
8. `content`

## Rate limit and constraints

- NewsAPI access is plan-dependent and rate limited.
- The extractor currently performs one API request per query.
- For larger runs, implement:
  - retry/backoff on `429`
  - request pacing
  - deduplication across overlapping queries

## Repro steps

```bash
cd phase1
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export NEWSAPI_KEY="<your-key>"
python scripts/extractors/extract_newsapi.py --query "rail safety" --query "infrastructure risk"
```
