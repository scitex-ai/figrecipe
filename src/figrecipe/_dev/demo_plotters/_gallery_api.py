#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File: figrecipe/_dev/demo_plotters/_gallery_api.py

"""Gallery generation API (figrecipe-native).

Owns the scitex.plt.gallery surface (``generate``, ``get_plot_spec``,
``get_plot_data``) without depending on the ``scitex`` umbrella. Plots come
from the demo_plotters ``REGISTRY`` (signature ``plot_func(fr, rng, ax)``).

Usage
-----
>>> import figrecipe as fr
>>> fr.gallery.generate("./gallery")
>>> fr.gallery.generate("./gallery", category="line_curve")
>>> spec = fr.gallery.get_plot_spec("line_curve", "plot")
>>> df = fr.gallery.get_plot_data("line_curve", "plot")
"""

from pathlib import Path
from typing import Any, Dict, Optional

from ._categories import CATEGORIES
from ._registry import REGISTRY

__all__ = ["generate", "get_plot_spec", "get_plot_data"]


def _new_rng(seed: int = 42):
    import numpy as np

    return np.random.default_rng(seed)


def _category_for_plot(plot_name: str) -> str:
    for cat_name, plots in CATEGORIES.items():
        if plot_name in plots:
            return cat_name
    return "uncategorized"


def _plots_to_generate(category=None, plot_type=None):
    if plot_type is not None:
        return [plot_type]
    if category is not None:
        if category not in CATEGORIES:
            raise ValueError(
                f"Unknown category: {category}. Available: {list(CATEGORIES.keys())}"
            )
        return list(CATEGORIES[category])
    return [p for plots in CATEGORIES.values() for p in plots]


def generate(  # noqa: C901
    output_dir="./gallery",
    category: Optional[str] = None,
    plot_type: Optional[str] = None,
    dpi: int = 150,
    save_csv: bool = True,
    save_png: bool = True,
    save_svg: bool = True,
    save_plot: bool = True,
    verbose: bool = True,
):
    """Generate gallery plots (figrecipe bundles + extracted PNG/SVG/CSV).

    Parameters
    ----------
    output_dir : str or Path
        Output directory for the gallery.
    category : str, optional
        Generate only plots in this category (see ``gallery.CATEGORIES``).
    plot_type : str, optional
        Generate only this specific plot type.
    dpi : int
        Resolution for raster output.
    save_csv, save_png, save_svg, save_plot : bool
        Which artifacts to keep.
    verbose : bool
        Print progress messages.

    Returns
    -------
    dict
        Generated file paths and any errors.
    """
    import shutil

    import figrecipe as fr
    from figrecipe.presets import SCITEX_STYLE

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    plots = _plots_to_generate(category, plot_type)
    if verbose:
        print(f"Generating {len(plots)} plots to {output_dir}")

    results: Dict[str, list] = {
        "png": [],
        "svg": [],
        "csv": [],
        "plot": [],
        "errors": [],
    }

    # Pass only the layout kwargs figrecipe.subplots accepts as explicit
    # parameters; other SCITEX_STYLE keys are recorder/output settings that
    # would leak into Figure.set().
    import inspect

    _subplots_params = set(inspect.signature(fr.subplots).parameters)
    style = {
        k: v
        for k, v in SCITEX_STYLE.items()
        if k in _subplots_params and k not in ("nrows", "ncols")
    }

    for plot_name in plots:
        plot_func = REGISTRY.get(plot_name)
        if plot_func is None:
            if verbose:
                print(f"  [SKIP] {plot_name}: not implemented")
            continue

        cat_dir = output_dir / _category_for_plot(plot_name)
        cat_dir.mkdir(parents=True, exist_ok=True)

        try:
            fig, ax = fr.subplots(**style)
            # Keep the RecordingFigure from subplots; the plotter may return
            # the underlying mpl figure when given an existing ax.
            plot_func(fr, _new_rng(), ax)

            png_path = cat_dir / f"{plot_name}.png"
            fr.save(fig, png_path, dpi=dpi, validate=False, verbose=False)

            if save_png and png_path.exists():
                results["png"].append(str(png_path))
                if verbose:
                    print(f"  [PNG] {png_path}")

            # figrecipe save() emits <stem>.yaml (recipe) + <stem>_data/*.csv
            recipe_path = png_path.with_suffix(".yaml")
            data_dir = cat_dir / f"{plot_name}_data"

            if save_csv and data_dir.is_dir():
                merged = cat_dir / f"{plot_name}.csv"
                _merge_data_csvs(data_dir, merged)
                if merged.exists():
                    results["csv"].append(str(merged))
                    if verbose:
                        print(f"  [CSV] {merged}")

            if save_svg:
                svg_path = cat_dir / f"{plot_name}.svg"
                try:
                    mpl_fig = getattr(fig, "fig", fig)
                    mpl_fig.savefig(svg_path, format="svg")
                    results["svg"].append(str(svg_path))
                    if verbose:
                        print(f"  [SVG] {svg_path}")
                except Exception as e:  # noqa: BLE001
                    if verbose:
                        print(f"  [WARN] svg for {plot_name}: {e}")

            if save_plot and recipe_path.exists():
                results["plot"].append(str(recipe_path))
            elif not save_plot:
                if recipe_path.exists():
                    recipe_path.unlink()
                if data_dir.is_dir():
                    shutil.rmtree(data_dir)

            try:
                fr.pyplot.close(fig)
            except Exception:  # noqa: BLE001
                pass

        except Exception as e:  # noqa: BLE001
            results["errors"].append({"plot": plot_name, "error": str(e)})
            if verbose:
                print(f"  [ERROR] {plot_name}: {e}")

    if verbose:
        print(
            f"\nGenerated: {len(results['png'])} PNG, {len(results['svg'])} SVG, "
            f"{len(results['csv'])} CSV, {len(results['plot'])} recipes"
        )
        if results["errors"]:
            print(f"Errors: {len(results['errors'])}")

    return results


def _merge_data_csvs(data_dir: Path, out_path: Path) -> None:
    """Concatenate per-trace CSVs in ``data_dir`` into a single wide CSV."""
    import pandas as pd

    frames = []
    for csv in sorted(data_dir.glob("*.csv")):
        try:
            df = pd.read_csv(csv)
            df = df.add_prefix(f"{csv.stem}__")
            frames.append(df.reset_index(drop=True))
        except Exception:  # noqa: BLE001
            continue
    if frames:
        pd.concat(frames, axis=1).to_csv(out_path, index=False)


def get_plot_spec(category: str, plot_name: str) -> Dict[str, Any]:
    """Get a minimal spec dictionary for a gallery plot.

    Parameters
    ----------
    category : str
        Plot category (see ``gallery.CATEGORIES``).
    plot_name : str
        Plot name within the category.

    Returns
    -------
    dict
        Spec dictionary for the plot type.
    """
    if category not in CATEGORIES:
        raise ValueError(
            f"Unknown category: {category}. Available: {list(CATEGORIES.keys())}"
        )
    if plot_name not in CATEGORIES[category]:
        raise ValueError(f"Unknown plot: {plot_name} in category {category}")

    return {
        "schema": {"name": "figrecipe.plot", "version": "1.0.0"},
        "plot_type": plot_name,
        "category": category,
        "axes": {"xlabel": "", "ylabel": ""},
    }


def get_plot_data(category: str, plot_name: str):
    """Get sample data for a gallery plot as a DataFrame.

    Parameters
    ----------
    category : str
        Plot category (see ``gallery.CATEGORIES``).
    plot_name : str
        Plot name within the category.

    Returns
    -------
    pandas.DataFrame or None
        Sample data for the plot, or None if it has no extractable data.
    """
    import tempfile
    import warnings

    if category not in CATEGORIES:
        raise ValueError(
            f"Unknown category: {category}. Available: {list(CATEGORIES.keys())}"
        )
    if plot_name not in CATEGORIES[category]:
        raise ValueError(f"Unknown plot: {plot_name} in category {category}")

    plot_func = REGISTRY.get(plot_name)
    if plot_func is None:
        return None

    try:
        import pandas as pd

        import figrecipe as fr

        with tempfile.TemporaryDirectory() as tmp:
            rec_fig, ax = fr.subplots()
            # Plotter may return the underlying mpl figure; keep the
            # RecordingFigure for saving so data is recorded.
            plot_func(fr, _new_rng(), ax)
            out = Path(tmp) / f"{plot_name}.png"
            fr.save(rec_fig, out, validate=False, verbose=False)

            extracted = fr.extract_data(out.with_suffix(".yaml"))
            try:
                fr.pyplot.close(rec_fig)
            except Exception:  # noqa: BLE001
                pass

        # Flatten {trace: {col: array}} into a single wide DataFrame.
        columns: Dict[str, Any] = {}
        for trace, cols in extracted.items():
            if isinstance(cols, dict):
                for col, values in cols.items():
                    columns[f"{trace}__{col}"] = list(values)
        if not columns:
            return None
        max_len = max(len(v) for v in columns.values())
        for k, v in columns.items():
            if len(v) < max_len:
                columns[k] = list(v) + [None] * (max_len - len(v))
        return pd.DataFrame(columns)

    except Exception as e:  # noqa: BLE001
        warnings.warn(f"Could not get data for {category}/{plot_name}: {e}")
        return None


# EOF
