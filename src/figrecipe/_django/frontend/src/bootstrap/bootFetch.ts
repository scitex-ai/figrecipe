/** Boot-resilience fetch helpers (figrecipe-boot-resilience-20261016).
 *
 * The app-shell init fetch paths (file tree, repo monitor) run at module
 * scope in main.tsx, before and beside the React render. An HTTP error
 * already degrades (error object / empty list), but a NETWORK-level failure
 * — blocked fetch, CORS, DNS, offline — rejects the promise, escaping the
 * adapter contract as an unhandled rejection and leaving the shell pane
 * empty with no degraded state.
 *
 * These factories own the full adapter fetch bodies behind an injected
 * fetch, so every failure class (reject, HTTP error, malformed body)
 * resolves to the same degraded value the HTTP-error path already
 * returns. No React, SDK, or DOM imports: importable under
 * `node --experimental-strip-types` (see tests/bootResilience.test.ts).
 */

export interface BootResponse {
  readonly ok: boolean;
  readonly status: number;
  readonly statusText: string;
  json(): Promise<unknown>;
}

export type FetchImpl = (url: string) => Promise<BootResponse>;
export type ApiUrl = (endpoint: string) => string;

export interface Deps {
  readonly fetchImpl: FetchImpl;
  readonly apiUrl: ApiUrl;
}

export interface TreeResult {
  readonly success: boolean;
  readonly tree: unknown[];
  readonly rootPath?: string;
  readonly error?: string;
}

function failureMessage(e: unknown): string {
  return e instanceof Error ? e.message : String(e);
}

/** File-tree fetch: rejects nothing; network failure -> success:false. */
export function createFileTreeFetcher(deps: Deps) {
  return {
    async fetchTree(rootPath?: string): Promise<TreeResult> {
      const url = rootPath
        ? deps.apiUrl(`api/tree?working_dir=${encodeURIComponent(rootPath)}`)
        : deps.apiUrl("api/tree");
      try {
        const resp = await deps.fetchImpl(url);
        if (!resp.ok)
          return {
            success: false,
            tree: [],
            error: `HTTP ${resp.status}: ${resp.statusText}`,
          };
        const data = ((await resp.json()) ?? {}) as {
          tree?: unknown[];
          working_dir?: string;
        };
        return {
          success: true,
          tree: Array.isArray(data.tree) ? data.tree : [],
          rootPath: data.working_dir,
        };
      } catch (e) {
        return { success: false, tree: [], error: failureMessage(e) };
      }
    },
  };
}

export interface RecentFile {
  readonly path: string;
  readonly name: string;
  readonly modified_at: string;
  readonly action?: string;
}

/** Repo-monitor fetch: rejects nothing; any failure -> []. */
export function createRecentFilesFetcher(deps: Deps) {
  return {
    async fetchRecentFiles(): Promise<RecentFile[]> {
      try {
        const resp = await deps.fetchImpl(
          deps.apiUrl("api/files?recent=true&limit=50"),
        );
        if (!resp.ok) return [];
        const data = ((await resp.json()) ?? {}) as {
          files?: Array<{
            path: string;
            name?: string;
            modified_at?: string;
            mtime?: string;
            action?: string;
          }>;
        };
        // Normalize response: api/files returns { files: [...] }.
        const files = Array.isArray(data.files) ? data.files : [];
        return files.map((f) => ({
          path: f.path,
          name: f.name ?? f.path.split("/").pop() ?? f.path,
          modified_at: f.modified_at ?? f.mtime ?? new Date().toISOString(),
          action: f.action,
        }));
      } catch {
        return [];
      }
    },
    getFileUrl(path: string): string {
      return deps.apiUrl(`api/file-content/${path}?raw=true`);
    },
  };
}
