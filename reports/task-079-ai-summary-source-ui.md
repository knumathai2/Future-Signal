# TASK-079 — AI issue briefing and verified-source UI

_Date: 2026-07-11 · Status: Complete_

## Result

- Replaced the v4 change-episode report with the v5 `AI 이슈 브리핑` reading
  order: 핵심 요약 → 현재 데이터 해석 → 3–4 조건부 시나리오 → 주요 요인 →
  확인할 자료와 변화 → 검증 자료 → 관계 범위/데이터 한계/해석 주의.
- Added typed list/card rendering for scenarios, factors, and watch items.
- Verified source cards show stored title, type, domain, optional time, and the
  exact stored URL. Links use `target="_blank"` and `rel="noopener noreferrer"`
  with source-type-specific labels.
- The zero-source region stays visible and explicitly states that no material
  passed the public criteria and the background of the numeric movement is not
  established.
- Loading, not-yet-generated, and request-failure states remain isolated from
  the issue/chart flow, with data timing and caution nearby.

## Verification

- TypeScript typecheck: pass
- ESLint: pass
- Strict v5 parser regression: pass
- Production build: pass (existing bundle-size warning only)
- Browser: 320px, 375px, and 1280px have no horizontal overflow.
- Browser fixture states: zero, one, and three verified candidates render.
- Three-candidate fixture: three cards, four exact safe source links.
- Clean final tab: zero console errors.

