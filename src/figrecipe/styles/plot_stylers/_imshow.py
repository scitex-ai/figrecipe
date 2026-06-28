#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Imshow styler for publication-quality image plots."""

__all__ = ["ImshowStyler", "style_imshow"]

from typing import Any, Optional

from ._base import PlotStyler

# Sentinel distinguishing "caller did not pass aspect" (-> default to the
# style's "equal") from an explicit aspect the caller DID pass (including the
# string "auto"). Using ``None`` for the default is not enough: ``None`` is a
# legitimate value a caller might forward, and historically caused an explicit
# user aspect to be clobbered back to "equal" when the styler was re-applied.
_ASPECT_UNSET = object()


class ImshowStyler(PlotStyler):
    """Styler for matplotlib imshow elements.

    Applies consistent interpolation and aspect settings to image plots
    for publication-quality figures.

    Parameters
    ----------
    style : DotDict, optional
        Style configuration. If None, uses current global style.

    Examples
    --------
    >>> import figrecipe as fr
    >>> import numpy as np
    >>> fig, ax = fr.subplots()
    >>> im = ax.imshow(np.random.rand(10, 10))
    >>> styler = ImshowStyler()
    >>> styler.apply(im, ax)
    """

    style_section = "imshow"

    def apply(
        self,
        image: Any,
        ax: Optional[Any] = None,
        interpolation: Optional[str] = None,
        aspect: Any = _ASPECT_UNSET,
        cmap: Optional[str] = None,
    ) -> Any:
        """Apply styling to an imshow plot.

        Parameters
        ----------
        image : AxesImage
            Image returned by ax.imshow().
        ax : Axes, optional
            The axes containing the image (for aspect ratio).
        interpolation : str, optional
            Interpolation method. Default from style or "nearest".
        aspect : str, optional
            Aspect ratio. If the caller passes one EXPLICITLY (e.g. "auto"),
            it wins and is applied as-is. Only when the caller omits ``aspect``
            entirely does this default to the style's "equal" -- so a user's
            ``ax.imshow(..., aspect="auto")`` is never clobbered to "equal".
        cmap : str, optional
            Colormap to apply.

        Returns
        -------
        AxesImage
            The styled image.
        """
        # Get parameters with defaults from style
        if interpolation is None:
            interpolation = self.get_param("interpolation", "nearest")
        # Only fall back to the style default when the caller did NOT pass an
        # aspect. An explicitly-passed aspect (including "auto") wins.
        if aspect is _ASPECT_UNSET:
            aspect = self.get_param("aspect", "equal")

        # Apply interpolation
        image.set_interpolation(interpolation)

        # Apply colormap if specified
        if cmap is not None:
            image.set_cmap(cmap)

        # Apply aspect to axes if provided
        if ax is not None:
            ax.set_aspect(aspect)

        return image


# Convenience function
def style_imshow(
    image: Any,
    ax: Optional[Any] = None,
    interpolation: Optional[str] = None,
    aspect: Any = _ASPECT_UNSET,
    cmap: Optional[str] = None,
    style: Any = None,
) -> Any:
    """Apply publication-quality styling to an imshow plot.

    This is a convenience function that creates an ImshowStyler and applies it.

    Parameters
    ----------
    image : AxesImage
        Image returned by ax.imshow().
    ax : Axes, optional
        The axes containing the image.
    interpolation : str, optional
        Interpolation method. Default: "nearest".
    aspect : str, optional
        Aspect ratio. If passed explicitly (e.g. "auto") it wins; only when
        omitted does it default to the style's "equal".
    cmap : str, optional
        Colormap to apply.
    style : DotDict, optional
        Style configuration.

    Returns
    -------
    AxesImage
        The styled image.

    Examples
    --------
    >>> import figrecipe as fr
    >>> import numpy as np
    >>> fig, ax = fr.subplots()
    >>> im = ax.imshow(np.random.rand(10, 10))
    >>> fr.style_imshow(im, ax)
    """
    styler = ImshowStyler(style=style)
    return styler.apply(
        image,
        ax=ax,
        interpolation=interpolation,
        aspect=aspect,
        cmap=cmap,
    )


# EOF
