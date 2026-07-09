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

export type IssueReportContent = {
  issue_explainer: string;
  why_it_matters: string;
  current_reading: string;
  scenario_major_change: string;
  scenario_limited_change: string;
  scenario_status_quo: string;
  check_points: string;
  caution_note: string;
};

export type IssueReportSuccessResponse = {
  id: string;
  generated_at: string;
  data_as_of: string;
  status: "success";
  content: IssueReportContent;
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
