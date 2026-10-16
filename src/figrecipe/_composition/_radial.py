#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic layout helpers ported from the p5js skill.

Card figrecipe-bioinformatics-figure-beauty-20261006, source-adoption phase:
``radial_positions`` (references/core-api.md radial layout) places ``n``
points evenly on a circle; ``poisson_disk`` (references/visual-effects.md
Bridson sampling) scatters points with a minimum-distance guarantee. Both
are pure NumPy, seeded, and engine-free — proven in PoC3.
"""

import numpy as np

__all__ = ["radial_positions", "poisson_disk"]


def radial_positions(
    n: int,
    radius: float = 1.0,
    start_angle: float = -np.pi / 2,
) -> np.ndarray:
    """Place ``n`` points evenly on a circle of ``radius``.

    ``start_angle`` puts the first point at the top (12 o'clock), matching
    the hub-spoke convention used in PoC3.
    """
    angles = start_angle + 2 * np.pi * np.arange(n) / n
    return np.column_stack([radius * np.cos(angles), radius * np.sin(angles)])


def poisson_disk(
    width: float,
    height: float,
    min_dist: float,
    seed: int = 7,
    candidates: int = 30,
) -> np.ndarray:
    """Bridson Poisson-disk sampling over a ``width`` x ``height`` rect.

    Returns points with pairwise distance >= ``min_dist`` (up to the
    rejection limit ``candidates`` per active point). Deterministic for a
    given ``seed``.
    """
    rng = np.random.default_rng(seed)
    cell = min_dist / np.sqrt(2)
    cols, rows = int(np.ceil(width / cell)), int(np.ceil(height / cell))
    grid = np.full((rows, cols), -1)
    pts: list = []
    active: list = []

    def _insert(p: np.ndarray) -> int:
        pts.append(p)
        active.append(len(pts) - 1)
        grid[int(p[1] / cell), int(p[0] / cell)] = len(pts) - 1
        return len(pts) - 1

    _insert(rng.uniform([0, 0], [width, height]))
    while active:
        i = active[rng.integers(len(active))]
        px, py = pts[i]
        found = False
        for _ in range(candidates):
            a = rng.uniform(0, 2 * np.pi)
            m = min_dist + rng.uniform(0, min_dist)
            qx, qy = px + np.cos(a) * m, py + np.sin(a) * m
            if not (0 <= qx < width and 0 <= qy < height):
                continue
            c, r = int(qx / cell), int(qy / cell)
            ok = True
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    nc, nr = c + dx, r + dy
                    if 0 <= nc < cols and 0 <= nr < rows and grid[nr, nc] != -1:
                        q = pts[grid[nr, nc]]
                        if float(np.hypot(q[0] - qx, q[1] - qy)) < min_dist:
                            ok = False
                            break
                if not ok:
                    break
            if ok:
                _insert(np.array([qx, qy]))
                found = True
                break
        if not found:
            active.remove(i)
    return np.array(pts)

