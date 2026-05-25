#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Single-plot bundle (.plt.zip) - thin wrapper over figrecipe bundle functions."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any, Optional, Tuple, Union

__all__ = ["Pltz"]


class Pltz:
    """Single-plot bundle (.plt.zip).

    Thin wrapper around figrecipe's existing bundle functions:
    - load_bundle()
    - save_bundle()
    - reproduce_bundle()

    Bundle structure (inside ZIP)::

        {stem}/
            spec.json    # WHAT to plot (semantic specification)
            style.json   # HOW it looks (appearance settings)
            data.csv     # Raw data
            recipe.yaml  # Reproducible recipe
            exports/
                figure.png
    """

    def __init__(self, path: Union[str, Path]):
        from ._load import load_bundle

        self.path = Path(path)
        self.spec, self.style, self.data = load_bundle(self.path)

    @classmethod
    def from_png(
        cls,
        png_bytes: bytes,
        path: Union[str, Path],
        plot_type: str = "image",
        spec: Optional[dict] = None,
        style: Optional[dict] = None,
        hitmap_bytes: Optional[bytes] = None,
        hitmap_color_map: Optional[dict] = None,
        data_csv: Optional[str] = None,
    ) -> "Pltz":
        """Create a .plt.zip bundle wrapping a pre-rendered PNG image.

        Useful when a figure is rendered externally (e.g., from a gallery
        template) and needs to be stored as a figrecipe bundle.

        Parameters
        ----------
        png_bytes : bytes
            PNG image data.
        path : str or Path
            Output path for the .plt.zip file.
        plot_type : str, optional
            Plot type label stored in spec.json (default: "image").
        spec : dict, optional
            Additional spec entries (default: {}).
        style : dict, optional
            Style entries (default: {}).

        Returns
        -------
        Pltz
            Loaded Pltz instance wrapping the saved bundle.
        """
        import shutil
        import tempfile

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        bundle_spec = {"plot_type": plot_type}
        if spec:
            bundle_spec.update(spec)

        tmp = Path(tempfile.mktemp(suffix=".plt.zip"))
        try:
            with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(
                    "manifest.json",
                    json.dumps({"bundle_type": "PLTZ", "version": "1.0"}, indent=2),
                )
                zf.writestr(
                    "spec.json",
                    json.dumps(bundle_spec, indent=2),
                )
                zf.writestr(
                    "style.json",
                    json.dumps(style or {}, indent=2),
                )
                zf.writestr("exports/figure.png", png_bytes)
                if hitmap_bytes:
                    zf.writestr("exports/hitmap.png", hitmap_bytes)
                if hitmap_color_map:
                    zf.writestr(
                        "metadata/hitmap_color_map.json",
                        json.dumps(hitmap_color_map, indent=2),
                    )
                if data_csv:
                    zf.writestr("data.csv", data_csv)
            shutil.move(str(tmp), str(path))
        except Exception:
            if tmp.exists():
                tmp.unlink()
            raise

        return cls(path)

    @classmethod
    def create(cls, path: Union[str, Path], fig) -> "Pltz":
        """Save a RecordingFigure as a .plt.zip bundle.

        Parameters
        ----------
        path : str or Path
            Output path. If it doesn't end in .zip, .zip is appended.
        fig : RecordingFigure
            Figure created with figrecipe.subplots().

        Returns
        -------
        Pltz
            Loaded Pltz instance wrapping the saved bundle.
        """
        from ._save import save_bundle

        actual_path = save_bundle(fig, path)
        return cls(actual_path)

    def get_preview(self) -> Optional[bytes]:
        """Read pre-rendered preview PNG from bundle.

        Returns
        -------
        bytes or None
            PNG bytes, or None if no preview image is stored.
        """
        try:
            with zipfile.ZipFile(self.path) as zf:
                for name in zf.namelist():
                    if name.endswith(".png") and "hitmap" not in name:
                        return zf.read(name)
        except Exception:
            pass
        return None

    def render_preview(self) -> Optional[bytes]:
        """Reproduce figure and render to PNG bytes.

        Returns
        -------
        bytes or None
            PNG bytes, or None on failure.
        """
        import io
        import os

        os.environ["MPLBACKEND"] = "Agg"
        try:
            import matplotlib

            matplotlib.use("Agg")
            from ._load import reproduce_bundle

            fig, axes = reproduce_bundle(self.path)
            mpl_fig = fig.fig if hasattr(fig, "fig") else fig
            buf = io.BytesIO()
            mpl_fig.savefig(buf, format="png", dpi=150)
            buf.seek(0)
            return buf.read()
        except Exception:
            return None

    def save(self) -> None:
        """Save spec/style changes back to bundle in-place.

        Updates spec.json and style.json inside the ZIP without
        re-rendering the figure.
        """
        # Read all current entries
        with zipfile.ZipFile(self.path, "r") as zf:
            entries = {name: zf.read(name) for name in zf.namelist()}

        # Detect prefix used inside ZIP (figrecipe uses {stem}/ as root dir)
        root_dir = self.path.stem
        # Double extension: "panelA.plt.zip" → stem "panelA.plt"
        if root_dir.endswith(".plt"):
            root_dir = root_dir[:-4]

        spec_key = (
            f"{root_dir}/spec.json"
            if f"{root_dir}/spec.json" in entries
            else "spec.json"
        )
        style_key = (
            f"{root_dir}/style.json"
            if f"{root_dir}/style.json" in entries
            else "style.json"
        )

        entries[spec_key] = json.dumps(self.spec, indent=2, default=str).encode()
        entries[style_key] = json.dumps(self.style, indent=2, default=str).encode()

        # Rebuild ZIP atomically via temp file
        import shutil
        import tempfile

        tmp = Path(tempfile.mktemp(suffix=self.path.suffix))
        try:
            with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
                for name, data in entries.items():
                    zf.writestr(name, data)
            shutil.move(str(tmp), str(self.path))
        except Exception:
            if tmp.exists():
                tmp.unlink()
            raise

    def update_preview(self) -> None:
        """Re-render and update preview PNG in bundle."""
        preview = self.render_preview()
        if not preview:
            return

        with zipfile.ZipFile(self.path, "r") as zf:
            entries = {name: zf.read(name) for name in zf.namelist()}

        # Find existing PNG (not hitmap)
        png_key = next(
            (n for n in entries if n.endswith(".png") and "hitmap" not in n),
            None,
        )
        if png_key is None:
            root_dir = self.path.stem
            if root_dir.endswith(".plt"):
                root_dir = root_dir[:-4]
            png_key = f"{root_dir}/exports/figure.png"

        entries[png_key] = preview

        import shutil
        import tempfile

        tmp = Path(tempfile.mktemp(suffix=self.path.suffix))
        try:
            with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
                for name, data in entries.items():
                    zf.writestr(name, data)
            shutil.move(str(tmp), str(self.path))
        except Exception:
            if tmp.exists():
                tmp.unlink()
            raise

    def reproduce(self) -> Tuple[Any, Any]:
        """Reproduce figure from bundle.

        Returns
        -------
        tuple
            (fig, axes) reproduced from bundle.
        """
        from ._load import reproduce_bundle

        return reproduce_bundle(self.path)


# EOF
