# Master Source Template (Excel) Column Guide

This guide describes how API-extracted data maps to the SBB Risk Radar master Excel format.

## Template reference

- File: `data/normalized/master/SBB_Risk_Radar_Master_Source_Template_Normalization.xlsx`
- Output CSV: `data/normalized/master/master_source_v0.csv`

## Source → Master mapping

### NewsAPI

| NewsAPI field | Master column |
|---------------|----------------|
| source.name | source_name, quelle |
| author | author_or_org |
| title | title_raw, working_title |
| description | summary_raw, kurzbeschrieb |
| url | document_url |
| publishedAt | published_at, datum |
| content | text_raw |
| query | page_reference_raw, section_category, stichwoerter |

### GNews

| GNews field | Master column |
|-------------|---------------|
| source.name | source_name, quelle |
| title | title_raw, working_title |
| description | summary_raw, kurzbeschrieb |
| url | document_url |
| publishedAt | published_at, datum |
| content | text_raw |
| query | page_reference_raw, section_category, stichwoerter |

### Fixed values (all records)

- source_group: `api`
- source_type: `article`
- record_granularity: `item`
- file_format: `json`
- extraction_method: `api`
- access_status: `ok`
- parse_status: `success`
- language: `en`
- pipeline_version: `v0`
