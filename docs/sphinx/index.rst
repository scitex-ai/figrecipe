.. FigRecipe documentation master file

FigRecipe - Reproducible Scientific Figures
=============================================================

**FigRecipe** is a framework for creating reproducible, style-editable scientific figures via YAML recipes. It wraps matplotlib with automatic recording, enabling figures to be reproduced, modified, and shared. Part of `SciTeX <https://scitex.ai>`_.

.. figure:: /_static/figrecipe_concept.png
   :alt: FigRecipe: Reproducible Scientific Figures
   :width: 100%
   :align: center

   FigRecipe separates data, style, and specification for fully reproducible scientific figures.

Role in SciTeX Ecosystem
-------------------------

FigRecipe is the **first app built on the SciTeX platform** -- it proves the app pattern
that other apps follow. It works standalone (``figrecipe gui open``) AND embedded in
scitex-cloud. The orchestrator re-exports it as ``scitex.plt``.

.. code-block:: text

   scitex (orchestrator) -- re-exports figrecipe as scitex.plt
     |-- scitex-app        -- runtime SDK (FigRecipe inherits ScitexAppConfig)
     |-- scitex-ui         -- React/TS components (FigRecipe consumes these)
     +-- figrecipe (this package) -- reference app

- **scitex** (`docs <https://scitex-python.readthedocs.io/>`_): Orchestrator that re-exports ``scitex.plt``
- **scitex-app** (`docs <https://scitex-app.readthedocs.io/>`_): Runtime SDK providing ``ScitexAppConfig``
- **scitex-ui** (`docs <https://scitex-ui.readthedocs.io/>`_): Shared frontend components consumed by FigRecipe

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   terminology
   gallery
   style_reference
   cli_reference
   mcp_spec

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/figrecipe

Key Features
------------

- **Automatic Recording**: All matplotlib calls automatically recorded to YAML
- **Reproducibility**: Recreate any figure from its recipe file
- **Style Editing**: Change styles without regenerating data
- **Data Preservation**: Plot data saved to CSV files
- **CSV Column Input**: Reference CSV columns in declarative specs
- **Statistical Annotations**: Add significance brackets with p-values
- **Multi-Panel Composition**: Combine figures with fr.compose()
- **Diagrams**: Box-and-arrow diagrams with mm-based coordinates, 9 validation rules (R1--R9), auto-fix, and flex layout
- **MCP Integration**: AI agents can create figures via MCP server
- **47 Plot Types**: All standard matplotlib plot types supported

Quick Example
-------------

Python API:

.. code-block:: python

    import figrecipe as fr
    import numpy as np

    # Create figure (auto-recording enabled)
    fig, ax = fr.subplots()

    # Standard matplotlib API
    x = np.linspace(0, 10, 100)
    ax.plot(x, np.sin(x), label="sin(x)")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.legend()

    # Save creates image + recipe + data CSVs
    fr.save(fig, "my_plot.png")

CLI:

.. code-block:: bash

    # Reproduce a figure from recipe
    figrecipe reproduce my_plot.yaml -o reproduced.png

    # Launch GUI editor
    figrecipe gui open my_plot.yaml

    # Validate reproduction fidelity
    figrecipe validate my_plot.yaml

MCP Server:

.. code-block:: bash

    # Start MCP server for AI agent integration
    figrecipe mcp start

Four Freedoms for Research
--------------------------

0. The freedom to **run** your research anywhere -- your machine, your terms.
1. The freedom to **study** how every step works -- from raw data to final manuscript.
2. The freedom to **redistribute** your workflows, not just your papers.
3. The freedom to **modify** any module and share improvements with the community.

AGPL-3.0 -- because research infrastructure deserves the same freedoms as the software it runs on.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
