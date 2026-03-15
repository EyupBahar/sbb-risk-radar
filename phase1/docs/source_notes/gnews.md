# Source Note - GNews

## Source identification

- Source name: GNews
- Base endpoint used: `https://gnews.io/api/v4/search`
- Access type: API key based authentication
- Script: `scripts/extractors/extract_gnews.py`

## Access and authentication

- Auth method: `apikey` query parameter (`GNEWS_API_KEY` environment variable).
- Expected failure modes:
  - `401` for invalid/missing API key
  - `403` for forbidden access (plan/permission)
  - `429` for rate limit/quota exceed

## Test queries executed

Default queries in extractor:

- `rail safety`
- `infrastructure risk`

## Output artifacts

- Raw JSON files: `data/raw/gnews/gnews_<query>_<timestamp>.json`
- Normalized CSV: `data/normalized/gnews_sample_v0.csv`
- Profiling note: `data/profiling/gnews_profile.md`

## Normalization schema (v0)

Columns written to normalized CSV:

1. `source_name`
2. `title`
3. `description`
4. `content`
5. `url`
6. `image`
7. `published_at`
8. `query`

## Main differences vs NewsAPI

- **Parameter names:** GNews uses `apikey` and `max`; NewsAPI uses `apiKey` and `pageSize`.
- **Response shape:** both return `articles`, but metadata richness can differ.
- **Provider policy:** auth, quotas, and rate limits are independent and must be validated separately.

## Repro steps

```bash
cd phase1
GNEWS_API_KEY="<your-key>" python3 scripts/extractors/extract_gnews.py --query "rail safety" --query "infrastructure risk"
```
