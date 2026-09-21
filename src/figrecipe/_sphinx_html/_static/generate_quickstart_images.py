#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate quickstart images for RTD documentation."""

import sys
from pathlib import Path

import scitex_logging as slogging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

import numpy as np

import figrecipe as fr

console = slogging.getConsole(f"{__name__}.console")

OUT = Path(__file__).parent


def create_trig_plot():
    """Create the trigonometric plot example."""
    fig, ax = fr.subplots()

    x = np.linspace(0, 2 * np.pi, 100)
    ax.plot(x, np.sin(x), label="sin(x)", color="blue", id="sine")
    ax.plot(x, np.cos(x), label="cos(x)", color="red", id="cosine")

    ax.set_xlabel("X (radians)")
    ax.set_ylabel("Y")
    ax.set_title("Trigonometric Functions")
    ax.legend()

    fr.save(fig, OUT / "quickstart_trig.png", verbose=False)
    console.info(f"Created: {OUT / 'quickstart_trig.png'}")


def create_bundle_example():
    """Create bundle format example."""
    fig, ax = fr.subplots()

    x = np.array([1, 2, 3, 4, 5])
    y = np.array([1, 4, 9, 16, 25])
    ax.scatter(x, y, s=100, c="steelblue", id="data")
    ax.plot(x, y, "--", alpha=0.5, color="gray", id="trend")

    ax.set_xlabel("X")
    ax.set_ylabel("Y = X²")
    ax.set_title("Quadratic Data")

    # Save as bundle
    fr.save(fig, OUT / "quickstart_bundle.zip", verbose=False)
    console.info(f"Created: {OUT / 'quickstart_bundle.zip'}")

    # Also save PNG for display
    fr.save(fig, OUT / "quickstart_bundle.png", verbose=False)
    console.info(f"Created: {OUT / 'quickstart_bundle.png'}")


def create_composition_example():
    """Create composition example."""
    # Panel A
    fig1, ax1 = fr.subplots()
    ax1.bar(["A", "B", "C"], [3, 7, 5], color=["#3498db", "#e74c3c", "#2ecc71"])
    ax1.set_title("Bar Chart")
    fr.save(fig1, OUT / "quickstart_panel_a.png", verbose=False)

    # Panel B
    fig2, ax2 = fr.subplots()
    ax2.plot([1, 2, 3, 4], [1, 4, 2, 3], "o-", color="#9b59b6")
    ax2.set_title("Line Plot")
    fr.save(fig2, OUT / "quickstart_panel_b.png", verbose=False)

    # Compose
    fr.compose(
        sources=[OUT / "quickstart_panel_a.yaml", OUT / "quickstart_panel_b.yaml"],
        output_path=OUT / "quickstart_composed.png",
        layout="horizontal",
        panel_labels=True,
    )
    console.info(f"Created: {OUT / 'quickstart_composed.png'}")


if __name__ == "__main__":
    create_trig_plot()
    create_bundle_example()
    # Note: Composition example skipped - requires compose API fix
    # create_composition_example()
    console.info("\nDone! Quickstart images generated.")
