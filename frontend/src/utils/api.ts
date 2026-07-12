import type {
  GenerationRequestResponse,
  GenerationRequestStatusResponse,
  GenerationStreamBlock,
  IssueReportLoadState,
} from "../types/issue";
import {
  parseGenerationStreamBlock,
  parseReportResponse,
} from "./reportParser";

export class HttpError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "HttpError";
    this.status = status;
  }
}

/** Fetch and parse JSON while preserving the response status for route errors. */
export async function fetchJson<T>(
  url: string,
  message: string,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(url, { signal });
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
      `/api/issues/${encodeURIComponent(issueId)}/report`,
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
    `/api/issues/${encodeURIComponent(issueId)}/report/generate`,
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
    `/api/issues/${encodeURIComponent(issueId)}/report/requests/${encodeURIComponent(requestId)}/stream`,
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
