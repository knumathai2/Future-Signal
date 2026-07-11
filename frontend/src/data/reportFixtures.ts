/** Development-only v4 bundles for responsive/browser verification. */
import type {
  IssueReportContent,
  IssueReportContextCandidate,
  IssueReportSuccessResponse,
} from "../types/issue";

const BASE_CONTENT: IssueReportContent = {
  issue_overview:
    "이 이슈는 공개 문서에 적힌 조건의 충족 여부를 정해진 기한 기준으로 추적합니다.",
  observed_change:
    "데이터 기준 시각에 공개 예측시장 참여자 데이터에 반영된 기대값은 43.2%입니다. 관찰된 비교값은 24시간 변화 -6.1퍼센트포인트, 7일 변화 -9.4퍼센트포인트입니다.",
  context_summary: null,
  relationship_boundary:
    "관찰된 움직임은 공개 데이터에 기록된 흐름이며, 현실의 결과 또는 함께 제시된 공개 정보와의 관계를 입증하지 않습니다.",
  what_to_check:
    "게시된 조건 문구와 기준 시각 이후 공개 자료의 갱신 내용을 추가로 확인해야 합니다.",
  data_limitations:
    "공개 예측시장 참여자 데이터는 전체 대중의 판단을 대표하지 않습니다. 수치와 맥락은 해당 기준 시각에 저장된 근거 범위에서만 해석해야 합니다.",
  caution_note:
    "이 내용은 공개 예측시장 참여자 데이터에 나타난 흐름을 정리한 것이며, 전체 대중의 판단을 대표하거나 현실의 결과를 입증하지 않습니다. 24시간 변화 폭이 큰 구간은 단기 변동에 민감할 수 있으므로 다른 자료를 통해 독립적으로 확인해야 합니다.",
};

const CANDIDATES: IssueReportContextCandidate[] = [
  {
    id: "66666666-6666-4666-8666-666666666661",
    title: "관련 당사자 간 다자 협의 일정이 공개됨",
    event_at: "2026-07-02T09:00:00Z",
    summary: "공식 공개 자료에 다자 협의 일정과 참여 범위가 기록되었습니다.",
    sources: [
      {
        title: "다자 협의 일정 공지",
        url: "https://example.gov/notices/dialogue-schedule",
        domain: "example.gov",
        published_at: "2026-07-02T08:30:00Z",
        source_type: "official",
      },
    ],
  },
  {
    id: "66666666-6666-4666-8666-666666666662",
    title: "공개 브리핑 문서가 배포됨",
    event_at: "2026-07-04T09:00:00Z",
    summary:
      "서로 다른 공개 출처에 브리핑의 일정과 핵심 문서가 기록되었습니다.",
    sources: [
      {
        title: "공개 브리핑 안내",
        url: "https://example.org/briefing/public-note",
        domain: "example.org",
        published_at: "2026-07-04T08:00:00Z",
        source_type: "independent_secondary",
      },
      {
        title: "브리핑 문서 요약",
        url: "https://news.example.com/context/briefing",
        domain: "news.example.com",
        published_at: null,
        source_type: "independent_secondary",
      },
    ],
  },
  {
    id: "66666666-6666-4666-8666-666666666663",
    title: "후속 공개 일정이 문서에 추가됨",
    event_at: "2026-07-06T09:00:00Z",
    summary:
      "공식 공개 문서에 후속 일정과 확인 가능한 기준 시각이 추가되었습니다.",
    sources: [
      {
        title: "후속 일정 문서",
        url: "https://example.gov/notices/follow-up",
        domain: "example.gov",
        published_at: "2026-07-06T08:15:00Z",
        source_type: "official",
      },
    ],
  },
];

function fixture(
  id: string,
  candidates: IssueReportContextCandidate[],
): IssueReportSuccessResponse {
  return {
    id,
    status: "success",
    report_version: "v4",
    generated_at: "2026-07-08T00:05:00Z",
    data_as_of: "2026-07-07T23:00:00Z",
    episode_at: "2026-07-07T23:00:00Z",
    content: {
      ...BASE_CONTENT,
      context_summary:
        candidates.length === 0
          ? null
          : "같은 검토 구간에 기록된 공개 정보 후보를 근거 범위 안에서 정리했습니다. " +
            candidates.map((candidate) => candidate.summary).join(" "),
    },
    evidence_refs: [
      "metric:1",
      ...candidates.map((candidate) => `candidate:${candidate.id}`),
    ],
    context_candidates: candidates,
  };
}

export const V4_FIXTURE_ZERO = fixture(
  "77777777-7777-4777-8777-777777777770",
  [],
);
export const V4_FIXTURE_ONE = fixture(
  "77777777-7777-4777-8777-777777777771",
  CANDIDATES.slice(0, 1),
);
export const V4_FIXTURE_THREE = fixture(
  "77777777-7777-4777-8777-777777777773",
  CANDIDATES,
);

export function getDevelopmentReportFixture(
  name: string | null,
): IssueReportSuccessResponse | null {
  if (
    typeof window === "undefined" ||
    (window.location.hostname !== "localhost" &&
      window.location.hostname !== "127.0.0.1")
  ) {
    return null;
  }
  if (name === "v4-0") return V4_FIXTURE_ZERO;
  if (name === "v4-1") return V4_FIXTURE_ONE;
  if (name === "v4-3") return V4_FIXTURE_THREE;
  return null;
}
