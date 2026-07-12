CLI Reference
=============

FigRecipe provides a comprehensive command-line interface for working with figures.

Usage
-----

.. code-block:: bash

   figrecipe [COMMAND] [OPTIONS]

Run ``figrecipe --help`` to see all available commands.

Figure Creation
---------------

plot
^^^^

Create a figure from a declarative YAML specification.

.. code-block:: bash

   figrecipe plot spec.yaml -o output.png

   # Options:
   #   -o, --output PATH    Output file path
   #   --dpi INTEGER        DPI for raster output (default: 300)
   #   --no-recipe          Don't save recipe file

reproduce
^^^^^^^^^

Reproduce a figure from its saved recipe.

.. code-block:: bash

   figrecipe reproduce recipe.yaml -o reproduced.png

   # Options:
   #   -o, --output PATH    Output file path
   #   --format TEXT        Output format: png, pdf, svg
   #   --dpi INTEGER        DPI for raster output

compose
^^^^^^^

Compose multiple figures into a single multi-panel figure.

.. code-block:: bash

   figrecipe compose panel_a.png panel_b.png -o figure.png

   # Options:
   #   -o, --output PATH    Output file path
   #   --layout TEXT        Layout: horizontal, vertical, grid
   #   --gap FLOAT          Gap between panels in mm
   #   --labels/--no-labels Add panel labels (A, B, C...)
   #   --label-style TEXT   uppercase, lowercase, numeric

gui
^^^

Launch the interactive GUI editor for figure styling. `gui` is a command
group with four verbs: `open` (auto-serves + opens the browser), `serve`
(foreground server), `status`, and `stop`.

.. code-block:: bash

   figrecipe gui open recipe.yaml

   # Options (gui open / gui serve):
   #   --port INTEGER       Server port (default: 31296)
   #   --host TEXT          Host address
   #   --no-browser         Don't open browser automatically (gui open only)
   #   --desktop            Launch as native desktop window (gui open only)

   figrecipe gui status                  # Is a server running? where?
   figrecipe gui stop -y                 # Stop the running server

Image Processing
----------------

convert
^^^^^^^

Convert between image formats.

.. code-block:: bash

   figrecipe convert input.png output.pdf

crop
^^^^

Crop whitespace from figure images.

.. code-block:: bash

   figrecipe crop figure.png -o cropped.png

   # Options:
   #   -o, --output PATH    Output file path
   #   --margin FLOAT       Margin to keep in mm (default: 1.0)
   #   --overwrite          Overwrite input file

diff
^^^^

Compare two images and show statistics.

.. code-block:: bash

   figrecipe diff original.png reproduced.png

   # Output: MSE, SSIM, and other comparison metrics

hitmap
^^^^^^

Generate a hitmap visualization showing differences between images.

.. code-block:: bash

   figrecipe hitmap original.png reproduced.png -o diff.png

   # Options:
   #   -o, --output PATH    Output file path

Data & Validation
-----------------

extract
^^^^^^^

Extract plotted data from a recipe file.

.. code-block:: bash

   figrecipe extract recipe.yaml

   # Output: JSON with {call_id: {x: [...], y: [...], ...}}

validate
^^^^^^^^

Validate that a recipe reproduces its original figure.

.. code-block:: bash

   figrecipe validate recipe.yaml

   # Options:
   #   --threshold FLOAT    MSE threshold (default: 100)

info
^^^^

Show information about a recipe file.

.. code-block:: bash

   figrecipe info recipe.yaml

   # Options:
   #   -v, --verbose        Show detailed call information

Diagram
-------

diagram
^^^^^^^

Create diagrams from YAML specifications.

.. code-block:: bash

   figrecipe diagram create spec.yaml -o diagram.png

   # Subcommands:
   #   create      Create diagram from spec
   #   compile     Compile to Mermaid/Graphviz format
   #   render      Render to image file
   #   presets     List available presets

Style & Appearance
------------------

style
^^^^^

Manage figure styles.

.. code-block:: bash

   figrecipe style list              # List available presets
   figrecipe style show PRESET       # Show preset details
   figrecipe style apply recipe.yaml # Apply style to recipe

fonts
^^^^^

Check font availability.

.. code-block:: bash

   figrecipe fonts check "Arial"     # Check if font is available
   figrecipe fonts list              # List available fonts

Integration
-----------

mcp
^^^

MCP (Model Context Protocol) server commands for AI agent integration.

.. code-block:: bash

   figrecipe mcp start               # Start MCP server
   figrecipe mcp list-tools          # List available MCP tools
   figrecipe mcp list-tools -v       # Verbose tool listing
   figrecipe mcp install --claude-code  # Install to Claude Code

list-python-apis
^^^^^^^^^^^^^^^^

List available Python API functions.

.. code-block:: bash

   figrecipe list-python-apis

   # Options:
   #   -v, --verbose        Show detailed function signatures

Utility
-------

completion
^^^^^^^^^^

Generate shell completion scripts.

.. code-block:: bash

   figrecipe completion bash > ~/.figrecipe-complete.bash
   figrecipe completion zsh > ~/.figrecipe-complete.zsh

version
^^^^^^^

Show version information.

.. code-block:: bash

   figrecipe version
