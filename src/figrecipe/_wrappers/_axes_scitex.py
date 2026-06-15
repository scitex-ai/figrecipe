#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SciTeX scientific plot methods mixin for RecordingAxes.

Provides stx_* methods (confusion matrix, ECDF, raster, heatmap, etc.)
that record composite calls for recipe reproduction.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from .._recorder import Recorder


class SciTexMixin:
    """Mixin providing scientific plot methods on RecordingAxes.

    Each method:
    1. Suppresses per-call recording with _no_record()
    2. Calls the standalone implementation on self._ax
    3. Records one composite call for reproduction

    Usage:
        >>> ax.stx_conf_mat(confusion_matrix)
        >>> ax.stx_mean_std(data_2d)
        >>> ax.stx_ecdf(values)
    """

    _ax: "Axes"
    _recorder: "Recorder"
    _position: tuple
    _track: bool

    def _record_stx_call(self, method_name, args, kwargs, call_id=None):
        """Record a composite stx_* call."""
        self._recorder.record_call(
            ax_position=self._position,
            method_name=method_name,
            args=args,
            kwargs=kwargs,
            call_id=call_id,
        )

    # ── Shaded line family ──────────────────────────────────────────

    def stx_shaded_line(
        self, xs, ys_lower, ys_middle, ys_upper, *, id=None, track=True, **kwargs
    ):
        """Plot line(s) with shaded uncertainty regions."""
        from .._scitex_compat._shaded_lines import stx_shaded_line

        with self._no_record():
            result = stx_shaded_line(
                self._ax, xs, ys_lower, ys_middle, ys_upper, **kwargs
            )
        if self._track and track:
            self._record_stx_call(
                "stx_shaded_line", (xs, ys_lower, ys_middle, ys_upper), kwargs, id
            )
        return result

    def stx_line(self, x, y=None, *, id=None, track=True, **kwargs):
        """Plot a simple line (matplotlib-convention: x, y).

        See figrecipe#110: signature flipped from the legacy
        (values_1d, xx=None) form so `ax.stx_line(x, y)` matches
        `ax.plot(x, y)`.
        """
        from .._scitex_compat._shaded_lines import stx_line

        with self._no_record():
            result = stx_line(self._ax, x, y=y, **kwargs)
        if self._track and track:
            self._record_stx_call("stx_line", (x,), {"y": y, **kwargs}, id)
        return result

    def stx_mean_std(self, values_2d, xx=None, sd=1, *, id=None, track=True, **kwargs):
        """Plot mean line with +-sd shading."""
        from .._scitex_compat._shaded_lines import stx_mean_std

        with self._no_record():
            result = stx_mean_std(self._ax, values_2d, xx=xx, sd=sd, **kwargs)
        if self._track and track:
            self._record_stx_call(
                "stx_mean_std", (values_2d,), {"xx": xx, "sd": sd, **kwargs}, id
            )
        return result

    def stx_mean_ci(
        self, values_2d, xx=None, perc=95, *, id=None, track=True, **kwargs
    ):
        """Plot mean line with confidence interval shading."""
        from .._scitex_compat._shaded_lines import stx_mean_ci

        with self._no_record():
            result = stx_mean_ci(self._ax, values_2d, xx=xx, perc=perc, **kwargs)
        if self._track and track:
            self._record_stx_call(
                "stx_mean_ci", (values_2d,), {"xx": xx, "perc": perc, **kwargs}, id
            )
        return result

    def stx_median_iqr(self, values_2d, xx=None, *, id=None, track=True, **kwargs):
        """Plot median line with IQR shading."""
        from .._scitex_compat._shaded_lines import stx_median_iqr

        with self._no_record():
            result = stx_median_iqr(self._ax, values_2d, xx=xx, **kwargs)
        if self._track and track:
            self._record_stx_call(
                "stx_median_iqr", (values_2d,), {"xx": xx, **kwargs}, id
            )
        return result

    # ── Scientific plots ────────────────────────────────────────────

    def stx_conf_mat(
        self,
        conf_mat_2d,
        x_labels=None,
        y_labels=None,
        *,
        id=None,
        track=True,
        **kwargs,
    ):
        """Plot a confusion matrix."""
        from .._scitex_compat._scientific import stx_conf_mat

        with self._no_record():
            result = stx_conf_mat(
                self._ax, conf_mat_2d, x_labels=x_labels, y_labels=y_labels, **kwargs
            )
        if self._track and track:
            self._record_stx_call(
                "stx_conf_mat",
                (conf_mat_2d,),
                {"x_labels": x_labels, "y_labels": y_labels, **kwargs},
                id,
            )
        return result

    def stx_ecdf(self, values_1d, *, id=None, track=True, **kwargs):
        """Plot an empirical CDF."""
        from .._scitex_compat._scientific import stx_ecdf

        with self._no_record():
            result = stx_ecdf(self._ax, values_1d, **kwargs)
        if self._track and track:
            self._record_stx_call("stx_ecdf", (values_1d,), kwargs, id)
        return result

    def stx_raster(self, spike_times_list, *, id=None, track=True, **kwargs):
        """Plot a raster/event plot."""
        from .._scitex_compat._scientific import stx_raster

        with self._no_record():
            result = stx_raster(self._ax, spike_times_list, **kwargs)
        if self._track and track:
            self._record_stx_call("stx_raster", (spike_times_list,), kwargs, id)
        return result

    def stx_scatter_hist(self, x, y, *, id=None, track=True, **kwargs):
        """Scatter plot with marginal histograms or per-class KDE curves.

        Pass ``kde=True`` for smooth marginal densities, ``groups=<labels>``
        for one KDE per class, and ``palette={group: color}`` to colour both
        the per-group KDE curves and the scatter points. ``x`` may be a pandas
        datetime Series (scatter stays on the datetime axis; the KDE is
        estimated on the date2num float grid). See the underlying
        ``stx_scatter_hist`` for the full parameter list.
        """
        from .._scitex_compat._scientific import stx_scatter_hist

        with self._no_record():
            result = stx_scatter_hist(self._ax, x, y, **kwargs)
        if self._track and track:
            self._record_stx_call("stx_scatter_hist", (x, y), kwargs, id)
        return result

    # ── Heatmap ─────────────────────────────────────────────────────

    def stx_heatmap(self, values_2d, *, id=None, track=True, **kwargs):
        """Plot a heatmap with smart annotation colors."""
        from .._scitex_compat._heatmap import stx_heatmap

        with self._no_record():
            result = stx_heatmap(self._ax, values_2d, **kwargs)
        if self._track and track:
            self._record_stx_call("stx_heatmap", (values_2d,), kwargs, id)
        return result

    # ── Simple helpers ──────────────────────────────────────────────

    def stx_fillv(self, starts, ends, color="red", alpha=0.2, *, id=None, track=True):
        """Fill vertical spans."""
        from .._scitex_compat._simple import stx_fillv

        with self._no_record():
            result = stx_fillv(self._ax, starts, ends, color=color, alpha=alpha)
        if self._track and track:
            self._record_stx_call(
                "stx_fillv", (starts, ends), {"color": color, "alpha": alpha}, id
            )
        return result

    def stx_rectangle(self, xx, yy, ww, hh, *, id=None, track=True, **kwargs):
        """Add a rectangle patch."""
        from .._scitex_compat._simple import stx_rectangle

        with self._no_record():
            result = stx_rectangle(self._ax, xx, yy, ww, hh, **kwargs)
        if self._track and track:
            self._record_stx_call("stx_rectangle", (xx, yy, ww, hh), kwargs, id)
        return result

    def stx_image(self, arr_2d, *, id=None, track=True, **kwargs):
        """Display 2D array as image with correct orientation."""
        from .._scitex_compat._simple import stx_image

        with self._no_record():
            result = stx_image(self._ax, arr_2d, **kwargs)
        if self._track and track:
            self._record_stx_call("stx_image", (arr_2d,), kwargs, id)
        return result

    def stx_violin(self, values_list, *, id=None, track=True, **kwargs):
        """Plot violins from a list of arrays."""
        from .._scitex_compat._simple import stx_violin

        with self._no_record():
            result = stx_violin(self._ax, values_list, **kwargs)
        if self._track and track:
            self._record_stx_call("stx_violin", (values_list,), kwargs, id)
        return result

    def stx_scalebar(self, x_len, y_len, *, id=None, track=True, **kwargs):
        """Draw an L-shaped scale bar for axis-off trace / EEG panels.

        The horizontal arm encodes time (``x_len``) and the vertical arm
        encodes amplitude (``y_len``), sharing a corner, with padded labels
        that do not overlap. Use with ``ax.axis("off")``. See the underlying
        ``stx_scalebar`` for the full parameter list (``x_label``, ``y_label``,
        ``loc``, ``color``, ``lw``, ``pad_frac``, ``label_pad_frac``).
        """
        from .._scitex_compat._simple import stx_scalebar

        with self._no_record():
            result = stx_scalebar(self._ax, x_len, y_len, **kwargs)
        if self._track and track:
            self._record_stx_call("stx_scalebar", (x_len, y_len), kwargs, id)
        return result


__all__ = ["SciTexMixin"]

# ── Branding aliases (driven by scitex_dev._branding registry) ──────────────
# Generates ax.fr_*() aliases for each ax.stx_*() method. The helper rebinds
# __module__ on the alias methods to the counterpart brand's umbrella attr
# (scitex.plt) so that help() on the umbrella side does not leak figrecipe
# as the source module. Previously this was a manual setattr loop driven by
# a FIGRECIPE_ALIAS env var; the registry replaces both.
#
# Defensive import: ``scitex_dev._branding`` ships on scitex-dev develop and
# is not in the PyPI v0.11.16 wheel yet (see socialia commit 5640a56 for the
# same fallback pattern). When the installed scitex-dev predates the
# registry, skip alias registration — the stx_* methods remain functional;
# only the fr_* aliases on the figrecipe-branded surface are absent until
# scitex-dev>=0.11.17 lands. Once 0.11.17 is on PyPI this try/except is a
# no-op (the registry always wins).
try:
    from scitex_dev._branding import (
        register_method_aliases as _register_aliases,  # noqa: E402
    )

    _register_aliases(SciTexMixin, brand_key="scitex-plt")
    del _register_aliases
except ModuleNotFoundError:
    pass

# EOF
