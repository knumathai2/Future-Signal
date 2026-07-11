export type CautionLevel =
  | "sufficient"
  | "caution_low_activity"
  | "caution_high_volatility"
  | "insufficient_data";

export type IssueHistoryPoint = {
  timestamp: string;
  value: number;
};

export type IssueInflectionPoint = {
  timestamp: string;
  change: number;
  label: string;
};

export type RelatedEventCandidate = {
  title: string;
  date: string;
  note: string;
};

export type Issue = {
  id: string;
  title: string;
  sourceTitle?: string;
  displaySubtitle?: string;
  topicLabel?: string;
  resolutionCondition?: string;
  description: string;
  category: string;
  currentExpectationValue: number;
  change24h: number | null;
  change7d: number | null;
  change30d?: number | null;
  cautionLevel: CautionLevel;
  dataAsOf: string;
  history: IssueHistoryPoint[];
  inflectionPoints: IssueInflectionPoint[];
  relatedEventCandidates?: RelatedEventCandidate[];
};

export type DataStatus = "loading" | "ready" | "empty" | "error";

export type ChartWindow = "24h" | "7d" | "30d";

export type IssueListSort = "heat" | "change" | "recent";

export type DirectionSummary = {
  upwardCount: number;
  downwardCount: number;
  unchangedCount: number;
  insufficientCount: number;
  directionalCount: number;
  upwardRatio: number;
  downwardRatio: number;
};

export type CategorySummary = {
  label: string;
  totalCount: number;
  validCount: number;
  averageChange: number | null;
};

export type IssueReportContent = {
  issue_overview: string;
  observed_change: string;
  context_summary: string | null;
  relationship_boundary: string;
  what_to_check: string;
  data_limitations: string;
  caution_note: string;
};

export type IssueReportContextSource = {
  title: string;
  url: string;
  domain: string;
  published_at: string | null;
  source_type: "official" | "independent_secondary";
};

export type IssueReportContextCandidate = {
  id: string;
  title: string;
  event_at: string;
  summary: string;
  sources: IssueReportContextSource[];
};

export type IssueReportSuccessResponse = {
  id: string;
  status: "success";
  report_version: "v4";
  generated_at: string;
  data_as_of: string;
  episode_at: string;
  content: IssueReportContent;
  evidence_refs: string[];
  context_candidates: IssueReportContextCandidate[];
};

export type IssueReportNotYetGeneratedResponse = {
  status: "not_yet_generated";
};

export type IssueReportResponse =
  IssueReportSuccessResponse | IssueReportNotYetGeneratedResponse;

export type IssueReportLoadState =
  | { status: "loading" }
  | { status: "success"; report: IssueReportSuccessResponse }
  | { status: "not_yet_generated" }
  | { status: "error" };
