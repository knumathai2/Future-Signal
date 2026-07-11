/** Strict runtime parser for the ADR-048 v5 evidence bundle. */
import type {
  IssueReportContent,
  IssueReportContextCandidate,
  IssueReportContextSource,
  IssueReportLoadState,
  IssueReportSuccessResponse,
} from "../types/issue";

type LengthBounds = { min: number; max: number };

const CONTENT_KEYS: ReadonlySet<keyof IssueReportContent> = new Set([
  "executive_summary",
  "current_data_interpretation",
  "conditional_scenarios",
  "factors_to_check",
  "signals_to_watch",
  "evidence_synthesis",
  "relationship_boundary",
  "data_limitations",
  "caution_note",
]);

const CONTENT_LENGTH_BOUNDS: Record<string, LengthBounds> = {
  executive_summary: { min: 80, max: 1200 },
  current_data_interpretation: { min: 50, max: 1200 },
  evidence_synthesis: { min: 50, max: 1800 },
  relationship_boundary: { min: 50, max: 500 },
  data_limitations: { min: 50, max: 900 },
  caution_note: { min: 120, max: 700 },
};

const SUCCESS_KEYS = new Set([
  "id",
  "status",
  "report_version",
  "generated_at",
  "data_as_of",
  "episode_at",
  "content",
  "evidence_refs",
  "context_candidates",
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
const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const UTC_ISO_TIMESTAMP_PATTERN =
  /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?(Z|\+00:00)$/;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasExactKeys(
  raw: Record<string, unknown>,
  keys: ReadonlySet<string>,
): boolean {
  const rawKeys = Object.keys(raw);
  return rawKeys.length === keys.size && rawKeys.every((key) => keys.has(key));
}

function unicodeCodePointLength(value: string): number {
  return Array.from(value.trim()).length;
}

function sentenceCount(value: string): number {
  const matches = value.trim().match(/[.!?]+(?=\s|$)/g);
  return matches?.length ?? 1;
}

function normalizeUtcIsoTimestamp(value: string): string | null {
  const match = UTC_ISO_TIMESTAMP_PATTERN.exec(value);
  if (!match) {
    return null;
  }
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) {
    return null;
  }
  const parsedDate = new Date(parsed);
  const [, year, month, day, hour, minute, second] = match;
  if (
    parsedDate.getUTCFullYear() !== Number(year) ||
    parsedDate.getUTCMonth() + 1 !== Number(month) ||
    parsedDate.getUTCDate() !== Number(day) ||
    parsedDate.getUTCHours() !== Number(hour) ||
    parsedDate.getUTCMinutes() !== Number(minute) ||
    parsedDate.getUTCSeconds() !== Number(second)
  ) {
    return null;
  }
  const fraction = (match[7] ?? "").padEnd(6, "0");
  return `${year}-${month}-${day}T${hour}:${minute}:${second}.${fraction}Z`;
}

function validateContent(raw: unknown): IssueReportContent | null {
  if (!isRecord(raw) || !hasExactKeys(raw, CONTENT_KEYS)) {
    return null;
  }
  const record = raw;
  function text(key: string, nullable = false): string | null | undefined {
    const value = record[key];
    if (nullable && value === null) return null;
    if (typeof value !== "string") {
      return undefined;
    }
    const trimmed = value.trim();
    const bounds = CONTENT_LENGTH_BOUNDS[key];
    const length = unicodeCodePointLength(trimmed);
    if (
      length < bounds.min ||
      length > bounds.max ||
      sentenceCount(trimmed) > 5
    ) {
      return undefined;
    }
    return trimmed;
  }
  function items(
    key: string,
    bodyKey: "narrative" | "explanation",
    min: number,
    max: number,
  ) {
    const value = record[key];
    if (!Array.isArray(value) || value.length < min || value.length > max) return null;
    const parsed = value.map((item) => {
      if (!isRecord(item) || !hasExactKeys(item, new Set(["title", bodyKey, "basis"]))) return null;
      if (typeof item.title !== "string" || typeof item[bodyKey] !== "string") return null;
      if (
        item.basis !== "market_definition" &&
        item.basis !== "observed_data" &&
        item.basis !== "verified_context" &&
        item.basis !== "data_limitation"
      ) return null;
      const title = item.title.trim();
      const body = item[bodyKey].trim();
      if (title.length < 2 || body.length < 20 || sentenceCount(body) > 5) return null;
      return { title, [bodyKey]: body, basis: item.basis };
    });
    return parsed.some((item) => item === null) ? null : parsed;
  }
  const executiveSummary = text("executive_summary");
  const currentDataInterpretation = text("current_data_interpretation");
  const evidenceSynthesis = text("evidence_synthesis", true);
  const relationshipBoundary = text("relationship_boundary");
  const dataLimitations = text("data_limitations");
  const cautionNote = text("caution_note");
  const conditionalScenarios = items("conditional_scenarios", "narrative", 1, 4);
  const factorsToCheck = items("factors_to_check", "explanation", 2, 6);
  const signalsToWatch = items("signals_to_watch", "explanation", 2, 6);
  if (
    typeof executiveSummary !== "string" || typeof currentDataInterpretation !== "string" ||
    evidenceSynthesis === undefined || relationshipBoundary === undefined ||
    typeof relationshipBoundary !== "string" || typeof dataLimitations !== "string" ||
    typeof cautionNote !== "string" ||
    conditionalScenarios === null || factorsToCheck === null || signalsToWatch === null
  ) return null;
  return {
    executive_summary: executiveSummary,
    current_data_interpretation: currentDataInterpretation,
    conditional_scenarios: conditionalScenarios as IssueReportContent["conditional_scenarios"],
    factors_to_check: factorsToCheck as IssueReportContent["factors_to_check"],
    signals_to_watch: signalsToWatch as IssueReportContent["signals_to_watch"],
    evidence_synthesis: evidenceSynthesis,
    relationship_boundary: relationshipBoundary,
    data_limitations: dataLimitations,
    caution_note: cautionNote,
  };
}

function validateSource(
  raw: unknown,
  generatedAt: string,
): IssueReportContextSource | null {
  if (!isRecord(raw) || !hasExactKeys(raw, SOURCE_KEYS)) {
    return null;
  }
  if (
    typeof raw.title !== "string" ||
    raw.title.trim().length === 0 ||
    typeof raw.url !== "string" ||
    typeof raw.domain !== "string" ||
    raw.domain.trim().length === 0 ||
    (raw.source_type !== "official" &&
      raw.source_type !== "independent_secondary")
  ) {
    return null;
  }
  let sourceUrl: URL;
  try {
    sourceUrl = new URL(raw.url);
  } catch {
    return null;
  }
  if (
    (sourceUrl.protocol !== "http:" && sourceUrl.protocol !== "https:") ||
    sourceUrl.username !== "" ||
    sourceUrl.password !== "" ||
    sourceUrl.hostname.toLowerCase() !== raw.domain.trim().toLowerCase()
  ) {
    return null;
  }
  let publishedAt: string | null = null;
  if (raw.published_at !== null) {
    if (typeof raw.published_at !== "string") {
      return null;
    }
    publishedAt = normalizeUtcIsoTimestamp(raw.published_at);
    if (publishedAt === null || publishedAt > generatedAt) {
      return null;
    }
  }
  return {
    title: raw.title.trim(),
    url: raw.url,
    domain: raw.domain.trim().toLowerCase(),
    published_at: raw.published_at === null ? null : raw.published_at,
    source_type: raw.source_type,
  };
}

function validateCandidate(
  raw: unknown,
  generatedAt: string,
): IssueReportContextCandidate | null {
  if (!isRecord(raw) || !hasExactKeys(raw, CANDIDATE_KEYS)) {
    return null;
  }
  if (
    typeof raw.id !== "string" ||
    !UUID_PATTERN.test(raw.id) ||
    typeof raw.title !== "string" ||
    raw.title.trim().length === 0 ||
    typeof raw.summary !== "string" ||
    raw.summary.trim().length === 0 ||
    typeof raw.event_at !== "string" ||
    !Array.isArray(raw.sources) ||
    raw.sources.length === 0
  ) {
    return null;
  }
  const eventAt = normalizeUtcIsoTimestamp(raw.event_at);
  if (eventAt === null || eventAt > generatedAt) {
    return null;
  }
  const sources = raw.sources.map((source) =>
    validateSource(source, generatedAt),
  );
  if (sources.some((source) => source === null)) {
    return null;
  }
  return {
    id: raw.id,
    title: raw.title.trim(),
    event_at: raw.event_at,
    summary: raw.summary.trim(),
    sources: sources as IssueReportContextSource[],
  };
}

export function parseReportResponse(raw: unknown): IssueReportLoadState {
  if (!isRecord(raw)) {
    return { status: "error" };
  }
  if (raw.status === "not_yet_generated") {
    return hasExactKeys(raw, new Set(["status"]))
      ? { status: "not_yet_generated" }
      : { status: "error" };
  }
  if (
    raw.status !== "success" ||
    raw.report_version !== "v5" ||
    !hasExactKeys(raw, SUCCESS_KEYS) ||
    typeof raw.id !== "string" ||
    !UUID_PATTERN.test(raw.id) ||
    typeof raw.generated_at !== "string" ||
    typeof raw.data_as_of !== "string" ||
    typeof raw.episode_at !== "string" ||
    !Array.isArray(raw.evidence_refs) ||
    !Array.isArray(raw.context_candidates) ||
    raw.context_candidates.length > 3
  ) {
    return { status: "error" };
  }
  const generatedAt = normalizeUtcIsoTimestamp(raw.generated_at);
  const dataAsOf = normalizeUtcIsoTimestamp(raw.data_as_of);
  const episodeAt = normalizeUtcIsoTimestamp(raw.episode_at);
  if (
    generatedAt === null ||
    dataAsOf === null ||
    episodeAt === null ||
    dataAsOf > generatedAt ||
    episodeAt > generatedAt
  ) {
    return { status: "error" };
  }
  const content = validateContent(raw.content);
  if (content === null) {
    return { status: "error" };
  }
  const candidates = raw.context_candidates.map((candidate) =>
    validateCandidate(candidate, generatedAt),
  );
  if (candidates.some((candidate) => candidate === null)) {
    return { status: "error" };
  }
  const typedCandidates = candidates as IssueReportContextCandidate[];
  const candidateIds = typedCandidates.map((candidate) => candidate.id);
  if (new Set(candidateIds).size !== candidateIds.length) {
    return { status: "error" };
  }
  const expectedRefs = [
    raw.evidence_refs[0],
    ...candidateIds.map((id) => `candidate:${id}`),
  ];
  if (
    typeof raw.evidence_refs[0] !== "string" ||
    !/^metric:\d+$/.test(raw.evidence_refs[0]) ||
    raw.evidence_refs.length !== expectedRefs.length ||
    !raw.evidence_refs.every(
      (reference, index) => reference === expectedRefs[index],
    ) ||
    (content.evidence_synthesis === null) !== (typedCandidates.length === 0)
  ) {
    return { status: "error" };
  }

  const report: IssueReportSuccessResponse = {
    id: raw.id,
    status: "success",
    report_version: "v5",
    generated_at: raw.generated_at,
    data_as_of: raw.data_as_of,
    episode_at: raw.episode_at,
    content,
    evidence_refs: raw.evidence_refs as string[],
    context_candidates: typedCandidates,
  };
  return { status: "success", report };
}
