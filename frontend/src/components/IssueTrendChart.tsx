import { useMemo } from "react";
import {
  Line,
  LineChart,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type {
  ChartWindow,
  Issue,
  IssueHistoryPoint,
  IssueReportContextCandidate,
} from "../types/issue";
import {
  formatDataTimestamp,
  formatExpectationValue,
  formatPercentagePointChange,
  formatShortDate,
  windowLabel,
} from "../utils/format";
import { getWindowedHistory } from "../utils/history";

type IssueTrendChartProps = {
  issue: Issue;
  windowKey: ChartWindow;
  contextCandidates?: IssueReportContextCandidate[];
};

type TooltipPayload = {
  value?: number;
  payload?: ChartPoint;
};

type TooltipProps = {
  active?: boolean;
  label?: string;
  payload?: TooltipPayload[];
};

type ChartPoint = IssueHistoryPoint & {
  changeFromPrevious: number | null;
};

function formatAvailableSpan(availableSpanMs: number): string {
  const hours = Math.max(0, Math.floor(availableSpanMs / (60 * 60 * 1000)));

  if (hours < 48) {
    return `${hours}시간`;
  }

  return `${Math.floor(hours / 24)}일`;
}

function CustomTooltip({ active, label, payload }: TooltipProps) {
  if (!active || !payload?.length || !label) {
    return null;
  }

  return (
    <div className="rounded-lg border border-line bg-card px-3 py-2 shadow-soft">
      <div className="text-xs font-semibold text-ink">
        {formatShortDate(label)}
      </div>
      <div className="mt-1 text-xs text-ink-soft">
        공개 데이터에 반영된 기대값:{" "}
        <span className="font-bold text-ink">
          {formatExpectationValue(Number(payload[0].value ?? 0))}
        </span>
      </div>
      <div className="mt-1 text-xs text-ink-soft">
        이전 관측값 대비:{" "}
        <span className="font-bold text-ink">
          {formatPercentagePointChange(payload[0].payload?.changeFromPrevious)}
        </span>
      </div>
      <div className="mt-1 text-[11px] text-ink-faint">
        {formatDataTimestamp(label)}
      </div>
    </div>
  );
}

export function IssueTrendChart({
  issue,
  windowKey,
  contextCandidates = [],
}: IssueTrendChartProps) {
  const windowedHistory = useMemo(
    () => getWindowedHistory(issue.history, windowKey),
    [issue.history, windowKey],
  );
  const visibleHistory = windowedHistory.points;

  const chartData = useMemo<ChartPoint[]>(
    () =>
      visibleHistory.map((point, index) => {
        if (index === 0) {
          return {
            ...point,
            changeFromPrevious: null,
          };
        }

        return {
          ...point,
          changeFromPrevious: Number(
            (point.value - visibleHistory[index - 1].value).toFixed(1),
          ),
        };
      }),
    [visibleHistory],
  );

  const markerPoints = useMemo(() => {
    const visibleTimestamps = new Set(
      visibleHistory.map((point) => point.timestamp),
    );

    return issue.inflectionPoints
      .filter((point) => visibleTimestamps.has(point.timestamp))
      .map((point) => {
        const historyPoint = visibleHistory.find(
          (item) => item.timestamp === point.timestamp,
        );

        return historyPoint ? { ...point, value: historyPoint.value } : null;
      })
      .filter((point): point is NonNullable<typeof point> => point !== null);
  }, [issue.inflectionPoints, visibleHistory]);

  const contextMarkerPoints = useMemo(() => {
    if (visibleHistory.length === 0) {
      return [];
    }
    const start = Date.parse(visibleHistory[0].timestamp);
    const end = Date.parse(visibleHistory[visibleHistory.length - 1].timestamp);
    return contextCandidates.flatMap((candidate) => {
      const eventTime = Date.parse(candidate.event_at);
      if (!Number.isFinite(eventTime) || eventTime < start || eventTime > end) {
        return [];
      }
      const nearest = visibleHistory.reduce((closest, point) =>
        Math.abs(Date.parse(point.timestamp) - eventTime) <
        Math.abs(Date.parse(closest.timestamp) - eventTime)
          ? point
          : closest,
      );
      return [{ candidate, ...nearest }];
    });
  }, [contextCandidates, visibleHistory]);

  const domain = useMemo(() => {
    const values = visibleHistory.map((point) => point.value);
    if (values.length === 0) {
      return [0, 100] as [number, number];
    }
    const min = Math.min(...values);
    const max = Math.max(...values);
    const padding = Math.max(2, (max - min) * 0.16);

    return [
      Math.max(0, Math.floor(min - padding)),
      Math.min(100, Math.ceil(max + padding)),
    ] as [number, number];
  }, [visibleHistory]);

  const firstMarker = markerPoints[0];

  if (!windowedHistory.hasSufficientHistory) {
    return (
      <div className="rounded-lg border border-line bg-card p-4">
        <div
          className={[
            "flex h-[260px] w-full items-center justify-center rounded-lg",
            "border border-dashed border-line-soft px-6 text-center sm:h-[300px]",
          ].join(" ")}
        >
          <div className="max-w-md">
            <p className="text-sm font-bold text-ink">
              {windowLabel(windowKey)} 추이를 표시하기에 이력이 부족합니다
            </p>
            <p className="mt-2 text-sm leading-6 text-ink-soft">
              선택한 기간에는 시작 기준점과 현재 지점이 모두 필요합니다. 현재
              확인 가능한 이력 범위는 약{" "}
              {formatAvailableSpan(windowedHistory.availableSpanMs)}입니다.
            </p>
          </div>
        </div>
        <p className="mt-3 text-xs leading-5 text-ink-faint">
          데이터 기준 시각: {formatDataTimestamp(issue.dataAsOf)}
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-line bg-card p-4">
      <div className="h-[260px] w-full sm:h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 16, right: 20, bottom: 6, left: -12 }}
          >
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatShortDate}
              axisLine={false}
              tickLine={false}
              minTickGap={28}
              tick={{ fill: "oklch(54% 0.015 55)", fontSize: 11 }}
            />
            <YAxis
              domain={domain}
              tickFormatter={(value) => `${value}%`}
              axisLine={false}
              tickLine={false}
              width={42}
              tick={{ fill: "oklch(54% 0.015 55)", fontSize: 11 }}
            />
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ stroke: "oklch(87% 0.015 65)" }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#b84416"
              strokeWidth={2.4}
              dot={false}
              activeDot={{
                r: 4,
                stroke: "#241c18",
                strokeWidth: 1.5,
              }}
              isAnimationActive={false}
            />
            {markerPoints.map((point) => (
              <ReferenceDot
                key={point.timestamp}
                x={point.timestamp}
                y={point.value}
                r={4}
                fill="#241c18"
                stroke="oklch(99% 0.006 75)"
                strokeWidth={2}
              />
            ))}
            {contextMarkerPoints.map(({ candidate, timestamp, value }) => (
              <ReferenceDot
                key={candidate.id}
                id={`candidate-marker-${candidate.id}`}
                data-candidate-id={candidate.id}
                x={timestamp}
                y={value}
                r={5}
                fill="#b84416"
                stroke="oklch(99% 0.006 75)"
                strokeWidth={2}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <p className="mt-3 text-sm leading-6 text-ink-soft">
        {firstMarker
          ? `${formatShortDate(firstMarker.timestamp)}: ${
              firstMarker.label
            } (${formatPercentagePointChange(
              firstMarker.change,
            )}). 표시는 관측된 기준선 통과를 가리키며 원인을 뜻하지 않습니다.`
          : "이 구간에는 5%p 기준선을 넘는 관측 변화가 없습니다."}
      </p>
      <p className="mt-2 text-xs leading-5 text-ink-faint">
        데이터 기준 시각: {formatDataTimestamp(issue.dataAsOf)}
      </p>
      {contextMarkerPoints.length > 0 ? (
        <div className="mt-3 border-t border-line-soft pt-3">
          <p className="text-xs font-bold text-ink">
            같은 검토 구간의 공개 정보 표시
          </p>
          <ul className="mt-2 flex flex-wrap gap-2">
            {contextMarkerPoints.map(({ candidate }) => (
              <li key={candidate.id}>
                <a
                  href={`#context-candidate-${candidate.id}`}
                  data-candidate-id={candidate.id}
                  className="inline-flex min-h-11 items-center rounded-full border border-line px-3 text-xs font-semibold text-accent hover:border-accent"
                >
                  {formatShortDate(candidate.event_at)} · {candidate.title}
                </a>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-[11px] leading-5 text-ink-faint">
            공개 정보 표시는 날짜를 차트의 가장 가까운 관측 지점에 연결한
            것이며, 관찰된 변화와의 관계를 뜻하지 않습니다.
          </p>
        </div>
      ) : null}
    </div>
  );
}
