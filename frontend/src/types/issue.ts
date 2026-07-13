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

export type V8ReportSectionType =
  | "current_situation"
  | "recent_change"
  | "interpretation"
  | "key_conditions"
  | "what_to_watch"
  | "limitations";

export type V8ReportSection = {
  type: V8ReportSectionType;
  title: string;
  format: "paragraph" | "bullets";
  content: string | null;
  items: string[];
  evidence_refs: string[];
};

export type V8SupportedClaim = {
  ref: string;
  text: string;
  excerpt: string;
  citation_id: string;
};

export type V8ReportSource = {
  id: string;
  context_ref: string;
  citation_id: string;
  title: string;
  url: string;
  domain: string;
  source_level: "A" | "B" | "C";
  supported_claims: V8SupportedClaim[];
  retrieved_at: string;
};

export type V8IssueReportResponse = {
  id: string;
  status: "fresh" | "stale" | "generating" | "failed_with_last_good";
  report_version: "v8";
  headline: string;
  summary: string;
  sections: V8ReportSection[];
  sources: V8ReportSource[];
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
  | V8IssueReportResponse
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

export type GenerationStreamBlock =
  | {
      sequence: 0;
      block_type: "headline_summary";
      payload: {
        kind: "headline_summary";
        headline: string;
        summary: string;
      };
    }
  | {
      sequence: number;
      block_type: "section";
      payload: {
        kind: "section";
        index: number;
        section: V8ReportSection;
      };
    };

export type StreamingBriefingState = {
  headline: string;
  summary: string;
  sections: V8ReportSection[];
};

export type ScenarioPremiseClass =
  | "confirmed_fact"
  | "stored_observation"
  | "user_assumption"
  | "model_scenario"
  | "unverified_context";

export type ScenarioTurn = {
  turn_id: string;
  sequence: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
};

export type ScenarioPremise = {
  premise_id: string;
  premise_class: ScenarioPremiseClass;
  text: string;
  origin_turn_id: string;
};

export type ScenarioSession = {
  session_id: string;
  issue_id: string;
  created_at: string;
  expires_at: string;
  max_turns: 8;
  remaining_turns: number;
  policy_version: string;
  data_as_of: string;
  caution_note: string;
  turns: ScenarioTurn[];
  premises: ScenarioPremise[];
};

export type ScenarioSessionCreated = Omit<
  ScenarioSession,
  "remaining_turns" | "turns" | "premises"
> & {
  session_capability: string;
};

export type ScenarioTurnCreated = {
  turn_id: string;
  sequence: number;
  status: "queued";
  created: boolean;
  requested_at: string;
  stream_path: string;
};

export type ScenarioTurnStatus = {
  turn_id: string;
  sequence: number;
  state: "queued" | "running" | "succeeded" | "failed";
  attempt_number: number;
  requested_at: string;
  updated_at: string;
  assistant_turn_id: string | null;
  error_code: string | null;
};

export type ScenarioContentBlock =
  | { sequence: number; block_type: "paragraph"; text: string }
  | {
      sequence: number;
      block_type: "list";
      ordered: boolean;
      items: string[];
    };
