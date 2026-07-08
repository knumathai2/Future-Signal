import type {
  ChartWindow,
  Issue,
  CautionLevel,
  IssueHistoryPoint,
  IssueInflectionPoint,
  RelatedEventCandidate,
} from "../types/issue";

const DATE_TIME_FORMATTER = new Intl.DateTimeFormat("ko-KR", {
  year: "numeric",
  month: "numeric",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
  timeZone: "UTC",
});

const SHORT_DATE_FORMATTER = new Intl.DateTimeFormat("ko-KR", {
  month: "numeric",
  day: "numeric",
  timeZone: "UTC",
});

const CATEGORY_LABELS: Record<string, string> = {
  climate: "기후",
  culture: "문화",
  education: "교육",
  energy: "에너지",
  environment: "환경",
  "global affairs": "국제 이슈",
  health: "보건",
  international: "국제",
  economy: "경제",
  politics: "정치",
  science: "과학",
  technology: "기술",
  world: "세계",
};

export function formatDataTimestamp(timestamp: string): string {
  return `${DATE_TIME_FORMATTER.format(new Date(timestamp))} UTC`;
}

export function formatShortDate(timestamp: string): string {
  return SHORT_DATE_FORMATTER.format(new Date(timestamp));
}

export function formatExpectationValue(value: number): string {
  return `${Math.round(value)}%`;
}

export function formatPercentagePointChange(
  value: number | null | undefined,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "데이터 부족";
  }

  if (Math.abs(value) < 0.05) {
    return "0.0pp";
  }

  const sign = value > 0 ? "+" : "-";
  return `${sign}${Math.abs(value).toFixed(1)}pp`;
}

export function windowLabel(windowKey: ChartWindow): string {
  if (windowKey === "24h") {
    return "24시간";
  }

  if (windowKey === "7d") {
    return "7일";
  }

  return "30일";
}

export function formatCategoryLabel(category: string): string {
  const normalized = category.trim().toLowerCase().replace(/[_-]+/g, " ");

  return CATEGORY_LABELS[normalized] ?? category;
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

function toPercentagePoint(value: number | null | undefined): number | null {
  if (value === null || value === undefined) {
    return null;
  }

  return Number((value * 100).toFixed(1));
}

export function mapApiIssueToFrontendIssue(
  apiIssue: ApiIssueSummary,
  dataAsOf: string,
): Issue {
  const currentExpectationValue = apiIssue.current_value * 100;

  return {
    id: apiIssue.id,
    title: apiIssue.title,
    description: "",
    category: apiIssue.category,
    currentExpectationValue: Number(currentExpectationValue.toFixed(1)),
    change24h: toPercentagePoint(apiIssue.change_24h),
    change7d: toPercentagePoint(apiIssue.change_7d),
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
        label: "관측된 변화가 5pp 기준선을 넘었습니다",
      });
    }
  }

  const relatedEventCandidates: RelatedEventCandidate[] = apiDetail.related_events.map((e) => ({
    title: e.event_title,
    date: e.event_date,
    note: e.note,
  }));

  const currentExpectationValue = apiDetail.current_value * 100;
  const change24h = toPercentagePoint(apiDetail.change_24h);
  const change7d = toPercentagePoint(apiDetail.change_7d);

  let change30d: number | null = null;
  if (history.length > 0) {
    change30d = Number((currentExpectationValue - history[0].value).toFixed(1));
  }

  return {
    id: apiDetail.id,
    title: apiDetail.title,
    description: apiDetail.description,
    category: apiDetail.category,
    currentExpectationValue: Number(currentExpectationValue.toFixed(1)),
    change24h,
    change7d,
    change30d,
    cautionLevel: apiDetail.confidence_level,
    dataAsOf: apiDetail.data_as_of,
    history,
    inflectionPoints,
    relatedEventCandidates,
  };
}
