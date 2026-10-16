/** Leaf workspace entry; the host owns its shell and project file tree. */
import "@scitex/sdk/ui/css/app.css";
import "./styles/app-variables.css";
import "./styles/layout.css";
import "./styles/context-menu.css";
import "./styles/canvas.css";
import "./styles/panels.css";
import "./styles/gallery.css";
import "./styles/export-dialog.css";
import "./styles/feedback.css";
import "./styles/ribbon.css";
import "./styles/panel-resizer.css";
import "./styles/mobile.css";
import "./styles/workspace.css";
import { mountFigrecipeEditor, unmountFigrecipeEditor } from "./bridge/MountPoint";

let mountedContainer: HTMLElement | null = null;

// ES modules execute once even when the host injects their script again. The
// generic loader announces each new partial after replacing its DOM.
//
// Mount failures must NEVER leave a silent blank body behind the shell
// (live defect 2026-10-16: /apps/figrecipe/?project=... renders shell only).
// A throwing mount resolves to an explanatory error state in the container;
// module evaluation always survives so later injections can retry.
function renderMountError(container: HTMLElement, error: unknown): void {
  const detail = error instanceof Error ? error.message : String(error);
  container.innerHTML = "";
  const alert = document.createElement("div");
  alert.setAttribute("role", "alert");
  alert.className = "figrecipe-mount-error";
  // Inline padding: stylesheets themselves are a failure class here.
  alert.style.padding = "16px";
  alert.textContent = `FigRecipe could not start here: ${detail}`;
  container.append(alert);
}

function syncWorkspaceMount(): void {
  const container = document.querySelector<HTMLElement>('[data-app-slug="figrecipe"][data-embedded="true"]');
  if (container === mountedContainer) return;
  if (mountedContainer) {
    try {
      unmountFigrecipeEditor();
    } catch (e) {
      console.error("[figrecipe] workspace unmount failed:", e);
    }
    mountedContainer = null;
  }
  if (!container) return;
  try {
    mountFigrecipeEditor({
      container,
      workingDir: container.dataset.workingDir,
      initialFile: container.dataset.recipe,
      projectId: container.dataset.projectId,
      projectName: container.dataset.projectName,
      darkMode: document.documentElement.dataset.theme === "dark" || document.body.classList.contains("dark-theme"),
    });
  } catch (e) {
    console.error("[figrecipe] workspace mount failed:", e);
    renderMountError(container, e);
    return;
  }
  mountedContainer = container;
}

document.addEventListener("workspace:module-injected", syncWorkspaceMount);
syncWorkspaceMount();
