import type { ChartWindow, IssueHistoryPoint } from "../types/issue";

const DAY_MS = 24 * 60 * 60 * 1000;

export const WINDOW_DURATION_MS: Record<ChartWindow, number> = {
  "24h": DAY_MS,
  "7d": 7 * DAY_MS,
  "30d": 30 * DAY_MS,
};

type TimedHistoryPoint = IssueHistoryPoint & {
  time: number;
};

export type WindowedHistory = {
  points: IssueHistoryPoint[];
  hasSufficientHistory: boolean;
  availableSpanMs: number;
  requiredSpanMs: number;
};

function toTimedHistory(history: IssueHistoryPoint[]): TimedHistoryPoint[] {
  return history
    .map((point) => ({
      ...point,
      time: new Date(point.timestamp).getTime(),
    }))
    .filter((point) => Number.isFinite(point.time))
    .sort((left, right) => left.time - right.time);
}

function stripTime(point: TimedHistoryPoint): IssueHistoryPoint {
  return {
    timestamp: point.timestamp,
    value: point.value,
  };
}

function findBaselineIndex(
  history: TimedHistoryPoint[],
  windowStartTime: number,
): number {
  let baselineIndex = -1;

  for (let index = 0; index < history.length; index += 1) {
    if (history[index].time <= windowStartTime) {
      baselineIndex = index;
    } else {
      break;
    }
  }

  return baselineIndex;
}

export function getWindowedHistory(
  history: IssueHistoryPoint[],
  windowKey: ChartWindow,
): WindowedHistory {
  const sortedHistory = toTimedHistory(history);
  const requiredSpanMs = WINDOW_DURATION_MS[windowKey];

  if (sortedHistory.length === 0) {
    return {
      points: [],
      hasSufficientHistory: false,
      availableSpanMs: 0,
      requiredSpanMs,
    };
  }

  const latestPoint = sortedHistory[sortedHistory.length - 1];
  const windowStartTime = latestPoint.time - requiredSpanMs;
  const baselineIndex = findBaselineIndex(sortedHistory, windowStartTime);
  const firstPoint = sortedHistory[0];
  const startIndex = baselineIndex >= 0 ? baselineIndex : 0;
  const points = sortedHistory.slice(startIndex).map(stripTime);

  return {
    points,
    hasSufficientHistory: baselineIndex >= 0 && points.length >= 2,
    availableSpanMs: latestPoint.time - firstPoint.time,
    requiredSpanMs,
  };
}

export function calculateHistoryChangeForWindow(
  history: IssueHistoryPoint[],
  currentValue: number,
  windowKey: ChartWindow,
): number | null {
  const sortedHistory = toTimedHistory(history);

  if (sortedHistory.length === 0) {
    return null;
  }

  const latestPoint = sortedHistory[sortedHistory.length - 1];
  const windowStartTime = latestPoint.time - WINDOW_DURATION_MS[windowKey];
  const baselineIndex = findBaselineIndex(sortedHistory, windowStartTime);

  if (baselineIndex < 0) {
    return null;
  }

  return Number((currentValue - sortedHistory[baselineIndex].value).toFixed(1));
}
