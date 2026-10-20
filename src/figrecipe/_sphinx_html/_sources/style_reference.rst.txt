Style Reference
===============

FigRecipe supports customizable styles for publication-ready figures. This page documents the style parameters and their defaults.

Style Anatomy
-------------

The following diagram shows all configurable style parameters on a figure:

.. figure:: /_static/scitex_style_anatomy.jpg
   :alt: SciTeX Style Anatomy
   :width: 100%
   :align: center

   SciTeX style anatomy — all configurable parameters annotated on six plot types.

Style Parameters
----------------

Figure Settings
^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Parameter
     - Default
     - Description
   * - ``dpi``
     - 300
     - Output resolution in dots per inch
   * - ``format``
     - pdf
     - Default output format (png, pdf, svg)
   * - ``facecolor``
     - white
     - Figure background color

Axes Settings
^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Parameter
     - Default
     - Description
   * - ``axes_size_mm``
     - [40, 28]
     - Default axes size in millimeters [width, height]
   * - ``axes_linewidth_mm``
     - 0.2
     - Axes border thickness in mm

Labels and Title
^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Parameter
     - Default
     - Description
   * - ``title_pt``
     - 8
     - Title font size in points
   * - ``title_pad``
     - 4
     - Title padding from axes in points
   * - ``axis_label_pt``
     - 7
     - Axis label font size in points
   * - ``axis_label_pad``
     - 2
     - Axis label padding in points

Ticks
^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Parameter
     - Default
     - Description
   * - ``tick_label_pt``
     - 7
     - Tick label font size in points
   * - ``tick_length_mm``
     - 0.8
     - Major tick length in mm
   * - ``tick_width_mm``
     - 0.2
     - Tick line width in mm
   * - ``tick_direction``
     - out
     - Tick direction (in, out, inout)
   * - ``n_ticks``
     - 3-4
     - Target number of major ticks per axis
   * - ``minor_tick_color``
     - 0.25
     - Minor tick label color (gray value)

Lines and Markers
^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Parameter
     - Default
     - Description
   * - ``trace_mm``
     - 0.12
     - Default line width in mm
   * - ``scatter_mm``
     - 0.8
     - Default marker size in mm
   * - ``marker_edge``
     - none
     - Marker edge style

Legend
^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Parameter
     - Default
     - Description
   * - ``legend_pt``
     - 6
     - Legend font size in points
   * - ``legend_frameon``
     - false
     - Whether to show legend frame

Spines
^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Parameter
     - Default
     - Description
   * - ``spine_width_mm``
     - 0.2
     - Spine line width in mm
   * - ``spine_visible``
     - [bottom, left]
     - Which spines are visible (top/right hidden by default)

Grid
^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Parameter
     - Default
     - Description
   * - ``grid``
     - false
     - Whether to show grid
   * - ``grid_linestyle``
     - --
     - Grid line style
   * - ``grid_linewidth``
     - 0.5
     - Grid line width
   * - ``grid_color``
     - 0.25
     - Grid color (gray value)

Loading Styles
--------------

Python API
^^^^^^^^^^

.. code-block:: python

   import figrecipe as fr

   # Load a preset style
   fr.load_style("SCITEX")

   # List available presets
   presets = fr.list_presets()
   print(presets)

   # Unload style (return to matplotlib defaults)
   fr.unload_style()

Available Presets
^^^^^^^^^^^^^^^^^

- ``default`` - Basic clean style
- ``SCITEX`` - Publication-ready scientific style (recommended)
- ``SCITEX_DARK`` - Dark mode variant

Custom Styles
^^^^^^^^^^^^^

You can create custom styles by providing a dictionary:

.. code-block:: python

   custom_style = {
       "figure": {
           "dpi": 300,
           "facecolor": "white",
       },
       "axes": {
           "linewidth_mm": 0.3,
       },
       "fonts": {
           "title_pt": 10,
           "axis_label_pt": 8,
       },
       "ticks": {
           "direction": "in",
           "length_mm": 1.0,
       },
   }

   fr.load_style(custom_style)
