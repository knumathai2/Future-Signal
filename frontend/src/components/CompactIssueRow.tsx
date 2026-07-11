import { Link } from "react-router-dom";
import { CautionBadge } from "./CautionBadge";
import type { ChartWindow, Issue } from "../types/issue";
import {
  formatCategoryLabel,
  formatExpectationValue,
  formatPercentagePointChange,
  issueChangeForWindow,
  windowLabel,
} from "../utils/format";

type CompactIssueRowProps = {
  issue: Issue;
  windowKey: Extract<ChartWindow, "24h" | "7d">;
  from: string;
};

/** A compact, semantic list row with a short accessible link name. */
export function CompactIssueRow({
  issue,
  windowKey,
  from,
}: CompactIssueRowProps) {
  return (
    <li className="border-b border-line-soft bg-card transition last:border-b-0 hover:bg-accent-soft">
      <article className="grid min-h-[112px] gap-3 px-4 py-3 sm:min-h-0 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center sm:py-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-bold text-ink-faint">
              {issue.topicLabel ?? formatCategoryLabel(issue.category)}
            </span>
            <CautionBadge level={issue.cautionLevel} />
          </div>
          <h3 className="mt-2 text-sm font-bold leading-5 text-ink">
            <Link
              to={`/issues/${encodeURIComponent(issue.id)}`}
              state={{ from }}
              className="inline-flex min-h-11 items-center rounded-sm hover:text-accent"
            >
              {issue.title}
            </Link>
          </h3>
          {issue.displaySubtitle ? (
            <p className="mt-1 line-clamp-1 text-xs leading-5 text-ink-soft">
              {issue.displaySubtitle}
            </p>
          ) : null}
        </div>

        <dl className="grid grid-cols-2 gap-4 sm:min-w-[220px] sm:text-right">
          <div>
            <dt className="text-[11px] font-semibold text-ink-faint">
              현재 기대값
            </dt>
            <dd className="mt-1 text-lg font-extrabold text-accent">
              {formatExpectationValue(issue.currentExpectationValue)}
            </dd>
          </div>
          <div>
            <dt className="text-[11px] font-semibold text-ink-faint">
              {windowLabel(windowKey)} 변화
            </dt>
            <dd className="mt-1 text-lg font-extrabold text-comparison">
              {formatPercentagePointChange(
                issueChangeForWindow(issue, windowKey),
              )}
            </dd>
          </div>
        </dl>
      </article>
    </li>
  );
}
