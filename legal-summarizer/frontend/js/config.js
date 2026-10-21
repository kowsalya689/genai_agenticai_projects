// Leave empty when the UI is served by the FastAPI app (same origin).
// Set to e.g. "http://127.0.0.1:8000" if you host the frontend somewhere else (remember to add that origin to ALLOWED_ORIGINS in .env).
export const API_BASE = window.LEXBRIEF_API_BASE || "";
export const API_PREFIX = "/api/v1";
export const SUMMARIZE_TIMEOUT_MS = 10 * 60 * 1000;   // CPU summarisation of long contracts can take minutes
