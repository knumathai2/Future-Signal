/** Development-only v6 bundles for responsive/browser verification. */
import type {
  IssueReportBriefing,
  IssueReportContextCandidate,
  IssueReportMode,
  IssueReportSuccessResponse,
} from "../types/issue";

const CANDIDATES: IssueReportContextCandidate[] = [
  {
    id: "66666666-6666-4666-8666-666666666661",
    title: "관련 당사자 간 다자 협의 일정이 공개됨",
    event_at: "2026-07-05T09:00:00Z",
    summary: "공식 공개 자료에 다자 협의 일정과 참여 범위가 기록되었습니다.",
    sources: [
      {
        title: "다자 협의 일정 공지",
        url: "https://example.gov/notices/dialogue-schedule",
        domain: "example.gov",
        published_at: "2026-07-05T08:30:00Z",
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
        published_at: null,
        source_type: "official",
      },
    ],
  },
];

const scenario = {
  title: "공개 협의 범위가 달라지는 경우",
  text: "만약 공개 협의의 범위가 달라지는 경우 관련 문서가 다루는 상황을 일반적으로 구분해 살펴볼 수 있습니다.",
  basis: "general_scenario" as const,
};
const material = {
  scenario_index: 1,
  title: "공개 문서 범위",
  text: "공개 협의의 참여 범위와 후속 자료가 다루는 항목을 확인할 자료입니다.",
  basis: "general_scenario" as const,
};

function verifiedBackground(candidates: IssueReportContextCandidate[]) {
  return {
    text: "공식 공개 자료에는 다자 협의 일정과 참여 범위가 기록되어 있으며 관찰 흐름과의 관계를 입증하지 않습니다.",
    basis: "verified_context" as const,
    candidate_ids: candidates.map((candidate) => candidate.id),
  };
}

function briefing(
  mode: IssueReportMode,
  candidates: IssueReportContextCandidate[],
): IssueReportBriefing {
  if (mode === "change_with_evidence") {
    return {
      mode,
      verified_background: verifiedBackground(candidates),
      conditional_interpretations: [
        {
          title: "후속 자료가 같은 범위를 다루는 경우",
          text: "만약 후속 공개 자료가 같은 협의 범위를 다루는 경우 자료에 기록된 범위를 조건부로 비교할 수 있습니다.",
          basis: "verified_context",
          candidate_ids: [candidates[0].id],
        },
      ],
    };
  }
  if (mode === "change_without_evidence") {
    return {
      mode,
      conditional_scenarios: [scenario],
      materials_to_check: [material],
    };
  }
  if (mode === "stable_with_evidence") {
    return {
      mode,
      issue_explanation: {
        text: "이 이슈는 공개 협의가 공적 기록에서 어떤 범위로 다뤄지는지를 살펴보는 항목입니다.",
        basis: "market_definition",
      },
      verified_background: verifiedBackground(candidates),
      conditional_scenarios: [scenario],
    };
  }
  return {
    mode,
    issue_explanation: {
      text: "이 이슈는 공개 협의의 여러 상황을 이해하기 위한 통상적인 구분을 다루는 항목입니다.",
      basis: "general_scenario",
    },
    conditional_scenarios: [scenario],
    materials_to_check: [material],
  };
}

function fixture(
  id: string,
  mode: IssueReportMode,
  candidates: IssueReportContextCandidate[],
): IssueReportSuccessResponse {
  const significant = mode.startsWith("change_");
  return {
    id,
    status: "success",
    report_version: "v6",
    report_mode: mode,
    generated_at: "2026-07-08T00:05:00Z",
    data_as_of: "2026-07-07T23:00:00Z",
    episode_at: "2026-07-07T23:00:00Z",
    observed_change: {
      metric_id: 1,
      window: "24h",
      current_value: 0.432,
      change_value: significant ? -0.061 : -0.01,
      significant,
      threshold: 0.05,
    },
    briefing: briefing(mode, candidates),
    resolution_reference: {
      status: "available",
      condition_text:
        "공개 문서에 적힌 조건이 기준일까지 충족되는지를 판정합니다.",
      deadline: "2026-12-31T00:00:00Z",
      exclusions: ["임시 상태는 포함하지 않습니다."],
      source_url: "https://example.gov/rules",
    },
    evidence_refs: [
      "metric:1",
      ...candidates.map((candidate) => `candidate:${candidate.id}`),
    ],
    context_candidates: candidates,
    relationship_boundary:
      "관찰된 움직임은 공개 데이터에 기록된 흐름이며 현실의 결과 또는 함께 제시된 공개 정보와의 관계를 입증하지 않습니다.",
    data_limitations:
      "공개 예측시장 참여자 데이터는 전체 대중의 판단을 대표하지 않습니다. 수치와 맥락은 해당 기준 시각에 저장된 근거 범위에서만 해석해야 합니다.",
    caution_note:
      "이 내용은 공개 예측시장 참여자 데이터에 나타난 흐름을 정리한 것이며 전체 대중의 판단을 대표하거나 현실의 결과를 입증하지 않습니다. 활동 수준과 변동에 따라 해석 범위가 달라질 수 있으므로 다른 자료를 통해 독립적으로 확인해야 합니다.",
  };
}

function trumpStableNoEvidenceFixture(): IssueReportSuccessResponse {
  return {
    ...fixture(
      "77777777-7777-4777-8777-777777777775",
      "stable_without_evidence",
      [],
    ),
    generated_at: "2026-07-11T07:00:00Z",
    data_as_of: "2026-07-11T06:37:15.248359Z",
    episode_at: "2026-07-11T06:37:15.248359Z",
    observed_change: {
      metric_id: 486,
      window: "24h",
      current_value: 0.055,
      change_value: 0,
      significant: false,
      threshold: 0.05,
    },
    briefing: {
      mode: "stable_without_evidence",
      issue_explanation: {
        text: "Trump 대통령직 변화 이슈를 이해하기 위한 일반적인 상황 구분을 다루는 항목입니다.",
        basis: "general_scenario",
      },
      conditional_scenarios: [
        {
          title: "공식 기록의 범위가 달라지는 경우",
          text: "만약 Trump 대통령직과 관련된 공식 기록의 범위가 달라지는 경우 문서가 다루는 상태를 일반적으로 구분해 살펴볼 수 있습니다.",
          basis: "general_scenario",
        },
      ],
      materials_to_check: [
        {
          scenario_index: 1,
          title: "공식 기록의 문서 범위",
          text: "대통령직 상태를 다루는 공식 기록의 문서 유형과 공개 주체를 확인할 자료입니다.",
          basis: "general_scenario",
        },
      ],
    },
    resolution_reference: {
      status: "available",
      condition_text:
        'This market will resolve to "Yes" if President of the United States Donald Trump announces he has resigned or will resign the presidency by December 31, 2026, 11:59 PM ET. Otherwise, this market will resolve to "No."',
      deadline: "2026-12-31T00:00:00Z",
      exclusions: [],
      source_url: null,
    },
    evidence_refs: ["metric:486"],
  };
}

const FIXTURES = new Map<string, IssueReportSuccessResponse>([
  [
    "v6-change-evidence",
    fixture(
      "77777777-7777-4777-8777-777777777771",
      "change_with_evidence",
      CANDIDATES.slice(0, 1),
    ),
  ],
  [
    "v6-change-no-evidence",
    fixture(
      "77777777-7777-4777-8777-777777777772",
      "change_without_evidence",
      [],
    ),
  ],
  [
    "v6-stable-evidence",
    fixture(
      "77777777-7777-4777-8777-777777777773",
      "stable_with_evidence",
      CANDIDATES,
    ),
  ],
  [
    "v6-stable-no-evidence",
    fixture(
      "77777777-7777-4777-8777-777777777774",
      "stable_without_evidence",
      [],
    ),
  ],
  ["v6-trump-stable-no-evidence", trumpStableNoEvidenceFixture()],
]);

export function getDevelopmentReportFixture(
  name: string | null,
): IssueReportSuccessResponse | null {
  if (
    typeof window === "undefined" ||
    (window.location.hostname !== "localhost" &&
      window.location.hostname !== "127.0.0.1")
  )
    return null;
  return name ? (FIXTURES.get(name) ?? null) : null;
}
