"""Leaf-owned workspace content, with authority supplied through the SDK.

The host must stamp its resolved app mount as ``stx_mount`` after calling the
context builder. The workspace request's URL is not the app's API mount.
"""

import os
from pathlib import Path

from figrecipe._utils._optional import missing_extra

try:
    from django.middleware.csrf import get_token
    from django.views.decorators.csrf import ensure_csrf_cookie
except ImportError as exc:
    raise missing_extra(exc) from exc

from ._project_access import prepare_request


def build_workspace_context(request, current_project=None):
    """Resolve the SDK project rather than trusting a host's presentation object.

    Raises SDK AccessError/CapabilityUnavailable before rendering or file I/O.
    ``current_project`` retains the generic host context-builder signature.
    """
    prepare_request(request)
    get_token(request)
    access = getattr(request, "_figrecipe_project", None)
    working_dir = (
        str(request._figrecipe_working_dir)
        if access
        else os.environ.get("FIGRECIPE_WORKING_DIR", "")
    )
    from figrecipe import __version__

    return {
        "app_slug": "figrecipe",
        "app_label": "FigRecipe",
        "app_version": __version__,
        "hosted": access is not None,
        "project_id": access.id if access else "",
        "project_name": access.name if access else "",
        "working_dir": working_dir,
        "working_dir_name": access.name if access else Path(working_dir).name,
        "recipe": request.GET.get("recipe", ""),
        # An explicit empty mount is valid; an undeclared mount cannot route.
        "stx_mount": None,
    }


@ensure_csrf_cookie
def render_workspace_content(request, current_project=None, *, stx_mount):
    """Render leaf content under an explicitly resolved host app mount.

    ``stx_mount`` comes from the host's route declaration, never the partial
    request URL or a query parameter. The empty string declares a root mount.
    Project authority still comes from the SDK provider; ``current_project``
    is only the existing generic context-builder argument.

    SDK access errors propagate before rendering so the host can retain its
    existing authentication/error response policy.
    """
    if not isinstance(stx_mount, str):
        raise TypeError("The host must explicitly declare the app mount")
    try:
        from django.shortcuts import render
    except ImportError as exc:
        raise missing_extra(exc) from exc

    context = build_workspace_context(request, current_project)
    context["stx_mount"] = stx_mount
    return render(request, "figrecipe/workspace_partial.html", context)
