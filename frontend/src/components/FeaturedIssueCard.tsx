import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { CautionBadge } from "./CautionBadge";
import type { ApiIssueHistoryResponse } from "../utils/format";
import type { ChartWindow, Issue, IssueHistoryPoint } from "../types/issue";
import { fetchJson } from "../utils/api";
import {
  formatCategoryLabel,
  formatCompactDataTimestamp,
  formatDataTimestamp,
  formatExpectationValue,
  formatPercentagePointChange,
  issueChangeForWindow,
  windowLabel,
} from "../utils/format";

type FeaturedIssueCardProps = {
  issue: Issue;
  windowKey: Extract<ChartWindow, "24h" | "7d">;
  from: string;
};

type TrendStatus = "loading" | "ready" | "empty";

function Sparkline({ points }: { points: IssueHistoryPoint[] }) {
  const polyline = useMemo(() => {
    if (points.length < 2) {
      return "";
    }

    const values = points.map((point) => point.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = Math.max(1, max - min);

    return points
      .map((point, index) => {
        const x = (index / (points.length - 1)) * 180;
        const y = 62 - ((point.value - min) / range) * 52;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
  }, [points]);

  if (!polyline) {
    return null;
  }

  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 180 72"
      preserveAspectRatio="none"
      className="h-16 w-full"
    >
      <path d="M0 66 H180" stroke="oklch(93% 0.01 65)" strokeWidth="1" />
      <polyline
        points={polyline}
        fill="none"
        stroke="oklch(52% 0.13 45)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** Featured issue with a non-blocking compact history preview. */
export function FeaturedIssueCard({
  issue,
  windowKey,
  from,
}: FeaturedIssueCardProps) {
  const [trendStatus, setTrendStatus] = useState<TrendStatus>("loading");
  const [history, setHistory] = useState<IssueHistoryPoint[]>([]);

  useEffect(() => {
    const controller = new AbortController();
    setTrendStatus("loading");
    setHistory([]);

    fetchJson<ApiIssueHistoryResponse>(
      `/api/issues/${encodeURIComponent(issue.id)}/history?window=${windowKey}`,
      "Failed to load featured issue history",
      controller.signal,
    )
      .then((response) => {
        const points = response.points.map((point) => ({
          timestamp: point.captured_at,
          value: Number((point.value * 100).toFixed(1)),
        }));
        setHistory(points);
        setTrendStatus(points.length >= 2 ? "ready" : "empty");
      })
      .catch((error) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        console.error(error);
        setTrendStatus("empty");
      });

    return () => controller.abort();
  }, [issue.id, windowKey]);

  return (
    <article className="rounded-xl border border-line bg-card p-3 shadow-soft sm:p-5">
      <div className="grid gap-4 md:grid-cols-[minmax(0,1.25fr)_minmax(220px,0.75fr)] md:items-end">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-[11px] font-bold text-ink-faint">
              {issue.topicLabel ?? formatCategoryLabel(issue.category)}
            </span>
            <CautionBadge level={issue.cautionLevel} />
          </div>
          <h2 className="mt-2 text-base font-bold leading-6 text-ink sm:text-xl sm:leading-7">
            {issue.title}
          </h2>
          {issue.displaySubtitle ? (
            <p className="mt-1 hidden line-clamp-1 text-xs leading-5 text-ink-soft sm:block sm:text-sm">
              {issue.displaySubtitle}
            </p>
          ) : null}

          <dl className="mt-3 grid max-w-md grid-cols-2 gap-3">
            <div>
              <dt className="text-[11px] font-semibold text-ink-faint">
                현재 기대값
              </dt>
              <dd className="mt-1 text-2xl font-extrabold text-ink sm:text-3xl">
                {formatExpectationValue(issue.currentExpectationValue)}
              </dd>
            </div>
            <div>
              <dt className="text-[11px] font-semibold text-ink-faint">
                {windowLabel(windowKey)} 변화
              </dt>
              <dd className="mt-1 text-xl font-extrabold text-ink">
                {formatPercentagePointChange(
                  issueChangeForWindow(issue, windowKey),
                )}
              </dd>
            </div>
          </dl>
        </div>

        <div className="hidden min-h-16 md:block">
          {trendStatus === "loading" ? (
            <div className="h-16 animate-pulse rounded-lg bg-line-soft" />
          ) : trendStatus === "ready" ? (
            <Sparkline points={history} />
          ) : (
            <p className="flex h-16 items-center justify-center rounded-lg border border-dashed border-line text-xs text-ink-faint">
              선택 기간의 추세 이력이 충분하지 않습니다
            </p>
          )}
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between gap-2 border-t border-line-soft pt-3">
        <span
          className="text-[10px] font-semibold text-ink-faint sm:text-[11px]"
          title={`데이터 기준 시각: ${formatDataTimestamp(issue.dataAsOf)}`}
        >
          기준: {formatCompactDataTimestamp(issue.dataAsOf)}
        </span>
        <Link
          to={`/issues/${encodeURIComponent(issue.id)}`}
          state={{ from }}
          className="inline-flex min-h-11 shrink-0 items-center rounded-full bg-accent px-3 text-xs font-bold text-card transition hover:brightness-95 sm:px-4"
          aria-label={`${issue.title} 상세 분석 보기`}
        >
          상세 보기 →
        </Link>
      </div>
    </article>
  );
}
