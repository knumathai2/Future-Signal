/**
 * Typed v3 report fixture data for browser verification.
 *
 * These fixtures exercise the ADR-033 contract without a live v3 DB row.
 * They are used for local development and are not shipped in production.
 */
import type { IssueReportSuccessResponse } from "../types/issue";

// ---------------------------------------------------------------------------
// Valid v3 fixtures
// ---------------------------------------------------------------------------

/**
 * Full v3 success response with non-null external_context (8 visible sections).
 */
export const V3_FIXTURE_FULL: IssueReportSuccessResponse = {
  id: "fixture-v3-full-0001",
  status: "success",
  report_version: "v3",
  generated_at: "2026-07-10T09:05:00Z",
  data_as_of: "2026-07-10T09:00:00Z",
  content: {
    issue_overview:
      "이 이슈는 공개된 기한까지 문서에 적힌 조건이 충족되는지를 추적합니다. " +
      "현재 해당 조건의 충족 여부에 대한 관심이 공개 예측시장 데이터에 반영되어 있습니다.",
    current_data_reading:
      "데이터 기준 시각에 공개 예측시장 참여자 데이터에 반영된 기대값은 63%이며, " +
      "24시간 전보다 8.2퍼센트포인트 높게 관찰되었습니다. 7일 전과 비교하면 " +
      "11.0퍼센트포인트 상승 방향으로 관찰되었습니다.",
    possible_outlook:
      "이후 공개 데이터에서 관찰된 움직임의 지속, 확대 또는 완화가 확인되더라도, " +
      "이는 데이터의 흐름만 설명하며 현실의 결과나 변화의 이유를 입증하지 않습니다. " +
      "어떤 방향이든 독립적 확인이 필요합니다.",
    possible_drivers:
      "수동 검토를 마친 맥락 후보의 제목과 기록 날짜는 관찰된 움직임과 함께 비교할 수 있습니다. " +
      "해당 시점은 비교를 위해 제공되며, 현재 데이터는 이 맥락 후보와 움직임 사이의 관계를 " +
      "입증하지 않습니다.",
    external_context:
      "수동 검토를 마친 맥락 메모는 관찰된 움직임과 함께 살펴볼 정보로만 제공되며, " +
      "변화의 원인으로 제시되지 않습니다.",
    what_to_check:
      "이슈에 적힌 기준과 기한, 맥락 후보의 기록 날짜, 이후 공개 데이터 갱신 내용을 " +
      "추가로 확인해야 합니다.",
    data_limitations:
      "이 읽기는 활동량, 유동성, 24시간 변화 폭, 24시간 및 7일 이력 범위의 영향을 받습니다. " +
      "공개 예측시장 참여자 데이터는 전체 대중의 판단을 대표하지 않습니다.",
    caution_note:
      "이 내용은 공개 예측시장 참여자 데이터에 나타난 흐름을 정리한 것이며, " +
      "전체 대중의 판단을 대표하거나 현실의 결과를 입증하지 않습니다. " +
      "24시간 및 7일 비교 지점이 있고 활동량과 유동성이 설정된 하한보다 낮지 않으며 " +
      "24시간 변화 폭이 큰 움직임 기준을 넘지 않지만, " +
      "다른 자료를 통해 독립적으로 확인해야 합니다.",
  },
};

/**
 * v3 success response with external_context=null (7 visible sections).
 */
export const V3_FIXTURE_NULL_CONTEXT: IssueReportSuccessResponse = {
  id: "fixture-v3-null-ctx-0002",
  status: "success",
  report_version: "v3",
  generated_at: "2026-07-10T09:05:00Z",
  data_as_of: "2026-07-10T09:00:00Z",
  content: {
    ...V3_FIXTURE_FULL.content,
    external_context: null,
    possible_drivers:
      "이 움직임과 함께 비교할 수 있도록 수동 검토를 마친 맥락 후보가 없습니다. " +
      "현재 데이터는 관찰된 움직임만 보여 주며, 추가 맥락은 다른 자료를 통해 " +
      "독립적으로 확인해야 합니다.",
  },
};

/**
 * v3 success with maximum-length content for wrapping/layout verification.
 * Each field is padded to near the ADR-033 upper bound.
 */
export const V3_FIXTURE_MAX_LENGTH: IssueReportSuccessResponse = {
  id: "fixture-v3-max-len-0003",
  status: "success",
  report_version: "v3",
  generated_at: "2026-07-10T09:05:00Z",
  data_as_of: "2026-07-10T09:00:00Z",
  content: {
    issue_overview:
      "이 이슈는 공개된 기한까지 특정 조건의 충족 여부를 추적합니다. " +
      "해당 조건에 대한 공개 데이터의 기대값 변화가 관찰되고 있으며, " +
      "이 관찰은 데이터에 반영된 흐름일 뿐 실제 결과를 입증하지 않습니다. " +
      "조건의 정의와 기한은 원본 문서에서 확인할 수 있으며, " +
      "여기에서 제시하는 값은 공개 예측시장 참여자 데이터에서 도출된 것입니다. " +
      "이 이슈의 배경과 맥락을 이해하려면 추가 자료를 참고해야 하며, " +
      "공개 데이터만으로는 충분한 판단이 어렵습니다. " +
      "현재까지 관찰된 데이터 흐름은 참고용이며 실제 결과와 직접 연결되지 않고, " +
      "데이터의 활동 수준과 참여 범위도 제한적일 수 있습니다.",
    current_data_reading:
      "데이터 기준 시각에 공개 예측시장 참여자 데이터에 반영된 기대값은 63%이며 " +
      "이전 24시간 동안 8.2퍼센트포인트 상승 방향으로 관찰되었습니다. " +
      "7일 전과 비교하면 11.0퍼센트포인트 상승 방향으로 관찰되었으며, " +
      "이 기간 동안 기대값은 꾸준히 한 방향으로 움직였습니다. " +
      "활동량은 일정 수준 이상으로 유지되고 있으나, " +
      "이 읽기는 공개 데이터에 반영된 흐름일 뿐 실제 사건의 발생 확률을 의미하지 않습니다. " +
      "변동폭이 확대되는 구간에서는 한 시점의 읽기에 과도한 의미를 부여하지 않아야 합니다. " +
      "데이터 기준 시각 이후의 변화는 이 읽기에 포함되지 않습니다.",
    possible_outlook:
      "이후 공개 데이터에서 관찰된 움직임의 지속, 확대 또는 완화가 확인되더라도, " +
      "이는 데이터의 흐름만 설명하며 현실의 결과나 변화의 이유를 입증하지 않습니다. " +
      "지속적인 상승 흐름이 관찰되더라도 이것이 조건 충족 가능성의 증가를 의미하지 않으며, " +
      "반대로 하락 흐름이 관찰되더라도 조건 불충족을 의미하지 않습니다. " +
      "어떤 방향이든 독립적 확인이 필요하며, 단기 움직임에 과도한 의미를 부여하지 않아야 합니다. " +
      "공개 데이터의 특성상 참여자 구성과 활동 수준에 따라 흐름이 달라질 수 있습니다.",
    possible_drivers:
      "수동 검토를 마친 맥락 후보의 제목과 기록 날짜는 관찰된 움직임과 함께 비교할 수 있습니다. " +
      "해당 시점은 비교를 위해 제공되며, 현재 데이터는 이 맥락 후보와 움직임 사이의 관계를 입증하지 않습니다. " +
      "맥락 후보는 수동 검토를 거친 것이며, 자동으로 수집되거나 매칭된 것이 아닙니다. " +
      "제공된 맥락 후보 외에 추가적인 요인이 존재할 수 있으며, " +
      "여기에 나열되지 않은 요인도 움직임과 관련될 수 있습니다. " +
      "이 섹션은 원인 분석이 아니라 비교 참고용입니다.",
    external_context:
      "수동 검토를 마친 맥락 메모는 관찰된 움직임과 함께 살펴볼 정보로만 제공되며, " +
      "변화의 원인으로 제시되지 않습니다. 관련 사건의 시기와 내용은 독립적으로 확인해야 하며, " +
      "이 맥락 메모가 움직임을 설명한다고 해석하지 않아야 합니다. " +
      "자동 수집된 뉴스나 분석이 아니라 수동으로 정리된 참고 자료입니다. " +
      "맥락 메모에 포함된 날짜와 제목은 원본 출처에서 재확인해야 합니다.",
    what_to_check:
      "이슈에 적힌 기준과 기한을 원본 문서에서 확인해야 합니다. " +
      "맥락 후보의 기록 날짜와 출처를 독립적으로 검증해야 합니다. " +
      "이후 공개 데이터 갱신 내용을 추적하여 흐름의 변화를 관찰할 수 있습니다. " +
      "데이터 기준 시각과 현재 시각 사이의 차이를 고려해야 합니다. " +
      "활동량과 유동성 수준의 변화도 함께 확인해야 합니다.",
    data_limitations:
      "이 읽기는 활동량, 유동성, 24시간 변화 폭, 24시간 및 7일 이력 범위의 영향을 받습니다. " +
      "공개 예측시장 참여자 데이터는 전체 대중의 판단을 대표하지 않습니다. " +
      "참여자의 수와 구성이 제한적일 수 있으며, 특정 시간대의 활동 편향이 존재할 수 있습니다. " +
      "유동성이 낮은 경우 소수의 참여가 기대값에 큰 영향을 미칠 수 있습니다. " +
      "이력 범위가 짧은 경우 장기적인 흐름을 파악하기 어렵습니다.",
    caution_note:
      "이 내용은 공개 예측시장 참여자 데이터에 나타난 흐름을 정리한 것이며, " +
      "전체 대중의 판단을 대표하거나 현실의 결과를 입증하지 않습니다. " +
      "24시간 및 7일 비교 지점이 있고 활동량과 유동성이 설정된 하한보다 낮지 않으며 " +
      "24시간 변화 폭이 큰 움직임 기준을 넘지 않지만, " +
      "다른 자료를 통해 독립적으로 확인해야 합니다. " +
      "이 요약은 금융, 법률, 정치 등 전문적 조언을 제공하지 않으며, " +
      "중요한 판단의 유일한 근거로 사용해서는 안 됩니다.",
  },
};

// ---------------------------------------------------------------------------
// Invalid fixture shapes — for testing error-state handling
// ---------------------------------------------------------------------------

/** Missing a required key (no caution_note). */
export const V3_INVALID_MISSING_KEY = {
  id: "fixture-invalid-missing",
  status: "success",
  report_version: "v3",
  generated_at: "2026-07-10T09:05:00Z",
  data_as_of: "2026-07-10T09:00:00Z",
  content: {
    issue_overview: V3_FIXTURE_FULL.content.issue_overview,
    current_data_reading: V3_FIXTURE_FULL.content.current_data_reading,
    possible_outlook: V3_FIXTURE_FULL.content.possible_outlook,
    possible_drivers: V3_FIXTURE_FULL.content.possible_drivers,
    external_context: V3_FIXTURE_FULL.content.external_context,
    what_to_check: V3_FIXTURE_FULL.content.what_to_check,
    data_limitations: V3_FIXTURE_FULL.content.data_limitations,
    // caution_note intentionally missing
  },
};

/** Empty required value. */
export const V3_INVALID_EMPTY_VALUE = {
  id: "fixture-invalid-empty",
  status: "success",
  report_version: "v3",
  generated_at: "2026-07-10T09:05:00Z",
  data_as_of: "2026-07-10T09:00:00Z",
  content: {
    ...V3_FIXTURE_FULL.content,
    issue_overview: "",
  },
};

/** Whitespace-only required value. */
export const V3_INVALID_WHITESPACE = {
  id: "fixture-invalid-whitespace",
  status: "success",
  report_version: "v3",
  generated_at: "2026-07-10T09:05:00Z",
  data_as_of: "2026-07-10T09:00:00Z",
  content: {
    ...V3_FIXTURE_FULL.content,
    current_data_reading: "   \n  ",
  },
};

/** external_context is empty string (invalid — only null hides the section). */
export const V3_INVALID_EMPTY_CONTEXT = {
  id: "fixture-invalid-empty-ctx",
  status: "success",
  report_version: "v3",
  generated_at: "2026-07-10T09:05:00Z",
  data_as_of: "2026-07-10T09:00:00Z",
  content: {
    ...V3_FIXTURE_FULL.content,
    external_context: "",
  },
};

/** Extra content key. */
export const V3_INVALID_EXTRA_KEY = {
  id: "fixture-invalid-extra",
  status: "success",
  report_version: "v3",
  generated_at: "2026-07-10T09:05:00Z",
  data_as_of: "2026-07-10T09:00:00Z",
  content: {
    ...V3_FIXTURE_FULL.content,
    surprise_field: "unexpected",
  },
};

/** Legacy v2 shape — should fail validation. */
export const V3_INVALID_LEGACY_V2 = {
  id: "fixture-invalid-legacy",
  generated_at: "2026-07-10T09:05:00Z",
  data_as_of: "2026-07-10T09:00:00Z",
  status: "success",
  content: {
    issue_explainer: "legacy",
    why_it_matters: "legacy",
    current_reading: "legacy",
    scenario_major_change: "legacy",
    scenario_limited_change: "legacy",
    scenario_status_quo: "legacy",
    check_points: "legacy",
    caution_note: "legacy",
  },
};

/** Missing report_version. */
export const V3_INVALID_NO_VERSION = {
  id: "fixture-invalid-no-ver",
  status: "success",
  generated_at: "2026-07-10T09:05:00Z",
  data_as_of: "2026-07-10T09:00:00Z",
  content: V3_FIXTURE_FULL.content,
};

/** Wrong report_version. */
export const V3_INVALID_WRONG_VERSION = {
  id: "fixture-invalid-wrong-ver",
  status: "success",
  report_version: "v2",
  generated_at: "2026-07-10T09:05:00Z",
  data_as_of: "2026-07-10T09:00:00Z",
  content: V3_FIXTURE_FULL.content,
};
