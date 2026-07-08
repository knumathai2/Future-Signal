import { CautionBadge } from "./CautionBadge";
import { IssueCard } from "./IssueCard";
import {
  formatDataTimestamp,
  formatPercentagePointChange,
} from "../utils/format";
import type { DataStatus, Issue } from "../types/issue";

type DashboardProps = {
  issues: Issue[];
  status: DataStatus;
  dataAsOf: string;
  staleDataAsOf: string;
  onIssueSelect: (issueId: string) => void;
  onRefresh: () => void;
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
      <h3 className="text-base font-bold text-ink">No issues are available yet</h3>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-ink-soft">
        The dummy data source is empty. Once issue records are available, the
        dashboard will rank them by observed change.
      </p>
    </div>
  );
}

function ErrorState({ staleDataAsOf }: { staleDataAsOf: string }) {
  return (
    <div className="mb-4 rounded-lg border border-line bg-card px-5 py-4">
      <h3 className="text-base font-bold text-ink">Showing last available data</h3>
      <p className="mt-1 text-sm leading-6 text-ink-soft">
        The latest refresh did not complete. Displaying the last available
        issue set from {formatDataTimestamp(staleDataAsOf)}.
      </p>
    </div>
  );
}

export function Dashboard({
  issues,
  status,
  dataAsOf,
  staleDataAsOf,
  onIssueSelect,
  onRefresh,
}: DashboardProps) {
  const topReassessedIssues = [...issues].sort(
    (left, right) => Math.abs(right.change24h) - Math.abs(left.change24h),
  );

  const weeklyRows = [...issues]
    .sort((left, right) => Math.abs(right.change7d) - Math.abs(left.change7d))
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
          <span className="text-xl font-extrabold tracking-tight">Outlook Signals</span>
        </div>

        <div className="flex flex-wrap items-center gap-4 text-sm">
          <a className="text-ink-soft hover:text-accent" href="#information-note">
            Information note
          </a>
          <span className="text-xs text-ink-faint">
            Data as of {formatDataTimestamp(dataAsOf)}
          </span>
          <button
            type="button"
            onClick={onRefresh}
            className="rounded-full border border-line px-3 py-1.5 text-xs font-bold text-ink-soft transition hover:border-accent hover:text-accent"
          >
            Refresh data
          </button>
        </div>
      </header>

      <section className="mt-8">
        <h1 className="max-w-3xl text-3xl font-bold tracking-tight text-ink">
          Today's most reassessed issues
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-ink-soft">
          See how the reflected expectation value has shifted on major global
          issues, based on Polymarket public data.
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
              Figures reflect Polymarket public data, not certified facts about
              real-world outcomes. Interpretation requires caution.
            </p>
          </div>
        </div>
      </section>

      <section className="mt-8">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-lg font-bold text-ink">Largest 24-hour shifts</h2>
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
          <h2 className="text-lg font-bold text-ink">Notable shifts this week</h2>
          <div className="mt-4 overflow-hidden rounded-lg border border-line">
            {weeklyRows.map((issue) => (
              <button
                key={issue.id}
                type="button"
                onClick={() => onIssueSelect(issue.id)}
                className="flex w-full flex-col gap-3 border-b border-line-soft bg-card px-4 py-4 text-left last:border-b-0 transition hover:bg-line-soft sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:gap-3">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-ink-faint">
                    {issue.category}
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
          Outlook Signals is an information analysis and issue-monitoring
          service. It does not provide financial, legal, political, or other
          professional advice.
        </p>
        <p className="mt-2 max-w-3xl">
          This indicator reflects changing expectations in Polymarket public
          data. It does not represent the judgment of the public at large, and
          interpretation requires caution depending on data activity level and
          volatility.
        </p>
      </footer>
    </div>
  );
}
