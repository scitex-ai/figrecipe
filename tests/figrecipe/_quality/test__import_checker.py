"""STX-I001 / STX-I009 — raw matplotlib.pyplot / seaborn imports (figrecipe-owned)."""

import ast

import pytest

spi = pytest.importorskip("scitex_dev.linter.spi")

from scitex_dev.linter.config import LinterConfig  # noqa: E402

from figrecipe._quality._import_checker import (  # noqa: E402
    I001_SPEC,
    I009_SPEC,
    bind_raw_import_checker,
)

_RULES = (spi.Rule(**I001_SPEC), spi.Rule(**I009_SPEC))


class _Checker(bind_raw_import_checker(*_RULES, spi)):
    # The rules' `requires` (umbrella scitex) may be absent here.
    available = {"scitex": True}


def _findings(source, config=None):
    checker = _Checker(source.splitlines(), config or LinterConfig())
    checker.visit(ast.parse(source))
    return [(i.rule.id, i.line, i.rule.severity) for i in checker.issues]


def test_metadata_matches_engine_compatibility_copy():
    # Arrange
    from scitex_dev.linter.rules import ALL_RULES

    # Act
    ours = {r.id: r for r in _RULES}
    # Assert — delete together with the engine copy once the handover ends.
    assert ours == {rid: ALL_RULES[rid] for rid in ours}


def test_pyplot_and_seaborn_imports_are_reported_like_the_engine():
    # Arrange
    source = (
        "import matplotlib.pyplot as plt\n"
        "from matplotlib import pyplot, colors\n"
        "from matplotlib.pyplot import subplots\n"
        "from matplotlib import colors\n"
        "import seaborn as sns\n"
        "import matplotlib\n"
    )
    # Act
    found = [(rid, line) for rid, line, _ in _findings(source)]
    # Assert
    assert found == [
        ("STX-I001", 1),
        ("STX-I001", 2),
        ("STX-I001", 3),
        ("STX-I009", 5),
    ]


def test_research_error_pin_still_applies():
    # Arrange
    config = LinterConfig(per_rule_severity={"STX-I001": "error"})
    # Act
    found = _findings("import matplotlib.pyplot as plt\n", config)
    # Assert
    assert found == [("STX-I001", 1, "error")]
