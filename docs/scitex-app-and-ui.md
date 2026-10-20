# Shared App and UI ownership

The coordinated migration uses one Python distribution, `scitex-sdk>=0.3.0`.
Its canonical component namespaces are `scitex_sdk.app` and `scitex_sdk.ui`.
The former `scitex-app` and `scitex-ui` distributions are not direct FigRecipe
requirements in this candidate. This is an unpublished migration, not a claim
that older deployed consumers have already moved.

```python
from scitex_sdk.app import get_files
from scitex_sdk import ui, get_frontend_package_dir
```

Django templates and static assets use `scitex_sdk/app` and `scitex_sdk/ui`.
Register `scitex_sdk.ui` for the shared shell assets. The chat model label
`scitex_app` and its existing tables/FKs are deliberately preserved while the
owning Python module becomes `scitex_sdk.app._chat`.

The SDK wheel includes a frontend package named `@scitex/sdk`. FigRecipe uses
its public `@scitex/sdk/ui/...` exports; no sibling repository source alias is
part of runtime compilation. For a pip-installed SDK, run `python configure.py`
in the frontend directory before `npm install`. The helper discovers the owning
package through `scitex_sdk.get_frontend_package_dir()` and configures its file
dependency. `.npmrc` packs this dependency so React peers resolve from the
consumer. The committed default also supports the pinned sibling SDK source.

Native checks retain strict TypeScript, production app/library builds, exported
symbol coverage, Python/frontend version agreement and lockfile identity. CI
verifies the exact SDK source commit declared by this candidate. Publication
requires that owner to be released and the remaining transitive consumers to
stop installing the retired distributions.

See [FigRecipe integration](SCITEX_APP_INTEGRATION.md) for leaf mounting,
authorization, lifecycle and remaining hosted parity limits.
