import { useEffect, useMemo, useState } from "react";
import { useLocation, useSearchParams } from "react-router-dom";
import { SiteHeader } from "./AppShell";
import { CompactIssueRow } from "./CompactIssueRow";
import { GlobalFooter, ShortCautionNotice } from "./InformationNotice";
import { useIssueList } from "../hooks/useIssueList";
import type { IssueListSort } from "../types/issue";
import { formatCategoryLabel, windowLabel } from "../utils/format";
import {
  parseForcedStatus,
  parseListSort,
  parseListWindow,
  parsePage,
} from "../utils/routeState";

type IssueListPageProps = { categories: string[] };

const PAGE_SIZE = 10;
const ACTIVE_FILTER_CLASS =
  "inline-flex min-h-11 items-center rounded-full border border-accent bg-accent-soft px-4 text-xs font-bold text-accent";
const INACTIVE_FILTER_CLASS =
  "inline-flex min-h-11 items-center rounded-full border border-line bg-card px-4 text-xs font-bold text-ink-soft transition hover:border-accent hover:text-accent";

function sortLabel(sort: IssueListSort): string {
  if (sort === "change") {
    return "변화 폭";
  }
  if (sort === "recent") {
    return "최근 기준";
  }
  return "재평가 강도";
}

function normalizeSearchValue(value: string): string {
  return value.trim().toLocaleLowerCase("ko-KR");
}

function ListSkeleton() {
  return (
    <div
      className="overflow-hidden rounded-xl border border-line"
      aria-label="목록 로딩 중"
    >
      {Array.from({ length: 6 }).map((_, index) => (
        <div
          key={index}
          className="h-24 animate-pulse border-b border-line-soft bg-line-soft last:border-b-0"
        />
      ))}
    </div>
  );
}

function EmptyResults({ hasSearch }: { hasSearch: boolean }) {
  return (
    <div className="rounded-xl border border-dashed border-line px-6 py-12 text-center">
      <h2 className="text-base font-bold text-ink">
        {hasSearch
          ? "검색 조건에 맞는 이슈가 없습니다"
          : "표시할 이슈가 없습니다"}
      </h2>
      <p className="mt-2 text-sm leading-6 text-ink-soft">
        {hasSearch
          ? "검색어 또는 필터를 조정해 다시 확인해 주세요."
          : "선택한 분류의 이슈 기록이 준비되면 목록에 표시합니다."}
      </p>
    </div>
  );
}

function ErrorState() {
  return (
    <div
      className="rounded-lg border border-line bg-card px-4 py-3"
      role="status"
    >
      <h2 className="text-sm font-bold text-ink">
        마지막으로 확인 가능한 목록을 유지합니다
      </h2>
      <p className="mt-1 text-xs leading-5 text-ink-soft">
        최신 갱신이 완료되지 않았습니다. 화면의 기준 시각과 해석 주의를 함께
        확인해 주세요.
      </p>
    </div>
  );
}

/** Searchable and shareable full issue-list route. */
export function IssueListPage({ categories }: IssueListPageProps) {
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [filtersOpen, setFiltersOpen] = useState(false);

  const query = searchParams.get("q") ?? "";
  const activeCategory = searchParams.get("category") ?? "";
  const activeWindow = parseListWindow(searchParams.get("window"));
  const activeSort = parseListSort(searchParams.get("sort"));
  const requestedPage = parsePage(searchParams.get("page"));
  const forcedStatus = parseForcedStatus(searchParams);
  const { issues, status, isRefreshing, dataAsOf, refresh } = useIssueList({
    windowKey: activeWindow,
    sort: activeSort,
    category: activeCategory || undefined,
    forcedStatus,
  });

  useEffect(() => {
    const normalized = new URLSearchParams(searchParams);
    let changed = false;
    const rawWindow = searchParams.get("window");
    const rawSort = searchParams.get("sort");
    const rawPage = searchParams.get("page");

    if (rawWindow && rawWindow !== "24h" && rawWindow !== "7d") {
      normalized.delete("window");
      changed = true;
    }
    if (
      rawSort &&
      !(["heat", "change", "recent"] as string[]).includes(rawSort)
    ) {
      normalized.delete("sort");
      changed = true;
    }
    if (rawPage && (!/^\d+$/.test(rawPage) || Number(rawPage) < 1)) {
      normalized.delete("page");
      changed = true;
    }
    if (
      activeCategory &&
      categories.length > 0 &&
      !categories.map(formatCategoryLabel).includes(activeCategory)
    ) {
      normalized.delete("category");
      normalized.delete("page");
      changed = true;
    }

    if (changed) {
      setSearchParams(normalized, { replace: true });
    }
  }, [activeCategory, categories, searchParams, setSearchParams]);

  const normalizedQuery = normalizeSearchValue(query);
  const matchingIssues = useMemo(() => {
    if (!normalizedQuery) {
      return issues;
    }

    return issues.filter((issue) =>
      [
        issue.title,
        issue.displaySubtitle ?? "",
        issue.topicLabel ?? "",
        formatCategoryLabel(issue.category),
      ]
        .map(normalizeSearchValue)
        .some((value) => value.includes(normalizedQuery)),
    );
  }, [issues, normalizedQuery]);

  const pageCount = Math.max(1, Math.ceil(matchingIssues.length / PAGE_SIZE));
  const activePage =
    status === "loading" ? requestedPage : Math.min(requestedPage, pageCount);
  const visibleIssues = matchingIssues.slice(
    (activePage - 1) * PAGE_SIZE,
    activePage * PAGE_SIZE,
  );
  const from = `${location.pathname}${location.search}`;

  useEffect(() => {
    if (status === "loading" || requestedPage === activePage) {
      return;
    }
    const next = new URLSearchParams(searchParams);
    if (activePage === 1) {
      next.delete("page");
    } else {
      next.set("page", String(activePage));
    }
    setSearchParams(next, { replace: true });
  }, [activePage, requestedPage, searchParams, setSearchParams, status]);

  function updateParam(
    key: "q" | "category" | "window" | "sort" | "page",
    value: string,
    replace = false,
  ) {
    const next = new URLSearchParams(searchParams);
    if (
      !value ||
      (key === "window" && value === "24h") ||
      (key === "sort" && value === "heat")
    ) {
      next.delete(key);
    } else {
      next.set(key, value);
    }
    if (key !== "page") {
      next.delete("page");
    }
    setSearchParams(next, { replace });
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
        aria-labelledby="issues-title"
        className="outline-none"
      >
        <section className="mt-6">
          <div className="flex items-center gap-3">
            <span
              aria-hidden="true"
              className="h-8 w-1 rounded-full bg-accent"
            />
            <h1
              id="issues-title"
              className="text-2xl font-bold text-ink sm:text-3xl"
            >
              전체 이슈
            </h1>
          </div>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-ink-soft">
            현재 관찰 중인 이슈를 검색하고 기간·분류·정렬 기준으로 살펴봅니다.
          </p>
        </section>

        <ShortCautionNotice
          context="dashboard"
          className="mt-4"
          showMethodologyLink
        />

        <section className="mt-5" aria-labelledby="issue-search-title">
          <h2 id="issue-search-title" className="sr-only">
            이슈 검색과 필터
          </h2>
          <div className="flex gap-2">
            <label className="min-w-0 flex-1">
              <span className="sr-only">이슈 검색</span>
              <input
                type="search"
                value={query}
                onChange={(event) => updateParam("q", event.target.value, true)}
                placeholder="이슈 검색"
                className="min-h-11 w-full rounded-xl border border-line bg-card px-4 text-sm text-ink outline-none transition placeholder:text-ink-faint focus:border-accent focus:ring-2 focus:ring-accent-soft"
              />
            </label>
            <button
              type="button"
              onClick={() => setFiltersOpen((value) => !value)}
              aria-expanded={filtersOpen}
              aria-controls="issue-filters"
              className="inline-flex min-h-11 items-center rounded-xl border border-accent bg-accent-soft px-4 text-xs font-bold text-accent md:hidden"
            >
              필터
            </button>
          </div>

          <div
            id="issue-filters"
            className={`${filtersOpen ? "mt-4 block" : "hidden"} rounded-xl border border-line bg-card p-4 md:mt-4 md:block`}
          >
            <fieldset>
              <legend className="text-xs font-bold text-ink-faint">
                카테고리
              </legend>
              <div
                className="mt-2 flex flex-wrap gap-2"
                role="group"
                aria-label="카테고리 필터"
              >
                <button
                  type="button"
                  onClick={() => updateParam("category", "")}
                  aria-pressed={!activeCategory}
                  className={
                    !activeCategory
                      ? ACTIVE_FILTER_CLASS
                      : INACTIVE_FILTER_CLASS
                  }
                >
                  전체
                </button>
                {categories.map((category) => {
                  const label = formatCategoryLabel(category);
                  return (
                    <button
                      key={category}
                      type="button"
                      onClick={() => updateParam("category", label)}
                      aria-pressed={activeCategory === label}
                      className={
                        activeCategory === label
                          ? ACTIVE_FILTER_CLASS
                          : INACTIVE_FILTER_CLASS
                      }
                    >
                      {label}
                    </button>
                  );
                })}
              </div>
            </fieldset>

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <fieldset>
                <legend className="text-xs font-bold text-ink-faint">
                  기간
                </legend>
                <div
                  className="mt-2 flex gap-2"
                  role="group"
                  aria-label="기간 필터"
                >
                  {(["24h", "7d"] as const).map((windowKey) => (
                    <button
                      key={windowKey}
                      type="button"
                      onClick={() => updateParam("window", windowKey)}
                      aria-pressed={activeWindow === windowKey}
                      className={
                        activeWindow === windowKey
                          ? ACTIVE_FILTER_CLASS
                          : INACTIVE_FILTER_CLASS
                      }
                    >
                      {windowLabel(windowKey)}
                    </button>
                  ))}
                </div>
              </fieldset>

              <fieldset>
                <legend className="text-xs font-bold text-ink-faint">
                  정렬
                </legend>
                <div
                  className="mt-2 flex flex-wrap gap-2"
                  role="group"
                  aria-label="정렬 기준"
                >
                  {(["heat", "change", "recent"] as const).map((sort) => (
                    <button
                      key={sort}
                      type="button"
                      onClick={() => updateParam("sort", sort)}
                      aria-pressed={activeSort === sort}
                      className={
                        activeSort === sort
                          ? ACTIVE_FILTER_CLASS
                          : INACTIVE_FILTER_CLASS
                      }
                    >
                      {sortLabel(sort)}
                    </button>
                  ))}
                </div>
              </fieldset>
            </div>
          </div>
        </section>

        <section className="mt-6" aria-labelledby="issue-results-title">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 id="issue-results-title" className="text-lg font-bold text-ink">
              검색 결과
            </h2>
            <p
              className="rounded-full bg-accent-soft px-3 py-1.5 text-sm font-bold text-accent"
              aria-live="polite"
            >
              {matchingIssues.length}개 이슈
              {isRefreshing ? " · 목록 갱신 중" : ""}
            </p>
          </div>

          {status === "error" ? (
            <div className="mt-3">
              <ErrorState />
            </div>
          ) : null}

          <div className="mt-3" aria-busy={isRefreshing}>
            {status === "loading" ? <ListSkeleton /> : null}
            {status !== "loading" && visibleIssues.length === 0 ? (
              <EmptyResults hasSearch={Boolean(query || activeCategory)} />
            ) : null}
            {visibleIssues.length > 0 ? (
              <ul className="overflow-hidden rounded-xl border border-line">
                {visibleIssues.map((issue) => (
                  <CompactIssueRow
                    key={issue.id}
                    issue={issue}
                    windowKey={activeWindow}
                    from={from}
                  />
                ))}
              </ul>
            ) : null}
          </div>

          {matchingIssues.length > PAGE_SIZE ? (
            <nav
              className="mt-5 flex flex-wrap items-center justify-center gap-1"
              aria-label="검색 결과 페이지"
            >
              <button
                type="button"
                onClick={() => updateParam("page", String(activePage - 1))}
                disabled={activePage === 1}
                className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-full border border-line px-3 text-xs font-bold text-ink-soft disabled:cursor-not-allowed disabled:opacity-40"
                aria-label="이전 페이지"
              >
                ←
              </button>
              {Array.from({ length: pageCount }, (_, index) => index + 1).map(
                (page) => (
                  <button
                    key={page}
                    type="button"
                    onClick={() =>
                      updateParam("page", page === 1 ? "" : String(page))
                    }
                    aria-current={page === activePage ? "page" : undefined}
                    className={
                      page === activePage
                        ? "inline-flex min-h-11 min-w-11 items-center justify-center rounded-full bg-accent text-xs font-bold text-card"
                        : "inline-flex min-h-11 min-w-11 items-center justify-center rounded-full border border-line text-xs font-bold text-ink-soft hover:border-accent hover:text-accent"
                    }
                  >
                    {page}
                  </button>
                ),
              )}
              <button
                type="button"
                onClick={() => updateParam("page", String(activePage + 1))}
                disabled={activePage === pageCount}
                className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-full border border-line px-3 text-xs font-bold text-ink-soft disabled:cursor-not-allowed disabled:opacity-40"
                aria-label="다음 페이지"
              >
                →
              </button>
            </nav>
          ) : null}
        </section>
      </main>

      <GlobalFooter className="mt-8" />
    </div>
  );
}
