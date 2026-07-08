import type { ChartWindow } from "../types/issue";

const DATE_TIME_FORMATTER = new Intl.DateTimeFormat("en-US", {
  month: "numeric",
  day: "numeric",
  year: "numeric",
  hour: "numeric",
  minute: "2-digit",
  timeZone: "UTC",
});

const SHORT_DATE_FORMATTER = new Intl.DateTimeFormat("en-US", {
  month: "numeric",
  day: "numeric",
  timeZone: "UTC",
});

export function formatDataTimestamp(timestamp: string): string {
  return `${DATE_TIME_FORMATTER.format(new Date(timestamp))} UTC`;
}

export function formatShortDate(timestamp: string): string {
  return SHORT_DATE_FORMATTER.format(new Date(timestamp));
}

export function formatExpectationValue(value: number): string {
  return `${Math.round(value)}%`;
}

export function formatPercentagePointChange(value: number): string {
  if (Math.abs(value) < 0.05) {
    return "0.0pp";
  }

  const sign = value > 0 ? "+" : "-";
  return `${sign}${Math.abs(value).toFixed(1)}pp`;
}

export function windowLabel(windowKey: ChartWindow): string {
  if (windowKey === "24h") {
    return "24 hours";
  }

  if (windowKey === "7d") {
    return "7 days";
  }

  return "30 days";
}
