import type {
  GenerationRequestResponse,
  GenerationRequestStatusResponse,
  GenerationStreamBlock,
  IssueReportLoadState,
  ScenarioContentBlock,
  ScenarioSession,
  ScenarioSessionCreated,
  ScenarioTurnCreated,
  ScenarioTurnStatus,
} from "../types/issue";
import {
  parseGenerationStreamBlock,
  parseReportResponse,
} from "./reportParser";
import {
  parseScenarioSession,
  parseScenarioSessionCreated,
  parseScenarioStreamBlock,
  parseScenarioTurnCreated,
  parseScenarioTurnStatus,
} from "./scenarioParser";
import { apiUrl } from "./apiUrl";

export class HttpError extends Error {
  status: number;
  code: string | null;

  constructor(message: string, status: number, code: string | null = null) {
    super(message);
    this.name = "HttpError";
    this.status = status;
    this.code = code;
  }
}

/** Fetch and parse JSON while preserving the response status for route errors. */
export async function fetchJson<T>(
  url: string,
  message: string,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(apiUrl(url), { signal });
  if (!response.ok) {
    throw new HttpError(message, response.status);
  }

  return (await response.json()) as T;
}

/** Load and validate the stored issue report without blocking core detail data. */
export async function loadIssueReport(
  issueId: string,
  signal?: AbortSignal,
): Promise<IssueReportLoadState> {
  try {
    const response = await fetch(
      apiUrl(`/api/issues/${encodeURIComponent(issueId)}/report`),
      { signal },
    );
    if (!response.ok) {
      throw new HttpError("Failed to load issue report", response.status);
    }

    const raw: unknown = await response.json();
    return parseReportResponse(raw);
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    console.error(error);
    return { status: "error" };
  }
}

/** Append or join one v7 generation request. Provider work never runs here. */
export async function requestIssueReport(
  issueId: string,
  refreshContext = false,
  signal?: AbortSignal,
): Promise<GenerationRequestResponse> {
  const response = await fetch(
    apiUrl(`/api/issues/${encodeURIComponent(issueId)}/report/generate`),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_context: refreshContext }),
      signal,
    },
  );
  if (!response.ok)
    throw new HttpError("Failed to request issue report", response.status);
  return (await response.json()) as GenerationRequestResponse;
}

/** Read the append-only request state used by the detail-route poller. */
export async function loadGenerationRequestStatus(
  issueId: string,
  requestId: string,
  signal?: AbortSignal,
): Promise<GenerationRequestStatusResponse> {
  return fetchJson<GenerationRequestStatusResponse>(
    `/api/issues/${encodeURIComponent(issueId)}/report/requests/${encodeURIComponent(requestId)}`,
    "Failed to load generation request status",
    signal,
  );
}

type GenerationStreamHandlers = {
  onBlock: (block: GenerationStreamBlock) => void;
  onComplete: () => void;
  onGenerationError: () => void;
  onTransportError: () => void;
};

/** Subscribe to validated append-only blocks; callers own the polling fallback. */
export function subscribeToGenerationStream(
  issueId: string,
  requestId: string,
  handlers: GenerationStreamHandlers,
): () => void {
  const source = new EventSource(
    apiUrl(
      `/api/issues/${encodeURIComponent(issueId)}/report/requests/${encodeURIComponent(requestId)}/stream`,
    ),
  );
  const block = (event: Event) => {
    try {
      const parsed = parseGenerationStreamBlock(
        JSON.parse((event as MessageEvent<string>).data),
      );
      if (!parsed) throw new Error("Invalid generation stream block");
      handlers.onBlock(parsed);
    } catch (error) {
      console.error(error);
      source.close();
      handlers.onTransportError();
    }
  };
  const complete = () => {
    source.close();
    handlers.onComplete();
  };
  const generationError = () => {
    source.close();
    handlers.onGenerationError();
  };
  source.addEventListener("block", block);
  source.addEventListener("complete", complete);
  source.addEventListener("generation_error", generationError);
  source.onerror = () => {
    source.close();
    handlers.onTransportError();
  };
  return () => source.close();
}

async function scenarioResponse<T>(
  response: Response,
  parser: (value: unknown) => T | null,
  message: string,
): Promise<T> {
  if (!response.ok) {
    let code: string | null = null;
    try {
      const body: unknown = await response.json();
      if (
        typeof body === "object" &&
        body !== null &&
        "detail" in body &&
        typeof body.detail === "object" &&
        body.detail !== null &&
        "code" in body.detail &&
        typeof body.detail.code === "string"
      ) {
        code = body.detail.code;
      }
    } catch {
      // The public status remains enough for a generic, non-enumerating UI error.
    }
    throw new HttpError(message, response.status, code);
  }
  const parsed = parser(await response.json());
  if (!parsed) throw new HttpError(`${message}: invalid response`, 502);
  return parsed;
}

function scenarioHeaders(capability: string): HeadersInit {
  return {
    Authorization: `Bearer ${capability}`,
    "Content-Type": "application/json",
  };
}

/** Create an anonymous issue-scoped scenario session and receive its capability once. */
export async function createScenarioSession(
  issueId: string,
  signal?: AbortSignal,
): Promise<ScenarioSessionCreated> {
  const response = await fetch(
    apiUrl(`/api/issues/${encodeURIComponent(issueId)}/scenario-sessions`),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
      signal,
    },
  );
  return scenarioResponse(
    response,
    parseScenarioSessionCreated,
    "Failed to create scenario session",
  );
}

/** Read one caller-owned scenario session using a bearer capability. */
export async function loadScenarioSession(
  issueId: string,
  sessionId: string,
  capability: string,
  signal?: AbortSignal,
): Promise<ScenarioSession> {
  const response = await fetch(
    apiUrl(
      `/api/issues/${encodeURIComponent(issueId)}/scenario-sessions/${encodeURIComponent(sessionId)}`,
    ),
    { headers: scenarioHeaders(capability), signal },
  );
  return scenarioResponse(
    response,
    parseScenarioSession,
    "Failed to load scenario session",
  );
}

/** Append one idempotent user turn without placing the capability in a URL. */
export async function createScenarioTurn(
  issueId: string,
  sessionId: string,
  capability: string,
  message: string,
  idempotencyKey: string,
  signal?: AbortSignal,
): Promise<ScenarioTurnCreated> {
  const response = await fetch(
    apiUrl(
      `/api/issues/${encodeURIComponent(issueId)}/scenario-sessions/${encodeURIComponent(sessionId)}/turns`,
    ),
    {
      method: "POST",
      headers: {
        ...scenarioHeaders(capability),
        "Idempotency-Key": idempotencyKey,
      },
      body: JSON.stringify({ message }),
      signal,
    },
  );
  return scenarioResponse(
    response,
    parseScenarioTurnCreated,
    "Failed to create scenario turn",
  );
}

/** Poll one owned scenario turn as a fallback for interrupted streaming. */
export async function loadScenarioTurnStatus(
  issueId: string,
  sessionId: string,
  turnId: string,
  capability: string,
  signal?: AbortSignal,
): Promise<ScenarioTurnStatus> {
  const response = await fetch(
    apiUrl(
      `/api/issues/${encodeURIComponent(issueId)}/scenario-sessions/${encodeURIComponent(sessionId)}/turns/${encodeURIComponent(turnId)}`,
    ),
    { headers: scenarioHeaders(capability), signal },
  );
  return scenarioResponse(
    response,
    parseScenarioTurnStatus,
    "Failed to load scenario turn",
  );
}

/** Delete only the caller-owned ephemeral scenario graph. */
export async function deleteScenarioSession(
  issueId: string,
  sessionId: string,
  capability: string,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(
    apiUrl(
      `/api/issues/${encodeURIComponent(issueId)}/scenario-sessions/${encodeURIComponent(sessionId)}`,
    ),
    { method: "DELETE", headers: scenarioHeaders(capability), signal },
  );
  if (!response.ok)
    throw new HttpError("Failed to delete scenario session", response.status);
}

type ScenarioStreamHandlers = {
  onSnapshot: (state: ScenarioTurnStatus["state"]) => void;
  onBlock: (block: ScenarioContentBlock) => void;
  onComplete: () => void;
  onFailed: () => void;
  onTransportError: () => void;
};

/** Replay authenticated validated blocks with a bounded cursor-preserving reconnect. */
export function subscribeToScenarioStream(
  streamPath: string,
  capability: string,
  handlers: ScenarioStreamHandlers,
): () => void {
  const controller = new AbortController();
  let lastEventId = "";

  const dispatch = (rawEvent: string) => {
    let eventName = "message";
    let data = "";
    for (const line of rawEvent.split(/\r?\n/)) {
      if (line.startsWith("id:")) lastEventId = line.slice(3).trim();
      if (line.startsWith("event:")) eventName = line.slice(6).trim();
      if (line.startsWith("data:")) data += line.slice(5).trim();
    }
    if (!data) return false;
    let payload: unknown;
    try {
      payload = JSON.parse(data);
    } catch {
      throw new Error("Invalid scenario stream event");
    }
    if (eventName === "block") {
      const block = parseScenarioStreamBlock(payload);
      if (!block) throw new Error("Invalid scenario stream block");
      handlers.onBlock(block);
    } else if (
      eventName === "snapshot" &&
      typeof payload === "object" &&
      payload !== null &&
      "state" in payload &&
      typeof payload.state === "string" &&
      TURN_STREAM_STATES.has(payload.state)
    ) {
      handlers.onSnapshot(payload.state as ScenarioTurnStatus["state"]);
    } else if (eventName === "complete") {
      handlers.onComplete();
      return true;
    } else if (eventName === "failed") {
      handlers.onFailed();
      return true;
    }
    return false;
  };

  const connect = async () => {
    for (
      let attempt = 0;
      attempt < 3 && !controller.signal.aborted;
      attempt += 1
    ) {
      try {
        const headers: HeadersInit = { Authorization: `Bearer ${capability}` };
        if (lastEventId) headers["Last-Event-ID"] = lastEventId;
        const response = await fetch(apiUrl(streamPath), {
          headers,
          signal: controller.signal,
        });
        if (!response.ok || !response.body)
          throw new Error("Scenario stream unavailable");
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        while (!controller.signal.aborted) {
          const { value, done } = await reader.read();
          buffer += decoder.decode(value, { stream: !done });
          const events = buffer.split(/\r?\n\r?\n/);
          buffer = events.pop() ?? "";
          for (const event of events) if (dispatch(event)) return;
          if (done) break;
        }
      } catch {
        if (controller.signal.aborted) return;
      }
      if (attempt < 2)
        await new Promise((resolve) => window.setTimeout(resolve, 1500));
    }
    if (!controller.signal.aborted) handlers.onTransportError();
  };

  void connect();
  return () => controller.abort();
}

const TURN_STREAM_STATES = new Set([
  "queued",
  "running",
  "succeeded",
  "failed",
]);
