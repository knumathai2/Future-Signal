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
import type { ChartWindow, Issue, IssueHistoryPoint } from "../types/issue";
import { formatExpectationValue, formatShortDate } from "../utils/format";

type IssueTrendChartProps = {
  issue: Issue;
  windowKey: ChartWindow;
};

type TooltipPayload = {
  value?: number;
};

type TooltipProps = {
  active?: boolean;
  label?: string;
  payload?: TooltipPayload[];
};

const WINDOW_POINT_COUNTS: Record<ChartWindow, number> = {
  "24h": 2,
  "7d": 8,
  "30d": 31,
};

function getVisibleHistory(
  history: IssueHistoryPoint[],
  windowKey: ChartWindow,
): IssueHistoryPoint[] {
  return history.slice(-WINDOW_POINT_COUNTS[windowKey]);
}

function CustomTooltip({ active, label, payload }: TooltipProps) {
  if (!active || !payload?.length || !label) {
    return null;
  }

  return (
    <div className="rounded-lg border border-line bg-card px-3 py-2 shadow-soft">
      <div className="text-xs font-semibold text-ink">{formatShortDate(label)}</div>
      <div className="mt-1 text-xs text-ink-soft">
        Reflected expectation value:{" "}
        <span className="font-bold text-ink">
          {formatExpectationValue(Number(payload[0].value ?? 0))}
        </span>
      </div>
    </div>
  );
}

export function IssueTrendChart({ issue, windowKey }: IssueTrendChartProps) {
  const visibleHistory = useMemo(
    () => getVisibleHistory(issue.history, windowKey),
    [issue.history, windowKey],
  );

  const markerPoints = useMemo(() => {
    const visibleTimestamps = new Set(visibleHistory.map((point) => point.timestamp));

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

  return (
    <div className="rounded-lg border border-line bg-card p-4">
      <div className="h-[260px] w-full sm:h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={visibleHistory}
            margin={{ top: 16, right: 20, bottom: 6, left: -12 }}
          >
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatShortDate}
              axisLine={false}
              tickLine={false}
              minTickGap={28}
              tick={{ fill: "oklch(62% 0.015 55)", fontSize: 11 }}
            />
            <YAxis
              domain={domain}
              tickFormatter={(value) => `${value}%`}
              axisLine={false}
              tickLine={false}
              width={42}
              tick={{ fill: "oklch(62% 0.015 55)", fontSize: 11 }}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: "oklch(87% 0.015 65)" }} />
            <Line
              type="monotone"
              dataKey="value"
              stroke="oklch(52% 0.13 45)"
              strokeWidth={2.4}
              dot={false}
              activeDot={{ r: 4, stroke: "oklch(22% 0.02 55)", strokeWidth: 1.5 }}
              isAnimationActive={false}
            />
            {markerPoints.map((point) => (
              <ReferenceDot
                key={point.timestamp}
                x={point.timestamp}
                y={point.value}
                r={4}
                fill="oklch(22% 0.02 55)"
                stroke="oklch(99% 0.006 75)"
                strokeWidth={2}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <p className="mt-3 text-sm leading-6 text-ink-soft">
        {firstMarker
          ? `${firstMarker.label} on ${formatShortDate(
              firstMarker.timestamp,
            )}. Markers identify observed threshold crossings, not causes.`
          : "No observed change beyond the 5pp threshold appears in this window."}
      </p>
    </div>
  );
}
