# Source Note - Newsdata.io (Secondary API)

## Feasibility snapshot

- Status: tested with sample request
- Endpoint tested: `https://newsdata.io/api/1/news`
- Sample response saved: `data/raw/secondary/newsdata_sample_response.json`

## Access requirements

- Authentication: API key (`apikey`) query param or `X-ACCESS-KEY` header
- Signup and email verification required to receive active key

## Free tier and request limits (from official docs)

- Free plan: `200` credits/day
- Articles per credit (free): `10`
- Some advanced features are paid-only (archive, AI fields, full content)

## Field coverage (brief)

Common response fields include:
- `title`, `link`, `description`, `content`
- `source_id`, `source_name`, `source_url`
- `pubDate`, `language`, `country`, `category`

Compared to NewsAPI:
- Generally richer provider metadata objects are available in docs.
- Different naming conventions (`link`, `pubDate`) vs NewsAPI (`url`, `publishedAt`).

## Constraints and opportunities

- Constraint: strict daily credit model on free plan.
- Opportunity: broader filtering dimensions and richer metadata in higher tiers.
