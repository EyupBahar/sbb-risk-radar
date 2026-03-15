# GNews Profiling Note

- Run timestamp (UTC): 2026-03-15T11:51:53.586366+00:00
- API calls executed: 2
- Total normalized rows: 20
- Run status: success

## Query-level counts

- `rail safety`: 10 article(s)
- `infrastructure risk`: 10 article(s)

## Comparison comments vs NewsAPI

- GNews may return fewer metadata fields than NewsAPI (for example, no author in many cases).
- GNews uses `max` for result size and `apikey` parameter name, while NewsAPI uses `pageSize` and `apiKey`.
- Rate limit/plan behavior differs by provider and should be monitored separately.

## Rate limit observations

- Handle `429` with retry/backoff for larger extraction runs.
