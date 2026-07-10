import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { SiteHeader } from "./AppShell";
import { CompactIssueRow } from "./CompactIssueRow";
import { FeaturedIssueCard } from "./FeaturedIssueCard";
import { GlobalFooter, ShortCautionNotice } from "./InformationNotice";
import { useIssueList } from "../hooks/useIssueList";
import type { Issue } from "../types/issue";
import { fetchJson } from "../utils/api";
import {
  type ApiIssueListResponse,
  formatCategoryLabel,
  formatPercentagePointChange,
  issueChangeForWindow,
  mapApiIssueToFrontendIssue,
  windowLabel,
} from "../utils/format";
import { parseForcedStatus, parseListWindow } from "../utils/routeState";

type DashboardProps = { categories: string[] };

type CategorySummary = {
  label: string;
  count: number;
  largestChange: number | null | undefined;
};

type CategoryIssueGroups = Record<string, Issue[]>;

function HomeSkeleton() {
  return (
    <div aria-label="이슈를 불러오는 중" className="space-y-4">
      <div className="h-[220px] animate-pulse rounded-xl border border-line bg-card" />
      <div className="overflow-hidden rounded-xl border border-line bg-card">
        {Array.from({ length: 4 }).map((_, index) => (
          <div
            key={index}
            className="h-24 animate-pulse border-b border-line-soft bg-line-soft last:border-b-0"
          />
        ))}
      </div>
    </div>
  );
}

function ErrorState({ dataAsOf }: { dataAsOf: string }) {
  return (
    <div
      className="rounded-lg border border-line bg-card px-4 py-3"
      role="status"
    >
      <h2 className="text-sm font-bold text-ink">
        마지막으로 확인 가능한 데이터를 표시합니다
      </h2>
      <p className="mt-1 text-xs leading-5 text-ink-soft">
        최신 갱신이 완료되지 않아 화면에 표시된 기준 시각의 목록을 유지합니다.
        <span className="sr-only">{dataAsOf}</span>
      </p>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-xl border border-dashed border-line px-6 py-12 text-center">
      <h2 className="text-base font-bold text-ink">
        표시할 이슈가 아직 없습니다
      </h2>
      <p className="mt-2 text-sm leading-6 text-ink-soft">
        이슈 기록이 준비되면 최근 관측 변화 순서로 표시합니다.
      </p>
    </div>
  );
}

function summarizeCategory(
  label: string,
  matching: Issue[],
  windowKey: "24h" | "7d",
): CategorySummary | null {
  if (matching.length === 0) {
    return null;
  }

  const issueWithLargestChange = matching.reduce<Issue | null>(
    (largest, issue) => {
      const next = issueChangeForWindow(issue, windowKey);
      if (next === null || next === undefined) {
        return largest;
      }
      if (!largest) {
        return issue;
      }
      const currentLargest = issueChangeForWindow(largest, windowKey);
      return currentLargest === null ||
        currentLargest === undefined ||
        Math.abs(next) > Math.abs(currentLargest)
        ? issue
        : largest;
    },
    null,
  );

  return {
    label,
    count: matching.length,
    largestChange: issueWithLargestChange
      ? issueChangeForWindow(issueWithLargestChange, windowKey)
      : null,
  };
}

function buildFallbackCategorySummaries(
  issues: Issue[],
  categories: string[],
  windowKey: "24h" | "7d",
): CategorySummary[] {
  const grouped = new Map<string, Issue[]>();
  issues.forEach((issue) => {
    const label = formatCategoryLabel(issue.category);
    grouped.set(label, [...(grouped.get(label) ?? []), issue]);
  });

  const orderedLabels = Array.from(
    new Set([
      ...categories.map(formatCategoryLabel),
      ...Array.from(grouped.keys()).sort((left, right) =>
        left.localeCompare(right, "ko"),
      ),
    ]),
  );

  return orderedLabels.flatMap((label) => {
    const matching = grouped.get(label) ?? [];
    const summary = summarizeCategory(label, matching, windowKey);
    return summary ? [summary] : [];
  });
}

/** Discovery-focused home route: one featured issue, four rows, and category coverage. */
export function Dashboard({ categories }: DashboardProps) {
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeWindow = parseListWindow(searchParams.get("window"));
  const forcedStatus = parseForcedStatus(searchParams);
  const { issues, status, isRefreshing, dataAsOf, refresh } = useIssueList({
    windowKey: activeWindow,
    sort: "change",
    forcedStatus,
  });
  const [categoryIssueGroups, setCategoryIssueGroups] =
    useState<CategoryIssueGroups | null>(null);

  useEffect(() => {
    const raw = searchParams.get("window");
    if (raw && raw !== "24h" && raw !== "7d") {
      const normalized = new URLSearchParams(searchParams);
      normalized.delete("window");
      setSearchParams(normalized, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  useEffect(() => {
    if (categories.length === 0 || forcedStatus) {
      setCategoryIssueGroups(null);
      return;
    }

    const controller = new AbortController();
    setCategoryIssueGroups(null);

    Promise.all(
      categories.map(async (category) => {
        const label = formatCategoryLabel(category);
        const params = new URLSearchParams({
          category: label,
          window: activeWindow,
          sort: "change",
          limit: "100",
        });
        const data = await fetchJson<ApiIssueListResponse>(
          `/api/issues?${params.toString()}`,
          `Failed to load ${label} category summary`,
          controller.signal,
        );
        return [
          label,
          data.issues.map((issue) =>
            mapApiIssueToFrontendIssue(issue, data.data_as_of),
          ),
        ] as const;
      }),
    )
      .then((entries) => setCategoryIssueGroups(Object.fromEntries(entries)))
      .catch((error) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        console.error(error);
        setCategoryIssueGroups(null);
      });

    return () => controller.abort();
  }, [activeWindow, categories, forcedStatus]);

  const featuredIssue = issues[0] ?? null;
  const majorIssues = issues.slice(1, 5);
  const categorySummaries = useMemo(() => {
    if (!categoryIssueGroups) {
      return buildFallbackCategorySummaries(issues, categories, activeWindow);
    }

    return categories.flatMap((category) => {
      const label = formatCategoryLabel(category);
      const summary = summarizeCategory(
        label,
        categoryIssueGroups[label] ?? [],
        activeWindow,
      );
      return summary ? [summary] : [];
    });
  }, [activeWindow, categories, categoryIssueGroups, issues]);
  const from = `${location.pathname}${location.search}`;
  const hasIssues = issues.length > 0;

  function changeWindow(windowKey: "24h" | "7d") {
    const next = new URLSearchParams(searchParams);
    if (windowKey === "24h") {
      next.delete("window");
    } else {
      next.set("window", windowKey);
    }
    setSearchParams(next);
  }

  return (
    <div className="mx-auto min-h-screen w-full max-w-[1180px] px-4 py-4 sm:px-8 sm:py-6 lg:px-10 lg:py-8">
      <SiteHeader
        dataAsOf={dataAsOf}
        onRefresh={refresh}
        isRefreshing={isRefreshing}
      />

      <main
        id="main-content"
        data-route-main
        tabIndex={-1}
        aria-labelledby="home-title"
        className="outline-none"
      >
        <section className="mt-5 sm:mt-7">
          <h1
            id="home-title"
            className="max-w-3xl text-2xl font-bold text-ink sm:text-3xl"
          >
            지금 크게 달라진 이슈
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-ink-soft">
            공개 데이터에 반영된 최근 기대값 변화를 짧게 살펴볼 수 있습니다.
          </p>
        </section>

        <ShortCautionNotice
          context="dashboard"
          className="mt-4"
          showMethodologyLink
        />

        {status === "error" ? (
          <div className="mt-4">
            <ErrorState dataAsOf={dataAsOf} />
          </div>
        ) : null}

        <section className="mt-5" aria-labelledby="featured-issue-title">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2
              id="featured-issue-title"
              className="text-lg font-bold text-ink"
            >
              오늘의 대표 변화
            </h2>
            <div
              className="flex gap-1"
              role="group"
              aria-label="대표 변화 기간"
            >
              {(["24h", "7d"] as const).map((windowKey) => (
                <button
                  key={windowKey}
                  type="button"
                  onClick={() => changeWindow(windowKey)}
                  aria-pressed={activeWindow === windowKey}
                  className={
                    activeWindow === windowKey
                      ? "inline-flex min-h-11 items-center rounded-full border border-ink bg-ink px-4 text-xs font-bold text-card"
                      : "inline-flex min-h-11 items-center rounded-full border border-line px-4 text-xs font-bold text-ink-soft transition hover:border-accent hover:text-accent"
                  }
                >
                  {windowLabel(windowKey)}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-3" aria-busy={isRefreshing}>
            {status === "loading" ? <HomeSkeleton /> : null}
            {status === "empty" ? <EmptyState /> : null}
            {featuredIssue ? (
              <FeaturedIssueCard
                issue={featuredIssue}
                windowKey={activeWindow}
                from={from}
              />
            ) : null}
          </div>
        </section>

        {hasIssues ? (
          <>
            <section className="mt-7" aria-labelledby="major-issues-title">
              <div className="flex items-center justify-between gap-3">
                <h2
                  id="major-issues-title"
                  className="text-lg font-bold text-ink"
                >
                  최근 {windowLabel(activeWindow)} 주요 변화
                </h2>
                {isRefreshing ? (
                  <span
                    className="text-xs font-semibold text-ink-faint"
                    role="status"
                  >
                    목록 갱신 중
                  </span>
                ) : null}
              </div>
              <ul className="mt-3 overflow-hidden rounded-xl border border-line">
                {majorIssues.map((issue) => (
                  <CompactIssueRow
                    key={issue.id}
                    issue={issue}
                    windowKey={activeWindow}
                    from={from}
                  />
                ))}
              </ul>
              <Link
                to={`/issues?window=${activeWindow}&sort=change`}
                className="mt-3 inline-flex min-h-11 items-center text-sm font-bold text-accent"
              >
                전체 이슈 보기 →
              </Link>
            </section>

            <section className="mt-7" aria-labelledby="category-summary-title">
              <div className="flex items-center justify-between gap-3">
                <h2
                  id="category-summary-title"
                  className="text-lg font-bold text-ink"
                >
                  카테고리별 현황
                </h2>
                <span className="text-xs font-semibold text-ink-faint">
                  {windowLabel(activeWindow)} 기준
                </span>
              </div>
              <ul className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
                {categorySummaries.map((summary) => (
                  <li key={summary.label}>
                    <Link
                      to={`/issues?category=${encodeURIComponent(summary.label)}&window=${activeWindow}&sort=change`}
                      className="flex min-h-[112px] flex-col justify-between rounded-xl border border-line bg-card p-4 transition hover:border-accent"
                    >
                      <span className="text-sm font-bold text-ink">
                        {summary.label}
                      </span>
                      <span>
                        <span className="block text-xs text-ink-faint">
                          {summary.count}개 이슈
                        </span>
                        <span className="mt-1 block text-sm font-bold text-ink">
                          최대{" "}
                          {formatPercentagePointChange(summary.largestChange)}
                        </span>
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          </>
        ) : null}
      </main>

      <GlobalFooter className="mt-8" />
    </div>
  );
}
