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
const validContent = {
  executive_summary: "가".repeat(80),
  current_data_interpretation: "나".repeat(50),
  conditional_scenarios: [
    { title: "조건 하나", narrative: "다".repeat(30) },
    { title: "조건 둘", narrative: "라".repeat(30) },
    { title: "조건 셋", narrative: "마".repeat(30) },
  ],
  factors_to_check: [
    { title: "요인 하나", explanation: "바".repeat(20) },
    { title: "요인 둘", explanation: "사".repeat(20) },
  ],
  signals_to_watch: [
    { title: "자료 하나", explanation: "아".repeat(20) },
    { title: "자료 둘", explanation: "자".repeat(20) },
  ],
  evidence_synthesis: "차".repeat(50),
  relationship_boundary: "라".repeat(50),
  data_limitations: "바".repeat(50),
  caution_note: "사".repeat(120),
};
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

function makePayload(overrides = {}) {
  return {
    id: "77777777-7777-4777-8777-777777777777",
    status: "success",
    report_version: "v5",
    generated_at: "2026-07-11T09:05:00Z",
    data_as_of: "2026-07-11T09:00:00Z",
    episode_at: "2026-07-11T09:00:00Z",
    content: validContent,
    evidence_refs: ["metric:1", `candidate:${candidateId}`],
    context_candidates: [candidate],
    ...overrides,
  };
}

const success = parseReportResponse(makePayload());
assert.equal(success.status, "success");
assert.equal(success.report.report_version, "v5");
assert.equal(
  success.report.context_candidates[0].sources[0].domain,
  "example.gov",
);

const noCandidate = parseReportResponse(
  makePayload({
    content: { ...validContent, evidence_synthesis: null },
    evidence_refs: ["metric:1"],
    context_candidates: [],
  }),
);
assert.equal(noCandidate.status, "success");
assert.equal(noCandidate.report.content.evidence_synthesis, null);

const oneScenario = parseReportResponse(
  makePayload({
    content: {
      ...validContent,
      conditional_scenarios: validContent.conditional_scenarios.slice(0, 1),
      evidence_synthesis: null,
    },
    evidence_refs: ["metric:1"],
    context_candidates: [],
  }),
);
assert.equal(oneScenario.status, "success");
assert.equal(oneScenario.report.content.conditional_scenarios.length, 1);

assert.equal(
  parseReportResponse({ status: "not_yet_generated" }).status,
  "not_yet_generated",
);

for (const invalidPayload of [
  makePayload({ report_version: "v3" }),
  makePayload({ data_as_of: "2026-07-11T10:00:00Z" }),
  makePayload({ episode_at: "2026-07-11T10:00:00Z" }),
  makePayload({ evidence_refs: ["metric:1"] }),
  makePayload({ evidence_refs: ["metric:2", "candidate:missing"] }),
  makePayload({ context_candidates: [] }),
  makePayload({ content: { ...validContent, evidence_synthesis: null } }),
  makePayload({ content: { ...validContent, extra: "not allowed" } }),
  makePayload({ unexpected: true }),
  makePayload({
    context_candidates: [
      {
        ...candidate,
        sources: [{ ...candidate.sources[0], domain: "different.example" }],
      },
    ],
  }),
  makePayload({
    context_candidates: [
      {
        ...candidate,
        sources: [{ ...candidate.sources[0], citation_id: "internal" }],
      },
    ],
  }),
  makePayload({
    content: {
      ...validContent,
      executive_summary:
        "첫 문장입니다. 둘째 문장입니다. 셋째 문장입니다. " +
        "넷째 문장입니다. 다섯째 문장입니다. 여섯째 문장입니다.",
    },
  }),
]) {
  assert.equal(parseReportResponse(invalidPayload).status, "error");
}

console.log("v5 report parser regression checks passed");
