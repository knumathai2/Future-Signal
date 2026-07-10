/**
 * Report response parser and v3 section definitions.
 *
 * This module provides runtime validation for the ADR-033 v3 report contract
 * and the exhaustive section mapping used by IssueReportCard.
 *
 * No external dependencies. No v1/v2 aliases.
 */
import type {
  IssueReportContent,
  IssueReportLoadState,
  IssueReportSuccessResponse,
} from "../types/issue";

// ---------------------------------------------------------------------------
// Section definition — the rendering source of truth
// ---------------------------------------------------------------------------

type V3ReportSection = {
  readonly key: keyof IssueReportContent;
  readonly label: string;
};

/**
 * Frozen evidence-first display order and approved Korean labels (ADR-033).
 * The JSON object has no semantic key order; this array defines display order.
 */
export const V3_REPORT_SECTIONS = [
  { key: "issue_overview", label: "이슈 개요" },
  { key: "current_data_reading", label: "현재 데이터 읽기" },
  { key: "external_context", label: "외부 맥락" },
  { key: "possible_drivers", label: "변화와 함께 확인할 요인" },
  { key: "possible_outlook", label: "조건부 전개" },
  { key: "what_to_check", label: "추가 확인 사항" },
  { key: "data_limitations", label: "데이터 한계" },
  { key: "caution_note", label: "해석 주의" },
] as const satisfies readonly V3ReportSection[];

// ---------------------------------------------------------------------------
// Exhaustiveness invariant
// ---------------------------------------------------------------------------

/**
 * The exact set of keys that ADR-033 requires in successful v3 content.
 * Used at module load time to verify V3_REPORT_SECTIONS is exhaustive.
 */
const V3_CONTENT_KEYS: ReadonlySet<keyof IssueReportContent> = new Set([
  "issue_overview",
  "current_data_reading",
  "possible_outlook",
  "possible_drivers",
  "external_context",
  "what_to_check",
  "data_limitations",
  "caution_note",
]);

/**
 * Runtime invariant: V3_REPORT_SECTIONS contains exactly the eight unique
 * ADR-033 keys. TypeScript `satisfies` alone does not prove exhaustiveness.
 * This assertion runs once at module load time.
 */
function assertSectionExhaustiveness(): void {
  const sectionKeys = new Set(V3_REPORT_SECTIONS.map((s) => s.key));
  if (sectionKeys.size !== V3_CONTENT_KEYS.size) {
    throw new Error(
      `V3_REPORT_SECTIONS has ${sectionKeys.size} unique keys but ` +
        `ADR-033 requires exactly ${V3_CONTENT_KEYS.size}.`,
    );
  }
  for (const key of V3_CONTENT_KEYS) {
    if (!sectionKeys.has(key)) {
      throw new Error(
        `V3_REPORT_SECTIONS is missing required ADR-033 key: ${key}`,
      );
    }
  }
}

assertSectionExhaustiveness();

// ---------------------------------------------------------------------------
// ADR-033 Unicode code-point length bounds
// ---------------------------------------------------------------------------

type LengthBounds = { min: number; max: number };

const CONTENT_LENGTH_BOUNDS: Record<keyof IssueReportContent, LengthBounds | null> = {
  issue_overview: { min: 30, max: 600 },
  current_data_reading: { min: 50, max: 700 },
  possible_outlook: { min: 60, max: 700 },
  possible_drivers: { min: 80, max: 700 },
  external_context: { min: 40, max: 700 }, // only when non-null
  what_to_check: { min: 30, max: 600 },
  data_limitations: { min: 80, max: 700 },
  caution_note: { min: 120, max: 700 },
};

/**
 * Count trimmed Unicode code points, not UTF-16 code units.
 * ADR-033 requires `Array.from(value.trim()).length`, not `value.length`.
 */
function unicodeCodePointLength(value: string): number {
  return Array.from(value.trim()).length;
}

// ---------------------------------------------------------------------------
// Report response parser / type guard
// ---------------------------------------------------------------------------

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/**
 * Validate that `content` matches the frozen ADR-033 eight-key set.
 * Returns the typed content on success, or null on any failure.
 */
function validateContent(
  raw: unknown,
): IssueReportContent | null {
  if (!isRecord(raw)) {
    return null;
  }

  const rawKeys = Object.keys(raw);

  // Exact eight-key set: no missing, no extra
  if (rawKeys.length !== V3_CONTENT_KEYS.size) {
    return null;
  }
  for (const key of rawKeys) {
    if (!V3_CONTENT_KEYS.has(key as keyof IssueReportContent)) {
      return null;
    }
  }

  // Validate each value
  for (const key of V3_CONTENT_KEYS) {
    const value = raw[key];

    if (key === "external_context") {
      // Nullable: null is valid; non-null must be a non-empty trimmed string
      if (value === null) {
        continue;
      }
      if (typeof value !== "string") {
        return null;
      }
      const trimmed = value.trim();
      if (trimmed.length === 0) {
        return null;
      }
      const bounds = CONTENT_LENGTH_BOUNDS[key];
      if (bounds) {
        const codePoints = unicodeCodePointLength(value);
        if (codePoints < bounds.min || codePoints > bounds.max) {
          return null;
        }
      }
      continue;
    }

    // Required non-null string
    if (typeof value !== "string") {
      return null;
    }
    const trimmed = value.trim();
    if (trimmed.length === 0) {
      return null;
    }
    const bounds = CONTENT_LENGTH_BOUNDS[key];
    if (bounds) {
      const codePoints = unicodeCodePointLength(value);
      if (codePoints < bounds.min || codePoints > bounds.max) {
        return null;
      }
    }
  }

  return raw as unknown as IssueReportContent;
}

/**
 * Parse an untrusted report API response into a typed load state.
 *
 * A success payload is valid only when:
 * - top-level `status` is `"success"` and `report_version` is `"v3"`
 * - `id` is a non-empty string, `generated_at` and `data_as_of` are valid date strings
 * - `content` has the exact eight-key set with valid values
 *
 * The accepted empty response `{ status: "not_yet_generated" }` is also handled.
 *
 * Any other shape enters the report error state.
 */
export function parseReportResponse(raw: unknown): IssueReportLoadState {
  if (!isRecord(raw)) {
    return { status: "error" };
  }

  // Handle not_yet_generated
  if (raw.status === "not_yet_generated") {
    return { status: "not_yet_generated" };
  }

  // Validate success shape
  if (raw.status !== "success") {
    return { status: "error" };
  }

  if (raw.report_version !== "v3") {
    return { status: "error" };
  }

  if (
    typeof raw.id !== "string" ||
    raw.id.trim().length === 0 ||
    typeof raw.generated_at !== "string" ||
    Number.isNaN(Date.parse(raw.generated_at)) ||
    typeof raw.data_as_of !== "string" ||
    Number.isNaN(Date.parse(raw.data_as_of))
  ) {
    return { status: "error" };
  }

  const content = validateContent(raw.content);
  if (content === null) {
    return { status: "error" };
  }

  const report: IssueReportSuccessResponse = {
    id: raw.id as string,
    status: "success",
    report_version: "v3",
    generated_at: raw.generated_at as string,
    data_as_of: raw.data_as_of as string,
    content,
  };

  return { status: "success", report };
}

// ---------------------------------------------------------------------------
// Visible section helper
// ---------------------------------------------------------------------------

/**
 * Filter the ordered section definitions to exclude `external_context`
 * when its value is exactly `null`. All other sections always remain.
 */
export function getVisibleSections(
  content: IssueReportContent,
): readonly V3ReportSection[] {
  if (content.external_context === null) {
    return V3_REPORT_SECTIONS.filter((s) => s.key !== "external_context");
  }
  return V3_REPORT_SECTIONS;
}
