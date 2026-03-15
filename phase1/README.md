# SBB Risk Radar — Phase 1

Phase 1 extracts and normalizes news data from NewsAPI and GNews into the SBB master Excel format.

## Project structure

```
phase1/
├── scripts/
│   ├── utils/          # Shared HTTP and I/O helpers
│   │   ├── http.py
│   │   └── io.py
│   ├── extractors/
│   │   ├── extract_newsapi.py          # NewsAPI extractor
│   │   ├── extract_gnews.py            # GNews extractor
│   │   └── extract_secondary_samples.py # Newsdata + Mediastack feasibility
│   ├── normalize/
│   │   └── merge_master_source.py      # Merge to SBB master Excel format
│   └── portal/
│       └── data_portal.py              # Local browser portal (port 3000)
├── data/
│   ├── raw/            # Raw API JSON responses
│   ├── normalized/     # Normalized CSVs + master CSV
│   └── profiling/      # Per-source profiling notes
└── docs/
    ├── schema/         # Master schema definition
    ├── guides/         # Column mapping guide
    └── source_notes/   # Per-source notes and feasibility reports
```

## Setup

```bash
cd phase1
cp .env.example .env   # Fill in your API keys
```

## 1. Extract NewsAPI

```bash
NEWSAPI_KEY="<key>" python3 scripts/extractors/extract_newsapi.py \
  --query "rail safety" --query "infrastructure risk" \
  --insecure-skip-tls-verify
```

Output:
- `data/raw/newsapi/*.json`
- `data/normalized/newsapi_sample_v0.csv`
- `data/profiling/newsapi_profile.md`

## 2. Extract GNews

```bash
GNEWS_API_KEY="<key>" python3 scripts/extractors/extract_gnews.py \
  --query "rail safety" --query "infrastructure risk" \
  --insecure-skip-tls-verify
```

Output:
- `data/raw/gnews/*.json`
- `data/normalized/gnews_sample_v0.csv`
- `data/profiling/gnews_profile.md`

## 3. Fetch secondary API samples (optional)

```bash
NEWSDATA_API_KEY="<key>" MEDIASTACK_ACCESS_KEY="<key>" \
python3 scripts/extractors/extract_secondary_samples.py --query "rail safety" \
  --insecure-skip-tls-verify
```

Output:
- `data/raw/secondary/newsdata_sample_response.json`
- `data/raw/secondary/mediastack_sample_response.json`

## 4. Merge to master Excel format

```bash
python3 scripts/normalize/merge_master_source.py
```

Output: `data/normalized/master/master_source_v0.csv`  
Schema: aligned with `SBB_Risk_Radar_Master_Source_Template_Normalization.xlsx`

## 5. Run local portal

```bash
python3 scripts/portal/data_portal.py --port 3000
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000)

Portal shows:
- NewsAPI normalized table
- GNews normalized table
- Master CSV table (deck Excel format)
- Secondary raw responses (Newsdata, Mediastack)
- Latest raw JSON snapshots
