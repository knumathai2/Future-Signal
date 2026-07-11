import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Line, LineChart, ResponsiveContainer, YAxis } from "recharts";
import { CautionBadge } from "./CautionBadge";
import { DirectionalChange } from "./DirectionalChange";
import type { ApiIssueHistoryResponse } from "../utils/format";
import type { Issue, IssueHistoryPoint } from "../types/issue";
import type { ListWindow } from "../utils/routeState";
import { fetchJson } from "../utils/api";
import {
  formatCategoryLabel,
  formatCompactDataTimestamp,
  formatDataTimestamp,
  formatExpectationValue,
  issueChangeForWindow,
  windowLabel,
} from "../utils/format";

type FeaturedIssueCardProps = {
  issue: Issue;
  windowKey: ListWindow;
  from: string;
};

type TrendStatus = "loading" | "ready" | "empty" | "error";

function trendDescription(points: IssueHistoryPoint[]): string {
  const first = points[0]?.value;
  const last = points[points.length - 1]?.value;
  if (first === undefined || last === undefined) {
    return "";
  }

  const direction = last > first ? "상향" : last < first ? "하향" : "변화 없음";
  return `이력은 ${first.toFixed(1)}%에서 ${last.toFixed(1)}%로 ${direction}했습니다.`;
}

function HistoryPreview({ points }: { points: IssueHistoryPoint[] }) {
  const first = points[0];
  const last = points[points.length - 1];
  const lineColor =
    first && last && last.value < first.value
      ? "oklch(48% 0.075 245)"
      : "#b84416";
  const values = points.map((point) => point.value);
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const padding = Math.max((maximum - minimum) * 0.15, 1);

  return (
    <div>
      <p className="sr-only">{trendDescription(points)}</p>
      <div className="h-32 w-full sm:h-36">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={points}
            margin={{ top: 8, right: 4, bottom: 6, left: 4 }}
          >
            <YAxis hide domain={[minimum - padding, maximum + padding]} />
            <Line
              type="monotone"
              dataKey="value"
              stroke={lineColor}
              strokeWidth={3}
              dot={false}
              activeDot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-1 flex items-center justify-between gap-3 text-[10px] font-semibold text-ink-faint">
        <span>시작 {first?.value.toFixed(1)}%</span>
        <span>최근 {last?.value.toFixed(1)}%</span>
      </div>
    </div>
  );
}

/** Featured issue backed only by the selected issue's real history response. */
export function FeaturedIssueCard({
  issue,
  windowKey,
  from,
}: FeaturedIssueCardProps) {
  const [trendStatus, setTrendStatus] = useState<TrendStatus>("loading");
  const [history, setHistory] = useState<IssueHistoryPoint[]>([]);
  const [historyDataAsOf, setHistoryDataAsOf] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    setTrendStatus("loading");
    setHistory([]);
    setHistoryDataAsOf("");

    fetchJson<ApiIssueHistoryResponse>(
      `/api/issues/${encodeURIComponent(issue.id)}/history?window=${windowKey}`,
      "Failed to load featured issue history",
      controller.signal,
    )
      .then((response) => {
        const points = response.points
          .map((point) => ({
            timestamp: point.captured_at,
            value: Number((point.value * 100).toFixed(1)),
          }))
          .sort(
            (left, right) =>
              new Date(left.timestamp).getTime() -
              new Date(right.timestamp).getTime(),
          );
        setHistory(points);
        setHistoryDataAsOf(response.data_as_of);
        setTrendStatus(points.length >= 2 ? "ready" : "empty");
      })
      .catch((error) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        console.error(error);
        setTrendStatus("error");
      });

    return () => controller.abort();
  }, [issue.id, windowKey]);

  const selectedChange = issueChangeForWindow(issue, windowKey);
  const graphStatusCopy = useMemo(() => {
    if (trendStatus === "error") {
      return "선택 기간의 실제 이력을 불러오지 못했습니다";
    }
    return "선택 기간의 시계열이 부족해 그래프를 표시할 수 없습니다";
  }, [trendStatus]);

  return (
    <article className="h-full rounded-2xl border border-line bg-card p-4 shadow-soft sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-extrabold text-accent">
          {windowLabel(windowKey)} 관측 변화 상위
        </span>
        <CautionBadge level={issue.cautionLevel} />
      </div>

      <div className="mt-4">
        <span className="text-[11px] font-bold text-ink-faint">
          {issue.topicLabel ?? formatCategoryLabel(issue.category)}
        </span>
        <h2 className="mt-2 text-lg font-extrabold leading-7 text-ink sm:text-2xl sm:leading-8">
          {issue.title}
        </h2>
        {issue.displaySubtitle ? (
          <p className="mt-2 line-clamp-2 text-xs leading-5 text-ink-soft sm:text-sm sm:leading-6">
            {issue.displaySubtitle}
          </p>
        ) : null}
      </div>

      <dl className="mt-5 grid grid-cols-2 gap-3 rounded-xl bg-line-soft p-4">
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
          <dd className="mt-1 text-xl font-extrabold sm:text-2xl">
            <DirectionalChange value={selectedChange} />
          </dd>
        </div>
      </dl>

      <div className="mt-5" aria-live="polite">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-xs font-bold text-ink-soft">실제 이력 흐름</h3>
          {trendStatus === "ready" && historyDataAsOf ? (
            <span
              className="text-[10px] font-semibold text-ink-faint"
              title={`이력 기준 시각: ${formatDataTimestamp(historyDataAsOf)}`}
            >
              이력 기준 {formatCompactDataTimestamp(historyDataAsOf)}
            </span>
          ) : null}
        </div>
        <div className="mt-2 min-h-36 rounded-xl border border-line-soft px-3 py-2 sm:min-h-40">
          {trendStatus === "loading" ? (
            <div
              className="h-32 animate-pulse rounded-lg bg-line-soft sm:h-36"
              aria-label="대표 이슈 이력 로딩 중"
            />
          ) : trendStatus === "ready" ? (
            <HistoryPreview points={history} />
          ) : (
            <p className="flex h-32 items-center justify-center text-center text-xs leading-5 text-ink-faint sm:h-36">
              {graphStatusCopy}
            </p>
          )}
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-line-soft pt-4">
        <span
          className="text-[10px] font-semibold text-ink-faint sm:text-[11px]"
          title={`데이터 기준 시각: ${formatDataTimestamp(issue.dataAsOf)}`}
        >
          데이터 기준 {formatCompactDataTimestamp(issue.dataAsOf)}
        </span>
        <Link
          to={`/issues/${encodeURIComponent(issue.id)}`}
          state={{ from }}
          className="inline-flex min-h-11 shrink-0 items-center rounded-full bg-accent px-4 text-xs font-bold text-card transition hover:brightness-95"
          aria-label={`${issue.title} 상세 분석 보기`}
        >
          상세 보기 →
        </Link>
      </div>
    </article>
  );
}
