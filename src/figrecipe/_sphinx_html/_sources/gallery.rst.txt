Plot Gallery
============

FigRecipe supports all standard matplotlib plot types. Below are examples of each plot type with the declarative specification format used by the MCP server.

Basic Plots
-----------

Line Plot
^^^^^^^^^

.. figure:: /_static/gallery_line.png
   :alt: Line Plot
   :width: 80%
   :align: center

   Line plot with multiple series.

.. code-block:: python

   import figrecipe as fr
   import numpy as np

   fig, ax = fr.subplots()
   x = np.linspace(0, 10, 100)
   ax.plot(x, np.sin(x), label="sin(x)", id="sine")
   ax.plot(x, np.cos(x), label="cos(x)", id="cosine")
   ax.set_xlabel("X")
   ax.set_ylabel("Y")
   ax.legend()
   fr.save(fig, "line_plot.png")

MCP Specification:

.. code-block:: yaml

   figure:
     figsize: [6, 4]
   plots:
     - type: line
       x: [0, 1, 2, 3, 4, 5]
       y: [0, 1, 4, 9, 16, 25]
       label: "quadratic"
   xlabel: "X"
   ylabel: "Y"
   title: "Line Plot"

Scatter Plot
^^^^^^^^^^^^

.. figure:: /_static/gallery_scatter.png
   :alt: Scatter Plot
   :width: 80%
   :align: center

   Scatter plot with color mapping.

.. code-block:: python

   import figrecipe as fr
   import numpy as np

   fig, ax = fr.subplots()
   np.random.seed(42)
   x = np.random.randn(50)
   y = x + np.random.randn(50) * 0.5
   ax.scatter(x, y, c=x, cmap="viridis", s=50, id="data")
   ax.set_xlabel("X")
   ax.set_ylabel("Y")
   fr.save(fig, "scatter_plot.png")

MCP Specification:

.. code-block:: yaml

   plots:
     - type: scatter
       x: [1, 2, 3, 4, 5]
       y: [2, 4, 1, 5, 3]
       c: [0.1, 0.3, 0.5, 0.7, 0.9]
       cmap: viridis
       s: 50
   xlabel: "X"
   ylabel: "Y"

Bar Plot
^^^^^^^^

.. figure:: /_static/gallery_bar.png
   :alt: Bar Plot
   :width: 80%
   :align: center

   Vertical bar plot.

.. code-block:: python

   import figrecipe as fr

   fig, ax = fr.subplots()
   categories = ["A", "B", "C", "D", "E"]
   values = [23, 45, 12, 67, 34]
   ax.bar(categories, values, color="steelblue", id="bars")
   ax.set_xlabel("Category")
   ax.set_ylabel("Value")
   fr.save(fig, "bar_plot.png")

MCP Specification:

.. code-block:: yaml

   plots:
     - type: bar
       x: ["A", "B", "C", "D"]
       height: [10, 20, 15, 25]
       color: steelblue
   xlabel: "Category"
   ylabel: "Value"

Statistical Plots
-----------------

Histogram
^^^^^^^^^

.. figure:: /_static/gallery_hist.png
   :alt: Histogram
   :width: 80%
   :align: center

   Histogram showing data distribution.

.. code-block:: python

   import figrecipe as fr
   import numpy as np

   fig, ax = fr.subplots()
   np.random.seed(42)
   data = np.random.randn(1000)
   ax.hist(data, bins=30, alpha=0.7, color="steelblue", edgecolor="white", id="hist")
   ax.set_xlabel("Value")
   ax.set_ylabel("Frequency")
   fr.save(fig, "histogram.png")

Box Plot
^^^^^^^^

.. figure:: /_static/gallery_boxplot.png
   :alt: Box Plot
   :width: 80%
   :align: center

   Box plot comparing distributions.

.. code-block:: python

   import figrecipe as fr
   import numpy as np

   fig, ax = fr.subplots()
   np.random.seed(42)
   data = [np.random.randn(100) + i for i in range(4)]
   ax.boxplot(data, labels=["A", "B", "C", "D"], id="boxplot")
   ax.set_xlabel("Group")
   ax.set_ylabel("Value")
   fr.save(fig, "boxplot.png")

Violin Plot
^^^^^^^^^^^

.. figure:: /_static/gallery_violin.png
   :alt: Violin Plot
   :width: 80%
   :align: center

   Violin plot showing distribution shape.

.. code-block:: python

   import figrecipe as fr
   import numpy as np

   fig, ax = fr.subplots()
   np.random.seed(42)
   data = [np.random.randn(100) + i for i in range(4)]
   ax.violinplot(data, positions=[1, 2, 3, 4], id="violin")
   ax.set_xticks([1, 2, 3, 4])
   ax.set_xticklabels(["A", "B", "C", "D"])
   fr.save(fig, "violinplot.png")

2D Plots
--------

Heatmap / Imshow
^^^^^^^^^^^^^^^^

.. figure:: /_static/gallery_heatmap.png
   :alt: Heatmap
   :width: 80%
   :align: center

   Heatmap visualization of 2D data.

.. code-block:: python

   import figrecipe as fr
   import numpy as np

   fig, ax = fr.subplots()
   np.random.seed(42)
   data = np.random.randn(10, 10)
   im = ax.imshow(data, cmap="coolwarm", id="heatmap")
   fig.fig.colorbar(im, ax=ax._ax)
   fr.save(fig, "heatmap.png")

Contour Plot
^^^^^^^^^^^^

.. figure:: /_static/gallery_contour.png
   :alt: Contour Plot
   :width: 80%
   :align: center

   Filled contour plot.

.. code-block:: python

   import figrecipe as fr
   import numpy as np

   fig, ax = fr.subplots()
   x = np.linspace(-3, 3, 100)
   y = np.linspace(-3, 3, 100)
   X, Y = np.meshgrid(x, y)
   Z = np.sin(X) * np.cos(Y)
   cs = ax.contourf(X, Y, Z, levels=20, cmap="viridis", id="contour")
   fig.fig.colorbar(cs, ax=ax._ax)
   fr.save(fig, "contour.png")

Supported Plot Types (47)
-------------------------

FigRecipe supports all standard matplotlib axes methods:

**Line & Curve:**
``plot``, ``step``, ``fill``, ``fill_between``, ``fill_betweenx``, ``errorbar``, ``stackplot``, ``stairs``

**Scatter & Points:**
``scatter``

**Bar & Categorical:**
``bar``, ``barh``

**Distribution:**
``hist``, ``hist2d``, ``boxplot``, ``violinplot``, ``ecdf``

**2D Image & Matrix:**
``imshow``, ``matshow``, ``pcolor``, ``pcolormesh``, ``hexbin``, ``spy``

**Contour & Surface:**
``contour``, ``contourf``, ``tricontour``, ``tricontourf``, ``tripcolor``, ``triplot``

**Spectral & Signal:**
``specgram``, ``psd``, ``csd``, ``cohere``, ``angle_spectrum``, ``magnitude_spectrum``, ``phase_spectrum``, ``acorr``, ``xcorr``

**Vector & Flow:**
``quiver``, ``barbs``, ``streamplot``

**Special:**
``pie``, ``stem``, ``eventplot``, ``loglog``, ``semilogx``, ``semilogy``, ``graph``

CSV Column Workflow
-------------------

FigRecipe can read data directly from CSV files:

.. code-block:: yaml

   plots:
     - type: scatter
       data_file: "experiment_data.csv"
       x_column: "time_seconds"
       y_column: "signal_amplitude"
       label: "Experiment 1"

   xlabel: "Time (s)"
   ylabel: "Amplitude"

Statistical Annotations
-----------------------

Add significance brackets with p-values:

.. code-block:: yaml

   stat_annotations:
     - group1_idx: 0
       group2_idx: 1
       p_value: 0.003
       test: "t-test"
       stars: true
