/** Strict runtime parser for the ADR-051 v7 on-demand briefing contract. */
import type {
  IssueReportLoadState,
  IssueReportResponse,
  V7IssueReportResponse,
  V7ReportSection,
  V7ReportSectionType,
  V7ReportSource,
  V7SupportedClaim,
} from "../types/issue";

const UUID =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const SHA256 = /^[0-9a-f]{64}$/i;
const UTC_TIMESTAMP =
  /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,6})?(?:Z|\+00:00)$/;
const SECTION_TYPES = new Set<V7ReportSectionType>([
  "issue_overview",
  "current_context",
  "market_data",
  "external_context",
  "uncertainties",
  "what_to_watch",
]);
const FULL_KEYS = new Set([
  "id",
  "status",
  "report_version",
  "headline",
  "summary",
  "sections",
  "sources",
  "generated_at",
  "data_as_of",
  "context_as_of",
  "cache",
  "data_limitations",
  "caution_note",
  "request_id",
  "request_error_code",
]);

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function exact(raw: Record<string, unknown>, keys: ReadonlySet<string>) {
  const actual = Object.keys(raw);
  return actual.length === keys.size && actual.every((key) => keys.has(key));
}

function text(value: unknown, min: number, max: number): string | null {
  if (typeof value !== "string") return null;
  const clean = value.trim();
  const length = Array.from(clean).length;
  return length >= min && length <= max ? clean : null;
}

function timestamp(value: unknown): string | null {
  if (typeof value !== "string" || !UTC_TIMESTAMP.test(value)) return null;
  return Number.isFinite(Date.parse(value)) ? value : null;
}

function uuid(value: unknown): value is string {
  return typeof value === "string" && UUID.test(value);
}

function fingerprint(value: unknown): value is string {
  return typeof value === "string" && SHA256.test(value);
}

function parseClaim(raw: unknown): V7SupportedClaim | null {
  const keys = new Set(["ref", "text", "excerpt", "citation_id"]);
  if (!record(raw) || !exact(raw, keys)) return null;
  const ref = text(raw.ref, 3, 200);
  const claimText = text(raw.text, 1, 1800);
  const excerpt = text(raw.excerpt, 1, 4000);
  const citationId = text(raw.citation_id, 1, 500);
  return ref && claimText && excerpt && citationId
    ? { ref, text: claimText, excerpt, citation_id: citationId }
    : null;
}

function parseSource(raw: unknown, generatedAt: string): V7ReportSource | null {
  const keys = new Set([
    "id",
    "context_ref",
    "citation_id",
    "title",
    "url",
    "domain",
    "source_level",
    "supported_claims",
    "retrieved_at",
  ]);
  if (!record(raw) || !exact(raw, keys)) return null;
  const id = text(raw.id, 3, 200);
  const contextRef = text(raw.context_ref, 3, 200);
  const citationId = text(raw.citation_id, 1, 500);
  const title = text(raw.title, 1, 500);
  const domain = text(raw.domain, 1, 253)?.toLowerCase() ?? null;
  const retrievedAt = timestamp(raw.retrieved_at);
  if (
    !id?.startsWith("source:") ||
    !contextRef?.startsWith("context:") ||
    !citationId ||
    !title ||
    !domain ||
    !retrievedAt ||
    retrievedAt > generatedAt ||
    !["A", "B", "C"].includes(String(raw.source_level)) ||
    !Array.isArray(raw.supported_claims) ||
    raw.supported_claims.length < 1 ||
    raw.supported_claims.length > 8
  )
    return null;
  let url: URL;
  try {
    url = new URL(String(raw.url));
  } catch {
    return null;
  }
  if (
    !["http:", "https:"].includes(url.protocol) ||
    url.username ||
    url.password ||
    url.hostname.toLowerCase() !== domain
  )
    return null;
  const claims = raw.supported_claims.map(parseClaim);
  if (
    claims.some((claim) => claim === null) ||
    claims.some((claim) => claim?.citation_id !== citationId)
  )
    return null;
  return {
    id,
    context_ref: contextRef,
    citation_id: citationId,
    title,
    url: url.toString(),
    domain,
    source_level: raw.source_level as "A" | "B" | "C",
    supported_claims: claims as V7SupportedClaim[],
    retrieved_at: retrievedAt,
  };
}

function parseSection(raw: unknown): V7ReportSection | null {
  const keys = new Set([
    "type",
    "title",
    "format",
    "content",
    "items",
    "evidence_refs",
  ]);
  if (!record(raw) || !exact(raw, keys)) return null;
  const sectionType = raw.type as V7ReportSectionType;
  const title = text(raw.title, 2, 100);
  if (
    !SECTION_TYPES.has(sectionType) ||
    !title ||
    !Array.isArray(raw.items) ||
    raw.items.length > 8 ||
    !Array.isArray(raw.evidence_refs) ||
    raw.evidence_refs.length < 1 ||
    raw.evidence_refs.length > 12 ||
    !raw.evidence_refs.every((ref) => text(ref, 3, 200) !== null) ||
    new Set(raw.evidence_refs).size !== raw.evidence_refs.length
  )
    return null;
  if (raw.format === "paragraph") {
    const content = text(raw.content, 30, 1800);
    if (!content || raw.items.length) return null;
    return {
      type: sectionType,
      title,
      format: "paragraph",
      content,
      items: [],
      evidence_refs: raw.evidence_refs as string[],
    };
  }
  if (
    raw.format !== "bullets" ||
    raw.content !== null ||
    raw.items.length < 1 ||
    !raw.items.every((item) => text(item, 15, 500) !== null)
  )
    return null;
  return {
    type: sectionType,
    title,
    format: "bullets",
    content: null,
    items: raw.items.map((item) => String(item).trim()),
    evidence_refs: raw.evidence_refs as string[],
  };
}

function parseFull(raw: Record<string, unknown>): V7IssueReportResponse | null {
  if (!exact(raw, FULL_KEYS) || raw.report_version !== "v7" || !uuid(raw.id))
    return null;
  if (
    !["fresh", "stale", "generating", "failed_with_last_good"].includes(
      String(raw.status),
    )
  )
    return null;
  const headline = text(raw.headline, 10, 120);
  const summary = text(raw.summary, 40, 900);
  const generatedAt = timestamp(raw.generated_at);
  const dataAsOf = timestamp(raw.data_as_of);
  const contextAsOf =
    raw.context_as_of === null ? null : timestamp(raw.context_as_of);
  const limitations = text(raw.data_limitations, 20, 900);
  const caution = text(raw.caution_note, 20, 900);
  if (
    !headline ||
    !summary ||
    !generatedAt ||
    !dataAsOf ||
    dataAsOf > generatedAt ||
    (raw.context_as_of !== null && !contextAsOf) ||
    (contextAsOf && contextAsOf > generatedAt) ||
    !limitations ||
    !caution ||
    !Array.isArray(raw.sections) ||
    raw.sections.length < 2 ||
    raw.sections.length > 8 ||
    !Array.isArray(raw.sources) ||
    raw.sources.length > 24 ||
    !record(raw.cache) ||
    !exact(
      raw.cache,
      new Set(["state", "input_fingerprint", "current_fingerprint"]),
    ) ||
    !["fresh", "stale"].includes(String(raw.cache.state)) ||
    !fingerprint(raw.cache.input_fingerprint) ||
    (raw.cache.current_fingerprint !== null &&
      !fingerprint(raw.cache.current_fingerprint))
  )
    return null;
  const sections = raw.sections.map(parseSection);
  const sources = raw.sources.map((source) => parseSource(source, generatedAt));
  if (
    sections.some((section) => section === null) ||
    sources.some((source) => source === null)
  )
    return null;
  const typedSections = sections as V7ReportSection[];
  const types = typedSections.map((section) => section.type);
  if (
    !types.some(
      (type) => type === "issue_overview" || type === "current_context",
    ) ||
    types.filter((type) => type === "market_data").length > 1
  )
    return null;
  const typedSources = sources as V7ReportSource[];
  const contextRefs = new Set(typedSources.map((source) => source.context_ref));
  for (const section of typedSections) {
    for (const ref of section.evidence_refs) {
      if (ref.startsWith("context:") && !contextRefs.has(ref)) return null;
      if (ref.startsWith("source:")) {
        const source = typedSources.find((item) => item.id === ref);
        if (!source || !section.evidence_refs.includes(source.context_ref))
          return null;
      }
    }
  }
  const requestId = raw.request_id;
  const requestError = raw.request_error_code;
  if (requestId !== null && !uuid(requestId)) return null;
  if (requestError !== null && !text(requestError, 1, 200)) return null;
  if (raw.status === "generating" && requestId === null) return null;
  if (
    raw.status === "failed_with_last_good" &&
    (requestId === null || requestError === null)
  )
    return null;
  if (
    ["fresh", "stale"].includes(String(raw.status)) &&
    (requestId !== null || requestError !== null)
  )
    return null;
  return {
    ...(raw as unknown as V7IssueReportResponse),
    headline,
    summary,
    sections: typedSections,
    sources: typedSources,
    generated_at: generatedAt,
    data_as_of: dataAsOf,
    context_as_of: contextAsOf,
    data_limitations: limitations,
    caution_note: caution,
  };
}

export function parseReportResponse(raw: unknown): IssueReportLoadState {
  if (!record(raw) || typeof raw.status !== "string")
    return { status: "error" };
  if (raw.status === "idle")
    return exact(raw, new Set(["status"]))
      ? { status: "ready", response: { status: "idle" } }
      : { status: "error" };
  if (raw.status === "generating" && !("report_version" in raw)) {
    const keys = new Set([
      "status",
      "request_id",
      "input_fingerprint",
      "requested_at",
    ]);
    if (
      !exact(raw, keys) ||
      !uuid(raw.request_id) ||
      !fingerprint(raw.input_fingerprint) ||
      !timestamp(raw.requested_at)
    )
      return { status: "error" };
    return { status: "ready", response: raw as IssueReportResponse };
  }
  if (raw.status === "failed") {
    const keys = new Set(["status", "request_id", "error_code"]);
    if (
      !exact(raw, keys) ||
      !uuid(raw.request_id) ||
      !text(raw.error_code, 1, 200)
    )
      return { status: "error" };
    return { status: "ready", response: raw as IssueReportResponse };
  }
  const report = parseFull(raw);
  return report ? { status: "ready", response: report } : { status: "error" };
}
