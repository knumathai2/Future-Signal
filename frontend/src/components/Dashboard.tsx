import { CautionBadge } from "./CautionBadge";
import { IssueCard } from "./IssueCard";
import {
  formatCategoryLabel,
  formatDataTimestamp,
  formatPercentagePointChange,
  windowLabel,
} from "../utils/format";
import type { DataStatus, Issue } from "../types/issue";

type DashboardProps = {
  issues: Issue[];
  status: DataStatus;
  dataAsOf: string;
  staleDataAsOf: string;
  onIssueSelect: (issueId: string) => void;
  onRefresh: () => void;
  categories: string[];
  activeCategory: string | null;
  onCategoryChange: (category: string | null) => void;
  activeWindow: "24h" | "7d";
  onWindowChange: (window: "24h" | "7d") => void;
  activeSort: "heat" | "change" | "recent";
  onSortChange: (sort: "heat" | "change" | "recent") => void;
};

function DashboardSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {Array.from({ length: 6 }).map((_, index) => (
        <div key={index} className="rounded-lg border border-line bg-card p-5">
          <div className="h-3 w-2/5 animate-pulse rounded bg-line-soft" />
          <div className="mt-4 h-4 w-4/5 animate-pulse rounded bg-line-soft" />
          <div className="mt-5 grid grid-cols-3 gap-3">
            <div className="h-14 animate-pulse rounded-lg bg-line-soft" />
            <div className="h-14 animate-pulse rounded-lg bg-line-soft" />
            <div className="h-14 animate-pulse rounded-lg bg-line-soft" />
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-lg border border-dashed border-line px-6 py-14 text-center">
      <h3 className="text-base font-bold text-ink">표시할 이슈가 아직 없습니다</h3>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-ink-soft">
        선택한 필터에 해당하는 데이터가 비어 있습니다. 이슈 기록이 준비되면
        대시보드에 표시됩니다.
      </p>
    </div>
  );
}

function ErrorState({ staleDataAsOf }: { staleDataAsOf: string }) {
  return (
    <div className="mb-4 rounded-lg border border-line bg-card px-5 py-4">
      <h3 className="text-base font-bold text-ink">
        마지막으로 확인 가능한 데이터를 표시합니다
      </h3>
      <p className="mt-1 text-sm leading-6 text-ink-soft">
        최신 새로고침이 완료되지 않아 {formatDataTimestamp(staleDataAsOf)} 기준의
        마지막 이슈 목록을 표시합니다.
      </p>
    </div>
  );
}

function sortLabel(sortOption: "heat" | "change" | "recent"): string {
  if (sortOption === "heat") {
    return "재평가 강도";
  }

  if (sortOption === "change") {
    return "변화 폭";
  }

  return "최근 기준";
}

function absoluteChangeValue(value: number | null | undefined): number {
  return value === null || value === undefined ? -1 : Math.abs(value);
}

export function Dashboard({
  issues,
  status,
  dataAsOf,
  staleDataAsOf,
  onIssueSelect,
  onRefresh,
  categories,
  activeCategory,
  onCategoryChange,
  activeWindow,
  onWindowChange,
  activeSort,
  onSortChange,
}: DashboardProps) {
  const topReassessedIssues = issues;

  const weeklyRows = [...issues]
    .sort(
      (left, right) =>
        absoluteChangeValue(right.change7d) - absoluteChangeValue(left.change7d),
    )
    .slice(0, 5);

  const shouldShowIssueLists =
    (status === "ready" || status === "error") && topReassessedIssues.length > 0;

  return (
    <div className="mx-auto min-h-screen w-full max-w-[1180px] px-4 py-6 sm:px-8 lg:px-10 lg:py-10">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-line pb-5">
        <div className="flex items-center gap-2">
          <svg aria-hidden="true" viewBox="0 0 20 20" className="h-5 w-5">
            <rect x="2" y="10" width="4" height="8" fill="oklch(52% 0.13 45)" />
            <rect x="8" y="5" width="4" height="13" fill="oklch(22% 0.02 55)" />
            <rect x="14" y="1" width="4" height="17" fill="oklch(52% 0.13 45)" />
          </svg>
          <span className="text-xl font-extrabold">Outlook Signals</span>
        </div>

        <div className="flex flex-wrap items-center gap-4 text-sm">
          <a className="text-ink-soft hover:text-accent" href="#information-note">
            정보 안내
          </a>
          <span className="text-xs text-ink-faint">
            데이터 기준 시각: {formatDataTimestamp(dataAsOf)}
          </span>
          <button
            type="button"
            onClick={onRefresh}
            className="rounded-full border border-line px-3 py-1.5 text-xs font-bold text-ink-soft transition hover:border-accent hover:text-accent"
          >
            데이터 새로고침
          </button>
        </div>
      </header>

      <section className="mt-8">
        <h1 className="max-w-3xl text-3xl font-bold text-ink">
          최근 관측된 재평가가 큰 이슈
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-ink-soft">
          Polymarket 공개 데이터에 반영된 기대값이 주요 이슈에서 어떻게 달라졌는지
          관찰할 수 있습니다.
        </p>
      </section>

      <section className="mt-5 rounded-lg border border-line bg-card px-4 py-3">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-accent text-xs font-bold text-accent">
            i
          </div>
          <div>
            <CautionBadge level="sufficient" />
            <p className="mt-2 text-sm leading-6 text-ink-soft">
              수치는 Polymarket 공개 데이터에 반영된 기대값이며 실제 사건에 대한
              확정 사실이 아닙니다. 해석에 주의가 필요합니다.
            </p>
          </div>
        </div>
      </section>

      {/* Filters */}
      <section className="mt-8 flex flex-col gap-4 border-b border-line-soft pb-5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="mr-2 text-xs font-semibold text-ink-faint">분류:</span>
          <button
            type="button"
            onClick={() => onCategoryChange(null)}
            className={`rounded-full px-3 py-1.5 text-xs font-bold transition ${
              activeCategory === null
                ? "bg-ink text-card border border-ink"
                : "bg-card text-ink-soft border border-line hover:border-accent hover:text-accent"
              }`}
          >
            전체
          </button>
          {categories.map((category) => (
            <button
              key={category}
              type="button"
              onClick={() => onCategoryChange(category)}
              className={`rounded-full px-3 py-1.5 text-xs font-bold transition ${
                activeCategory === category
                  ? "bg-ink text-card border border-ink"
                  : "bg-card text-ink-soft border border-line hover:border-accent hover:text-accent"
              }`}
            >
              {formatCategoryLabel(category)}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4 mt-2">
          <div className="flex items-center gap-2">
            <span className="text-xs text-ink-faint">정렬:</span>
            <div className="inline-flex rounded-lg border border-line p-0.5 bg-card">
              {(["heat", "change", "recent"] as const).map((sortOption) => (
                <button
                  key={sortOption}
                  type="button"
                  onClick={() => onSortChange(sortOption)}
                  className={`rounded-md px-3 py-1.5 text-xs font-bold transition ${
                    activeSort === sortOption
                      ? "bg-line-soft text-ink font-extrabold"
                      : "text-ink-soft hover:text-accent"
                  }`}
                >
                  {sortLabel(sortOption)}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-ink-faint">기간:</span>
            <div className="inline-flex rounded-lg border border-line p-0.5 bg-card">
              {(["24h", "7d"] as const).map((windowOption) => (
                <button
                  key={windowOption}
                  type="button"
                  onClick={() => onWindowChange(windowOption)}
                  className={`rounded-md px-3 py-1.5 text-xs font-bold transition ${
                    activeWindow === windowOption
                      ? "bg-line-soft text-ink font-extrabold"
                      : "text-ink-soft hover:text-accent"
                  }`}
                >
                  {windowLabel(windowOption)}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mt-8">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-lg font-bold text-ink">
            {windowLabel(activeWindow)} 기준 관측 변화가 큰 이슈
          </h2>
        </div>

        <div className="mt-4">
          {status === "loading" ? <DashboardSkeleton /> : null}
          {status === "empty" ? <EmptyState /> : null}
          {status === "error" ? <ErrorState staleDataAsOf={staleDataAsOf} /> : null}
          {shouldShowIssueLists ? (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {topReassessedIssues.map((issue) => (
                <IssueCard
                  key={issue.id}
                  issue={issue}
                  onSelect={onIssueSelect}
                />
              ))}
            </div>
          ) : null}
        </div>
      </section>

      {shouldShowIssueLists ? (
        <section className="mt-10">
          <h2 className="text-lg font-bold text-ink">이번 주 관측 변화</h2>
          <div className="mt-4 overflow-hidden rounded-lg border border-line">
            {weeklyRows.map((issue) => (
              <button
                key={issue.id}
                type="button"
                onClick={() => onIssueSelect(issue.id)}
                className="flex w-full flex-col gap-3 border-b border-line-soft bg-card px-4 py-4 text-left last:border-b-0 transition hover:bg-line-soft sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:gap-3">
                  <span className="text-[11px] font-bold text-ink-faint">
                    {formatCategoryLabel(issue.category)}
                  </span>
                  <span className="text-sm font-semibold text-ink">{issue.title}</span>
                </div>
                <div className="flex items-center gap-4">
                  <CautionBadge level={issue.cautionLevel} />
                  <span className="text-sm font-bold text-ink">
                    {formatPercentagePointChange(issue.change7d)}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </section>
      ) : null}

      <footer
        id="information-note"
        className="mt-10 border-t border-line pt-5 text-xs leading-6 text-ink-faint"
      >
        <p className="max-w-3xl">
          Outlook Signals는 공개 데이터 기반의 정보 분석 및 이슈 관찰 서비스입니다.
          금융, 법률, 정치 또는 그 밖의 전문적 조언을 제공하지 않습니다.
        </p>
        <p className="mt-2 max-w-3xl">
          이 지표는 Polymarket 공개 데이터에 반영된 기대값의 변화를 보여줍니다.
          전체 대중의 판단을 대표하지 않으며, 데이터 활동 수준과 변동성에 따라
          해석에 주의가 필요합니다.
        </p>
      </footer>
    </div>
  );
}
