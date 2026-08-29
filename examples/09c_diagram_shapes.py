#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagram shapes showcase with fr.Diagram().

Demonstrates all available diagram shapes:
1. Shape gallery — all 7 shapes side by side
2. Data pipeline — mixing shapes by semantic role (node_class)
3. Software architecture — codeblock + cylinder + document

Outputs:
    ./09c_diagram_shapes_out/shape_gallery.png
    ./09c_diagram_shapes_out/data_pipeline.png
    ./09c_diagram_shapes_out/software_arch.png
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
    """Run diagram shape demos."""
    OUT = Path(CONFIG.SDIR_OUT)

    # --- 1. Shape gallery ---
    logger.info("Demo 1: Shape gallery (all 7 shapes)")
    s1 = fr.Diagram(width_mm=170, height_mm=55)
    shapes = [
        ("rounded", "rounded"),
        ("box", "box"),
        ("stadium", "stadium"),
        ("cylinder", "cylinder"),
        ("document", "document"),
        ("file", "file"),
        ("codeblock", "codeblock"),
    ]
    x = 15
    for sid, shape in shapes:
        s1.add_box(
            sid,
            shape,
            shape=shape,
            x_mm=x,
            y_mm=28,
            width_mm=20,
            height_mm=22,
        )
        x += 24
    fig1, ax1 = fr.subplots()
    ax1.diagram(s1, id="gallery")
    fr.save(fig1, OUT / "shape_gallery.png", validate=False)

    # --- 2. Data pipeline with semantic node classes ---
    logger.info("Demo 2: Data pipeline with node_class")
    s2 = fr.Diagram(
        title="Reproducible Analysis Pipeline",
        width_mm=170,
        height_mm=60,
    )
    s2.add_box("script", "analyze.py", node_class="code")
    s2.add_box("data", "raw_eeg.csv", node_class="input")
    s2.add_box("process", "Preprocess", node_class="processing")
    s2.add_box("report", "Figure 1", node_class="claim")
    s2.add_arrow("script", "data")
    s2.add_arrow("data", "process")
    s2.add_arrow("process", "report")
    s2.auto_layout(layout="lr", gap_mm=6, box_size_mm=(32, 22))
    fig2, ax2 = fr.subplots()
    ax2.diagram(s2, id="pipeline")
    fr.save(fig2, OUT / "data_pipeline.png", validate=False)

    # --- 3. Software architecture with codeblock ---
    logger.info("Demo 3: Software architecture")
    s3 = fr.Diagram(
        title="SciTeX Verification Architecture",
        width_mm=170,
        height_mm=110,
    )
    # Top: code layer
    s3.add_box(
        "session",
        "@stx.session",
        subtitle="Decorator",
        shape="codeblock",
        emphasis="primary",
        x_mm=45,
        y_mm=82,
        width_mm=40,
        height_mm=22,
    )
    s3.add_box(
        "io",
        "stx.io",
        subtitle="save / load",
        shape="codeblock",
        emphasis="primary",
        x_mm=125,
        y_mm=82,
        width_mm=40,
        height_mm=22,
    )
    # Middle: data layer
    s3.add_box(
        "db",
        "Session DB",
        subtitle="Postgres",
        shape="cylinder",
        emphasis="muted",
        x_mm=45,
        y_mm=55,
        width_mm=40,
        height_mm=25,
    )
    s3.add_box(
        "hashes",
        "File Hashes",
        subtitle="SHA-256",
        shape="cylinder",
        emphasis="muted",
        x_mm=125,
        y_mm=55,
        width_mm=40,
        height_mm=25,
    )
    # Bottom: output layer
    s3.add_box(
        "dag",
        "DAG Report",
        subtitle="Mermaid / HTML",
        shape="document",
        emphasis="success",
        x_mm=85,
        y_mm=15,
        width_mm=45,
        height_mm=22,
    )
    # Arrows
    s3.add_arrow("session", "db")
    s3.add_arrow("io", "hashes")
    s3.add_arrow("db", "dag")
    s3.add_arrow("hashes", "dag")
    fig3, ax3 = fr.subplots()
    ax3.diagram(s3, id="architecture")
    fr.save(fig3, OUT / "software_arch.png", validate=False)

    logger.info(f"All outputs saved to: {OUT}/")
    return 0


if __name__ == "__main__":
    main()

# EOF
