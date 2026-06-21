#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Terminal plotting via termplotlib."""

import numpy as np


def termplot(*args):
    """Plot y (and optional x) values in the terminal using termplotlib.

    Parameters
    ----------
    *args
        Either ``(y,)`` — plotted against its indices — or ``(x, y, ...)``
        where extra positional arguments are ignored.

    Returns
    -------
    None
        Displays the plot in the terminal.
    """
    import termplotlib as tpl

    if len(args) == 1:
        y = args[0]
        x = np.arange(len(y))
    elif len(args) >= 2:
        x, y = args[0], args[1]
    else:
        raise ValueError("termplot requires at least one argument (y values)")

    fig = tpl.figure()
    fig.plot(x, y)
    fig.show()


# EOF
