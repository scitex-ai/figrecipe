Installation
============

Basic Installation
------------------

Install FigRecipe from PyPI:

.. code-block:: bash

    pip install figrecipe

Full Installation
-----------------

Install with all optional dependencies:

.. code-block:: bash

    pip install figrecipe[all]

This includes:

- ``editor``: GUI editor (Django + React)
- ``imaging``: Image processing (Pillow, scipy)
- ``mcp``: MCP server for AI integration (fastmcp)

Individual Extras
-----------------

Install specific extras:

.. code-block:: bash

    # GUI editor only
    pip install figrecipe[editor]

    # MCP server only
    pip install figrecipe[mcp]

    # Image processing only
    pip install figrecipe[imaging]

Development Installation
------------------------

For development:

.. code-block:: bash

    git clone https://github.com/scitex-ai/figrecipe.git
    cd figrecipe
    pip install -e ".[all,dev]"

Requirements
------------

- Python 3.10+
- matplotlib >= 3.5
- numpy
- PyYAML
