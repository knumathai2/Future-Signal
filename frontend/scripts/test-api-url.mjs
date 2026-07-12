import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import ts from "typescript";

const moduleUrl = new URL("../src/utils/apiUrl.ts", import.meta.url);
const source = readFileSync(moduleUrl, "utf8").replace(
  "import.meta.env?.VITE_API_BASE_URL",
  "undefined",
);
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
  },
}).outputText;
const apiUrlModule = { exports: {} };
vm.runInNewContext(
  compiled,
  { exports: apiUrlModule.exports, module: apiUrlModule, URL },
  { filename: moduleUrl.pathname },
);
const { apiUrl, buildApiUrl, normalizeApiBaseUrl } = apiUrlModule.exports;

assert.equal(apiUrl("/api/issues"), "/api/issues");
assert.equal(normalizeApiBaseUrl(undefined), "");
assert.equal(normalizeApiBaseUrl("  "), "");
assert.equal(
  normalizeApiBaseUrl(" https://api.example.com/ "),
  "https://api.example.com",
);
assert.equal(
  buildApiUrl("/api/issues?q=%ED%95%9C%EA%B8%80", "https://api.example.com/"),
  "https://api.example.com/api/issues?q=%ED%95%9C%EA%B8%80",
);

for (const invalidBase of [
  "api.example.com",
  "ftp://api.example.com",
  "https://user:secret@api.example.com",
  "https://api.example.com/base",
  "https://api.example.com?version=1",
  "https://api.example.com/#fragment",
]) {
  assert.throws(
    () => normalizeApiBaseUrl(invalidBase),
    /absolute HTTP\(S\) origin/,
  );
}

for (const invalidPath of ["api/issues", "//other.example/api/issues"]) {
  assert.throws(() => apiUrl(invalidPath), /exactly one slash/);
}

console.log("API URL regression checks passed");
