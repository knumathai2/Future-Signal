# Polymarket Gamma/CLOB API Findings

**Date**: 2026-07-08
**Task**: TASK-004

## 1. Data Shape and Usable Fields
Based on testing the `/events` endpoint:
- **Event ID**: `id`
- **Market ID**: Inner array `markets[0].id`
- **Title**: Can use `title` (event level) or `question` (market level).
- **Description**: `description`
- **Category/Tags**: Found in `tags` (array of objects with `label` and `slug`).
- **Current Value/Price**: Located in `markets[0].outcomePrices` array, corresponding to `outcomes`. For binary markets, it's typically a string like `"0"`, `"0.34"`.
- **Volume**: `volume`
- **Liquidity**: `liquidity`
- **Dates**: `createdAt`, `updatedAt`, `endDate`

## 2. Pagination Behavior
The Gamma API supports standard `limit` and `offset` query parameters.
- Example: `?limit=10&offset=20` retrieves 10 items skipping the first 20.
- No special pagination headers were observed in the response.

## 3. Rate-Limit Observations
- A rapid test of 30 requests at 10 requests per second completed with a 100% success rate (all 200 OK).
- The API does not return standard `X-RateLimit-*` headers.
- Conclusion: Practical rate limits are sufficiently high for a 5-day hackathon MVP's batch collector running at a reasonable interval.

## 4. Known Issues / Missing Fields
- `resolutionSource`: Often empty or missing in both the event and market data.
- `current_value`: Requires parsing from `outcomePrices` string array.
