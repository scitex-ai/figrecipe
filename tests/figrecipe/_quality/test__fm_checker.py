"""figrecipe's FM001-FM009 checker reproduces the scitex-dev engine copy exactly.

The checker moved here from scitex-dev (``linter/_fm_checker.py``); while
the engine still ships its copy as a compatibility shim, every finding of
ours must equal the engine's on the same source and config.
"""

import ast

import pytest

spi = pytest.importorskip("scitex_dev.linter.spi")

from scitex_dev.linter.config import LinterConfig  # noqa: E402

from figrecipe._quality._fm_checker import bind_fm_checker  # noqa: E402
from figrecipe._quality._linter_rules import make_fm_rules  # noqa: E402

SOURCE = (
    "fig, ax = plt.subplots(figsize=(3, 2), constrained_layout=True)\n"
    "fig.tight_layout()\n"
    "fig.savefig('a.png', bbox_inches='tight')\n"
    "fig.set_size_inches(3, 2)\n"
    "ax.set_position([0, 0, 1, 1])\n"
    "plt.subplots_adjust(left=0.1)\n"
    "plt.rcParams['font.size'] = 7\n"
    "stx.plt.subplots(figsize=(1, 1))\n"
    "fr.save(fig, 'x.png')\n"
    "fig.tight_layout()  # stx-allow: STX-FM002\n"
)


def _issues(checker_cls, config):
    checker = checker_cls(SOURCE.splitlines(), config)
    checker.visit(ast.parse(SOURCE))
    return sorted(
        (i.rule.id, i.line, i.col, i.rule.severity, i.rule.message, i.rule.suggestion)
        for i in checker.issues
    )


@pytest.mark.parametrize(
    "config",
    [
        LinterConfig(enable=["FM"]),
        LinterConfig(enable=["FM"], per_rule_severity={"STX-FM006": "error"}),
        LinterConfig(enable=["FM"], category_severity_override={"figure": "error"}),
        LinterConfig(enable=["FM"], disable=["STX-FM001"]),
    ],
    ids=["default", "per-rule", "category-floor", "disable"],
)
def test_fm_checker_matches_engine_copy(config):
    # Arrange
    engine = pytest.importorskip("scitex_dev.linter._fm_checker").FMChecker
    ours = bind_fm_checker(make_fm_rules(spi.Rule), spi)
    # Act
    ours_found = _issues(ours, config)
    # Assert
    assert ours_found == _issues(engine, config)


def test_fm_checker_flags_each_inch_based_pattern():
    # Arrange
    ours = bind_fm_checker(make_fm_rules(spi.Rule), spi)
    # Act
    ids = {f[0] for f in _issues(ours, LinterConfig(enable=["FM"]))}
    # Assert
    assert ids == {f"STX-FM00{n}" for n in range(1, 10)}
