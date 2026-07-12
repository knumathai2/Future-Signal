import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import ts from "typescript";

const parserUrl = new URL("../src/utils/reportParser.ts", import.meta.url);
const compiled = ts.transpileModule(readFileSync(parserUrl, "utf8"), {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
  },
}).outputText;
const parserModule = { exports: {} };
vm.runInNewContext(
  compiled,
  { exports: parserModule.exports, module: parserModule, URL },
  { filename: parserUrl.pathname },
);
const { parseGenerationStreamBlock, parseReportResponse } =
  parserModule.exports;

const requestId = "88888888-8888-4888-8888-888888888888";
const fingerprint = "a".repeat(64);

function report(overrides = {}) {
  return {
    id: "77777777-7777-4777-8777-777777777777",
    status: "fresh",
    report_version: "v8",
    headline: "공식 조건과 현재 자료를 함께 정리한 브리핑",
    summary:
      "이 이슈는 저장된 설명에 따라 공식 조건이 충족되는지를 확인합니다. 현재 자료에는 기준 시각의 관찰값과 최근 비교값이 포함되어 있습니다. 최근 흐름은 이전보다 달라졌지만 실제 결과를 뜻하지 않으며, 제공된 근거 범위에서 현재 상황과 앞으로 확인할 조건을 함께 정리합니다.",
    sections: [
      {
        type: "current_situation",
        title: "이슈의 기준",
        format: "paragraph",
        content:
          "저장된 이슈 설명에 따라 공식 조건이 충족되는지를 확인하는 대상입니다.",
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
        ],
        evidence_refs: ["metric:1"],
      },
    ],
    sources: [],
    generated_at: "2026-07-11T09:05:00Z",
    data_as_of: "2026-07-11T09:00:00Z",
    context_as_of: null,
    cache: {
      state: "fresh",
      input_fingerprint: fingerprint,
      current_fingerprint: fingerprint,
    },
    data_limitations:
      "공개 데이터는 전체 대중의 판단을 대표하지 않으며 저장 범위 안에서 해석해야 합니다.",
    caution_note:
      "이 브리핑은 현실의 향후 결과를 예측하거나 자료 사이의 원인을 입증하지 않습니다.",
    request_id: null,
    request_error_code: null,
    ...overrides,
  };
}

for (const raw of [
  { status: "idle" },
  {
    status: "generating",
    request_id: requestId,
    input_fingerprint: fingerprint,
    requested_at: "2026-07-11T09:10:00Z",
  },
  { status: "failed", request_id: requestId, error_code: "generation_failed" },
  report(),
  report({
    generated_at: "2026-07-11T09:05:00+00:00",
    data_as_of: "2026-07-11T09:00:00.123456Z",
  }),
  report({
    status: "stale",
    cache: {
      state: "stale",
      input_fingerprint: fingerprint,
      current_fingerprint: "b".repeat(64),
    },
  }),
  report({ status: "generating", request_id: requestId }),
  report({
    status: "failed_with_last_good",
    request_id: requestId,
    request_error_code: "generation_failed",
  }),
]) {
  assert.equal(parseReportResponse(raw).status, "ready");
}

const source = {
  id: "source:fixture",
  context_ref: "context:66666666-6666-4666-8666-666666666666",
  citation_id: "citation:fixture",
  title: "기관 공식 문서",
  url: "https://example.gov/document",
  domain: "example.gov",
  source_level: "A",
  supported_claims: [
    {
      ref: "claim:fixture",
      text: "기관이 공식 문서를 공개했습니다.",
      excerpt: "공식 문서가 공개되었습니다.",
      citation_id: "citation:fixture",
    },
  ],
  retrieved_at: "2026-07-11T08:30:00Z",
};
const withSource = report({
  context_as_of: "2026-07-11T08:30:00Z",
  sources: [source],
  sections: [
    ...report().sections,
    {
      type: "interpretation",
      title: "확인된 자료",
      format: "paragraph",
      content:
        "기관이 공개한 문서의 지원 문장을 출처와 함께 확인할 수 있습니다.",
      items: [],
      evidence_refs: [source.context_ref, source.id],
    },
  ],
});
assert.equal(parseReportResponse(withSource).status, "ready");
const rootSourceUrl = "https://example.gov";
const rootSourceReport = {
  ...withSource,
  sources: [{ ...source, url: rootSourceUrl }],
};
const parsedRootSourceReport = parseReportResponse(rootSourceReport);
assert.equal(parsedRootSourceReport.status, "ready");
assert.equal(parsedRootSourceReport.response.sources[0].url, rootSourceUrl);

const streamedHeader = {
  sequence: 0,
  block_type: "headline_summary",
  payload: {
    kind: "headline_summary",
    headline: report().headline,
    summary: report().summary,
  },
};
const streamedSection = {
  sequence: 1,
  block_type: "section",
  payload: {
    kind: "section",
    index: 0,
    section: report().sections[0],
  },
};
assert.equal(
  parseGenerationStreamBlock(streamedHeader)?.block_type,
  "headline_summary",
);
assert.equal(
  parseGenerationStreamBlock(streamedSection)?.block_type,
  "section",
);
assert.equal(
  parseGenerationStreamBlock({
    ...streamedSection,
    payload: { ...streamedSection.payload, index: 1 },
  }),
  null,
);

for (const invalid of [
  { status: "idle", unexpected: true },
  report({ report_version: "v7" }),
  report({ data_as_of: "2026-07-11T10:00:00Z" }),
  report({ status: "generating", request_id: null }),
  report({ status: "fresh", request_id: requestId }),
  report({ sections: [report().sections[1], report().sections[1]] }),
  { ...withSource, sources: [{ ...source, domain: "different.example" }] },
  { ...withSource, sources: [{ ...source, source_level: "D" }] },
  {
    ...withSource,
    sources: [
      {
        ...source,
        supported_claims: [
          { ...source.supported_claims[0], citation_id: "citation:other" },
        ],
      },
    ],
  },
]) {
  assert.equal(parseReportResponse(invalid).status, "error");
}

console.log("v8 report parser regression checks passed");
