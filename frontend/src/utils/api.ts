import type { IssueReportLoadState } from "../types/issue";
import { parseReportResponse } from "./reportParser";

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
    const response = await fetch(`/api/issues/${issueId}/report`, { signal });
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
