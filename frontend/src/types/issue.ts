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

/** Legacy chart annotation shape retained until the separately approved TASK-109 cleanup. */
export type IssueReportContextCandidate = {
  id: string;
  title: string;
  event_at: string;
  summary: string;
  sources: Array<{
    title: string;
    url: string;
    domain: string;
    published_at: string | null;
    source_type: "official" | "independent_secondary";
  }>;
};

export type V7ReportSectionType =
  | "issue_overview"
  | "current_context"
  | "market_data"
  | "external_context"
  | "uncertainties"
  | "what_to_watch";

export type V7ReportSection = {
  type: V7ReportSectionType;
  title: string;
  format: "paragraph" | "bullets";
  content: string | null;
  items: string[];
  evidence_refs: string[];
};

export type V7SupportedClaim = {
  ref: string;
  text: string;
  excerpt: string;
  citation_id: string;
};

export type V7ReportSource = {
  id: string;
  context_ref: string;
  citation_id: string;
  title: string;
  url: string;
  domain: string;
  source_level: "A" | "B" | "C";
  supported_claims: V7SupportedClaim[];
  retrieved_at: string;
};

export type V7IssueReportResponse = {
  id: string;
  status: "fresh" | "stale" | "generating" | "failed_with_last_good";
  report_version: "v7";
  headline: string;
  summary: string;
  sections: V7ReportSection[];
  sources: V7ReportSource[];
  generated_at: string;
  data_as_of: string;
  context_as_of: string | null;
  cache: {
    state: "fresh" | "stale";
    input_fingerprint: string;
    current_fingerprint: string | null;
  };
  data_limitations: string;
  caution_note: string;
  request_id: string | null;
  request_error_code: string | null;
};

export type IssueReportResponse =
  | V7IssueReportResponse
  | { status: "idle" }
  | {
      status: "generating";
      request_id: string;
      input_fingerprint: string;
      requested_at: string;
    }
  | { status: "failed"; request_id: string; error_code: string };

export type IssueReportLoadState =
  | { status: "loading" }
  | { status: "ready"; response: IssueReportResponse }
  | { status: "error" };

export type GenerationRequestResponse = {
  request_id: string;
  status: "queued" | "running" | "fresh" | "failed";
  created: boolean;
  input_fingerprint: string;
};

export type GenerationRequestStatusResponse = {
  request_id: string;
  issue_id: string;
  state: "queued" | "running" | "succeeded" | "failed";
  attempt_number: number;
  requested_at: string;
  updated_at: string;
  input_fingerprint: string;
  report_id: string | null;
  error_code: string | null;
  successor_request_id: string | null;
};
