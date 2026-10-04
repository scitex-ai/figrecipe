# FigRecipe App integration

FigRecipe owns its Django views, URLconf, workspace content and React editor.
The coordinated candidate consumes `scitex-sdk>=0.3.2`, which physically owns
`scitex_sdk.app` and `scitex_sdk.ui`. SDK 0.3.2 is published; the FigRecipe 0.36.1
candidate retains its separate source, CI and distribution qualification.
Matching version strings alone do not identify reviewed artifacts.

## Install and mount

Use a GUI extra, for example `pip install 'figrecipe[editor,app]'`. Python
plotting remains independent of Django.
The `scitex.apps` entry point declares
`figrecipe._django.apps:FigRecipeEditorConfig`; discovery retains its SDK
embedding superclass and metadata. It fails with the missing GUI-extra message
rather than substituting a plain AppConfig.

```python
from figrecipe._django import INSTALLED_APPS_ENTRIES

INSTALLED_APPS += [
    *INSTALLED_APPS_ENTRIES,
    "scitex_sdk.ui",
]

from scitex_sdk.urls import mount_urlpatterns
urlpatterns += mount_urlpatterns("apps/figrecipe/", "figrecipe._django.urls")
```

The second leaf-owned registration discovers shared chat models from
`scitex_sdk.app._chat` under the existing `scitex_app` label. A host that already
owns that label must retain its single existing registration; duplicate labels
are invalid. The tuple includes
`figrecipe._django.apps.ScitexAppChatConfig`; standalone settings consume this
same tuple. A host must qualify its existing model and migration ownership
before adding the companion config.

SDK 0.3.2 plugin discovery installs only the primary entry-point AppConfig;
`installed_app_paths()` does not expand this tuple. Its public
`leaf_declarations()` accessor can read `INSTALLED_APPS_ENTRIES` with the
caller-supplied `tuple` type, but automatic mounting still needs a generic
settings-time consumer. The chat companion is not a second launcher plugin.

Chat/session history also needs a usable database. Streaming does not require
chat model registration or a database. The standalone
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

The leaf's `workspace.render_workspace_content` also renders that partial for
a generic host content endpoint. The caller supplies its resolved `stx_mount`
explicitly; `""` declares a root mount. The renderer obtains SDK project
authority before rendering and issues the CSRF cookie. Capability errors
propagate to the caller's existing response handling. A presentation-only
`current_project` never supplies filesystem authority. The full `workspace/`
page keeps its shell and remains a separate response.

Both full leaf templates extend `scitex_sdk/app/app_shell.html` and fill
`scitex_app_content`. SDK 0.3.0 supplies the adapter to its UI shell. A host can
shadow the generic adapter through its Django template directories while the
leaf retains its content, CSS and script blocks.
The legacy leaf standalone settings discover the genuine SDK App template
directory with a final filesystem loader, after project directories and
installed-app templates. A generic host must likewise discover it, either through
its single existing SDK App registration or a template-directory entry after
host overrides. Registering the SDK App core alongside the retained chat config
would duplicate their `scitex_app` label; this candidate keeps that registration
unchanged. The SDK standalone launcher already registers its App core.

`figrecipe._django.api_policy` exposes the existing read/write and editor-context
decisions, path-selector metadata, and dotted targets for the request guard and
guarded dispatcher. The leaf consumes these same declarations; specialized
path checks and request execution remain in the existing guard and dispatcher.
The metadata alone does not grant access. SDK 0.3.0 does not automatically
discover this policy export, so generic host intake must qualify its consumption
before replacing any existing host route or capability check.

The app package also publishes dependency-free dotted declarations named
`context_builder`, `partial_template`, `content_renderer`, `api_policy_module`
and `hosted_api_dispatcher`. The published SDK 0.3.2 accessor
`scitex_sdk.app.plugins.leaf_declarations` reads these names with caller-supplied
`str` types; it returns their values without resolving the dotted targets.
Consumers resolve the existing leaf callables at request time. The policy
module uses a distinct attribute name so importing its submodule cannot replace
the declaration. These exports add no manifest keys or automatic host adoption.

The content renderer still requires the server's explicit trusted `stx_mount`.
For the retained native Hub route, the guarded API prefix is
`/apps/figrecipe/figrecipe`, while navigation is `/apps/figrecipe`; navigation
does not supply that API mount. The hosted dispatcher declaration resolves to
the existing CSRF-protected leaf callable, preserving authentication, selected
project authority, path confinement and per-route write decisions. SDK 0.3.2
supplies the declaration accessor; SDK 0.3.0 does not. Protected host consumption
and mounted acceptance remain separate qualification steps.

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

## Recorded-data reads

`figrecipe._api._extract` owns record extraction, combined CSV projection, live
table shaping, column types and JSON conversion without importing Django, the
SDK or Hub. The public `extract_data(path)` loads the recipe once and delegates
to core. CSV and table HTTP adapters pass their existing live record to core
and retain their response formats, headers and errors. Table reads still prefer
the selected project table, then session-imported data, then the live record.
The CSV and table projections retain their distinct fields and padding; this
relocation does not change plotting, storage or native request authority.

## Frontend and static assets

The frontend imports the SDK's public `@scitex/sdk/ui/...` exports, including the
React bridge and shared CSS. For the installed SDK, run `python configure.py`,
then normal `npm install`, `npm run build`, and `npm run build:lib` in
`src/figrecipe/_django/frontend`. The committed dependency supports the exact
pinned SDK source checkout in CI. Both builds preserve strict TypeScript and
React peer deduplication. Templates extend `scitex_sdk/app/app_shell.html`;
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
