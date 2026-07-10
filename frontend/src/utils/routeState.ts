import type { DataStatus, IssueListSort } from "../types/issue";

export type ListWindow = "24h" | "7d";

export function parseForcedStatus(params: URLSearchParams): DataStatus | null {
  const value = params.get("state");
  return value === "loading" || value === "empty" || value === "error"
    ? value
    : null;
}

export function parseListWindow(value: string | null): ListWindow {
  return value === "7d" ? "7d" : "24h";
}

export function parseHomeWindow(value: string | null): ListWindow {
  return value === "24h" ? "24h" : "7d";
}

export function parseListSort(value: string | null): IssueListSort {
  return value === "change" || value === "recent" ? value : "heat";
}

export function parsePage(value: string | null): number {
  if (!value || !/^\d+$/.test(value)) {
    return 1;
  }

  return Math.max(1, Number(value));
}
