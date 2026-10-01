FigRecipe API Reference
=======================

The full public surface of ``figrecipe`` is documented inline below
via ``automodule``. The ``__all__`` declaration in
``figrecipe/__init__.py`` is the single source of truth for what
appears here; do NOT add explicit ``autofunction`` / ``autoclass``
directives below — Sphinx already discovers them through
``automodule :members:`` and a second declaration triggers
``duplicate object description`` warnings (treated as errors on PR
builds).

.. automodule:: figrecipe
   :members:
   :undoc-members:
   :show-inheritance:

Recording Wrappers (internal)
-----------------------------

These classes back the public ``subplots()`` return value. They live
under ``figrecipe._wrappers`` rather than the top-level namespace, so
they're documented here separately.

.. autoclass:: figrecipe._wrappers.RecordingFigure
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: figrecipe._wrappers.RecordingAxes
   :members:
   :undoc-members:
   :show-inheritance:
