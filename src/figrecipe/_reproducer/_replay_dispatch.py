#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Special-method dispatch for call replay.

Most recorded calls replay as ``getattr(ax, name)(*args, **kwargs)``. These do
not: some are figrecipe helpers rather than axes methods (``rotate_labels``,
``stx_*``), some need a reconstructed non-trivial object (patches, legends,
diagrams), and some are third-party (``sns.*``).

MATCH ORDER IS LOAD-BEARING and is the order of ``_HANDLERS`` below: the
``sns.`` prefix is tested FIRST and the ``stx_`` prefix LAST, after every exact
name. ``stx_`` must stay last so an exact name that happens to start with it
would still win; moving it earlier would shadow those handlers.

Every handler is normalised to ``(ax, call, result_cache) -> Any`` so the
caller needs no per-handler knowledge.
"""

from typing import Any, Callable, Dict, Optional

from .._recorder import CallRecord

Handler = Callable[[Any, CallRecord, Dict[str, Any]], Any]


def _replay_sns(ax: Any, call: CallRecord, result_cache: Dict[str, Any]) -> Any:
    from ._seaborn import replay_seaborn_call

    return replay_seaborn_call(ax, call)


def _replay_boxplot(ax: Any, call: CallRecord, result_cache: Dict[str, Any]) -> Any:
    from ._boxplot import replay_boxplot_call

    return replay_boxplot_call(ax, call)


def _replay_violinplot(ax: Any, call: CallRecord, result_cache: Dict[str, Any]) -> Any:
    from ._violin import replay_violinplot_call

    return replay_violinplot_call(ax, call)


def _replay_add_patch(ax: Any, call: CallRecord, result_cache: Dict[str, Any]) -> Any:
    from ._replay_patches import replay_add_patch_call

    return replay_add_patch_call(ax, call)


def _replay_joyplot(ax: Any, call: CallRecord, result_cache: Dict[str, Any]) -> Any:
    from ._custom_plots import replay_joyplot_call

    return replay_joyplot_call(ax, call)


def _replay_swarmplot(ax: Any, call: CallRecord, result_cache: Dict[str, Any]) -> Any:
    from ._custom_plots import replay_swarmplot_call

    return replay_swarmplot_call(ax, call)


def _replay_stat_annotation(
    ax: Any, call: CallRecord, result_cache: Dict[str, Any]
) -> Any:
    from .._wrappers._stat_annotation import draw_stat_annotation

    kwargs = call.kwargs.copy()
    x1, x2 = kwargs.pop("x1", 0), kwargs.pop("x2", 1)
    return draw_stat_annotation(ax, x1, x2, **kwargs)


def _replay_graph(ax: Any, call: CallRecord, result_cache: Dict[str, Any]) -> Any:
    from ._replay_graph import replay_graph_call

    return replay_graph_call(ax, call)


def _replay_diagram(ax: Any, call: CallRecord, result_cache: Dict[str, Any]) -> Any:
    from ._replay_diagram import replay_diagram_native_call

    return replay_diagram_native_call(ax, call)


def _replay_legend(ax: Any, call: CallRecord, result_cache: Dict[str, Any]) -> Any:
    from ._legend import replay_legend_call

    return replay_legend_call(ax, call, result_cache)


def _replay_stem(ax: Any, call: CallRecord, result_cache: Dict[str, Any]) -> Any:
    from ._stem import replay_stem_call

    return replay_stem_call(ax, call)


def _replay_rotate_labels(
    ax: Any, call: CallRecord, result_cache: Dict[str, Any]
) -> Any:
    # figrecipe tick-label rotation: a styles helper, not an mpl axes method,
    # so getattr(ax, "rotate_labels") fails on the raw replay axes. Dispatch
    # to the helper so the rotation (and the tick re-nicing it applies) is
    # reproduced -- otherwise labels stay horizontal + limits drift.
    from ..styles._axis_helpers import rotate_labels as _rotate_labels

    kw = {k: call.kwargs.get(k) for k in ("x", "y", "x_ha", "y_ha", "auto_adjust")}
    try:
        _rotate_labels(ax, **{k: v for k, v in kw.items() if v is not None})
    except Exception:
        pass
    return None


def _replay_stx(ax: Any, call: CallRecord, result_cache: Dict[str, Any]) -> Any:
    # figrecipe scitex-compat plot methods are functions taking a raw mpl
    # axes; a plain getattr(ax, name) fails on raw axes (e.g. mm-compose
    # add_axes panels), silently dropping the plot + its make_axes_locatable
    # marginals. Dispatch to the compat function so it reconstructs fully.
    from ._scitex import replay_stx_call

    return replay_stx_call(ax, call, result_cache)


#: ``(predicate, handler)`` pairs, tested in order. See the module docstring —
#: this order is behaviour, not style.
_HANDLERS = (
    (lambda name: name.startswith("sns."), _replay_sns),
    (lambda name: name == "boxplot", _replay_boxplot),
    (lambda name: name == "violinplot", _replay_violinplot),
    (lambda name: name == "add_patch", _replay_add_patch),
    (lambda name: name == "joyplot", _replay_joyplot),
    (lambda name: name == "swarmplot", _replay_swarmplot),
    (lambda name: name == "stat_annotation", _replay_stat_annotation),
    (lambda name: name == "graph", _replay_graph),
    (lambda name: name in ("diagram", "schematic"), _replay_diagram),
    (lambda name: name == "legend", _replay_legend),
    (lambda name: name == "stem", _replay_stem),
    (lambda name: name == "rotate_labels", _replay_rotate_labels),
    # LAST — see the module docstring.
    (lambda name: name.startswith("stx_"), _replay_stx),
)


def find_special_handler(method_name: str) -> Optional[Handler]:
    """Return the handler for ``method_name``, or ``None`` if it has none.

    ``None`` means "no special handler exists for this name" — a lookup miss,
    not a failure — and the caller should replay the call generically.
    """
    for matches, handler in _HANDLERS:
        if matches(method_name):
            return handler
    return None


__all__ = [
    "find_special_handler",
]
