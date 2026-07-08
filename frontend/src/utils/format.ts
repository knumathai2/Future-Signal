import type {
  ChartWindow,
  Issue,
  CautionLevel,
  IssueHistoryPoint,
  IssueInflectionPoint,
  RelatedEventCandidate,
} from "../types/issue";

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

export interface ApiIssueSummary {
  id: string;
  title: string;
  category: string;
  current_value: number;
  change_24h: number | null;
  change_7d: number | null;
  confidence_level: CautionLevel;
  heat_score: number | null;
}

export interface ApiIssueListResponse {
  data_as_of: string;
  issues: ApiIssueSummary[];
}

export interface ApiCategoriesResponse {
  categories: string[];
}

export interface ApiRelatedEventCandidate {
  event_title: string;
  event_date: string;
  note: string;
}

export interface ApiSignalOut {
  signal_type: "expectation_shift";
  severity: "low" | "medium" | "high" | "critical";
  window: string;
  magnitude: number;
  triggered_at: string;
}

export interface ApiIssueDetail {
  id: string;
  title: string;
  description: string;
  category: string;
  status: "active" | "closed" | "resolved";
  outcome_label: string;
  current_value: number;
  change_24h: number | null;
  change_7d: number | null;
  confidence_level: CautionLevel;
  heat_score: number | null;
  data_as_of: string;
  related_events: ApiRelatedEventCandidate[];
  signals: ApiSignalOut[];
}

export interface ApiHistoryPoint {
  captured_at: string;
  value: number;
}

export interface ApiIssueHistoryResponse {
  data_as_of: string;
  window: "24h" | "7d" | "30d";
  points: ApiHistoryPoint[];
}

export function mapApiIssueToFrontendIssue(
  apiIssue: ApiIssueSummary,
  dataAsOf: string,
): Issue {
  const currentExpectationValue = apiIssue.current_value * 100;
  const change24h =
    apiIssue.change_24h !== null && apiIssue.change_24h !== undefined
      ? apiIssue.change_24h * 100
      : 0;
  const change7d =
    apiIssue.change_7d !== null && apiIssue.change_7d !== undefined
      ? apiIssue.change_7d * 100
      : 0;

  return {
    id: apiIssue.id,
    title: apiIssue.title,
    description: "",
    category: apiIssue.category,
    currentExpectationValue: Number(currentExpectationValue.toFixed(1)),
    change24h: Number(change24h.toFixed(1)),
    change7d: Number(change7d.toFixed(1)),
    cautionLevel: apiIssue.confidence_level,
    dataAsOf,
    history: [],
    inflectionPoints: [],
    relatedEventCandidates: [],
  };
}

export function mapApiIssueDetailToFrontendIssue(
  apiDetail: ApiIssueDetail,
  apiHistory: ApiIssueHistoryResponse,
): Issue {
  const history: IssueHistoryPoint[] = apiHistory.points.map((p) => ({
    timestamp: p.captured_at,
    value: Number((p.value * 100).toFixed(1)),
  }));

  const inflectionPoints: IssueInflectionPoint[] = [];
  for (let i = 1; i < history.length; i++) {
    const change = Number((history[i].value - history[i - 1].value).toFixed(1));
    if (Math.abs(change) >= 5) {
      inflectionPoints.push({
        timestamp: history[i].timestamp,
        change,
        label: "Observed change exceeded the 5pp threshold",
      });
    }
  }

  const relatedEventCandidates: RelatedEventCandidate[] = apiDetail.related_events.map((e) => ({
    title: e.event_title,
    date: e.event_date,
    note: e.note,
  }));

  const currentExpectationValue = apiDetail.current_value * 100;
  const change24h = apiDetail.change_24h !== null ? apiDetail.change_24h * 100 : 0;
  const change7d = apiDetail.change_7d !== null ? apiDetail.change_7d * 100 : 0;

  let change30d = undefined;
  if (history.length > 0) {
    change30d = Number((currentExpectationValue - history[0].value).toFixed(1));
  }

  return {
    id: apiDetail.id,
    title: apiDetail.title,
    description: apiDetail.description,
    category: apiDetail.category,
    currentExpectationValue: Number(currentExpectationValue.toFixed(1)),
    change24h: Number(change24h.toFixed(1)),
    change7d: Number(change7d.toFixed(1)),
    change30d,
    cautionLevel: apiDetail.confidence_level,
    dataAsOf: apiDetail.data_as_of,
    history,
    inflectionPoints,
    relatedEventCandidates,
  };
}
