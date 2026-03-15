# Phase 1 - NewsAPI Extraction + Local Portal

## 1) Extract sample data

```bash
NEWSAPI_KEY="<your_key>" python3 scripts/extractors/extract_newsapi.py --query "rail safety" --query "infrastructure risk" --insecure-skip-tls-verify
```

Outputs:

- `data/raw/newsapi/*.json`
- `data/normalized/newsapi_sample_v0.csv`
- `data/profiling/newsapi_profile.md`

## 1b) Extract GNews sample data

```bash
GNEWS_API_KEY="<your_key>" python3 scripts/extractors/extract_gnews.py --query "rail safety" --query "infrastructure risk" --insecure-skip-tls-verify
```

Outputs:

- `data/raw/gnews/*.json`
- `data/normalized/gnews_sample_v0.csv`
- `data/profiling/gnews_profile.md`

## 1c) Fetch secondary API sample responses

```bash
NEWSDATA_API_KEY="<your_key_or_placeholder>" MEDIASTACK_ACCESS_KEY="<your_key_or_placeholder>" python3 scripts/extractors/extract_secondary_samples.py --query "rail safety" --insecure-skip-tls-verify
```

Outputs:

- `data/raw/secondary/newsdata_sample_response.json`
- `data/raw/secondary/mediastack_sample_response.json`

## 2) Merge into master Excel format

```bash
python3 scripts/normalize/merge_master_source.py
```

Output: `data/normalized/master/master_source_v0.csv` (deck Excel format)

## 3) Run local portal on port 3000

```bash
python3 scripts/portal/newsapi_portal.py --port 3000
```

Open:

- `http://127.0.0.1:3000`

Portal shows separate sections for:

- NewsAPI normalized rows
- GNews normalized rows
- Latest raw JSON snapshots (NewsAPI + GNews)
- Secondary raw responses (Newsdata + Mediastack)
