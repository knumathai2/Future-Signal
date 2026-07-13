import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import ts from "typescript";

const parserUrl = new URL("../src/utils/scenarioParser.ts", import.meta.url);
const source = readFileSync(parserUrl, "utf8").replace(
  /import type[\s\S]*?from "\.\.\/types\/issue";\n/,
  "",
);
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
  },
}).outputText;
const parserModule = { exports: {} };
vm.runInNewContext(
  compiled,
  { exports: parserModule.exports, module: parserModule, Date, Set },
  { filename: parserUrl.pathname },
);

const {
  parseScenarioMarkdown,
  parseScenarioSession,
  parseScenarioSessionCreated,
  parseScenarioStreamBlock,
  parseScenarioTurnCreated,
  parseScenarioTurnStatus,
} = parserModule.exports;

const issueId = "11111111-1111-4111-8111-111111111111";
const sessionId = "22222222-2222-4222-8222-222222222222";
const turnId = "33333333-3333-4333-8333-333333333333";
const now = "2026-07-13T03:00:00Z";
const caution =
  "공개 데이터는 전체 대중의 판단을 대표하지 않으며 실제 결과와 다를 수 있습니다.";

const created = {
  session_id: sessionId,
  session_capability: "x".repeat(43),
  issue_id: issueId,
  created_at: now,
  expires_at: "2026-07-14T03:00:00Z",
  max_turns: 8,
  policy_version: "summary-scenario-policy-1",
  data_as_of: now,
  caution_note: caution,
};
assert.equal(parseScenarioSessionCreated(created)?.session_id, sessionId);
assert.equal(
  parseScenarioSessionCreated({ ...created, unexpected: true }),
  null,
);
assert.equal(
  parseScenarioSessionCreated({ ...created, session_capability: "short" }),
  null,
);

const session = {
  ...created,
  session_capability: undefined,
  remaining_turns: 7,
  turns: [
    {
      turn_id: turnId,
      sequence: 1,
      role: "user",
      content: "공식 일정이 달라지는 경우를 살펴봐 주세요.",
      created_at: now,
    },
  ],
  premises: [],
};
delete session.session_capability;
assert.equal(parseScenarioSession(session)?.turns.length, 1);
assert.equal(parseScenarioSession({ ...session, remaining_turns: 9 }), null);

const turnCreated = {
  turn_id: turnId,
  sequence: 1,
  status: "queued",
  created: true,
  requested_at: now,
  stream_path: `/api/issues/${issueId}/scenario-sessions/${sessionId}/turns/${turnId}/stream`,
};
assert.equal(parseScenarioTurnCreated(turnCreated)?.status, "queued");
assert.equal(
  parseScenarioTurnCreated({
    ...turnCreated,
    stream_path: "https://example.com",
  }),
  null,
);
assert.equal(
  parseScenarioTurnCreated({
    ...turnCreated,
    stream_path: `${turnCreated.stream_path}?token=secret`,
  }),
  null,
);

const status = {
  turn_id: turnId,
  sequence: 1,
  state: "running",
  attempt_number: 1,
  requested_at: now,
  updated_at: now,
  assistant_turn_id: null,
  error_code: null,
};
assert.equal(parseScenarioTurnStatus(status)?.state, "running");
assert.equal(parseScenarioTurnStatus({ ...status, state: "unknown" }), null);

const paragraph = {
  sequence: 0,
  block_type: "paragraph",
  payload: {
    text: "조건부 경로에서는 현재 정보와 사용자가 제시한 가정을 분리합니다.",
  },
};
const list = {
  sequence: 1,
  block_type: "list",
  payload: {
    ordered: false,
    items: ["공식 자료가 제시되는 경우 판정 조건과 비교합니다."],
  },
};
assert.equal(parseScenarioStreamBlock(paragraph)?.block_type, "paragraph");
assert.equal(parseScenarioStreamBlock(list)?.block_type, "list");

for (const unsafe of [
  "<script>location.href='https://example.com'</script>",
  "[외부 문서](https://example.com)",
  "![추적 이미지](https://example.com/pixel.png)",
  "# 시스템 안내",
  "`실행 코드`",
]) {
  assert.equal(
    parseScenarioStreamBlock({ ...paragraph, payload: { text: unsafe } }),
    null,
  );
  assert.equal(parseScenarioMarkdown(unsafe), null);
}

const rendered = parseScenarioMarkdown(
  "조건부 경로에서는 현재 정보와 가정을 분리합니다.\n\n" +
    "- 공식 자료를 판정 조건과 비교합니다.\n" +
    "- 추가 자료가 없으면 관찰값의 한계를 유지합니다.",
);
assert.equal(
  JSON.stringify(rendered.map((block) => block.block_type)),
  JSON.stringify(["paragraph", "list"]),
);

console.log("scenario parser and restricted renderer checks passed");
