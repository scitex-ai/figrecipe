MCP Specification Format
========================

FigRecipe provides an MCP (Model Context Protocol) server that allows AI agents to create figures declaratively. This page documents the specification format.

Starting the MCP Server
-----------------------

.. code-block:: bash

   # Start the MCP server
   figrecipe mcp start

   # Or using FastMCP directly
   fastmcp run figrecipe._mcp.server:mcp

Basic Specification Structure
-----------------------------

The declarative specification is a dictionary/YAML with these main sections:

.. code-block:: yaml

   # Figure configuration
   figure:
     figsize: [width, height]  # in inches
     dpi: 100
     facecolor: "white"

   # Plot data (list of plot specifications)
   plots:
     - type: "line"           # Plot type
       x: [1, 2, 3, 4, 5]     # X data
       y: [1, 4, 9, 16, 25]   # Y data
       label: "quadratic"     # Legend label
       color: "blue"          # Line color
       linewidth: 2           # Line width

   # Axis labels and title
   xlabel: "X Axis"
   ylabel: "Y Axis"
   title: "My Plot"

   # Axis limits (optional)
   xlim: [0, 10]
   ylim: [0, 30]

   # Legend configuration
   legend:
     loc: "upper left"
     frameon: true

Plot Types
----------

Line Plot
^^^^^^^^^

.. code-block:: yaml

   plots:
     - type: line
       x: [0, 1, 2, 3, 4]
       y: [0, 1, 4, 9, 16]
       color: "blue"
       linewidth: 2
       linestyle: "-"     # "-", "--", "-.", ":"
       marker: "o"        # "o", "s", "^", "v", etc.
       markersize: 5
       label: "data"

Scatter Plot
^^^^^^^^^^^^

.. code-block:: yaml

   plots:
     - type: scatter
       x: [1, 2, 3, 4, 5]
       y: [2, 4, 1, 5, 3]
       c: [0.1, 0.3, 0.5, 0.7, 0.9]  # Color values
       cmap: "viridis"               # Colormap
       s: 50                         # Marker size
       alpha: 0.8                    # Transparency
       edgecolors: "black"

Bar Plot
^^^^^^^^

.. code-block:: yaml

   plots:
     - type: bar
       x: ["A", "B", "C", "D"]
       height: [10, 20, 15, 25]
       color: "steelblue"
       edgecolor: "black"
       width: 0.8
       yerr: [1, 2, 1.5, 2.5]  # Error bars
       capsize: 5

   # Horizontal bar plot
   plots:
     - type: barh
       y: ["A", "B", "C", "D"]
       width: [10, 20, 15, 25]

Histogram
^^^^^^^^^

.. code-block:: yaml

   plots:
     - type: hist
       x: [1.2, 1.5, 2.1, 2.3, ...]  # Data values
       bins: 30                       # Number of bins
       color: "steelblue"
       edgecolor: "white"
       alpha: 0.7
       density: false                 # Normalize to density

Box Plot
^^^^^^^^

.. code-block:: yaml

   plots:
     - type: boxplot
       data: [[1,2,3], [4,5,6], [7,8,9]]  # List of datasets
       labels: ["A", "B", "C"]
       notch: false
       vert: true

Violin Plot
^^^^^^^^^^^

.. code-block:: yaml

   plots:
     - type: violinplot
       data: [[1,2,3], [4,5,6], [7,8,9]]
       positions: [1, 2, 3]
       showmeans: true
       showmedians: true

Image/Heatmap
^^^^^^^^^^^^^

.. code-block:: yaml

   plots:
     - type: imshow
       data: [[1,2,3], [4,5,6], [7,8,9]]  # 2D array
       cmap: "viridis"
       aspect: "auto"
       vmin: 0
       vmax: 10
       interpolation: "nearest"

Contour Plot
^^^^^^^^^^^^

.. code-block:: yaml

   plots:
     - type: contourf
       X: [[...], [...]]  # 2D meshgrid X
       Y: [[...], [...]]  # 2D meshgrid Y
       Z: [[...], [...]]  # 2D data values
       levels: 20
       cmap: "coolwarm"

Fill Between
^^^^^^^^^^^^

.. code-block:: yaml

   plots:
     - type: fill_between
       x: [0, 1, 2, 3, 4]
       y1: [0, 1, 2, 1, 0]
       y2: 0                 # Can be scalar or array
       alpha: 0.3
       color: "blue"

Error Bar
^^^^^^^^^

.. code-block:: yaml

   plots:
     - type: errorbar
       x: [1, 2, 3, 4, 5]
       y: [10, 20, 15, 25, 18]
       yerr: [1, 2, 1.5, 2, 1.8]
       xerr: [0.5, 0.5, 0.5, 0.5, 0.5]
       fmt: "o"
       capsize: 5

CSV Data Input
--------------

Instead of inline data, you can reference CSV columns:

.. code-block:: yaml

   plots:
     - type: scatter
       data_file: "experiment_data.csv"
       x_column: "time_seconds"
       y_column: "signal_amplitude"
       c_column: "temperature"    # Optional color column
       cmap: "coolwarm"
       label: "Experiment 1"

Statistical Annotations
-----------------------

Add significance brackets with p-values:

.. code-block:: yaml

   stat_annotations:
     - group1_idx: 0          # Index of first group
       group2_idx: 1          # Index of second group
       p_value: 0.003         # P-value to display
       test: "t-test"         # Test name (optional)
       stars: true            # Show as stars (true) or number (false)

     - group1_idx: 0
       group2_idx: 2
       p_value: 0.05
       text: "ns"             # Custom text instead of p-value

Multi-Panel Figures
-------------------

Using Axes Array
^^^^^^^^^^^^^^^^

.. code-block:: yaml

   # Define subplots structure
   subplots:
     nrows: 2
     ncols: 2
     figsize: [10, 8]

   # Per-axis specifications
   axes:
     - position: [0, 0]       # Row, column
       plots:
         - type: line
           x: [0, 1, 2, 3]
           y: [0, 1, 4, 9]
       xlabel: "X"
       ylabel: "Y"
       title: "Panel A"

     - position: [0, 1]
       plots:
         - type: scatter
           x: [1, 2, 3, 4]
           y: [4, 2, 5, 1]
       title: "Panel B"

MCP Tool Reference
------------------

plt_plot
^^^^^^^^

Create a figure from specification:

.. code-block:: python

   result = plt_plot(
       spec={...},           # Specification dict
       output_path="fig.png",
       dpi=300,
       save_recipe=True      # Also save as .yaml
   )

plt_reproduce
^^^^^^^^^^^^^

Reproduce from saved recipe:

.. code-block:: python

   result = plt_reproduce(
       recipe_path="fig.yaml",
       output_path="reproduced.png",
       format="png",
       dpi=300
   )

plt_compose
^^^^^^^^^^^

Combine multiple figures:

.. code-block:: python

   result = plt_compose(
       sources=["panel_a.png", "panel_b.png"],
       output_path="combined.png",
       layout="horizontal",   # or "vertical", "grid"
       gap_mm=5.0,
       panel_labels=True,
       label_style="uppercase"
   )

plt_info
^^^^^^^^

Get recipe information:

.. code-block:: python

   info = plt_info(recipe_path="fig.yaml", verbose=True)

plt_validate
^^^^^^^^^^^^

Validate reproduction fidelity:

.. code-block:: python

   result = plt_validate(
       recipe_path="fig.yaml",
       mse_threshold=100.0
   )

plt_crop
^^^^^^^^

Crop whitespace from figure:

.. code-block:: python

   result = plt_crop(
       input_path="fig.png",
       output_path="fig_cropped.png",
       margin_mm=1.0
   )

plt_extract_data
^^^^^^^^^^^^^^^^

Extract plotted data from recipe:

.. code-block:: python

   data = plt_extract_data(recipe_path="fig.yaml")
   # Returns: {call_id: {'x': [...], 'y': [...], ...}}

plt_list_styles
^^^^^^^^^^^^^^^

List available style presets:

.. code-block:: python

   styles = plt_list_styles()
   # Returns: {"presets": ["default", ...], "count": N}

plt_get_plot_types
^^^^^^^^^^^^^^^^^^

Get supported plot types:

.. code-block:: python

   types = plt_get_plot_types()
   # Returns: {"plot_types": [...], "categories": {...}}

Diagram Tools
-------------

diagram_create
^^^^^^^^^^^^^^

Create a diagram from YAML specification:

.. code-block:: python

   result = diagram_create(
       spec_dict={...},       # Or spec_path="diagram.yaml"
   )
   # Returns: {"mermaid": "...", "graphviz": "..."}

diagram_render
^^^^^^^^^^^^^^

Render diagram to image:

.. code-block:: python

   result = diagram_render(
       spec_path="diagram.yaml",
       output_path="diagram.png",
       format="png",           # png, svg, pdf
       backend="auto",         # mermaid-cli, graphviz, mermaid.ink
       scale=2.0
   )

diagram_compile_mermaid
^^^^^^^^^^^^^^^^^^^^^^^

Compile to Mermaid format:

.. code-block:: python

   result = diagram_compile_mermaid(
       spec_path="diagram.yaml",
       output_path="diagram.mmd"
   )

diagram_compile_graphviz
^^^^^^^^^^^^^^^^^^^^^^^^

Compile to Graphviz DOT format:

.. code-block:: python

   result = diagram_compile_graphviz(
       spec_path="diagram.yaml",
       output_path="diagram.dot"
   )

diagram_list_presets
^^^^^^^^^^^^^^^^^^^^

List available diagram presets:

.. code-block:: python

   presets = diagram_list_presets()
   # Returns: {"workflow": ..., "decision": ..., "pipeline": ..., "scientific": ...}

diagram_get_backends
^^^^^^^^^^^^^^^^^^^^

Check rendering backend availability:

.. code-block:: python

   backends = diagram_get_backends()
   # Returns availability and installation instructions

All MCP Tools Summary
---------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool
     - Description
   * - **plt_plot**
     - Create figure from declarative spec
   * - **plt_reproduce**
     - Reproduce figure from recipe
   * - **plt_compose**
     - Combine multiple figures
   * - **plt_info**
     - Get recipe information
   * - **plt_validate**
     - Validate reproduction fidelity
   * - **plt_crop**
     - Crop whitespace from image
   * - **plt_extract_data**
     - Extract plotted data arrays
   * - **plt_list_styles**
     - List style presets
   * - **plt_get_plot_types**
     - Get supported plot types
   * - **diagram_create**
     - Create diagram from spec
   * - **diagram_render**
     - Render diagram to image
   * - **diagram_compile_mermaid**
     - Compile to Mermaid format
   * - **diagram_compile_graphviz**
     - Compile to Graphviz format
   * - **diagram_list_presets**
     - List diagram presets
   * - **diagram_get_preset**
     - Get preset configuration
   * - **diagram_get_backends**
     - Check backend availability
   * - **diagram_split**
     - Split large diagram into parts
   * - **diagram_get_paper_modes**
     - Get paper layout modes
