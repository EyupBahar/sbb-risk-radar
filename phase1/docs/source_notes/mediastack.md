# Source Note - Mediastack (Secondary API)

## Feasibility snapshot

- Status: tested with sample request
- Endpoint tested: `https://api.mediastack.com/v1/news`
- Sample response saved: `data/raw/secondary/mediastack_sample_response.json`

## Access requirements

- Authentication: `access_key` query param
- API key provisioned via Mediastack dashboard

## Free tier and request limits (from product/pricing pages)

- Free plan: `100` calls/month
- Free plan data is delayed (about 30 minutes)
- Free plan support is limited and feature set is constrained

## Field coverage (brief)

Typical article fields:
- `author`, `title`, `description`, `url`
- `source`, `image`, `category`, `language`, `country`, `published_at`
- pagination block (`limit`, `offset`, `count`, `total`)

Compared to NewsAPI:
- Similar core article fields, but naming differs (`published_at`, `source` string).
- Free plan may impose stronger freshness constraints due to delayed feed.

## Constraints and opportunities

- Constraint: very low free-tier volume and delayed data.
- Opportunity: straightforward schema and broad source aggregation for prototypes.
