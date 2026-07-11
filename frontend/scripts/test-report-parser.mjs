import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import ts from "typescript";

const parserUrl = new URL("../src/utils/reportParser.ts", import.meta.url);
const parserSource = readFileSync(parserUrl, "utf8");
const compiledParser = ts.transpileModule(parserSource, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
  },
}).outputText;
const parserModule = { exports: {} };
vm.runInNewContext(
  compiledParser,
  { exports: parserModule.exports, module: parserModule, URL },
  { filename: parserUrl.pathname },
);
const { parseReportResponse } = parserModule.exports;

const candidateId = "66666666-6666-4666-8666-666666666666";
const candidate = {
  id: candidateId,
  title: "검증된 공개 정보 후보",
  event_at: "2026-07-11T08:30:00Z",
  summary: "공개 자료에 기록된 내용을 근거 범위 안에서 정리했습니다.",
  sources: [
    {
      title: "공식 공개 자료",
      url: "https://example.gov/context",
      domain: "example.gov",
      published_at: "2026-07-11T08:00:00Z",
      source_type: "official",
    },
  ],
};
const scenario = {
  title: "공개 문서 범위가 달라지는 경우",
  text: "만약 공개 문서의 범위가 달라지는 경우 관련 상황을 일반적으로 구분해 살펴볼 수 있습니다.",
  basis: "general_scenario",
};
const material = {
  scenario_index: 1,
  title: "공개 문서 범위",
  text: "공개 문서가 다루는 항목과 후속 자료의 범위를 확인할 자료입니다.",
  basis: "general_scenario",
};
const verified = {
  text: "공식 공개 자료에는 관련 정보가 기록되어 있으며 관찰 흐름과의 관계를 입증하지 않습니다.",
  basis: "verified_context",
  candidate_ids: [candidateId],
};

function briefing(mode) {
  if (mode === "change_with_evidence")
    return {
      mode,
      verified_background: verified,
      conditional_interpretations: [
        {
          title: "후속 자료가 같은 범위를 다루는 경우",
          text: "만약 후속 공개 자료가 같은 범위를 다루는 경우 기록된 배경을 조건부로 비교할 수 있습니다.",
          basis: "verified_context",
          candidate_ids: [candidateId],
        },
      ],
    };
  if (mode === "change_without_evidence")
    return {
      mode,
      conditional_scenarios: [scenario],
      materials_to_check: [material],
    };
  if (mode === "stable_with_evidence")
    return {
      mode,
      issue_explanation: {
        text: "이 이슈는 공개 문서가 공적 기록에서 다뤄지는 범위를 살펴보는 항목입니다.",
        basis: "market_definition",
      },
      verified_background: verified,
      conditional_scenarios: [scenario],
    };
  return {
    mode,
    issue_explanation: {
      text: "이 이슈는 공개 문서의 여러 상황을 이해하기 위한 통상적인 구분을 다룹니다.",
      basis: "general_scenario",
    },
    conditional_scenarios: [scenario],
    materials_to_check: [material],
  };
}

function makePayload(mode = "change_with_evidence", overrides = {}) {
  const candidates = mode.endsWith("with_evidence") ? [candidate] : [];
  const significant = mode.startsWith("change_");
  return {
    id: "77777777-7777-4777-8777-777777777777",
    status: "success",
    report_version: "v6",
    report_mode: mode,
    generated_at: "2026-07-11T09:05:00Z",
    data_as_of: "2026-07-11T09:00:00Z",
    episode_at: "2026-07-11T09:00:00Z",
    observed_change: {
      metric_id: 1,
      window: "24h",
      current_value: 0.55,
      change_value: significant ? 0.08 : 0.01,
      significant,
      threshold: 0.05,
    },
    briefing: briefing(mode),
    resolution_reference: {
      status: "available",
      condition_text: "문서에 적힌 조건이 기준일까지 충족되는지를 판정합니다.",
      deadline: "2026-12-31T00:00:00Z",
      exclusions: [],
      source_url: null,
    },
    evidence_refs: [
      "metric:1",
      ...candidates.map((item) => `candidate:${item.id}`),
    ],
    context_candidates: candidates,
    relationship_boundary:
      "관찰된 움직임은 공개 데이터에 기록된 흐름이며 현실 결과 또는 함께 제시된 공개 정보와의 관계를 입증하지 않습니다.",
    data_limitations:
      "공개 예측시장 참여자 데이터는 전체 대중의 판단을 대표하지 않습니다. 저장된 근거 범위에서만 해석해야 합니다.",
    caution_note:
      "이 내용은 공개 예측시장 참여자 데이터에 나타난 흐름을 정리한 것이며 전체 대중의 판단을 대표하거나 현실의 결과를 입증하지 않습니다. 활동 수준과 변동에 따라 해석 범위가 달라질 수 있으므로 다른 자료를 통해 독립적으로 확인해야 합니다.",
    ...overrides,
  };
}

for (const mode of [
  "change_with_evidence",
  "change_without_evidence",
  "stable_with_evidence",
  "stable_without_evidence",
]) {
  const result = parseReportResponse(makePayload(mode));
  assert.equal(result.status, "success");
  assert.equal(result.report.report_mode, mode);
}

assert.equal(
  parseReportResponse({ status: "not_yet_generated" }).status,
  "not_yet_generated",
);

const duplicateBriefing = briefing("change_without_evidence");
duplicateBriefing.materials_to_check[0].text =
  duplicateBriefing.conditional_scenarios[0].text;

for (const invalid of [
  makePayload("change_with_evidence", { report_version: "v5" }),
  makePayload("change_with_evidence", { data_as_of: "2026-07-11T10:00:00Z" }),
  makePayload("change_with_evidence", { evidence_refs: ["metric:1"] }),
  makePayload("change_with_evidence", { context_candidates: [] }),
  makePayload("change_with_evidence", {
    briefing: { ...briefing("change_with_evidence"), unexpected: true },
  }),
  makePayload("change_without_evidence", { briefing: duplicateBriefing }),
  makePayload("change_without_evidence", {
    briefing: {
      ...briefing("change_without_evidence"),
      conditional_scenarios: [
        { ...scenario, text: `${scenario.text} 현재 값은 55입니다.` },
      ],
    },
  }),
  makePayload("change_with_evidence", {
    context_candidates: [
      {
        ...candidate,
        sources: [{ ...candidate.sources[0], domain: "different.example" }],
      },
    ],
  }),
  makePayload("change_with_evidence", {
    context_candidates: [
      {
        ...candidate,
        sources: [{ ...candidate.sources[0], citation_id: "internal" }],
      },
    ],
  }),
  makePayload("stable_without_evidence", {
    report_mode: "change_without_evidence",
  }),
])
  assert.equal(parseReportResponse(invalid).status, "error");

console.log("v6 report parser regression checks passed");
