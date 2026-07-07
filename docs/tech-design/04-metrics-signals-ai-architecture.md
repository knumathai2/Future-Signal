# Technical Design: Metrics, Signals, AI Report Architecture

_Source: former project-root Technical Design sections 7-10._

---

## 7. Metric Calculation Flow

(Detailed formulas already defined in Service Design §5 — this section is the engineering sequencing.)

1. For each market, pull the last N `market_snapshots` covering the widest window needed (30d if available, else whatever history exists).
2. Compute `change_24h` = `price(now) - price(now-24h)` (nearest available snapshot to that time), same pattern for `change_7d`.
3. If volatility/attention are in scope for the current build day (P1), compute them from the same pulled window — no separate query needed.
4. Compute `confidence_level` from volume, liquidity, and market age against fixed thresholds (define initial thresholds as constants, e.g., `min_volume_24h`, `min_snapshots_required` — expect to tune these once real data is seen on Day 2 of the hackathon, per PRD's Day 2 plan).
5. Compute `heat_score` as a simple weighted sum for MVP (e.g., `abs(change_24h) * 0.6 + normalized_volume * 0.4`) — do not over-engineer this formula before seeing real data; it only needs to produce a sensible top-10 ranking for the demo, not a validated model.
6. Upsert (insert new row) into `market_metrics`.

---

## 8. Sudden Change Signal Detection Flow

1. After metrics are computed for a market, check `abs(change_24h) >= threshold` (default 5pp, matching PRD §8.6).
2. Check whether an unresolved signal of the same type already exists for this market within the current window (cooldown check) — if so, skip to avoid duplicate/spammy signals.
3. If triggered and not a duplicate, classify severity (Section 5 badge tiers from Service Design §7 — MVP only needs to support `medium`, since only the single threshold-based "Expectation Shift Detected" signal is in scope).
4. Insert into `issue_signals`.
5. This is also exactly the trigger condition feeding batch step 8 (AI report regeneration) — a new signal is one of the three conditions that qualifies a market for report regeneration.

---

## 9. AI Report Generation Architecture

```
market_metrics (latest) + market_snapshots (window) + related_events (if any)
                    |
                    v
        build_prompt() -- fills a fixed template, never free text
                    |
                    v
        call LLM API (Claude or OpenAI)
                    |
                    v
        parse structured response into fixed sections
                    |
                    v
        run banned-phrase safety filter (UX Design §5.3 list)
                    |
              pass?  |  fail?
              v            v
        store in        discard, log failure,
        ai_reports       keep previous report live
```

### Regeneration conditions (cost control, per batch step 8)
A market qualifies for regeneration only if **any** of:
- A new `issue_signals` row fired for it this run, or
- It has no `ai_reports` row yet, or
- Its most recent report is older than a staleness threshold (recommend 24h for MVP).

And is capped at a **maximum reports per batch run** (e.g., top 10 by `heat_score` among qualifying markets) so a bad day of many signals firing at once can't blow the API budget.

### Cost-control strategy
- Template-constrained prompts (below) keep both input and output token counts small and predictable — no open-ended "analyze this market" prompt.
- Regenerate only on meaningful change, never on a fixed short interval regardless of data movement.
- Cap reports per run.
- Reuse (serve the existing row from `ai_reports`) whenever a market doesn't qualify for regeneration — the API layer never calls the LLM live.

---

## 10. AI Prompt and Output Design

### 10.1 System prompt (fixed, never modified per-request)
```
You are generating a short, neutral data summary for a public issue-monitoring
dashboard. You are describing PUBLIC PREDICTION-MARKET DATA, not predicting
real-world outcomes and not giving advice of any kind.

Rules you must always follow:
- Describe only what the data shows: direction, magnitude, and timing of change.
- Never state or imply that an outcome will or will not happen.
- Never use: bet, buy, sell, trade, position, long, short, profit, win rate,
  recommend, guaranteed, best pick, follow, copy, opportunity.
- Never suggest any action the reader should take.
- If a related event candidate is provided, describe it only as a "candidate
  for context," never as a cause.
- If data is limited (low volume, short history, high volatility), say so
  plainly instead of writing around it.
- Keep every section to 1-3 sentences.
```

### 10.2 User/task prompt template
```
Market title: {{title}}
Market description: {{description}}
Category: {{category}}
Current expectation value: {{current_value}}
24h change: {{change_24h}}
7d change: {{change_7d}}
Confidence level: {{confidence_level}}
Recent inflection point (if any): {{inflection_point_summary}}
Related event candidate (if any): {{related_event_or_none}}

Produce a JSON object with exactly these fields:
{
  "issue_summary": "...",
  "movement_explanation": "...",
  "key_change_context": "...",
  "uncertainty_summary": "...",
  "neutral_conclusion": "..."
}
```

### 10.3 Example output (stored in `ai_reports.content` as jsonb)
```json
{
  "issue_summary": "This market tracks whether [event] will be resolved as 'Yes' by [date], based on public trading activity on Polymarket.",
  "movement_explanation": "Over the past 7 days, the expectation reflected in this market rose by 11 percentage points, with the largest single shift occurring around [date].",
  "key_change_context": "A related event candidate around this time: [event]. This is offered as context, not as a confirmed cause.",
  "uncertainty_summary": "Trading activity on this market has been moderate over this period; interpret short-term swings with some caution.",
  "neutral_conclusion": "Public expectation on this issue has shifted upward over the past week, though the underlying data reflects market activity rather than a factual forecast."
}
```

### 10.4 Safety filter (runs after every generation, before storage)
1. Lowercase the full concatenated output and check against the prohibited-word list from UX Design §5.3 (bet, buy, sell, trade, position, long, short, profit, win rate, copy trader, follow, expert trader, best pick, recommended outcome, high-return, guaranteed).
2. Check for a small set of banned sentence patterns (regex) such as `"will (happen|occur)"`, `"you should"`, `"recommend"`.
3. If any check fails: discard the output, log the failure (which rule, which market) to `data_collection_logs` or a dedicated error log, keep the previous `ai_reports` row as the one served, and do **not** retry with the same prompt automatically — a failing generation likely indicates a prompt issue worth a human look, not a transient error.
4. If checks pass: store with `status = success`.

### 10.5 Report storage and regeneration
Already covered in Sections 4.6 and 9 — one row per generation event, never overwritten in place, so `ai_reports` doubles as a natural audit trail of how the summary changed over time if that's ever useful.

### 10.6 Error handling
- LLM API timeout/error → one retry, then `status = failed`, previous good report stays live.
- Malformed JSON in response → treat as a failure the same way (don't attempt partial parsing under time pressure).

---
