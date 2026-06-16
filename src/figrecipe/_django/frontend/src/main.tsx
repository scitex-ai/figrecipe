/** FigRecipe Editor — Bootstrap.
 * Shell (Console/Chat|Files|Viewer|App) from scitex-ui vanilla TS.
 * React is ONLY used for app content (DataTable, Canvas, Properties).
 */

import React from "react";
import ReactDOM from "react-dom/client";

// React app content (Plot/Canvas editor — NOT shell)
import { InnerEditor } from "./InnerEditor";
import { useEditorStore } from "./store/useEditorStore";

// Styles (app-specific)
import "./styles/app-variables.css";
import "./styles/layout.css";
import "./styles/context-menu.css";
import "./styles/canvas.css";
import "./styles/panels.css";
import "./styles/gallery.css";
import "./styles/export-dialog.css";
import "./styles/feedback.css";
import "./styles/mobile.css";

// scitex-ui CSS — single bundle import (shell + app + utils)
// @ts-ignore
import "@scitex/ui/src/scitex_ui/static/scitex_ui/css/all.css";

// Element inspector — debug overlay (Alt+I to toggle)
// @ts-ignore
import "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/utils/element-inspector";

// Context-aware zoom — app-specific panes only (shell panes use vanilla TS zoom)
import { bootstrapContextZoom } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/utils/context-zoom";

// Vanilla TS workspace shell — panel resizer initialization
import "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/shell/workspace-panel-resizer";

// Vanilla TS shell terminal — unified factory with adapter pattern
import { initTerminal } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/shell/terminal";
import type { TerminalConnectionAdapter } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/shell/terminal";

// Vanilla TS shell file tree — WorkspaceFilesTree (full-featured, adapter-based)
import { WorkspaceFilesTree } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/shell/workspace-files-tree";
import type { FileTreeAdapter } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/shell/workspace-files-tree";

// Vanilla TS shell toolbar + keyboard shortcuts
import {
  ToolbarManager,
  KeyboardShortcuts,
} from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/shell/toolbar";

// Vanilla TS shell keyboard shortcuts + modal (Alt+A, Alt+T, pane cycling)
import {
  initKeyboardShortcuts,
  registerShortcuts,
} from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/shell/keyboard-shortcuts";

// Vanilla TS shell repo monitor — recent file changes (adapter-based polling)
import {
  initRepoMonitor,
  initMonitorToggle,
} from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/shell/repo-monitor";
import type { RepoMonitorAdapter } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/shell/repo-monitor";

// Vanilla TS shell viewer — file viewing (images, PDFs, text)
import { ViewerManager } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/shell/viewer";
import type { ViewerAdapter } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/shell/viewer";

// Vanilla TS shell ChatMode — full chat orchestration (scitex-ui)
import { ChatMode } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/shell/chat";
import { figrecipeChatAdapter } from "./bootstrap/chatAdapter";

// Vanilla TS shell SessionsPanel — chat session management (scitex-ui)
import { SessionsPanel } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/shell/chat";
import type {
  SessionAdapter,
  SessionMessage,
} from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/shell/chat";

// Mount React InnerEditor into app content area ONLY
const root = document.getElementById("root");
const params = new URLSearchParams(window.location.search);
const embedded = params.get("mode") === "embedded";

if (root) {
  document.documentElement.setAttribute("data-theme", "dark");
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <InnerEditor embedded={embedded} />
    </React.StrictMode>,
  );
}

// Shell file tree — WorkspaceFilesTree connects to figrecipe's api/tree endpoint
const figrecipeFileTreeAdapter: FileTreeAdapter = {
  async fetchTree(rootPath?: string) {
    // rootPath (breadcrumb navigation) re-roots the backend tree via the
    // working_dir query param; omit it for the default launch folder.
    const url = rootPath
      ? `api/tree?working_dir=${encodeURIComponent(rootPath)}`
      : "api/tree";
    const resp = await fetch(url);
    if (!resp.ok)
      return {
        success: false,
        tree: [],
        error: `HTTP ${resp.status}: ${resp.statusText}`,
      };
    const data = await resp.json();
    // Return the absolute root the backend resolved so the breadcrumb shows the
    // path from filesystem root.
    return { success: true, tree: data.tree ?? [], rootPath: data.working_dir };
  },
  getCsrfToken() {
    const meta = document.querySelector<HTMLMetaElement>(
      'meta[name="csrf-token"]',
    );
    return meta?.content ?? "";
  },
};

const fileTree = new WorkspaceFilesTree({
  mode: "files",
  containerId: "ws-worktree-tree",
  ownerUsername: "figrecipe",
  projectSlug: "figrecipe",
  adapter: figrecipeFileTreeAdapter,
  showGitStatus: false,
  showFolderActions: false,
  showBreadcrumb: true,
  onFileSelect: (_path, item) => {
    window.dispatchEvent(
      new CustomEvent("figrecipe:file-select", {
        detail: { path: item.path, name: item.name },
      }),
    );
  },
});
fileTree.initialize();

// Shell repo monitor — polls api/files for recently modified files
const figrecipeRepoMonitorAdapter: RepoMonitorAdapter = {
  async fetchRecentFiles() {
    const resp = await fetch("api/files?recent=true&limit=50");
    if (!resp.ok) return [];
    const data = await resp.json();
    // Normalize response: api/files returns { files: [...] }
    const files = data.files ?? data ?? [];
    return files.map(
      (f: {
        path: string;
        name?: string;
        modified_at?: string;
        mtime?: string;
        action?: string;
      }) => ({
        path: f.path,
        name: f.name ?? f.path.split("/").pop() ?? f.path,
        modified_at: f.modified_at ?? f.mtime ?? new Date().toISOString(),
        action: f.action,
      }),
    );
  },
  getFileUrl(path: string) {
    return `api/file-content/${path}?raw=true`;
  },
};

initMonitorToggle();
initRepoMonitor({
  adapter: figrecipeRepoMonitorAdapter,
  pollIntervalMs: 10_000,
});

// Shell terminal — local PTY via WebSocket on port+1
const figrecipeTerminalAdapter: TerminalConnectionAdapter = {
  getWebSocketUrl() {
    const port = parseInt(window.location.port || "5050", 10);
    return `ws://127.0.0.1:${port + 1}/`;
  },
};
initTerminal({
  container: "#stx-shell-ai-console-terminal",
  adapter: figrecipeTerminalAdapter,
  clipboard: true,
});

// Shell toolbar + keyboard shortcuts
const toolbar = new ToolbarManager();
toolbar.init();
const shortcuts = new KeyboardShortcuts();
shortcuts.init();

// Shell keyboard shortcuts — Alt+A (toggle AI), Alt+T (cycle panes), etc.
initKeyboardShortcuts();
// Register figrecipe-specific shortcuts for the modal
registerShortcuts("figrecipe", [
  {
    title: "Figure Editor",
    shortcuts: [
      { keys: "Ctrl+Z", description: "Undo" },
      { keys: "Ctrl+Y", description: "Redo" },
      { keys: "Del", description: "Delete selected" },
    ],
  },
]);

// Shell viewer — opens files from file tree in the viewer pane
const figrecipeViewerAdapter: ViewerAdapter = {
  async readFile(path: string) {
    const resp = await fetch(`api/file-content/${path}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    return { content: data.content ?? "" };
  },
  getFileUrl(path: string) {
    return `api/file-content/${path}?raw=true`;
  },
};

let shellViewer: ViewerManager | null = null;
try {
  shellViewer = new ViewerManager({
    adapter: figrecipeViewerAdapter,
  });
} catch {
  // Viewer pane may not exist
}

// Wire file tree → viewer: double-clicking opens files in viewer
window.addEventListener("figrecipe:file-select", ((e: CustomEvent) => {
  if (shellViewer && e.detail?.path) {
    shellViewer.openFile(e.detail.path);
  }
}) as EventListener);

// Wire file tree → canvas: selecting a recipe (.yaml/.yml) loads its rendered
// figure onto the canvas. The WorkspaceFilesTree refactor (3a91d7f) dropped
// this, so selecting a recipe only opened the YAML text and the canvas stayed
// blank. switchFile() surfaces an error toast on failure (fail-loud).
window.addEventListener("figrecipe:file-select", ((e: CustomEvent) => {
  const path: string | undefined = e.detail?.path;
  if (path && /\.ya?ml$/i.test(path)) {
    void useEditorStore.getState().switchFile(path);
  }
}) as EventListener);

// ChatMode — figrecipe adapter posts to scitex-app's chat endpoint
// (figrecipeChatAdapter + FIGRECIPE_SYSTEM extracted to ./bootstrap/chatAdapter)

const chatPreview = document.getElementById("stx-shell-ai-image-preview");
const chatFileInput = document.getElementById(
  "stx-shell-ai-file-input",
) as HTMLInputElement | null;

const chatMode = new ChatMode();
chatMode.init(
  {
    messagesEl: document.getElementById("stx-shell-ai-messages"),
    inputEl: document.getElementById(
      "stx-shell-ai-input",
    ) as HTMLTextAreaElement,
    sendBtn: null,
    speakBtn: null,
    micBtn: document.getElementById("stx-shell-ai-mic") as HTMLButtonElement,
    sttModelSelect: null,
    modelBadge: document.getElementById("stx-shell-ai-model-badge"),
    volBars: Array.from(
      document.querySelectorAll<HTMLElement>(".stx-shell-ai-vol-bar"),
    ),
    imagePreviewEl: chatPreview,
    imageFileInput: chatFileInput,
    cameraBtn: document.getElementById(
      "stx-shell-ai-camera",
    ) as HTMLButtonElement,
    sketchBtn: document.getElementById(
      "stx-shell-ai-sketch",
    ) as HTMLButtonElement,
  },
  {
    adapter: figrecipeChatAdapter,
    // STT adapter — records audio, sends blob to transcription service
    // Uses browser SpeechRecognition as fallback (no server needed)
    sttAdapter: {
      async transcribe(_blob: Blob): Promise<string> {
        console.log("[figrecipe] Voice recorded, size:", _blob.size);
        // TODO: wire to scitex-app STT endpoint when available
        return "";
      },
    },
  },
);
chatMode.restoreConversation();

// SessionsPanel — chat session CRUD backed by scitex-app session API
const figrecipeSessionAdapter: SessionAdapter = {
  async listSessions() {
    const resp = await fetch("api/chat/sessions/");
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    return data.sessions ?? [];
  },
  async getMessages(sessionId: number) {
    const resp = await fetch(`api/chat/sessions/${sessionId}/messages/`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },
  async createSession(title?: string) {
    const resp = await fetch("api/chat/sessions/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: title || "New Chat" }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  },
  async deleteSession(sessionId: number) {
    const resp = await fetch(`api/chat/sessions/${sessionId}/`, {
      method: "DELETE",
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  },
  async addMessage(sessionId: number, role: string, content: string) {
    const resp = await fetch(`api/chat/sessions/${sessionId}/messages/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role, content }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  },
  async renameSession(sessionId: number, title: string) {
    const resp = await fetch(`api/chat/sessions/${sessionId}/`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  },
};

const sessionsPanel = new SessionsPanel();
const sessionsListEl = document.getElementById("stx-shell-ai-sessions-list");

if (sessionsListEl) {
  sessionsPanel.init(
    sessionsListEl,
    figrecipeSessionAdapter,
    (messages: SessionMessage[], _sessionId: number) => {
      // Switch session: use ChatMode's loadSessionMessages for proper rendering
      chatMode.loadSessionMessages(
        messages.map((m) => ({
          role: m.role,
          text: m.content,
          tools_used: [],
          media: [],
        })),
      );
    },
    () => {
      // New chat: clear messages area via ChatMode
      chatMode.clearChat();
    },
  );

  // Wire ChatMode -> SessionsPanel for auto-saving messages
  chatMode.setSessionsPanel(sessionsPanel);
}

// Wire Enter-to-send, C-p/C-n history, auto-resize on the chat textarea
const chatInput = document.getElementById(
  "stx-shell-ai-input",
) as HTMLTextAreaElement | null;
if (chatInput) {
  chatInput.addEventListener("keydown", (e: KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatMode.send();
      return;
    }
    // C-p / ArrowUp — previous history
    if (
      (e.key === "ArrowUp" || (e.ctrlKey && e.key === "p")) &&
      chatInput.selectionStart === 0
    ) {
      e.preventDefault();
      chatMode.navigateHistory(1);
      return;
    }
    // C-n / ArrowDown — next history
    if (
      (e.key === "ArrowDown" || (e.ctrlKey && e.key === "n")) &&
      chatInput.selectionEnd === chatInput.value.length
    ) {
      e.preventDefault();
      chatMode.navigateHistory(-1);
      return;
    }
  });
  // Auto-resize textarea
  chatInput.addEventListener("input", () => {
    chatInput.style.height = "auto";
    chatInput.style.height = Math.min(chatInput.scrollHeight, 150) + "px";
  });
}

// Clear chat on custom event (toolbar clear button)
document.addEventListener("stx-shell:clear-chat", () => {
  chatMode.clearChat();
});

// Camera button → ChatMode handles via refs, also support custom event
window.addEventListener("stx-shell:camera", () => {
  // ChatMode wires cameraBtn click internally; this handles custom events
  const btn = document.querySelector<HTMLButtonElement>(
    '.stx-shell-ai-input-btn[title="Camera"]',
  );
  btn?.click();
});

// Sketch button
window.addEventListener("stx-shell:sketch", () => {
  const btn = document.querySelector<HTMLButtonElement>(
    '.stx-shell-ai-input-btn[title="Sketch"]',
  );
  btn?.click();
});

// Mic button → toggle voice recording via ChatMode
window.addEventListener("stx-shell:mic-toggle", () => {
  chatMode.toggleRecording();
});

// Settings — popover is in the template (standalone_shell.html).
// On first open, populate the App Skills section with figrecipe info.
let agentSourcesPopulated = false;
window.addEventListener("stx-shell:settings", () => {
  if (agentSourcesPopulated) return;
  agentSourcesPopulated = true;

  const container = document.getElementById("ai-agent-sources-content");
  if (!container) return;

  // Render figrecipe as the standalone app skill (matching scitex-cloud's format)
  container.innerHTML = `
    <div class="ai-config-category expanded" data-cat="App Skills">
      <div class="ai-config-category-header">
        <i class="fas fa-chevron-right ai-config-category-chevron"></i>
        <span class="ai-config-category-name">App Skills</span>
        <span class="ai-config-category-count">1/1</span>
      </div>
      <div class="ai-config-grid">
        <div class="ai-config-skill" data-skill="figrecipe">
          <div class="ai-config-card enabled">
            <i class="fas fa-chart-line ai-config-card-icon"></i>
            <div class="ai-config-card-info">
              <div class="ai-config-card-name">
                FigRecipe <span class="ai-config-active-tag">active</span>
              </div>
              <div class="ai-config-card-desc">Interactive figure editor — plt_*</div>
            </div>
            <label class="ai-config-toggle" onclick="event.stopPropagation()">
              <input type="checkbox" checked />
              <span class="ai-config-slider"></span>
            </label>
          </div>
        </div>
      </div>
    </div>`;

  // Bind category expand/collapse
  container
    .querySelectorAll<HTMLElement>(".ai-config-category-header")
    .forEach((header) => {
      header.addEventListener("click", () => {
        header.closest(".ai-config-category")?.classList.toggle("expanded");
      });
    });
});

// Wire file tree refresh when AI modifies files
document.addEventListener("stx-shell:files-changed", () => {
  fileTree.refresh();
});

// Register zoom on app-specific panes
bootstrapContextZoom(
  [
    {
      selector: ".split-pane-left",
      storageKey: "figrecipe-table-zoom",
      min: 0.7,
      max: 1.6,
    },
    {
      selector: ".split-pane-center",
      storageKey: "figrecipe-center-zoom",
      min: 0.7,
      max: 1.6,
    },
    {
      selector: ".split-pane-right",
      storageKey: "figrecipe-props-zoom",
      min: 0.7,
      max: 1.6,
    },
  ],
  [],
);
