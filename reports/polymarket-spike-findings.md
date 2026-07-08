# Polymarket Gamma/CLOB API Findings

**Date**: 2026-07-08
**Task**: TASK-004

## 1. Data Shape and Usable Fields
Based on testing the `/events` endpoint:
- **Event ID**: `id`
- **Market ID**: Inner array `markets` (Note: Must iterate through `markets` as the first market is not always the open/active binary one).
- **Title**: Can use `title` (event level) or `question` (market level). Note: Mapped to `raw_data.title` and replaced with `ui_display.neutral_title` for display safety.
- **Description**: `description`
- **Category/Tags**: Found in `tags` (array of objects with `label` and `slug`). Mapped to `raw_data.category_tag` and replaced with `ui_display.neutral_tags`.
- **Current Value/Price**: Located in the valid inner market's `outcomePrices` array. For binary markets, it's typically a string like `"0"`, `"0.34"`.
- **Volume**: `volume`
- **Liquidity**: `liquidity`
- **Dates**: `createdAt`, `updatedAt`, `endDate`

## 2. Gamma Token Discovery
- **CLOB Tokens**: The `clobTokenIds` field in the inner market is parsed as a JSON string array.
- **History Token**: The token for the "Yes" outcome (first token in `clobTokenIds`) is captured as `price_history_token` to be used for charting price histories.
- **Price History Source**: Set to `CLOB` to indicate that price history will be fetched via the Polymarket CLOB API using the history token.

## 3. Pagination Behavior
The Gamma API supports standard `limit` and `offset` query parameters.
- Example: `?limit=10&offset=20` retrieves 10 items skipping the first 20.
- No special pagination headers were observed in the response.

## 4. Rate-Limit Observations
- A rapid test of 30 requests at 10 requests per second completed with a 100% success rate (all 200 OK).
- The API does not return standard `X-RateLimit-*` headers.
- Conclusion: Practical rate limits are sufficiently high for a 5-day hackathon MVP's batch collector running at a reasonable interval.

## 5. Known Issues / Missing Fields
- `resolutionSource`: Often empty or missing in both the event and market data.
- `current_value`: Requires parsing from `outcomePrices` string array.
- **Data Hygiene**: The raw Gamma API often includes product-unsafe prediction framing in titles and tags, requiring separation into display-safe `ui_display` fields.
