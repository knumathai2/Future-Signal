import type {
  ScenarioContentBlock,
  ScenarioPremise,
  ScenarioPremiseClass,
  ScenarioSession,
  ScenarioSessionCreated,
  ScenarioTurn,
  ScenarioTurnCreated,
  ScenarioTurnStatus,
} from "../types/issue";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const PREMISE_CLASSES = new Set<ScenarioPremiseClass>([
  "confirmed_fact",
  "stored_observation",
  "user_assumption",
  "model_scenario",
  "unverified_context",
]);
const TURN_STATES = new Set(["queued", "running", "succeeded", "failed"]);
const UNSAFE_MARKDOWN =
  /<|>|`|\[[^\]]*\]\s*\(|!\[|^\s{0,3}#{1,6}\s|^\s*>|^\s*\|/m;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasExactKeys(value: Record<string, unknown>, keys: string[]): boolean {
  const actual = Object.keys(value).sort();
  return (
    actual.length === keys.length &&
    actual.every((key, index) => key === [...keys].sort()[index])
  );
}

function isUuid(value: unknown): value is string {
  return typeof value === "string" && UUID_PATTERN.test(value);
}

function isTimestamp(value: unknown): value is string {
  return typeof value === "string" && Number.isFinite(Date.parse(value));
}

function isBoundedText(
  value: unknown,
  minimum: number,
  maximum: number,
): value is string {
  return (
    typeof value === "string" &&
    value.length >= minimum &&
    value.length <= maximum
  );
}

function parseTurn(value: unknown): ScenarioTurn | null {
  if (
    !isRecord(value) ||
    !hasExactKeys(value, [
      "turn_id",
      "sequence",
      "role",
      "content",
      "created_at",
    ]) ||
    !isUuid(value.turn_id) ||
    !Number.isInteger(value.sequence) ||
    Number(value.sequence) < 1 ||
    (value.role !== "user" && value.role !== "assistant") ||
    !isBoundedText(value.content, 1, 2500) ||
    !isTimestamp(value.created_at)
  ) {
    return null;
  }
  return value as ScenarioTurn;
}

function parsePremise(value: unknown): ScenarioPremise | null {
  if (
    !isRecord(value) ||
    !hasExactKeys(value, [
      "premise_id",
      "premise_class",
      "text",
      "origin_turn_id",
    ]) ||
    !isUuid(value.premise_id) ||
    typeof value.premise_class !== "string" ||
    !PREMISE_CLASSES.has(value.premise_class as ScenarioPremiseClass) ||
    !isBoundedText(value.text, 1, 2000) ||
    !isUuid(value.origin_turn_id)
  ) {
    return null;
  }
  return value as ScenarioPremise;
}

function validSessionBase(value: Record<string, unknown>): boolean {
  return (
    isUuid(value.session_id) &&
    isUuid(value.issue_id) &&
    isTimestamp(value.created_at) &&
    isTimestamp(value.expires_at) &&
    value.max_turns === 8 &&
    isBoundedText(value.policy_version, 1, 100) &&
    isTimestamp(value.data_as_of) &&
    isBoundedText(value.caution_note, 20, 900)
  );
}

/** Strictly validate the one-time session response before storing its capability. */
export function parseScenarioSessionCreated(
  value: unknown,
): ScenarioSessionCreated | null {
  if (
    !isRecord(value) ||
    !hasExactKeys(value, [
      "session_id",
      "session_capability",
      "issue_id",
      "created_at",
      "expires_at",
      "max_turns",
      "policy_version",
      "data_as_of",
      "caution_note",
    ]) ||
    !validSessionBase(value) ||
    !isBoundedText(value.session_capability, 40, 80)
  ) {
    return null;
  }
  return value as ScenarioSessionCreated;
}

/** Strictly validate an authenticated session snapshot. */
export function parseScenarioSession(value: unknown): ScenarioSession | null {
  if (
    !isRecord(value) ||
    !hasExactKeys(value, [
      "session_id",
      "issue_id",
      "created_at",
      "expires_at",
      "max_turns",
      "remaining_turns",
      "policy_version",
      "data_as_of",
      "caution_note",
      "turns",
      "premises",
    ]) ||
    !validSessionBase(value) ||
    !Number.isInteger(value.remaining_turns) ||
    Number(value.remaining_turns) < 0 ||
    Number(value.remaining_turns) > 8 ||
    !Array.isArray(value.turns) ||
    !Array.isArray(value.premises)
  ) {
    return null;
  }
  const turns = value.turns.map(parseTurn);
  const premises = value.premises.map(parsePremise);
  if (
    turns.some((turn) => turn === null) ||
    premises.some((premise) => premise === null)
  ) {
    return null;
  }
  return {
    ...(value as Omit<ScenarioSession, "turns" | "premises">),
    turns: turns as ScenarioTurn[],
    premises: premises as ScenarioPremise[],
  };
}

export function parseScenarioTurnCreated(
  value: unknown,
): ScenarioTurnCreated | null {
  if (
    !isRecord(value) ||
    !hasExactKeys(value, [
      "turn_id",
      "sequence",
      "status",
      "created",
      "requested_at",
      "stream_path",
    ]) ||
    !isUuid(value.turn_id) ||
    !Number.isInteger(value.sequence) ||
    Number(value.sequence) < 1 ||
    value.status !== "queued" ||
    typeof value.created !== "boolean" ||
    !isTimestamp(value.requested_at) ||
    typeof value.stream_path !== "string" ||
    !value.stream_path.startsWith("/api/issues/") ||
    value.stream_path.includes("?")
  ) {
    return null;
  }
  return value as ScenarioTurnCreated;
}

export function parseScenarioTurnStatus(
  value: unknown,
): ScenarioTurnStatus | null {
  if (
    !isRecord(value) ||
    !hasExactKeys(value, [
      "turn_id",
      "sequence",
      "state",
      "attempt_number",
      "requested_at",
      "updated_at",
      "assistant_turn_id",
      "error_code",
    ]) ||
    !isUuid(value.turn_id) ||
    !Number.isInteger(value.sequence) ||
    Number(value.sequence) < 1 ||
    typeof value.state !== "string" ||
    !TURN_STATES.has(value.state) ||
    !Number.isInteger(value.attempt_number) ||
    Number(value.attempt_number) < 0 ||
    !isTimestamp(value.requested_at) ||
    !isTimestamp(value.updated_at) ||
    !(value.assistant_turn_id === null || isUuid(value.assistant_turn_id)) ||
    !(value.error_code === null || isBoundedText(value.error_code, 1, 100))
  ) {
    return null;
  }
  return value as ScenarioTurnStatus;
}

/** Accept only server-validated paragraph/list block shapes. */
export function parseScenarioStreamBlock(
  value: unknown,
): ScenarioContentBlock | null {
  if (
    !isRecord(value) ||
    !Number.isInteger(value.sequence) ||
    Number(value.sequence) < 0
  )
    return null;
  if (value.block_type === "paragraph") {
    if (
      !isRecord(value.payload) ||
      !hasExactKeys(value.payload, ["text"]) ||
      !isBoundedText(value.payload.text, 20, 2500) ||
      UNSAFE_MARKDOWN.test(value.payload.text)
    )
      return null;
    return {
      sequence: Number(value.sequence),
      block_type: "paragraph",
      text: value.payload.text,
    };
  }
  if (value.block_type === "list") {
    if (
      !isRecord(value.payload) ||
      !hasExactKeys(value.payload, ["ordered", "items"]) ||
      typeof value.payload.ordered !== "boolean" ||
      !Array.isArray(value.payload.items) ||
      value.payload.items.length < 1 ||
      value.payload.items.length > 8 ||
      value.payload.items.some(
        (item) => !isBoundedText(item, 10, 500) || UNSAFE_MARKDOWN.test(item),
      )
    )
      return null;
    return {
      sequence: Number(value.sequence),
      block_type: "list",
      ordered: value.payload.ordered,
      items: value.payload.items as string[],
    };
  }
  return null;
}

/** Convert stored restricted Markdown into inert semantic blocks without HTML parsing. */
export function parseScenarioMarkdown(
  value: string,
): ScenarioContentBlock[] | null {
  if (!isBoundedText(value, 1, 2500) || UNSAFE_MARKDOWN.test(value))
    return null;
  const parts = value
    .split(/\n\s*\n/)
    .map((part) => part.trim())
    .filter(Boolean);
  if (!parts.length || parts.length > 12) return null;
  const blocks: ScenarioContentBlock[] = [];
  for (const [sequence, part] of parts.entries()) {
    const lines = part.split("\n");
    const ordered = lines.every((line) => /^\s*\d+\.\s+\S/.test(line));
    const unordered = lines.every((line) => /^\s*[-*+]\s+\S/.test(line));
    if (ordered || unordered) {
      const pattern = ordered ? /^\s*\d+\.\s+/ : /^\s*[-*+]\s+/;
      const items = lines.map((line) => line.replace(pattern, "").trim());
      if (
        items.some((item) => item.length < 1 || item.length > 500) ||
        items.length > 8
      )
        return null;
      blocks.push({ sequence, block_type: "list", ordered, items });
    } else {
      blocks.push({
        sequence,
        block_type: "paragraph",
        text: lines.map((line) => line.trim()).join("\n"),
      });
    }
  }
  return blocks;
}
