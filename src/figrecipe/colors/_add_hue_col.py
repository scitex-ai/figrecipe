#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add a hue column to a DataFrame (with a NaN dummy row for legend control)."""

import numpy as np
import pandas as pd


def add_hue_col(df):
    """Append a ``hue`` column plus a NaN dummy row.

    Adds ``hue=0`` to every existing row and appends one dummy row with
    ``hue=1`` (and NaN/None values elsewhere). Useful for forcing a two-level
    hue legend in seaborn-style plots when only one real group is present.

    Parameters
    ----------
    df : pandas.DataFrame
        Input data.

    Returns
    -------
    pandas.DataFrame
        Copy of ``df`` with the extra ``hue`` column and dummy row.
    """
    df = df.copy()
    df["hue"] = 0
    dummy_row = {}
    for col in df.columns:
        dtype = df[col].dtype
        if dtype is np.dtype(object):
            dummy_row[col] = np.nan
        if dtype is np.dtype(float):
            dummy_row[col] = np.nan
        if dtype is np.dtype(np.int64):
            dummy_row[col] = np.nan
        if dtype is np.dtype(bool):
            dummy_row[col] = None

    dummy_row = pd.DataFrame(pd.Series(dummy_row)).T
    dummy_row["hue"] = 1
    return pd.concat([df, dummy_row], axis=0)


# EOF
