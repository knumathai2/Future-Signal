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

export type ReportBasis =
  | "market_definition"
  | "observed_data"
  | "verified_context"
  | "general_scenario"
  | "data_limitation";

export type IssueReportMode =
  | "change_with_evidence"
  | "change_without_evidence"
  | "stable_with_evidence"
  | "stable_without_evidence";

export type MarketDefinitionBlock = {
  text: string;
  basis: "market_definition";
};

export type GeneralBlock = {
  text: string;
  basis: "general_scenario";
};

export type VerifiedBlock = {
  text: string;
  basis: "verified_context";
  candidate_ids: string[];
};

export type GeneralScenario = {
  title: string;
  text: string;
  basis: "general_scenario";
};

export type VerifiedInterpretation = {
  title: string;
  text: string;
  basis: "verified_context";
  candidate_ids: string[];
};

export type MaterialToCheck = {
  scenario_index: number;
  title: string;
  text: string;
  basis: "general_scenario";
};

export type IssueReportBriefing =
  | {
      mode: "change_with_evidence";
      verified_background: VerifiedBlock;
      conditional_interpretations: VerifiedInterpretation[];
    }
  | {
      mode: "change_without_evidence";
      conditional_scenarios: GeneralScenario[];
      materials_to_check: MaterialToCheck[];
    }
  | {
      mode: "stable_with_evidence";
      issue_explanation: MarketDefinitionBlock;
      verified_background: VerifiedBlock;
      conditional_scenarios: GeneralScenario[];
    }
  | {
      mode: "stable_without_evidence";
      issue_explanation: GeneralBlock;
      conditional_scenarios: GeneralScenario[];
      materials_to_check: MaterialToCheck[];
    };

export type IssueReportObservedChange = {
  metric_id: number;
  window: "24h";
  current_value: number;
  change_value: number | null;
  significant: boolean;
  threshold: number;
};

export type IssueReportResolutionReference = {
  status: "available" | "unavailable";
  condition_text: string | null;
  deadline: string | null;
  exclusions: string[];
  source_url: string | null;
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
  report_version: "v6";
  report_mode: IssueReportMode;
  generated_at: string;
  data_as_of: string;
  episode_at: string;
  observed_change: IssueReportObservedChange;
  briefing: IssueReportBriefing;
  resolution_reference: IssueReportResolutionReference;
  evidence_refs: string[];
  context_candidates: IssueReportContextCandidate[];
  relationship_boundary: string;
  data_limitations: string;
  caution_note: string;
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
