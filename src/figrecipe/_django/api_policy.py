"""Declared leaf endpoint policy consumed by the existing guarded dispatcher.

This metadata does not authorize requests, validate paths, enforce CSRF, or
promise OAuth/idempotency behavior. Those checks remain in the leaf guard and
the SDK host capability. Endpoint names are relative to the declared app mount.
"""

READ_ENDPOINTS = frozenset(
    {
        "ping",
        "preview",
        "hitmap",
        "style",
        "overrides",
        "theme",
        "list_themes",
        "diff",
        "get_labels",
        "get_axis_info",
        "get_legend_info",
        "get_axes_positions",
        "calls",
        "element_details",
        "get_captions",
        "datatable/data",
        "download/csv",
        "api/tree",
        "api/files",
        "api/download",
        "api/gallery",
        "stats/list_brackets",
        "api/switch",
    }
)
READ_PREFIXES = (
    "download/",
    "api/file-content/",
    "api/gallery/thumbnail/",
    "api/compose/export/",
)
METHOD_SENSITIVE_PREFIXES = ("call/", "api/chat/sessions/")
SAFE_METHODS = ("GET", "HEAD", "OPTIONS")

NO_EDITOR_ENDPOINTS = frozenset(
    {
        "ping",
        "list_themes",
        "api/tree",
        "api/files",
        "api/switch",
        "api/new",
        "api/gallery",
        "api/gallery/add",
        "api/gallery/demo",
        "api/compose",
        "api/import/stats-plot-spec",
        "api/chat/stream",
        "api/chat/sessions/",
    }
)
NO_EDITOR_PREFIXES = (
    "api/compose/export/",
    "api/gallery/thumbnail/",
    "api/file-content/",
    "api/chat/sessions/",
)

# The guard checks these selectors in both query and JSON body, including
# duplicate query values. A project id is authority selection, not a file path.
QUERY_BODY_PATH_SELECTORS = ("working_dir", "path", "recipe", "recipe_path")
PROJECT_SELECTOR = "project"
# The suffix is either a project-confined file or a package-relative asset name.
ENDPOINT_PATH_SELECTORS = (
    ("api/file-content/", "project"),
    ("api/gallery/thumbnail/", "package"),
)
REQUEST_GUARD = "figrecipe._django._project_access.prepare_request"
API_DISPATCHER = "figrecipe._django.views.api_dispatch"
HOSTED_API_DISPATCHER = "figrecipe._django.views._hosted_api_dispatch"


def requires_write(request, endpoint: str | None) -> bool:
    """Return the existing write-capability decision; unknown routes need write."""
    if endpoint is None or endpoint in READ_ENDPOINTS:
        return False
    if endpoint.startswith(READ_PREFIXES):
        return False
    if endpoint.startswith(METHOD_SENSITIVE_PREFIXES):
        return request.method not in SAFE_METHODS
    return True


def allows_no_editor(endpoint: str) -> bool:
    """Return whether the existing dispatcher permits absent editor context."""
    return endpoint in NO_EDITOR_ENDPOINTS or endpoint.startswith(NO_EDITOR_PREFIXES)
