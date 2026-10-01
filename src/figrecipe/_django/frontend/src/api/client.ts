import { gettext, interpolate } from "@scitex/sdk/ui/ts/_base/gettext.ts";
/** API client for communicating with the Django backend. */

let _base = import.meta.env.VITE_API_BASE || "";
let _workingDir: string | null = null;
let _recipe: string | null = null;
let _project: string | null = null;
let _session = 0;
let _controller = new AbortController();

export class ApiSessionExpired extends Error {}

/** Retire requests from the outgoing editor; they cannot update its successor. */
export function retireApiSession(): void {
  _session += 1;
  _controller.abort();
  _controller = new AbortController();
}

export function apiSessionId(): number { return _session; }
export function isApiSessionCurrent(session: number): boolean { return session === _session; }

function ensureCurrent(session: number): void {
  if (!isApiSessionCurrent(session)) throw new ApiSessionExpired("Editor session ended");
}

/**
 * The Django CSRF token, read from the `csrftoken` cookie.
 *
 * The hub mounts figrecipe behind Django's CSRF check and does NOT csrf_exempt
 * the mount (scitex-hub, 2026-09-14), so every non-GET API call must send it.
 * Without it, POST/PATCH/DELETE from the editor (e.g. api/gallery/demo) get a
 * 403 "Forbidden" — the live-audit demo-open failure. Django sets the cookie
 * via its CSRF middleware; this reads it (same-origin, so JS may). Returns ""
 * when absent (standalone / no cookie) — harmless on a CSRF-exempt host.
 */
export function csrfToken(): string {
  const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : "";
}

/** Set the API base URL at runtime (used by FigrecipeEditor when embedded). */
export function setApiBase(base: string) {
  const next = base.replace(/\/+$/, "");
  if (next !== _base) retireApiSession();
  _base = next;
}

/** Set the working directory for all API calls. */
export function setWorkingDir(dir: string) {
  if (dir !== _workingDir) retireApiSession();
  _workingDir = dir;
}

/** Set the recipe path for all API calls. */
export function setRecipe(recipe: string) {
  if (recipe !== _recipe) retireApiSession();
  _recipe = recipe;
}

/** null keeps the public editor's URL fallback; "" explicitly clears it. */
export function setProject(project: string | null): void {
  if (project !== _project) retireApiSession();
  _project = project;
}

/** Read the recipe — prefer runtime value, fall back to URL query param. */
function getRecipeParam(): string {
  if (_recipe !== null) return _recipe;
  const params = new URLSearchParams(window.location.search);
  return params.get("recipe") || "";
}

/** Append recipe= and working_dir= to endpoint URL. */
export function apiUrl(endpoint: string): string {
  const recipe = getRecipeParam();
  const sep = endpoint.includes("?") ? "&" : "?";
  let url = `${_base}/${endpoint}`;
  const params: string[] = [];
  if (recipe) params.push(`recipe=${encodeURIComponent(recipe)}`);
  if (_workingDir)
    params.push(`working_dir=${encodeURIComponent(_workingDir)}`);
  const project = _project ?? new URLSearchParams(window.location.search).get("project");
  if (project) params.push(`project=${encodeURIComponent(project)}`);
  if (params.length) url += `${sep}${params.join("&")}`;
  return url;
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const session = _session;
  const url = apiUrl(endpoint);
  const method = (options?.method || "GET").toUpperCase();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options?.headers as Record<string, string>) || {}),
  };
  // Django CSRF: every mutating (non-GET/HEAD) call must carry the token, or the
  // hub returns 403. GET is exempt.
  if (method !== "GET" && method !== "HEAD") {
    headers["X-CSRFToken"] = csrfToken();
  }
  try {
    const res = await fetch(url, { ...options, headers, signal: _controller.signal });
    ensureCurrent(session);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: res.statusText }));
      ensureCurrent(session);
      throw new Error(err.error || interpolate(gettext("API error: %s"), [res.status]));
    }
    const data = await res.json();
    ensureCurrent(session);
    return data;
  } catch (error) {
    ensureCurrent(session);
    throw error;
  }
}

async function requestBlob(endpoint: string, options?: RequestInit): Promise<Blob> {
  const session = _session;
  try {
    const res = await fetch(apiUrl(endpoint), { ...options, signal: _controller.signal });
    ensureCurrent(session);
    if (!res.ok) throw new Error(interpolate(gettext("Download failed: %s"), [res.status]));
    const blob = await res.blob();
    ensureCurrent(session);
    return blob;
  } catch (error) {
    ensureCurrent(session);
    throw error;
  }
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),

  post: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    }),

  /** Fetch raw bytes (for downloads). */
  getBlob: (endpoint: string): Promise<Blob> => requestBlob(endpoint),

  /** POST JSON and receive raw bytes (for compose export). */
  postBlob: (endpoint: string, data?: unknown): Promise<Blob> =>
    requestBlob(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
      body: data ? JSON.stringify(data) : undefined,
    }),
};
