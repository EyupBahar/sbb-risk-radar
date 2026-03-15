# NewsAPI Profiling Note

- Run timestamp (UTC): 2026-03-15T11:38:48.307247+00:00
- API calls executed: 2
- Total normalized rows: 20
- Run status: success

## Query-level counts

- `rail safety`: 10 article(s)
- `infrastructure risk`: 10 article(s)

## Rate limit observations

- NewsAPI free/developer plans are rate-limited and may return HTTP 429 when exceeded.
- Monitor response headers and HTTP status codes during larger-scale extraction.

## Data quality notes

- Duplicate headlines may appear across closely related queries.
- Some fields (`author`, `content`) can be null/empty depending on publisher.
