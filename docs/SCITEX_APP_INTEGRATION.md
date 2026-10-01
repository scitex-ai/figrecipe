# FigRecipe App integration

FigRecipe owns its Django views, URLconf, workspace content and React editor.
The coordinated candidate consumes `scitex-sdk>=0.3.0`, which physically owns
`scitex_sdk.app` and `scitex_sdk.ui`. The SDK release and this leaf migration are
unpublished; matching version strings alone do not identify reviewed artifacts.

## Install and mount

Use a GUI extra, for example `pip install 'figrecipe[editor,app]'`, once the
coordinated SDK is available. Python plotting remains independent of Django.
The `scitex.apps` entry point declares
`figrecipe._django.apps:FigRecipeEditorConfig`; discovery retains its SDK
embedding superclass and metadata. It fails with the missing GUI-extra message
rather than substituting a plain AppConfig.

```python
INSTALLED_APPS += [
    "figrecipe._django",
    "figrecipe._django.apps.ScitexAppChatConfig",
    "scitex_sdk.ui",
]

from scitex_sdk.urls import mount_urlpatterns
urlpatterns += mount_urlpatterns("apps/figrecipe/", "figrecipe._django.urls")
```

The second leaf-owned registration discovers shared chat models from
`scitex_sdk.app._chat` under the existing `scitex_app` label. A host that already
owns that label must retain its single existing registration; duplicate labels
are invalid. Chat/session history also needs a usable database. The standalone
settings keep the dummy database and answer 501 for database-backed session
endpoints. Leaf startup warns when the chat registration is omitted.

The SDK mount helper preserves both `figrecipe:*` and established
`figrecipe_app:*` reverse callers at the same paths. Plain Django `include()`
does not consume the declared namespace aliases. Root editor names,
`workspace/`, and existing nested `figrecipe/<endpoint>` routes remain available.
The generic host retains its independent route-ownership and authentication
checks; these changes do not authorize a legacy Hub route cutover.

## Project authority and workspace lifecycle

Hosted mode requires an authenticated request, a `SCITEX_PROJECT_PROVIDER`,
`SCITEX_PROJECT_STORAGE` with `project_path(project_id, request)` and
`can_write(project_id, request)`, and the browser provider URL. The leaf obtains
SDK project authority before file I/O, checks path selectors beneath that root,
keeps editors separated by user/project, requires literal-true write permission
and protects mutations with CSRF. Missing authority does not fall back to cwd.

The manifest declares `figrecipe/workspace_partial.html` and
`figrecipe._django.workspace.build_workspace_context`. The generic host supplies
the trusted `stx_mount` route after building context. An explicit empty string
means the root mount; absent mount context leaves the editor unavailable.
`workspace/` renders the same content in standalone and plugin modes.

The leaf subscribes to the existing `workspace:module-injected` event. Repeated
AJAX mount/unmount and project changes retire outgoing requests and reset plot,
canvas, clipboard, table, selection and undo targets while keeping display
preferences. The shared bridge checks container ownership before unmounting.
Each mount supplies its own project and API base; the global fetch function is
unchanged. A request already admitted by the server keeps its original project
authority even if the browser changes projects afterward. Resource API
resolution uses the SDK's `remember=False` option so late requests cannot
overwrite the newer navigation selection. Explicit navigation still remembers
its authorized project.

## Frontend and static assets

The frontend imports the SDK's public `@scitex/sdk/ui/...` exports, including the
React bridge and shared CSS. For the installed SDK, run `python configure.py`,
then normal `npm install`, `npm run build`, and `npm run build:lib` in
`src/figrecipe/_django/frontend`. The committed dependency supports the exact
pinned SDK source checkout in CI. Both builds preserve strict TypeScript and
React peer deduplication. Templates extend `scitex_sdk/ui/standalone_shell.html`;
compiled leaf assets remain under `figrecipe/`.

## Current feature and rollout limits

Plot, Data and Canvas are available in both modes. Canvas Save writes the
existing `composed.png` into the authorized project. Loading a recipe reproduces
that recipe; PNG save does not persist an editable composition or canvas layout.
Hosted ZIP remains explicit 501 until scoped extraction is implemented. The
standalone retains local directory selection, ZIP recipes and local terminal;
hosted terminal transport is host-owned.

The retained legacy Hub bridge, its model/migration ownership, full chat/store
parity, jobs/collaboration, editable composition persistence and production
source/build identity remain separate rollout gates. Synthetic local SQLite
chat testing establishes local ORM compatibility, not tenant store isolation.
No existing Hub domain route is removed by this leaf package candidate.

See [shared SDK ownership](scitex-app-and-ui.md) for dependency and packaging
contracts.
