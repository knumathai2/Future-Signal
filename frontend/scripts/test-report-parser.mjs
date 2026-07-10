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
  {
    exports: parserModule.exports,
    module: parserModule,
  },
  { filename: parserUrl.pathname },
);

const { getVisibleSections, parseReportResponse } = parserModule.exports;

const validContent = {
  issue_overview: "가".repeat(30),
  current_data_reading: "나".repeat(50),
  possible_outlook: "다".repeat(60),
  possible_drivers: "라".repeat(80),
  external_context: "마".repeat(40),
  what_to_check: "바".repeat(30),
  data_limitations: "사".repeat(80),
  caution_note: "아".repeat(120),
};

function makePayload(overrides = {}) {
  return {
    id: "7c2e1a90-0000-4000-8000-0000000000aa",
    status: "success",
    report_version: "v3",
    generated_at: "2026-07-10T09:05:00Z",
    data_as_of: "2026-07-10T09:00:00Z",
    content: validContent,
    ...overrides,
  };
}

assert.equal(parseReportResponse(makePayload()).status, "success");

const fullState = parseReportResponse(makePayload());
assert.equal(fullState.status, "success");
assert.deepEqual(
  Array.from(getVisibleSections(fullState.report.content), (section) => section.key),
  [
    "issue_overview",
    "current_data_reading",
    "external_context",
    "possible_drivers",
    "possible_outlook",
    "what_to_check",
    "data_limitations",
    "caution_note",
  ],
);

const nullContextState = parseReportResponse(
  makePayload({
    content: { ...validContent, external_context: null },
  }),
);
assert.equal(nullContextState.status, "success");
assert.deepEqual(
  Array.from(
    getVisibleSections(nullContextState.report.content),
    (section) => section.key,
  ),
  [
    "issue_overview",
    "current_data_reading",
    "possible_drivers",
    "possible_outlook",
    "what_to_check",
    "data_limitations",
    "caution_note",
  ],
);
assert.equal(
  parseReportResponse(
    makePayload({
      generated_at: "2026-07-10T09:05:00+00:00",
      data_as_of: "2026-07-10T09:00:00+00:00",
    }),
  ).status,
  "success",
);

for (const invalidPayload of [
  makePayload({ data_as_of: "not-a-date" }),
  makePayload({ data_as_of: "July 10, 2026 09:00 UTC" }),
  makePayload({ data_as_of: "2026-07-10T10:00:00Z" }),
  makePayload({ data_as_of: "2026-02-30T09:00:00Z" }),
  makePayload({
    generated_at: "2026-07-10T09:00:00.123455Z",
    data_as_of: "2026-07-10T09:00:00.123456Z",
  }),
  makePayload({
    content: {
      ...validContent,
      issue_overview:
        "첫 문장입니다. 둘째 문장입니다. 셋째 문장입니다. " +
        "넷째 문장입니다. 다섯째 문장입니다. 여섯째 문장입니다.",
    },
  }),
]) {
  assert.equal(parseReportResponse(invalidPayload).status, "error");
}

const paddedOverview = `\n${validContent.issue_overview}\n`;
const normalizedState = parseReportResponse(
  makePayload({
    content: {
      ...validContent,
      issue_overview: paddedOverview,
    },
  }),
);
assert.equal(normalizedState.status, "success");
assert.equal(normalizedState.report.content.issue_overview, validContent.issue_overview);

console.log("report parser regression checks passed");
