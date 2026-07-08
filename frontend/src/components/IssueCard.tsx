import { CautionBadge } from "./CautionBadge";
import { MetricTile } from "./MetricTile";
import {
  formatDataTimestamp,
  formatExpectationValue,
  formatPercentagePointChange,
} from "../utils/format";
import type { Issue } from "../types/issue";

type IssueCardProps = {
  issue: Issue;
  onSelect: (issueId: string) => void;
};

export function IssueCard({ issue, onSelect }: IssueCardProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(issue.id)}
      className="flex h-full flex-col rounded-lg border border-line bg-card p-5 text-left transition hover:border-accent focus-visible:border-accent"
    >
      <div className="flex items-start justify-between gap-3">
        <span className="text-[11px] font-bold uppercase tracking-wider text-ink-faint">
          {issue.category}
        </span>
        <CautionBadge level={issue.cautionLevel} />
      </div>

      <h3 className="mt-3 text-base font-semibold leading-snug text-ink">
        {issue.title}
      </h3>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <MetricTile
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
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <span className="text-xs text-ink-faint">
          Data as of {formatDataTimestamp(issue.dataAsOf)}
        </span>
        <span className="text-xs font-bold text-accent">View analysis</span>
      </div>
    </button>
  );
}
