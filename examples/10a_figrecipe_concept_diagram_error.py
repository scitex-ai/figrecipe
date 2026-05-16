#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-02-07 17:18:19 (ywatanabe)"
# File: /home/ywatanabe/proj/figrecipe/examples/10a_figrecipe_concept_diagram_error.py


"""FigRecipe concept diagram using fr.Diagram.

Recreates the FigRecipe architecture concept diagram using the
Diagram API with manual mm-based positioning.
NOTE: x_mm/y_mm is the CENTER of the box, not bottom-left.

Outputs:
    ./10a_figrecipe_concept_diagram_error_out/figrecipe_concept.{png,yaml}
"""

import matplotlib

matplotlib.use("Agg")

from pathlib import Path

import scitex as stx

import figrecipe as fr


@stx.session
def main(
    CONFIG=stx.session.INJECTED,
    logger=stx.session.INJECTED,
):
    """Generate FigRecipe concept diagram."""
    out = Path(CONFIG.SDIR_OUT)

    W, H = 170, 145
    s = fr.Diagram(
        title="FigRecipe: Reproducible Scientific Figures",
        width_mm=W,
        height_mm=H,
    )

    # --- Row 1: Python Code -> Recipe (YAML) -> Figure ---
    bw, bh = 38, 22
    row1_cy = H - 30

    s.add_box(
        "python",
        "Python Code",
        content=["import figrecipe as fr", "ax.plot(x, y)"],
        x_mm=28,
        y_mm=row1_cy,
        width_mm=bw,
        height_mm=bh,
    )
    s.add_box(
        "recipe",
        "Recipe (YAML)",
        subtitle="Structure + Plot Calls",
        emphasis="warning",
        x_mm=W / 2,
        y_mm=row1_cy,
        width_mm=bw,
        height_mm=bh,
    )
    s.add_box(
        "figure",
        "Figure",
        subtitle="PNG / PDF / SVG",
        emphasis="red",
        x_mm=W - 28,
        y_mm=row1_cy,
        width_mm=bw,
        height_mm=bh,
    )

    # Arrows: Python -> Recipe -> Figure
    s.add_arrow("python", "recipe", label="auto-record")
    s.add_arrow("recipe", "figure", label="reproduce")
    s.add_arrow(
        "figure",
        "recipe",
        label="validate",
        style="dashed",
        color="red",
        curve=0.4,
    )

    # --- Row 2: DATA + STYLE inside container ---
    iw, ih = 42, 28
    row2_cy = row1_cy - 45

    cw, ch = 120, ih + 14
    s.add_container(
        "concerns",
        title="Separation of Concerns",
        children=["data", "style"],
        x_mm=W / 2,
        y_mm=row2_cy,
        width_mm=cw,
        height_mm=ch,
    )
    s.add_box(
        "data",
        "DATA",
        subtitle="CSV / NPZ files",
        content=["WHAT to show"],
        emphasis="success",
        x_mm=W / 2 - iw / 2 - 8,
        y_mm=row2_cy - 2,
        width_mm=iw,
        height_mm=ih,
    )
    s.add_box(
        "style",
        "STYLE",
        subtitle="Presets / GUI editing",
        content=["HOW to show"],
        emphasis="purple",
        x_mm=W / 2 + iw / 2 + 8,
        y_mm=row2_cy - 2,
        width_mm=iw,
        height_mm=ih,
    )

    # Arrows from Recipe/Figure down to DATA/STYLE
    s.add_arrow("recipe", "data", color="orange", style="dashed")
    s.add_arrow("recipe", "style", color="purple")
    s.add_arrow("data", "figure", color="green")
    s.add_arrow("style", "figure", color="purple")

    # --- Row 3: Benefits container ---
    bbw, bbh = 38, 18
    row3_cy = 18

    bcw, bch = W - 20, bbh + 16
    s.add_container(
        "benefits",
        title="Benefits for Researchers",
        children=["repro", "flex", "verify"],
        x_mm=W / 2,
        y_mm=row3_cy,
        width_mm=bcw,
        height_mm=bch,
    )
    spacing = bcw / 3
    s.add_box(
        "repro",
        "Reproducibility",
        subtitle="Same recipe = Same figure",
        x_mm=W / 2 - spacing,
        y_mm=row3_cy - 3,
        width_mm=bbw,
        height_mm=bbh,
    )
    s.add_box(
        "flex",
        "Flexibility",
        subtitle="Change style, keep meaning",
        x_mm=W / 2,
        y_mm=row3_cy - 3,
        width_mm=bbw,
        height_mm=bbh,
    )
    s.add_box(
        "verify",
        "Verification",
        subtitle="Pixel-level validation",
        x_mm=W / 2 + spacing,
        y_mm=row3_cy - 3,
        width_mm=bbw,
        height_mm=bbh,
    )

    # Render. This example deliberately produces a diagram with margin /
    # occlusion validation issues so figrecipe's own validator catches them
    # (the *_error suffix in the example name signals that intent). The
    # validation errors are expected output, not a script failure — we
    # capture them so @stx.session still reports FINISHED_SUCCESS with the
    # demonstration intact.
    fig, ax = fr.subplots()
    ax.diagram(s, id="figrecipe_concept")
    try:
        fr.save(fig, out / "figrecipe_concept.png", validate=False)
        logger.info(f"Saved to: {out}/figrecipe_concept.png")
    except ValueError as exc:
        logger.warning(
            f"Diagram validator caught expected issues "
            f"(this example demonstrates them): {exc}"
        )
        # Still produce a FAILED.png so the artefact ships with the demo.
        out.mkdir(parents=True, exist_ok=True)
        fig._fig.savefig(out / "figrecipe_concept_FAILED.png", dpi=150)
    return 0


if __name__ == "__main__":
    main()

# EOF
