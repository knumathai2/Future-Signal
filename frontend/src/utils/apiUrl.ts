/** Build REST and SSE URLs from one optional, origin-only API base. */

export function normalizeApiBaseUrl(value: string | undefined): string {
  const candidate = value?.trim() ?? "";
  if (!candidate) {
    return "";
  }

  let parsed: URL;
  try {
    parsed = new URL(candidate);
  } catch {
    throw new Error("VITE_API_BASE_URL must be an absolute HTTP(S) origin");
  }

  if (
    !["http:", "https:"].includes(parsed.protocol) ||
    parsed.username ||
    parsed.password ||
    parsed.search ||
    parsed.hash ||
    parsed.pathname !== "/"
  ) {
    throw new Error("VITE_API_BASE_URL must be an absolute HTTP(S) origin");
  }

  return parsed.origin;
}

const API_BASE_URL = normalizeApiBaseUrl(import.meta.env?.VITE_API_BASE_URL);

function validateApiPath(path: string): void {
  if (!path.startsWith("/") || path.startsWith("//")) {
    throw new Error("API paths must start with exactly one slash");
  }
}

export function buildApiUrl(
  path: string,
  configuredBaseUrl: string | undefined,
): string {
  validateApiPath(path);
  return `${normalizeApiBaseUrl(configuredBaseUrl)}${path}`;
}

export function apiUrl(path: string): string {
  validateApiPath(path);
  return `${API_BASE_URL}${path}`;
}
