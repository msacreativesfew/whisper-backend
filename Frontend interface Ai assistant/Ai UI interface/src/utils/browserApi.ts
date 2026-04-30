const DEFAULT_LOCAL_API_BASE = "http://127.0.0.1:8000";

function trimTrailingSlash(value: string) {
  return value.replace(/\/+$/, "");
}

export function getBrowserApiBase() {
  // Priority 1: Check Railway environment variable (set by Railway automatically)
  if (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
    // For production deployments (Railway, Vercel, etc.), use the current origin
    return trimTrailingSlash(window.location.origin);
  }

  // Priority 2: Check explicit environment variables
  const envBase = (
    import.meta.env.VITE_API_BASE_URL ||
    import.meta.env.CLOUD_BACKEND_URL ||
    process.env.REACT_APP_API_URL ||
    ""
  ).trim();

  if (envBase) {
    return trimTrailingSlash(envBase);
  }

  // Priority 3: For local development with hostname detection
  if (typeof window !== "undefined") {
    const { hostname, origin, port } = window.location;
    const isLocalHost = hostname === "localhost" || hostname === "127.0.0.1";

    // If running on a dev server port, use the current origin
    if (!isLocalHost) {
      return trimTrailingSlash(origin);
    }

    // For localhost with explicit port (e.g., 5173 for Vite dev server)
    if (isLocalHost && port && port !== "5173") {
      return `http://${hostname}:${port}`;
    }
  }

  return DEFAULT_LOCAL_API_BASE;
}

export async function fetchBrowserApiJson<T>(path: string): Promise<T> {
  const response = await fetch(`${getBrowserApiBase()}${path}`, {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `HTTP API failed: ${response.status}${errorText ? ` ${errorText}` : ""}`,
    );
  }

  return response.json() as Promise<T>;
}
