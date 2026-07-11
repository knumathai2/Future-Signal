/** Strict runtime parser for the ADR-050 v6 evidence-aware report bundle. */
import type {
  GeneralScenario,
  IssueReportBriefing,
  IssueReportContextCandidate,
  IssueReportContextSource,
  IssueReportLoadState,
  IssueReportMode,
  IssueReportObservedChange,
  IssueReportResolutionReference,
  IssueReportSuccessResponse,
  MaterialToCheck,
  VerifiedBlock,
  VerifiedInterpretation,
} from "../types/issue";

const SUCCESS_KEYS = new Set([
  "id",
  "status",
  "report_version",
  "report_mode",
  "generated_at",
  "data_as_of",
  "episode_at",
  "observed_change",
  "briefing",
  "resolution_reference",
  "evidence_refs",
  "context_candidates",
  "relationship_boundary",
  "data_limitations",
  "caution_note",
]);
const CANDIDATE_KEYS = new Set([
  "id",
  "title",
  "event_at",
  "summary",
  "sources",
]);
const SOURCE_KEYS = new Set([
  "title",
  "url",
  "domain",
  "published_at",
  "source_type",
]);
const OBSERVED_KEYS = new Set([
  "metric_id",
  "window",
  "current_value",
  "change_value",
  "significant",
  "threshold",
]);
const REFERENCE_KEYS = new Set([
  "status",
  "condition_text",
  "deadline",
  "exclusions",
  "source_url",
]);
const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const UTC_ISO_TIMESTAMP_PATTERN =
  /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?(Z|\+00:00)$/;
const MODES = new Set<IssueReportMode>([
  "change_with_evidence",
  "change_without_evidence",
  "stable_with_evidence",
  "stable_without_evidence",
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasExactKeys(raw: Record<string, unknown>, keys: ReadonlySet<string>) {
  const rawKeys = Object.keys(raw);
  return rawKeys.length === keys.size && rawKeys.every((key) => keys.has(key));
}

function normalizeUtcIsoTimestamp(value: string): string | null {
  const match = UTC_ISO_TIMESTAMP_PATTERN.exec(value);
  if (!match || !Number.isFinite(Date.parse(value))) return null;
  const parsed = new Date(value);
  const [, year, month, day, hour, minute, second] = match;
  if (
    parsed.getUTCFullYear() !== Number(year) ||
    parsed.getUTCMonth() + 1 !== Number(month) ||
    parsed.getUTCDate() !== Number(day) ||
    parsed.getUTCHours() !== Number(hour) ||
    parsed.getUTCMinutes() !== Number(minute) ||
    parsed.getUTCSeconds() !== Number(second)
  )
    return null;
  return value;
}

function safeExternalUrl(value: unknown): string | null {
  if (typeof value !== "string") return null;
  try {
    const url = new URL(value);
    if (
      (url.protocol !== "http:" && url.protocol !== "https:") ||
      url.username ||
      url.password
    )
      return null;
    return value;
  } catch {
    return null;
  }
}

function cleanText(value: unknown, min: number, max: number): string | null {
  if (typeof value !== "string") return null;
  const text = value.trim();
  const length = Array.from(text).length;
  return length >= min && length <= max ? text : null;
}

function parseUuidList(value: unknown, min = 1): string[] | null {
  if (!Array.isArray(value) || value.length < min || value.length > 3)
    return null;
  if (
    !value.every((item) => typeof item === "string" && UUID_PATTERN.test(item))
  )
    return null;
  return new Set(value).size === value.length ? value : null;
}

function validateSource(
  raw: unknown,
  generatedAt: string,
): IssueReportContextSource | null {
  if (!isRecord(raw) || !hasExactKeys(raw, SOURCE_KEYS)) return null;
  const title = cleanText(raw.title, 1, 500);
  const url = safeExternalUrl(raw.url);
  if (
    title === null ||
    url === null ||
    typeof raw.domain !== "string" ||
    (raw.source_type !== "official" &&
      raw.source_type !== "independent_secondary")
  )
    return null;
  const parsedUrl = new URL(url);
  const domain = raw.domain.trim().toLowerCase();
  if (!domain || parsedUrl.hostname.toLowerCase() !== domain) return null;
  if (raw.published_at !== null) {
    if (
      typeof raw.published_at !== "string" ||
      normalizeUtcIsoTimestamp(raw.published_at) === null ||
      raw.published_at > generatedAt
    )
      return null;
  }
  return {
    title,
    url,
    domain,
    published_at: raw.published_at as string | null,
    source_type: raw.source_type,
  };
}

function validateCandidate(
  raw: unknown,
  generatedAt: string,
): IssueReportContextCandidate | null {
  if (!isRecord(raw) || !hasExactKeys(raw, CANDIDATE_KEYS)) return null;
  const title = cleanText(raw.title, 1, 500);
  const summary = cleanText(raw.summary, 1, 1800);
  if (
    typeof raw.id !== "string" ||
    !UUID_PATTERN.test(raw.id) ||
    title === null ||
    summary === null ||
    typeof raw.event_at !== "string" ||
    normalizeUtcIsoTimestamp(raw.event_at) === null ||
    raw.event_at > generatedAt ||
    !Array.isArray(raw.sources) ||
    raw.sources.length === 0
  )
    return null;
  const sources = raw.sources.map((source) =>
    validateSource(source, generatedAt),
  );
  if (sources.some((source) => source === null)) return null;
  return {
    id: raw.id,
    title,
    event_at: raw.event_at,
    summary,
    sources: sources as IssueReportContextSource[],
  };
}

function validateObserved(raw: unknown): IssueReportObservedChange | null {
  if (!isRecord(raw) || !hasExactKeys(raw, OBSERVED_KEYS)) return null;
  if (
    !Number.isInteger(raw.metric_id) ||
    raw.window !== "24h" ||
    typeof raw.current_value !== "number" ||
    raw.current_value < 0 ||
    raw.current_value > 1 ||
    (raw.change_value !== null && typeof raw.change_value !== "number") ||
    typeof raw.significant !== "boolean" ||
    raw.threshold !== 0.05
  )
    return null;
  return raw as unknown as IssueReportObservedChange;
}

function validateReference(
  raw: unknown,
): IssueReportResolutionReference | null {
  if (!isRecord(raw) || !hasExactKeys(raw, REFERENCE_KEYS)) return null;
  if (raw.status !== "available" && raw.status !== "unavailable") return null;
  if (
    !Array.isArray(raw.exclusions) ||
    !raw.exclusions.every((item) => typeof item === "string")
  ) {
    return null;
  }
  if (raw.status === "unavailable") {
    if (
      raw.condition_text !== null ||
      raw.deadline !== null ||
      raw.exclusions.length !== 0 ||
      raw.source_url !== null
    )
      return null;
  } else {
    if (cleanText(raw.condition_text, 1, 5000) === null) return null;
    if (
      raw.deadline !== null &&
      (typeof raw.deadline !== "string" ||
        normalizeUtcIsoTimestamp(raw.deadline) === null)
    )
      return null;
    if (raw.source_url !== null && safeExternalUrl(raw.source_url) === null)
      return null;
  }
  return raw as unknown as IssueReportResolutionReference;
}

function validateGeneralScenario(raw: unknown): GeneralScenario | null {
  if (!isRecord(raw) || !hasExactKeys(raw, new Set(["title", "text", "basis"])))
    return null;
  const title = cleanText(raw.title, 2, 100);
  const text = cleanText(raw.text, 30, 900);
  if (title === null || text === null || raw.basis !== "general_scenario")
    return null;
  if (
    !["만약", "경우", "된다면", "않는다면"].some((token) =>
      text.includes(token),
    )
  )
    return null;
  return { title, text, basis: "general_scenario" };
}

function validateMaterial(raw: unknown): MaterialToCheck | null {
  if (
    !isRecord(raw) ||
    !hasExactKeys(raw, new Set(["scenario_index", "title", "text", "basis"]))
  )
    return null;
  const title = cleanText(raw.title, 2, 120);
  const text = cleanText(raw.text, 20, 700);
  const scenarioIndex = raw.scenario_index;
  if (
    typeof scenarioIndex !== "number" ||
    !Number.isInteger(scenarioIndex) ||
    scenarioIndex < 1 ||
    scenarioIndex > 4 ||
    title === null ||
    text === null ||
    raw.basis !== "general_scenario"
  )
    return null;
  return {
    scenario_index: scenarioIndex,
    title,
    text,
    basis: "general_scenario",
  };
}

function validateVerifiedBlock(raw: unknown): VerifiedBlock | null {
  if (
    !isRecord(raw) ||
    !hasExactKeys(raw, new Set(["text", "basis", "candidate_ids"]))
  ) {
    return null;
  }
  const text = cleanText(raw.text, 30, 1200);
  const candidateIds = parseUuidList(raw.candidate_ids);
  if (
    text === null ||
    raw.basis !== "verified_context" ||
    candidateIds === null
  )
    return null;
  return { text, basis: "verified_context", candidate_ids: candidateIds };
}

function validateInterpretation(raw: unknown): VerifiedInterpretation | null {
  if (
    !isRecord(raw) ||
    !hasExactKeys(raw, new Set(["title", "text", "basis", "candidate_ids"]))
  )
    return null;
  const title = cleanText(raw.title, 2, 100);
  const text = cleanText(raw.text, 30, 900);
  const candidateIds = parseUuidList(raw.candidate_ids);
  if (
    title === null ||
    text === null ||
    raw.basis !== "verified_context" ||
    candidateIds === null ||
    !["만약", "경우", "된다면", "않는다면"].some((token) =>
      text.includes(token),
    )
  )
    return null;
  return {
    title,
    text,
    basis: "verified_context",
    candidate_ids: candidateIds,
  };
}

function parseArray<T>(
  value: unknown,
  parser: (item: unknown) => T | null,
  min: number,
  max: number,
): T[] | null {
  if (!Array.isArray(value) || value.length < min || value.length > max)
    return null;
  const parsed = value.map(parser);
  return parsed.some((item) => item === null) ? null : (parsed as T[]);
}

function validateBriefing(
  raw: unknown,
  mode: IssueReportMode,
): IssueReportBriefing | null {
  if (!isRecord(raw) || raw.mode !== mode) return null;
  if (mode === "change_with_evidence") {
    if (
      !hasExactKeys(
        raw,
        new Set(["mode", "verified_background", "conditional_interpretations"]),
      )
    )
      return null;
    const background = validateVerifiedBlock(raw.verified_background);
    const items = parseArray(
      raw.conditional_interpretations,
      validateInterpretation,
      1,
      4,
    );
    return background && items
      ? {
          mode,
          verified_background: background,
          conditional_interpretations: items,
        }
      : null;
  }
  if (mode === "change_without_evidence") {
    if (
      !hasExactKeys(
        raw,
        new Set(["mode", "conditional_scenarios", "materials_to_check"]),
      )
    )
      return null;
    const scenarios = parseArray(
      raw.conditional_scenarios,
      validateGeneralScenario,
      1,
      4,
    );
    const materials = parseArray(
      raw.materials_to_check,
      validateMaterial,
      1,
      8,
    );
    return scenarios &&
      materials &&
      materialsCoverScenarios(scenarios, materials)
      ? {
          mode,
          conditional_scenarios: scenarios,
          materials_to_check: materials,
        }
      : null;
  }
  if (mode === "stable_with_evidence") {
    if (
      !hasExactKeys(
        raw,
        new Set([
          "mode",
          "issue_explanation",
          "verified_background",
          "conditional_scenarios",
        ]),
      )
    )
      return null;
    const issue = validateSimpleBlock(
      raw.issue_explanation,
      "market_definition",
    );
    const background = validateVerifiedBlock(raw.verified_background);
    const scenarios = parseArray(
      raw.conditional_scenarios,
      validateGeneralScenario,
      1,
      4,
    );
    return issue && background && scenarios
      ? {
          mode,
          issue_explanation: issue,
          verified_background: background,
          conditional_scenarios: scenarios,
        }
      : null;
  }
  if (
    !hasExactKeys(
      raw,
      new Set([
        "mode",
        "issue_explanation",
        "conditional_scenarios",
        "materials_to_check",
      ]),
    )
  )
    return null;
  const issue = validateSimpleBlock(raw.issue_explanation, "general_scenario");
  const scenarios = parseArray(
    raw.conditional_scenarios,
    validateGeneralScenario,
    1,
    4,
  );
  const materials = parseArray(raw.materials_to_check, validateMaterial, 1, 8);
  return issue &&
    scenarios &&
    materials &&
    materialsCoverScenarios(scenarios, materials)
    ? {
        mode,
        issue_explanation: issue,
        conditional_scenarios: scenarios,
        materials_to_check: materials,
      }
    : null;
}

function validateSimpleBlock<
  B extends "market_definition" | "general_scenario",
>(raw: unknown, basis: B): { text: string; basis: B } | null {
  if (!isRecord(raw) || !hasExactKeys(raw, new Set(["text", "basis"])))
    return null;
  const text = cleanText(raw.text, 30, 900);
  return text !== null && raw.basis === basis ? { text, basis } : null;
}

function materialsCoverScenarios(
  scenarios: GeneralScenario[],
  materials: MaterialToCheck[],
) {
  const indices = new Set(materials.map((item) => item.scenario_index));
  return (
    scenarios.every((_, index) => indices.has(index + 1)) &&
    [...indices].every((index) => index <= scenarios.length)
  );
}

function briefingBodies(briefing: IssueReportBriefing): string[] {
  switch (briefing.mode) {
    case "change_with_evidence":
      return [
        briefing.verified_background.text,
        ...briefing.conditional_interpretations.map((item) => item.text),
      ];
    case "change_without_evidence":
      return [
        ...briefing.conditional_scenarios.map((item) => item.text),
        ...briefing.materials_to_check.map((item) => item.text),
      ];
    case "stable_with_evidence":
      return [
        briefing.issue_explanation.text,
        briefing.verified_background.text,
        ...briefing.conditional_scenarios.map((item) => item.text),
      ];
    case "stable_without_evidence":
      return [
        briefing.issue_explanation.text,
        ...briefing.conditional_scenarios.map((item) => item.text),
        ...briefing.materials_to_check.map((item) => item.text),
      ];
  }
}

function canonical(value: string) {
  return value
    .normalize("NFKC")
    .toLocaleLowerCase()
    .replace(/\d+(?:[.,:/-]\d+)*/g, "#")
    .replace(/[^a-z가-힣#]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokens(value: string) {
  return new Set(
    canonical(value)
      .split(" ")
      .filter((token) => token.length >= 2),
  );
}

function hasDuplicateBodies(briefing: IssueReportBriefing) {
  const bodies = briefingBodies(briefing);
  const normalized = bodies.map(canonical);
  if (new Set(normalized).size !== normalized.length) return true;
  return bodies.some((left, index) =>
    bodies.slice(index + 1).some((right) => {
      const leftTokens = tokens(left);
      const rightTokens = tokens(right);
      const union = new Set([...leftTokens, ...rightTokens]);
      const overlap = [...leftTokens].filter((token) =>
        rightTokens.has(token),
      ).length;
      return (
        Math.min(leftTokens.size, rightTokens.size) >= 4 &&
        overlap / union.size >= 0.82
      );
    }),
  );
}

function repeatsRule(
  briefing: IssueReportBriefing,
  reference: IssueReportResolutionReference,
) {
  if (reference.status !== "available" || reference.condition_text === null)
    return false;
  const ruleTokens = tokens(reference.condition_text);
  return briefingBodies(briefing).some((body) => {
    const overlap = [...tokens(body)].filter((token) =>
      ruleTokens.has(token),
    ).length;
    return (
      canonical(body).includes(canonical(reference.condition_text as string)) ||
      (overlap >= 4 && overlap / Math.max(1, ruleTokens.size) >= 0.7)
    );
  });
}

function verifiedCandidateIds(briefing: IssueReportBriefing): string[] {
  if (briefing.mode === "change_with_evidence")
    return briefing.verified_background.candidate_ids;
  if (briefing.mode === "stable_with_evidence")
    return briefing.verified_background.candidate_ids;
  return [];
}

export function parseReportResponse(raw: unknown): IssueReportLoadState {
  if (!isRecord(raw)) return { status: "error" };
  if (raw.status === "not_yet_generated") {
    return hasExactKeys(raw, new Set(["status"]))
      ? { status: "not_yet_generated" }
      : { status: "error" };
  }
  if (
    raw.status !== "success" ||
    raw.report_version !== "v6" ||
    !hasExactKeys(raw, SUCCESS_KEYS) ||
    typeof raw.report_mode !== "string" ||
    !MODES.has(raw.report_mode as IssueReportMode) ||
    typeof raw.id !== "string" ||
    !UUID_PATTERN.test(raw.id) ||
    typeof raw.generated_at !== "string" ||
    typeof raw.data_as_of !== "string" ||
    typeof raw.episode_at !== "string" ||
    !Array.isArray(raw.evidence_refs) ||
    !Array.isArray(raw.context_candidates) ||
    raw.context_candidates.length > 3
  )
    return { status: "error" };

  const mode = raw.report_mode as IssueReportMode;
  const generatedAt = normalizeUtcIsoTimestamp(raw.generated_at);
  const dataAsOf = normalizeUtcIsoTimestamp(raw.data_as_of);
  const episodeAt = normalizeUtcIsoTimestamp(raw.episode_at);
  if (
    !generatedAt ||
    !dataAsOf ||
    !episodeAt ||
    dataAsOf > generatedAt ||
    episodeAt > generatedAt
  ) {
    return { status: "error" };
  }
  const observed = validateObserved(raw.observed_change);
  const reference = validateReference(raw.resolution_reference);
  const briefing = validateBriefing(raw.briefing, mode);
  const relationshipBoundary = cleanText(raw.relationship_boundary, 50, 500);
  const dataLimitations = cleanText(raw.data_limitations, 50, 900);
  const cautionNote = cleanText(raw.caution_note, 120, 700);
  if (
    !observed ||
    !reference ||
    !briefing ||
    !relationshipBoundary ||
    !dataLimitations ||
    !cautionNote
  ) {
    return { status: "error" };
  }
  if (
    briefingBodies(briefing).some((text) => /\d/.test(text)) ||
    hasDuplicateBodies(briefing) ||
    repeatsRule(briefing, reference)
  ) {
    return { status: "error" };
  }

  const candidates = raw.context_candidates.map((candidate) =>
    validateCandidate(candidate, generatedAt),
  );
  if (candidates.some((candidate) => candidate === null))
    return { status: "error" };
  const typedCandidates = candidates as IssueReportContextCandidate[];
  const candidateIds = typedCandidates.map((candidate) => candidate.id);
  if (new Set(candidateIds).size !== candidateIds.length)
    return { status: "error" };
  const expectedRefs = [
    `metric:${observed.metric_id}`,
    ...candidateIds.map((id) => `candidate:${id}`),
  ];
  const hasEvidence = mode.endsWith("with_evidence");
  const hasChange = mode.startsWith("change_");
  if (
    raw.evidence_refs.length !== expectedRefs.length ||
    !raw.evidence_refs.every((ref, index) => ref === expectedRefs[index]) ||
    hasEvidence !== candidateIds.length > 0 ||
    hasChange !== observed.significant ||
    verifiedCandidateIds(briefing).join("|") !== candidateIds.join("|")
  )
    return { status: "error" };
  if (briefing.mode === "change_with_evidence") {
    const allowed = new Set(candidateIds);
    if (
      briefing.conditional_interpretations.some((item) =>
        item.candidate_ids.some((id) => !allowed.has(id)),
      )
    ) {
      return { status: "error" };
    }
  }

  const report: IssueReportSuccessResponse = {
    id: raw.id,
    status: "success",
    report_version: "v6",
    report_mode: mode,
    generated_at: raw.generated_at,
    data_as_of: raw.data_as_of,
    episode_at: raw.episode_at,
    observed_change: observed,
    briefing,
    resolution_reference: reference,
    evidence_refs: raw.evidence_refs as string[],
    context_candidates: typedCandidates,
    relationship_boundary: relationshipBoundary,
    data_limitations: dataLimitations,
    caution_note: cautionNote,
  };
  return { status: "success", report };
}
