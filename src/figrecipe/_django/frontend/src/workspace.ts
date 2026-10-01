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
function syncWorkspaceMount(): void {
  const container = document.querySelector<HTMLElement>('[data-app-slug="figrecipe"][data-embedded="true"]');
  if (container === mountedContainer) return;
  if (mountedContainer) unmountFigrecipeEditor();
  mountedContainer = container;
  if (!container) return;
  mountFigrecipeEditor({
    container,
    workingDir: container.dataset.workingDir,
    initialFile: container.dataset.recipe,
    projectId: container.dataset.projectId,
    projectName: container.dataset.projectName,
    darkMode: document.documentElement.dataset.theme === "dark" || document.body.classList.contains("dark-theme"),
  });
}

document.addEventListener("workspace:module-injected", syncWorkspaceMount);
syncWorkspaceMount();
