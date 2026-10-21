import { API_BASE, API_PREFIX, SUMMARIZE_TIMEOUT_MS } from "./config.js";

export class ApiError extends Error {
  constructor(message, { status = 0, code = "network_error", requestId = null } = {}) {
    super(message);
    this.status = status; this.code = code; this.requestId = requestId;
  }
}

async function request(path, { method = "GET", json, body, timeout = 30000, signal } = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeout);
  if (signal) signal.addEventListener("abort", () => ctrl.abort());
  const headers = { Accept: "application/json" };
  if (json !== undefined) { headers["Content-Type"] = "application/json"; body = JSON.stringify(json); }
  let res;
  try {
    res = await fetch(API_BASE + API_PREFIX + path, { method, headers, body, signal: ctrl.signal });
  } catch (err) {
    if (err.name === "AbortError") throw new ApiError(signal?.aborted ? "Cancelled." : "The request timed out.", { code: "timeout" });
    throw new ApiError("Cannot reach the server. Is it running?", { code: "network_error" });
  } finally {
    clearTimeout(timer);
  }
  const requestId = res.headers.get("X-Request-ID");
  let data = null;
  try { data = await res.json(); } catch { /* non-JSON body */ }
  if (!res.ok) {
    const e = data?.error;
    const msg = res.status === 429
      ? `${e?.message || "Too many requests."}`
      : e?.message || `Server error (${res.status}).`;
    throw new ApiError(msg, { status: res.status, code: e?.code || "http_error", requestId: e?.request_id || requestId });
  }
  return data;
}

export const api = {
  health: () => request("/health", { timeout: 5000 }),
  samples: () => request("/samples"),
  extract: (file) => { const fd = new FormData(); fd.append("file", file); return request("/extract", { method: "POST", body: fd, timeout: 60000 }); },
  summarize: (payload, signal) => request("/summarize", { method: "POST", json: payload, timeout: SUMMARIZE_TIMEOUT_MS, signal }),
};
