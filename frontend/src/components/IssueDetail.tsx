import { useMemo, useState } from "react";
import { CautionBadge } from "./CautionBadge";
import { CAUTION_COPY } from "./cautionCopy";
import { IssueTrendChart } from "./IssueTrendChart";
import { MetricTile } from "./MetricTile";
import {
  formatDataTimestamp,
  formatExpectationValue,
  formatPercentagePointChange,
  formatShortDate,
  windowLabel,
} from "../utils/format";
import type { ChartWindow, DataStatus, Issue } from "../types/issue";

type IssueDetailProps = {
  issue: Issue;
  dataStatus?: DataStatus;
  onBack: () => void;
};

const CHART_WINDOWS: ChartWindow[] = ["24h", "7d", "30d"];

function changeForWindow(
  issue: Issue,
  chartWindow: ChartWindow,
): number | null | undefined {
  if (chartWindow === "24h") {
    return issue.change24h;
  }

  if (chartWindow === "7d") {
    return issue.change7d;
  }

  return issue.change30d ?? issue.change7d;
}

function buildSummary(issue: Issue, chartWindow: ChartWindow): string {
  const change = changeForWindow(issue, chartWindow);
  const movementSentence =
    change === null || change === undefined || Number.isNaN(change)
      ? `does not have enough reference data for a ${windowLabel(
          chartWindow,
        )} change calculation`
      : `${
          Math.abs(change) < 0.05
            ? "held near its prior reading"
            : change > 0
              ? "moved upward"
              : "moved downward"
        } by ${formatPercentagePointChange(change)}`;
  const marker = issue.inflectionPoints[0];
  const markerSentence = marker
    ? `The largest threshold marker in the stored history appears on ${formatShortDate(
        marker.timestamp,
      )}, with an observed change of ${formatPercentagePointChange(marker.change)}.`
    : "No threshold marker is present in the stored history.";
  const relatedSentence = issue.relatedEventCandidates?.length
    ? "Related event candidates are listed for context only and are not presented as causes."
    : "No related event candidate is listed for this issue.";

  return `Over the past ${windowLabel(
    chartWindow,
  )}, the reflected expectation value ${movementSentence} in Polymarket public data. ${markerSentence} ${relatedSentence} ${
    CAUTION_COPY[issue.cautionLevel].detail
  }`;
}

export function IssueDetail({ issue, dataStatus = "ready", onBack }: IssueDetailProps) {
  const [chartWindow, setChartWindow] = useState<ChartWindow>("7d");

  const summary = useMemo(
    () => buildSummary(issue, chartWindow),
    [issue, chartWindow],
  );

  return (
    <div className="mx-auto min-h-screen w-full max-w-[1180px] px-4 py-6 sm:px-8 lg:px-10 lg:py-10">
      <button
        type="button"
        onClick={onBack}
        className="text-sm font-semibold text-ink-soft transition hover:text-accent"
      >
        Back to dashboard
      </button>

      <header className="mt-5">
        {dataStatus === "error" ? (
          <div className="mb-4 rounded-lg border border-line bg-card px-4 py-3">
            <h2 className="text-sm font-bold text-ink">Showing last available data</h2>
            <p className="mt-1 text-sm leading-6 text-ink-soft">
              The latest refresh did not complete. This detail view uses the same
              fallback issue set shown on the dashboard.
            </p>
          </div>
        ) : null}

        <div className="flex flex-wrap items-center gap-3">
          <span className="text-[11px] font-bold uppercase tracking-wider text-ink-faint">
            {issue.category}
          </span>
          <CautionBadge level={issue.cautionLevel} />
        </div>
        <h1 className="mt-3 max-w-4xl text-3xl font-bold tracking-tight text-ink">
          {issue.title}
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-ink-soft">
          {issue.description}
        </p>
        <p className="mt-2 text-xs text-ink-faint">
          Data as of {formatDataTimestamp(issue.dataAsOf)}
        </p>
      </header>

      <section className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-4">
        <MetricTile
          primary
          label="Reflected expectation value"
          value={formatExpectationValue(issue.currentExpectationValue)}
        />
        <MetricTile
          label="24h observed change"
          value={formatPercentagePointChange(issue.change24h)}
        />
        <MetricTile
          label="7d observed change"
          value={formatPercentagePointChange(issue.change7d)}
        />
        <MetricTile
          label="30d observed change"
          value={formatPercentagePointChange(issue.change30d ?? issue.change7d)}
        />
      </section>

      <section className="mt-4 rounded-lg border border-line bg-card px-4 py-3">
        <CautionBadge level={issue.cautionLevel} withDetail />
        <p className="mt-2 text-sm leading-6 text-ink-soft">
          This value reflects public data activity, not a certified fact about a
          real-world outcome. Data may be incomplete or volatile.
        </p>
      </section>

      <section className="mt-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h2 className="text-lg font-bold text-ink">
            Reflected expectation value over time
          </h2>
          <div className="flex gap-2" aria-label="Chart window">
            {CHART_WINDOWS.map((windowOption) => (
              <button
                key={windowOption}
                type="button"
                onClick={() => setChartWindow(windowOption)}
                className={
                  chartWindow === windowOption
                    ? "rounded-full border border-ink bg-ink px-3 py-1.5 text-xs font-bold text-card"
                    : "rounded-full border border-line px-3 py-1.5 text-xs font-bold text-ink-soft transition hover:border-accent hover:text-accent"
                }
              >
                {windowOption}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-3">
          <IssueTrendChart issue={issue} windowKey={chartWindow} />
        </div>
      </section>

      <section className="mt-10">
        <h2 className="text-lg font-bold text-ink">Related event candidates</h2>
        <p className="mt-1 text-sm leading-6 text-ink-faint">
          Manually curated context to review alongside observed change; not
          presented as causes.
        </p>

        {issue.relatedEventCandidates?.length ? (
          <div className="mt-4 space-y-3">
            {issue.relatedEventCandidates.map((event) => (
              <article
                key={`${event.date}-${event.title}`}
                className="rounded-lg border border-line bg-card px-4 py-3"
              >
                <div className="text-xs font-semibold text-ink-faint">
                  {formatShortDate(event.date)}
                </div>
                <h3 className="mt-1 text-sm font-bold text-ink">{event.title}</h3>
                <p className="mt-1 text-sm leading-6 text-ink-soft">{event.note}</p>
              </article>
            ))}
          </div>
        ) : (
          <p className="mt-4 rounded-lg border border-dashed border-line px-4 py-4 text-sm text-ink-faint">
            No related event candidate has been identified for this issue.
          </p>
        )}
      </section>

      <section className="mt-10 rounded-lg border border-line bg-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-bold text-ink">Issue summary</h2>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-ink-faint">
            Template-based data summary
          </span>
        </div>
        <p className="mt-4 max-w-4xl text-sm leading-7 text-ink">{summary}</p>
        <p className="mt-4 border-t border-line-soft pt-3 text-xs leading-6 text-ink-faint">
          This summary is generated from the dummy data contract and may contain
          incomplete context. It is not advice of any kind.
        </p>
      </section>

      <footer className="mt-10 border-t border-line pt-5 text-xs leading-6 text-ink-faint">
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
