# FigRecipe -- SciTeX App Reference Implementation

figrecipe is the first app built on the SciTeX app platform. It validates the entire app contract: manifest, Django bridge, frontend mounting, and file-based storage.

## Architecture Overview

```
figrecipe (pip package)
  src/figrecipe/
    _django/                    # Django integration package
      __init__.py               # AppConfig declaration
      apps.py                   # FigRecipeEditorConfig
      views.py                  # editor_page + api_dispatch
      urls.py                   # path("", ...) + path("<path:endpoint>", ...)
      handlers/                 # API handler modules
        core.py, files.py, gallery.py, compose.py, ...
      settings.py               # Standalone Django settings
      services.py               # Editor session management
    _editor/                    # Core editor logic (no Django)
    ...

scitex-cloud (platform)
  apps/workspace/figrecipe_app/
    manifest.json               # App metadata for registry
    urls/figrecipe.py           # Context-injecting URL wrapper
    views/__init__.py           # Workspace mount view
    templates/figrecipe_app/    # Django templates
    static/figrecipe_app/
      ts/_figrecipe-bridge-init.ts      # Entry point
      ts/_figrecipe-bridge/
        FigrecipeMountPoint.ts          # React root + fetch override
        VisEditorBridge.ts              # Two-way bridge events
        BridgeEventBus.ts              # Event pub/sub
```

## What figrecipe Provides

1. **`figrecipe._django`** -- A self-contained Django app that can run standalone (`python -m figrecipe._django.management.commands.figrecipe_editor`) or be included in any Django project
2. **`api_dispatch(request, endpoint)`** -- Single entry point that routes to handler functions by endpoint name
3. **`editor_page(request)`** -- Serves the React SPA HTML
4. **React frontend** -- Built separately, served as static files
5. **`manifest.json`** -- Declares name, icon, privileges, dependencies

## What scitex-cloud Provides

1. **Authentication** -- `request.user` is always populated
2. **Project context** -- `_inject_project_context()` adds `working_dir` to requests
3. **URL mounting** -- figrecipe is reachable at `/apps/figrecipe/figrecipe/<endpoint>`
4. **Theme** -- `dark-theme` body class, CSS custom properties
5. **Workspace chrome** -- Tab bar, file tree, AI panel surround the app

## The Bridge Pattern

The scitex-cloud side provides a **bridge** that connects the figrecipe React editor to the workspace:

### 1. Entry Point (`_figrecipe-bridge-init.ts`)

```typescript
import "scitex-ui/css/app.css";       // shared app styles
import "figrecipe-editor/styles/...";  // app-specific styles

mountFigrecipeEditor({
  container: mount,
  workingDir,
  darkMode: document.body.classList.contains("dark-theme"),
});
```

### 2. Fetch Override (`FigrecipeMountPoint.ts`)

The React editor makes API calls to relative paths like `/preview`, `/save`, `/api/files`. The fetch override rewrites these to the platform URL:

```
/preview?recipe=foo.yaml
  --> /apps/figrecipe/figrecipe/preview?recipe=foo.yaml
```

Only known figrecipe API paths are rewritten; all other fetches pass through unchanged.

### 3. Event Bridge (`BridgeEventBus.ts`)

Two-way communication between the React editor and the workspace:

| Event | Direction | Purpose |
|-------|-----------|---------|
| `figrecipe:fileSelect` | Editor -> Workspace | User clicked a file |
| `figrecipe:elementSelect` | Editor -> Workspace | User selected a plot element |
| `figrecipe:propertyChange` | Editor -> Workspace | Property panel value changed |
| `figrecipe:dataChange` | Editor -> Workspace | Data table contents changed |

## File-Based Storage (No ORM)

figrecipe uses **no Django models**. All data is stored as files in the user's project directory:

- Recipe files: `*.yaml`, `*.yml`
- Output images: `*.png`, `*.svg`, `*.pdf`
- Data files: `*.csv`
- Composition files: `*.figz`

This means figrecipe works identically in:
- **Standalone mode** -- `figrecipe_editor --recipe my_plot.yaml`
- **Cloud mode** -- mounted inside scitex-cloud workspace
- **Other Django projects** -- `INSTALLED_APPS += ["figrecipe._django", "figrecipe._django.apps.ScitexAppChatConfig"]` (BOTH entries; see "Mounting" below)

## The `_django` Convention

figrecipe establishes the convention for SciTeX apps with Django integration:

```python
# apps.py -- standard Django AppConfig
class FigRecipeEditorConfig(AppConfig):
    name = "figrecipe._django"
    label = "figrecipe_editor"

# views.py -- single dispatch entry point
def api_dispatch(request, endpoint):
    handler = HANDLERS.get(endpoint)
    return handler(request, editor)

# urls.py -- two paths: page + API catch-all
urlpatterns = [
    path("", views.editor_page, name="editor"),
    path("<path:endpoint>", views.api_dispatch, name="api"),
]
```

## Standalone Operation

figrecipe can run without scitex-cloud. The `settings.py` provides minimal Django config:

```python
# BOTH apps are required. `figrecipe._django` is the editor; the second registers
# scitex_app._chat's models, and the handler registry routes `api/chat/*` to views
# that query them. Mounting only the first leaves a host with no chat models and
# chat calls failing at request time rather than at startup.
INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "figrecipe._django",
    "figrecipe._django.apps.ScitexAppChatConfig",
]
# Optionally: "scitex_ui" for shared components
DATABASES = {}  # Editor-only installs need none; chat history does. Without a
                # usable database the chat SESSION endpoints answer 501 instead
                # of leaking a Django settings diagnostic into the browser.
```

FigRecipeEditorConfig.ready() warns at startup when the chat app is missing, so a
host sees the omission in its logs instead of as a broken chat at request time.

This validates a key platform principle: apps must be independently functional.

## Privilege Declaration

From `manifest.json`:

```json
{
  "privileges": [
    {
      "type": "filesystem",
      "scope": "project",
      "reason": "Read/write figure recipes and data files"
    }
  ]
}
```

figrecipe only needs project-scoped filesystem access. No network, no datastore, no job queue.

## Key Lessons from figrecipe

1. **Django `_django` sub-package** works well for apps that need server-side rendering
2. **Fetch override** is simpler than iframe postMessage for API routing
3. **File-based storage** means zero migration burden and full portability
4. **Bridge event bus** enables loose coupling between app and workspace
5. **Standalone settings.py** proves the app works without the platform

## Cross-References

- **scitex-cloud** (`docs/ARCHITECTURE/APP_PLATFORM.md`) -- How the platform discovers and mounts figrecipe generically
- **scitex-ui** (`docs/APP_SANDBOX.md`) -- CSS bundles consumed by the bridge init, future `<AppSandbox>` component
- **scitex-app** (`docs/APP_SDK.md`) -- `FilesBackend` protocol, path resolution utilities used for file operations
