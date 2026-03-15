# Master Source Schema v0

Schema aligned with `SBB_Risk_Radar_Master_Source_Template_Normalization.xlsx`.

## Columns

| Column | Description | NewsAPI/GNews mapping |
|--------|-------------|------------------------|
| record_id | Unique record ID | `src_newsapi_YYYYMMDD_NNN` / `src_gnews_YYYYMMDD_NNN` |
| batch_id | Batch identifier | `phase1_wk1` |
| source_name | Publisher/source name | From API `source.name` |
| source_group | Source category | `api` |
| source_type | Record type | `article` |
| record_granularity | Granularity | `item` |
| source_url | API base URL | `https://newsapi.org/` or `https://gnews.io/` |
| document_url | Article URL | `url` |
| source_document_id | Document ID | `{provider}_{content_hash}` |
| title_raw | Article title | `title` |
| summary_raw | Short description | `description` |
| text_raw | Full content | `content` |
| page_reference_raw | Query/ref | `query` |
| published_at | Publication date | `publishedAt` |
| retrieved_at | Fetch timestamp | Run time |
| language | Language code | `en` |
| country_hint | Country hint | (empty) |
| author_or_org | Author | `author` (NewsAPI only) |
| section_category | Category | `query` |
| file_format | Format | `json` |
| extraction_method | Method | `api` |
| access_status | Access status | `ok` |
| parse_status | Parse status | `success` |
| raw_storage_path | Raw JSON path | `data/raw/{provider}/` |
| normalized_storage_path | CSV path | `data/normalized/{provider}_sample_v0.csv` |
| text_length | Content length | `len(text_raw)` |
| content_hash | Content hash | SHA256 prefix |
| notes | Free text | (empty) |
| working_title | Working title | Same as title_raw |
| kurzbeschrieb | Short desc (DE) | Same as summary_raw |
| quelle | Source (DE) | Same as source_name |
| seitenangabe | Page ref (DE) | (empty) |
| stichwoerter | Keywords (DE) | Same as query |
| datum | Date (DE) | Same as published_at |
| betroffene_konzernziele | SBB field | (empty) |
| auswirkung | SBB field | (empty) |
| zeithorizont | SBB field | (empty) |
| geografische_relevanz | SBB field | (empty) |
| primaer_betroffene_division | SBB field | (empty) |
| sekundaer_betroffene_division | SBB field | (empty) |
| trend | SBB field | (empty) |
| kommentar | SBB field | (empty) |
| dedup_cluster_id | Dedup ID | (empty) |
| ai_confidence | AI confidence | (empty) |
| relevance_score_sbb | SBB relevance | (empty) |
| pipeline_version | Pipeline version | `v0` |

## Merge command

```bash
python3 scripts/normalize/merge_master_source.py
```

Output: `data/normalized/master/master_source_v0.csv`
