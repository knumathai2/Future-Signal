import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  Link,
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router-dom";
import { SiteHeader } from "./AppShell";
import { DirectionalChange } from "./DirectionalChange";
import { FeaturedIssueCard } from "./FeaturedIssueCard";
import { GlobalFooter, ShortCautionNotice } from "./InformationNotice";
import { IssueRanking } from "./IssueRanking";
import { useIssueList } from "../hooks/useIssueList";
import type { CategorySummary, Issue } from "../types/issue";
import { fetchJson } from "../utils/api";
import {
  type ApiIssueListResponse,
  formatCategoryLabel,
  formatCompactDataTimestamp,
  mapApiIssueToFrontendIssue,
  windowLabel,
} from "../utils/format";
import {
  buildCategorySummary,
  buildDirectionSummary,
  rankIssuesByChange,
} from "../utils/homeSummary";
import { parseForcedStatus, parseHomeWindow } from "../utils/routeState";

type DashboardProps = {
  categories: string[];
  categoriesStatus: "loading" | "ready" | "error";
};

type CategoryIssueGroups = Record<string, Issue[]>;
type CategoryLoadStatus = "loading" | "ready" | "empty" | "error";

type CategoryState = {
  groups: CategoryIssueGroups | null;
  status: CategoryLoadStatus;
  isRefreshing: boolean;
};

function FeaturedSkeleton() {
  return (
    <div
      className="h-[540px] animate-pulse rounded-2xl border border-line bg-card sm:h-[560px]"
      aria-label="대표 이슈를 불러오는 중"
    />
  );
}

function HomeSectionsSkeleton() {
  return (
    <div aria-label="메인 요약을 불러오는 중" className="mt-7 space-y-7">
      <div className="h-52 animate-pulse rounded-2xl border border-line bg-card" />
      <div className="h-[420px] animate-pulse rounded-2xl border border-line bg-card" />
      <div className="h-48 animate-pulse rounded-2xl border border-line bg-card" />
    </div>
  );
}

function ErrorState({ dataAsOf }: { dataAsOf: string }) {
  return (
    <div
      className="rounded-xl border border-line bg-card px-4 py-3"
      role="status"
    >
      <h2 className="text-sm font-bold text-ink">
        마지막으로 확인 가능한 데이터를 표시합니다
      </h2>
      <p className="mt-1 text-xs leading-5 text-ink-soft">
        최신 갱신이 완료되지 않아 기준 시각{" "}
        {formatCompactDataTimestamp(dataAsOf)}의 내용을 유지합니다.
      </p>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-2xl border border-dashed border-line px-6 py-14 text-center">
      <h2 className="text-base font-bold text-ink">
        표시할 관측 이슈가 아직 없습니다
      </h2>
      <p className="mt-2 text-sm leading-6 text-ink-soft">
        비교 가능한 이슈 기록이 준비되면 요약과 순위를 함께 표시합니다.
      </p>
    </div>
  );
}

function FeaturedEmptyState() {
  return (
    <div className="flex min-h-[360px] items-center justify-center rounded-2xl border border-dashed border-line bg-card px-6 text-center">
      <div>
        <p className="text-sm font-bold text-ink">대표 이슈가 없습니다</p>
        <p className="mt-2 text-xs leading-5 text-ink-soft">
          비교 가능한 변화값이 준비되면 실제 변화폭 1위를 표시합니다.
        </p>
      </div>
    </div>
  );
}

function localCategoryGroups(
  issues: Issue[],
  categories: string[],
): CategoryIssueGroups {
  return Object.fromEntries(
    categories.map((category) => {
      const label = formatCategoryLabel(category);
      return [
        label,
        issues.filter((issue) => formatCategoryLabel(issue.category) === label),
      ];
    }),
  );
}

function CategoryCards({
  summaries,
  activeWindow,
}: {
  summaries: CategorySummary[];
  activeWindow: "24h" | "7d";
}) {
  return (
    <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {summaries.map((summary) => (
        <li key={summary.label}>
          <Link
            to={`/issues?category=${encodeURIComponent(summary.label)}&window=${activeWindow}&sort=change`}
            className="flex min-h-[132px] flex-col justify-between rounded-xl border border-line bg-card p-4 transition hover:border-accent"
            aria-label={`${summary.label} 카테고리 이슈 보기`}
          >
            <span className="text-sm font-bold text-ink">{summary.label}</span>
            <span>
              <span className="block text-[11px] font-semibold text-ink-faint">
                유효 {summary.validCount}개 / 전체 {summary.totalCount}개
              </span>
              <span className="mt-2 block text-sm font-extrabold">
                <DirectionalChange value={summary.averageChange} />
              </span>
              <span className="mt-1 block text-[10px] text-ink-faint">
                단순 평균
              </span>
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}

/** Home route with real top-five ranking, directional counts, and category means. */
export function Dashboard({ categories, categoriesStatus }: DashboardProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState("");
  const activeWindow = parseHomeWindow(searchParams.get("window"));
  const forcedStatus = parseForcedStatus(searchParams);
  const { issues, status, isRefreshing, dataAsOf, refresh } = useIssueList({
    windowKey: activeWindow,
    sort: "change",
    forcedStatus,
  });
  const [categoryState, setCategoryState] = useState<CategoryState>({
    groups: null,
    status: "loading",
    isRefreshing: false,
  });

  useEffect(() => {
    const raw = searchParams.get("window");
    if (raw && raw !== "24h" && raw !== "7d") {
      const normalized = new URLSearchParams(searchParams);
      normalized.delete("window");
      setSearchParams(normalized, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  useEffect(() => {
    if (forcedStatus) {
      return;
    }
    if (categoriesStatus === "loading") {
      setCategoryState((previous) => ({
        ...previous,
        status: previous.groups ? previous.status : "loading",
      }));
      return;
    }
    if (categoriesStatus === "error") {
      setCategoryState((previous) => ({
        ...previous,
        status: "error",
        isRefreshing: false,
      }));
      return;
    }
    if (categories.length === 0) {
      setCategoryState({ groups: {}, status: "empty", isRefreshing: false });
      return;
    }

    const controller = new AbortController();
    setCategoryState((previous) => ({
      ...previous,
      status: previous.groups ? previous.status : "loading",
      isRefreshing: Boolean(previous.groups),
    }));

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
      .then((entries) => {
        setCategoryState({
          groups: Object.fromEntries(entries),
          status: "ready",
          isRefreshing: false,
        });
      })
      .catch((error) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        console.error(error);
        setCategoryState((previous) => ({
          ...previous,
          status: "error",
          isRefreshing: false,
        }));
      });

    return () => controller.abort();
  }, [activeWindow, categories, categoriesStatus, forcedStatus]);

  useEffect(() => {
    if (!forcedStatus) {
      return;
    }
    if (forcedStatus === "loading") {
      setCategoryState({
        groups: null,
        status: "loading",
        isRefreshing: false,
      });
      return;
    }
    if (forcedStatus === "empty") {
      setCategoryState({ groups: {}, status: "empty", isRefreshing: false });
      return;
    }

    setCategoryState({
      groups: localCategoryGroups(issues, categories),
      status: "error",
      isRefreshing: false,
    });
  }, [categories, forcedStatus, issues]);

  const rankedIssues = useMemo(
    () => rankIssuesByChange(issues, activeWindow),
    [activeWindow, issues],
  );
  const featuredIssue = rankedIssues[0] ?? null;
  const topIssues = rankedIssues.slice(0, 5);
  const directionSummary = useMemo(
    () => buildDirectionSummary(issues, activeWindow),
    [activeWindow, issues],
  );
  const categorySummaries = useMemo(() => {
    if (!categoryState.groups) {
      return [];
    }
    return categories.map((category) => {
      const label = formatCategoryLabel(category);
      return buildCategorySummary(
        label,
        categoryState.groups?.[label] ?? [],
        activeWindow,
      );
    });
  }, [activeWindow, categories, categoryState.groups]);
  const from = `${location.pathname}${location.search}`;
  const hasIssues = issues.length > 0;

  function changeWindow(windowKey: "24h" | "7d") {
    const next = new URLSearchParams(searchParams);
    if (windowKey === "7d") {
      next.delete("window");
    } else {
      next.set("window", windowKey);
    }
    setSearchParams(next);
  }

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const params = new URLSearchParams();
    if (query.trim()) {
      params.set("q", query.trim());
    }
    params.set("window", activeWindow);
    params.set("sort", "change");
    navigate(`/issues?${params.toString()}`);
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
        <section className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,0.82fr)_minmax(0,1.18fr)] lg:items-stretch">
          <div className="flex min-w-0 flex-col justify-center">
            <span className="text-xs font-extrabold text-accent">
              공개 데이터로 읽는 기대 변화
            </span>
            <h1
              id="home-title"
              className="mt-3 text-3xl font-extrabold leading-tight text-ink sm:text-4xl"
            >
              뉴스 이후, 기대는 어떻게 달라졌을까요?
            </h1>
            <p className="mt-4 max-w-xl text-sm leading-6 text-ink-soft sm:text-base sm:leading-7">
              주요 이슈의 기대값이 공개 데이터에서 어느 방향으로 움직였는지
              변화폭과 실제 이력으로 살펴봅니다.
            </p>

            <fieldset className="mt-6">
              <legend className="text-xs font-bold text-ink-faint">
                메인 관측 기간
              </legend>
              <div
                className="mt-2 flex gap-2"
                role="group"
                aria-label="메인 관측 기간"
              >
                {(["24h", "7d"] as const).map((windowKey) => (
                  <button
                    key={windowKey}
                    type="button"
                    onClick={() => changeWindow(windowKey)}
                    aria-pressed={activeWindow === windowKey}
                    className={
                      activeWindow === windowKey
                        ? "inline-flex min-h-11 items-center rounded-full border border-ink bg-ink px-5 text-xs font-bold text-card"
                        : "inline-flex min-h-11 items-center rounded-full border border-line bg-card px-5 text-xs font-bold text-ink-soft transition hover:border-accent hover:text-accent"
                    }
                  >
                    {windowLabel(windowKey)}
                  </button>
                ))}
              </div>
            </fieldset>

            <form onSubmit={submitSearch} className="mt-5 flex gap-2">
              <label className="min-w-0 flex-1">
                <span className="sr-only">메인 이슈 검색</span>
                <input
                  type="search"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="관심 이슈 검색"
                  className="min-h-11 w-full rounded-xl border border-line bg-card px-4 text-sm text-ink outline-none placeholder:text-ink-faint focus:border-accent"
                />
              </label>
              <button
                type="submit"
                className="inline-flex min-h-11 shrink-0 items-center rounded-xl bg-accent px-4 text-xs font-bold text-card"
              >
                검색
              </button>
            </form>

            <ShortCautionNotice
              context="dashboard"
              className="mt-5"
              showMethodologyLink
            />
          </div>

          <div className="min-w-0">
            {status === "loading" ? <FeaturedSkeleton /> : null}
            {status === "empty" ? <FeaturedEmptyState /> : null}
            {featuredIssue ? (
              <FeaturedIssueCard
                issue={featuredIssue}
                windowKey={activeWindow}
                from={from}
              />
            ) : null}
          </div>
        </section>

        {status === "error" ? (
          <div className="mt-5">
            <ErrorState dataAsOf={dataAsOf} />
          </div>
        ) : null}

        {status === "loading" ? <HomeSectionsSkeleton /> : null}
        {status === "empty" ? (
          <div className="mt-7">
            <EmptyState />
          </div>
        ) : null}

        {hasIssues ? (
          <>
            <section className="mt-8" aria-labelledby="direction-summary-title">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <span className="text-xs font-bold text-ink-faint">
                    {windowLabel(activeWindow)} 기준
                  </span>
                  <h2
                    id="direction-summary-title"
                    className="mt-1 text-xl font-extrabold text-ink"
                  >
                    관측 이슈 요약
                  </h2>
                </div>
                <span className="text-xs font-semibold text-ink-faint">
                  데이터 기준 {formatCompactDataTimestamp(dataAsOf)}
                </span>
              </div>

              <div className="mt-4 rounded-2xl border border-line bg-card p-4 sm:p-6">
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <div className="rounded-xl bg-accent-soft p-3">
                    <span className="text-xs font-bold text-accent">
                      ↑ 상향
                    </span>
                    <strong className="mt-2 block text-2xl text-ink">
                      {directionSummary.upwardCount}개
                    </strong>
                  </div>
                  <div className="rounded-xl bg-decline-soft p-3">
                    <span className="text-xs font-bold text-decline">
                      ↓ 하향
                    </span>
                    <strong className="mt-2 block text-2xl text-ink">
                      {directionSummary.downwardCount}개
                    </strong>
                  </div>
                  <div className="rounded-xl bg-line-soft p-3">
                    <span className="text-xs font-bold text-ink-soft">
                      → 변화 없음
                    </span>
                    <strong className="mt-2 block text-2xl text-ink">
                      {directionSummary.unchangedCount}개
                    </strong>
                  </div>
                  <div className="rounded-xl border border-dashed border-line p-3">
                    <span className="text-xs font-bold text-ink-faint">
                      비교 데이터 부족
                    </span>
                    <strong className="mt-2 block text-2xl text-ink">
                      {directionSummary.insufficientCount}개
                    </strong>
                  </div>
                </div>

                <div className="mt-5">
                  <div className="flex items-center justify-between gap-3 text-[11px] font-bold">
                    <span className="text-accent">
                      ↑ {directionSummary.upwardRatio.toFixed(1)}%
                    </span>
                    <span className="text-decline">
                      ↓ {directionSummary.downwardRatio.toFixed(1)}%
                    </span>
                  </div>
                  {directionSummary.directionalCount > 0 ? (
                    <div
                      className="mt-2 flex h-3 overflow-hidden rounded-full bg-line-soft"
                      role="img"
                      aria-label={`방향이 있는 ${directionSummary.directionalCount}개 중 상향 ${directionSummary.upwardRatio.toFixed(1)}%, 하향 ${directionSummary.downwardRatio.toFixed(1)}%`}
                    >
                      <span
                        className="h-full bg-accent"
                        style={{ width: `${directionSummary.upwardRatio}%` }}
                      />
                      <span
                        className="h-full bg-decline"
                        style={{ width: `${directionSummary.downwardRatio}%` }}
                      />
                    </div>
                  ) : (
                    <div className="mt-2 flex h-11 items-center justify-center rounded-xl border border-dashed border-line text-xs text-ink-faint">
                      방향 비율을 계산할 이슈가 없습니다
                    </div>
                  )}
                  <p className="mt-3 text-xs leading-5 text-ink-faint">
                    집계 해석 주의 · 비율의 분모는 상향과 하향 이슈만 사용하며,
                    변화 없음과 비교 데이터 부족은 별도 건수로 표시합니다.
                  </p>
                </div>
              </div>
            </section>

            <section className="mt-8" aria-labelledby="major-issues-title">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <span className="text-xs font-bold text-ink-faint">
                    변화폭 절댓값 순
                  </span>
                  <h2
                    id="major-issues-title"
                    className="mt-1 text-xl font-extrabold text-ink"
                  >
                    주요 변동 이슈
                  </h2>
                </div>
                <Link
                  to={`/issues?window=${activeWindow}&sort=change`}
                  className="inline-flex min-h-11 items-center text-sm font-bold text-accent"
                >
                  전체 이슈 보기 →
                </Link>
              </div>
              {isRefreshing ? (
                <p
                  className="mt-2 text-xs font-semibold text-ink-faint"
                  role="status"
                >
                  마지막 데이터를 유지한 채 목록을 갱신하고 있습니다.
                </p>
              ) : null}
              <div className="mt-4" aria-busy={isRefreshing}>
                <IssueRanking
                  issues={topIssues}
                  windowKey={activeWindow}
                  from={from}
                />
              </div>
            </section>

            <section className="mt-8" aria-labelledby="category-summary-title">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <span className="text-xs font-bold text-ink-faint">
                    {windowLabel(activeWindow)} 단순 평균
                  </span>
                  <h2
                    id="category-summary-title"
                    className="mt-1 text-xl font-extrabold text-ink"
                  >
                    카테고리별 관측 변화
                  </h2>
                </div>
                <span className="text-xs font-semibold text-ink-faint">
                  데이터 기준 {formatCompactDataTimestamp(dataAsOf)}
                </span>
              </div>

              <div className="mt-4 rounded-xl border border-line bg-card px-4 py-3">
                <p className="text-xs font-bold text-ink">집계 해석 주의</p>
                <p className="mt-1 text-xs leading-5 text-ink-soft">
                  카테고리 값은 유효한 이슈 변화값의 단순 산술평균이며, 이슈별
                  활동 수준과 변동성 차이를 별도로 가중하지 않습니다.
                </p>
              </div>

              {categoryState.status === "error" ? (
                <div
                  className="mt-3 rounded-xl border border-line bg-card px-4 py-3"
                  role="status"
                >
                  <p className="text-xs font-bold text-ink">
                    카테고리 집계 갱신을 완료하지 못했습니다
                  </p>
                  <p className="mt-1 text-xs leading-5 text-ink-soft">
                    이전 집계가 있으면 그대로 유지하며, 없으면 수치를 표시하지
                    않습니다.
                  </p>
                </div>
              ) : null}

              <div className="mt-4" aria-busy={categoryState.isRefreshing}>
                {categoryState.status === "loading" && !categoryState.groups ? (
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
                    {Array.from({ length: 5 }).map((_, index) => (
                      <div
                        key={index}
                        className="h-[132px] animate-pulse rounded-xl border border-line bg-card"
                      />
                    ))}
                  </div>
                ) : null}
                {categoryState.status === "empty" ? (
                  <div className="rounded-xl border border-dashed border-line px-5 py-10 text-center text-sm text-ink-soft">
                    표시할 카테고리 집계가 없습니다.
                  </div>
                ) : null}
                {categorySummaries.length > 0 ? (
                  <CategoryCards
                    summaries={categorySummaries}
                    activeWindow={activeWindow}
                  />
                ) : null}
                {categoryState.isRefreshing ? (
                  <p
                    className="mt-3 text-xs font-semibold text-ink-faint"
                    role="status"
                  >
                    이전 집계를 유지한 채 새 데이터를 확인하고 있습니다.
                  </p>
                ) : null}
              </div>
            </section>
          </>
        ) : null}
      </main>

      <GlobalFooter className="mt-10" />
    </div>
  );
}
