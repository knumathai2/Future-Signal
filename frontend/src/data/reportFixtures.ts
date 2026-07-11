/** Development-only v8 bundles for responsive and browser verification. */
import type {
  IssueReportResponse,
  V8IssueReportResponse,
} from "../types/issue";

const ID = "77777777-7777-4777-8777-777777777777";
const REQUEST_ID = "88888888-8888-4888-8888-888888888888";
const FINGERPRINT = "a".repeat(64);

const baseReport: V8IssueReportResponse = {
  id: ID,
  status: "fresh",
  report_version: "v8",
  headline: "공식 조건과 현재 공개 자료를 함께 살펴본 브리핑",
  summary:
    "이 이슈는 저장된 설명에 따라 공식 조건이 충족되는지를 확인합니다. 현재 자료에는 기준 시각의 관찰값과 최근 비교값이 포함되어 있습니다. 최근 흐름은 이전보다 달라졌지만 실제 결과를 뜻하지 않으며, 제공된 근거 범위에서 현재 상황과 앞으로 확인할 조건을 함께 정리합니다.",
  sections: [
    {
      type: "current_situation",
      title: "이슈의 기준",
      format: "paragraph",
      content:
        "저장된 이슈 설명에 따라 공식 조건이 충족되는지를 확인하는 대상이며, 현실의 향후 결과를 단정하지 않습니다.",
      items: [],
      evidence_refs: ["market_definition:fixture"],
    },
    {
      type: "recent_change",
      title: "현재 공개 데이터",
      format: "bullets",
      content: null,
      items: [
        "기준 시각의 관찰값과 최근 비교값을 서로 구분하여 확인할 수 있습니다.",
        "관찰된 움직임만으로 실제 사건과의 관계를 입증할 수는 없습니다.",
      ],
      evidence_refs: ["metric:486"],
    },
  ],
  sources: [],
  generated_at: "2026-07-11T09:05:00Z",
  data_as_of: "2026-07-11T09:00:00Z",
  context_as_of: null,
  cache: {
    state: "fresh",
    input_fingerprint: FINGERPRINT,
    current_fingerprint: FINGERPRINT,
  },
  data_limitations:
    "공개 예측시장 참여자 데이터는 전체 대중의 판단을 대표하지 않으며 저장된 근거 범위에서만 해석해야 합니다.",
  caution_note:
    "이 브리핑은 공개 데이터와 확인 가능한 자료를 정리한 것으로 현실의 향후 결과를 예측하거나 원인을 입증하지 않습니다.",
  request_id: null,
  request_error_code: null,
};

const sourceReport: V8IssueReportResponse = {
  ...baseReport,
  id: "77777777-7777-4777-8777-777777777778",
  context_as_of: "2026-07-11T08:30:00Z",
  sections: [
    ...baseReport.sections,
    {
      type: "interpretation",
      title: "확인된 공개 자료",
      format: "paragraph",
      content:
        "기관이 공개한 문서의 지원 문장을 출처와 함께 확인할 수 있으며, 관찰 흐름과의 인과관계는 제시하지 않습니다.",
      items: [],
      evidence_refs: [
        "context:66666666-6666-4666-8666-666666666666",
        "source:fixture-source",
      ],
    },
  ],
  sources: [
    {
      id: "source:fixture-source",
      context_ref: "context:66666666-6666-4666-8666-666666666666",
      citation_id: "citation:fixture",
      title: "기관 공식 공개 문서",
      url: "https://example.gov/document",
      domain: "example.gov",
      source_level: "A",
      supported_claims: [
        {
          ref: "claim:fixture",
          text: "기관이 관련 조건을 설명하는 공식 문서를 공개했습니다.",
          excerpt: "관련 조건을 설명하는 공식 문서가 공개되었습니다.",
          citation_id: "citation:fixture",
        },
      ],
      retrieved_at: "2026-07-11T08:30:00Z",
    },
  ],
};

const FIXTURES = new Map<string, IssueReportResponse>([
  ["v8-fresh", baseReport],
  ["v8-sources", sourceReport],
  [
    "v7-stale",
    {
      ...baseReport,
      id: "77777777-7777-4777-8777-777777777779",
      status: "stale",
      cache: {
        state: "stale",
        input_fingerprint: FINGERPRINT,
        current_fingerprint: "b".repeat(64),
      },
    },
  ],
  [
    "v7-generating",
    {
      status: "generating",
      request_id: REQUEST_ID,
      input_fingerprint: FINGERPRINT,
      requested_at: "2026-07-11T09:10:00Z",
    },
  ],
  [
    "v7-generating-last-good",
    { ...baseReport, status: "generating", request_id: REQUEST_ID },
  ],
  [
    "v7-failed",
    {
      status: "failed",
      request_id: REQUEST_ID,
      error_code: "generation_failed",
    },
  ],
  [
    "v7-failed-last-good",
    {
      ...baseReport,
      status: "failed_with_last_good",
      request_id: REQUEST_ID,
      request_error_code: "generation_failed",
    },
  ],
]);

export function getDevelopmentReportFixture(
  name: string | null,
): IssueReportResponse | null {
  if (
    typeof window === "undefined" ||
    (window.location.hostname !== "localhost" &&
      window.location.hostname !== "127.0.0.1")
  )
    return null;
  return name ? (FIXTURES.get(name) ?? null) : null;
}
