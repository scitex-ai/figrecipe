Terminology
===========

Consistent naming across FigRecipe code, docs, and UI.

Core Hierarchy
--------------

::

    Canvas (editor workspace)
     └─ Figure (matplotlib Figure, mm-sized)
         └─ Axes (single plot panel)
             ├─ Axis (x or y ruler with ticks)
             └─ Plot (visual data: lines, bars, scatter, etc.)

Figure
~~~~~~

A **matplotlib** ``Figure`` — the top-level container for all visual elements.
In FigRecipe, figure dimensions are defined in exact mm via the style system
(margins, axes sizes, spacing).

- Wrapped as ``RecordingFigure`` to track recipe operations
- ``fig._fig`` accesses the underlying matplotlib Figure
- One figure = one ``.yaml`` recipe = one output image

Axes
~~~~

A **single plot panel** (matplotlib ``Axes``). One figure can contain a grid
of axes (e.g., 2×3). Each axes has its own coordinate system, spines, ticks,
labels, and title.

- FigRecipe returns axes as a 2D list: ``axes[row][col]``
- Plural "axes" refers to multiple panels, **not** the x/y axis lines

Axis
~~~~

A **single x or y ruler line** (matplotlib ``XAxis`` / ``YAxis``).
Part of an axes. Contains tick marks, tick labels, an axis label
(e.g., "Time (s)"), and a scale (linear, log, etc.).

Not to be confused with "axes" (the panel container).

Plot
~~~~

The **visual data representation** drawn within an axes — lines, bars,
scatter points, histograms, contours, images, etc. In matplotlib these
are "artists" (``Line2D``, ``PathCollection``, ``BarContainer``, etc.).

Panel
~~~~~

Synonym for **axes** in FigRecipe context. Used in panel labels ("A", "B", "C"),
``panel_bboxes``, ``align_panels()``, and ``distribute_panels()``.

Canvas
~~~~~~

The **editor workspace** — an HTML/CSS container with a mm-grid background,
rulers, zoom/pan controls, and snap guides. Not a matplotlib object.
Figures are placed on the canvas at absolute pixel positions.

Style
~~~~~

A **named configuration** (e.g., ``SCITEX``) defining mm-based dimensions:
margins, axes sizes, spacing, fonts, line widths, colors.

Recipe
~~~~~~

A **YAML file** that fully describes how to reproduce a figure:
plot type, data source, style overrides, panel layout.

Editor-Specific Terms
---------------------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Term
     - Meaning
   * - **Hitmap**
     - Color-coded overlay mapping pixel regions to figure elements
   * - **Bbox**
     - Bounding box — ``{x, y, width, height}`` in image pixels
   * - **Placed figure**
     - A figure positioned on the canvas at ``(x, y)``
   * - **Snap guide**
     - Visual alignment line shown during drag
   * - **Composition**
     - Multi-figure arrangement on the canvas

Common Confusions
-----------------

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Wrong
     - Right
     - Why
   * - "the axes line"
     - "the axis"
     - Axes = panel, axis = ruler line
   * - "tight layout"
     - "mm-based layout"
     - FigRecipe uses explicit mm positions, not auto-layout
   * - "canvas background"
     - "figure background"
     - Canvas is the editor; figure is the matplotlib object
   * - ``bbox_inches="tight"``
     - (omit)
     - Breaks mm coordinates — never use in FigRecipe editor
