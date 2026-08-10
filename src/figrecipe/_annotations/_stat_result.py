#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""``StatResult`` — the display-side port for a completed statistical test.

figrecipe DISPLAYS statistics; it never computes them. This dataclass is the
boundary between those two concerns (ports & adapters): a producer — scitex-stats,
scipy, R, a CSV of pre-computed results — fills in the fields, and figrecipe turns
them into a doctrine-compliant, italic-symbol annotation string. figrecipe does not
import scitex-stats, and scitex-stats does not know figrecipe exists; the only
coupling is the field names below.

The doctrine (see ``_skills/figrecipe/27_six-stat-annotation-doctrine.md``) requires
all six of n / CI / method / p / effect size / test statistic on every statistical
annotation. Before this module the only way to satisfy it was to hand-type the
mathtext:

    ax.add_stat_annotation(x1=0, x2=1, text=r"$\\it{N}$=12, $\\it{n}$=340, ...")

which is both tedious and unverifiable — a typo'd exponent or a forgotten field
looks fine until review. ``StatResult`` builds that string instead, so the six
fields are structurally present or you get a warning naming exactly which ones
are not.
"""

from __future__ import annotations

__all__ = ["StatResult", "MISSING_STAT_FIELD_WARNING"]

import warnings
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence, Tuple, Union

MISSING_STAT_FIELD_WARNING = (
    "Statistical annotation is missing required field(s): {missing}. The six-stat "
    "doctrine requires n, CI, method, p-value, effect size, and test statistic "
    "(see figrecipe skill 27_six-stat-annotation-doctrine). Supply them, or move "
    "them into the caption and pass require_complete=False to silence this."
)

# Statistical symbols that are NOT simply an italicised latin letter.
_SYMBOL_MATHTEXT = {
    "chi2": r"\chi^2",
    "chisq": r"\chi^2",
    "eta2": r"\eta^2",
    "eta_squared": r"\eta^2",
    "partial_eta2": r"\eta_p^2",
    "omega2": r"\omega^2",
    "rho": r"\rho",
    "tau": r"\tau",
}

_DofT = Union[float, int, Sequence[float], None]


def _mathtext(symbol: str) -> str:
    """Render a statistical symbol as italic mathtext (doctrine rule: italics)."""
    special = _SYMBOL_MATHTEXT.get(symbol.lower())
    body = special if special is not None else rf"\it{{{symbol}}}"
    return f"${body}$"


def _format_one_dof(dof: float) -> str:
    """Integer dof render bare; a fractional dof (Welch) keeps one decimal.

    Welch's correction produces a non-integer dof (e.g. 694.053). Printing its
    full float precision is noise -- no reader needs the third decimal of a
    degrees-of-freedom -- so collapse it to a single decimal, and to a bare
    integer when it is one.
    """
    if float(dof).is_integer():
        return f"{int(dof)}"
    return f"{dof:.1f}"


def _format_dof(dof: _DofT) -> str:
    """Render degrees of freedom as ``(338)`` or ``(2, 57)``; empty when absent."""
    if dof is None:
        return ""
    if isinstance(dof, (int, float)):
        return f"({_format_one_dof(dof)})"
    return "(" + ", ".join(_format_one_dof(d) for d in dof) + ")"


def _format_p(p_value: float, precision: int = 3) -> str:
    """Render a p-value, collapsing to ``< 0.001`` below display precision."""
    floor = 10.0**-precision
    symbol = _mathtext("p")
    if p_value < floor:
        return f"{symbol} < {floor:g}"
    return f"{symbol} = {p_value:.{precision}f}"


@dataclass(frozen=True)
class StatResult:
    """A completed statistical test, ready to be rendered onto a figure.

    Only ``p_value`` is structurally required — a result with no p-value is not a
    test result at all. The other five doctrine fields are optional at the type
    level but their absence is reported by :meth:`missing_fields` and warned about
    at render time, because "incomplete but loud" is more useful than "complete or
    TypeError": a producer that genuinely cannot supply a CI (e.g. a permutation
    test) should still be able to render, with the gap visible.

    Parameters
    ----------
    p_value : float
        The p-value of the test.
    method : str, optional
        Human-readable test name, e.g. ``"Welch's t-test"``. Rendered upright.
    statistic : float, optional
        The test statistic's value.
    statistic_name : str
        Symbol for the test statistic (``"t"``, ``"F"``, ``"U"``, ``"chi2"``, ...).
    dof : float or sequence of float, optional
        Degrees of freedom; a scalar renders ``t(338)``, a pair renders ``F(2, 57)``.
    effect_size : float, optional
        The effect size's value.
    effect_name : str
        Symbol for the effect size (``"d"``, ``"r"``, ``"eta2"``, ...).
    ci : tuple of (float, float), optional
        Confidence interval around the estimate.
    ci_level : int
        Confidence level as a percentage. Default 95.
    n : int, optional
        Number of observations (windows / trials / samples) — lowercase *n*.
    n_subjects : int, optional
        Number of subjects — capital *N*. Keep distinct from ``n``: collapsing the
        two hides the unit of statistical independence from the reader.
    n_unit, n_subjects_unit : str
        Optional units, e.g. ``"windows"`` / ``"patients"``.

    Examples
    --------
    >>> result = StatResult(
    ...     p_value=0.0004, method="Pearson correlation",
    ...     statistic=5.1, statistic_name="t", dof=338,
    ...     effect_size=0.42, effect_name="r", ci=(0.21, 0.60),
    ...     n=340, n_subjects=12,
    ... )
    >>> result.stars
    '***'
    >>> "Pearson correlation" in result.annotation()
    True
    """

    p_value: float
    method: Optional[str] = None
    statistic: Optional[float] = None
    statistic_name: str = "t"
    dof: _DofT = None
    effect_size: Optional[float] = None
    effect_name: str = "d"
    ci: Optional[Tuple[float, float]] = None
    ci_level: int = 95
    n: Optional[int] = None
    n_subjects: Optional[int] = None
    n_unit: str = ""
    n_subjects_unit: str = ""
    extras: Mapping[str, Any] = field(default_factory=dict)

    @property
    def stars(self) -> str:
        """Significance stars for this p-value."""
        # Single source of truth: the same threshold table the bracket helper uses.
        from .._wrappers._stat_annotation import p_to_stars

        return p_to_stars(self.p_value)

    def missing_fields(self) -> list:
        """Names of the doctrine's six fields that this result cannot render."""
        missing = []
        if self.n is None and self.n_subjects is None:
            missing.append("n")
        if self.ci is None:
            missing.append("CI")
        if not self.method:
            missing.append("method")
        if self.effect_size is None:
            missing.append("effect size")
        if self.statistic is None:
            missing.append("test statistic")
        return missing

    def _sample_size_part(self) -> str:
        parts = []
        for symbol, value, unit in (
            ("N", self.n_subjects, self.n_subjects_unit),
            ("n", self.n, self.n_unit),
        ):
            if value is None:
                continue
            suffix = f" {unit}" if unit else ""
            parts.append(f"{_mathtext(symbol)} = {value:,}{suffix}")
        return ", ".join(parts)

    def annotation(
        self,
        sep: str = ", ",
        precision: int = 3,
        stars: bool = False,
        require_complete: bool = True,
    ) -> str:
        """Render the six-stat annotation string, with italic statistical symbols.

        Parameters
        ----------
        sep : str
            Separator between fields. Pass ``",\\n"`` to wrap onto two lines when a
            panel is too narrow for one.
        precision : int
            Decimal places for the p-value before it collapses to ``< 0.001``.
        stars : bool
            Prepend the significance stars on their own line. The stars are a
            convenience for the reader, never a substitute for the p-value — the
            exact number is always rendered alongside them.
        require_complete : bool
            Warn (never raise) when any of the six doctrine fields is absent. Set
            False when the missing fields genuinely live in the caption instead.

        Returns
        -------
        str
            e.g. ``"$N$ = 12, $n$ = 340, Pearson correlation, $t$(338) = 5.10,
            $p$ < 0.001, $r$ = 0.42, 95% CI [0.21, 0.60]"``
        """
        if require_complete:
            missing = self.missing_fields()
            if missing:
                warnings.warn(
                    MISSING_STAT_FIELD_WARNING.format(missing=", ".join(missing)),
                    UserWarning,
                    stacklevel=2,
                )

        parts = []
        sample_sizes = self._sample_size_part()
        if sample_sizes:
            parts.append(sample_sizes)
        if self.method:
            parts.append(self.method)
        if self.statistic is not None:
            symbol = _mathtext(self.statistic_name)
            parts.append(f"{symbol}{_format_dof(self.dof)} = {self.statistic:.2f}")
        parts.append(_format_p(self.p_value, precision=precision))
        if self.effect_size is not None:
            parts.append(f"{_mathtext(self.effect_name)} = {self.effect_size:.2f}")
        if self.ci is not None:
            low, high = self.ci
            parts.append(f"{self.ci_level}% CI [{low:.2f}, {high:.2f}]")

        body = sep.join(parts)
        return f"{self.stars}\n{body}" if stars else body

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "StatResult":
        """Build a ``StatResult`` from a producer's result dict — the adapter seam.

        This is how scitex-stats (or scipy, or a stored results table) hands a test
        result to figrecipe without either side importing the other. Common key
        spellings are accepted. Keys that match nothing are preserved verbatim in
        ``extras`` rather than dropped, so a producer whose schema drifts leaves a
        trace instead of vanishing into a silently-incomplete annotation — and the
        render-time completeness warning still names whatever field went missing.

        Raises
        ------
        KeyError
            If no p-value key is present — that is not a test result.
        """
        aliases = {
            "p_value": ("p_value", "pval", "p", "pvalue"),
            "method": ("method", "test", "test_name", "testname"),
            "statistic": ("statistic", "stat", "test_statistic"),
            "statistic_name": ("statistic_name", "stat_name", "statistic_symbol"),
            "dof": ("dof", "df", "degrees_of_freedom"),
            "effect_size": ("effect_size", "effect", "effsize"),
            "effect_name": ("effect_name", "effect_type", "effect_symbol"),
            "ci": ("ci", "conf_int", "confidence_interval"),
            "ci_level": ("ci_level", "confidence_level"),
            "n": ("n", "nobs", "n_samples", "sample_size"),
            "n_subjects": ("n_subjects", "N", "n_subj"),
            "n_unit": ("n_unit",),
            "n_subjects_unit": ("n_subjects_unit",),
        }
        consumed = set()
        kwargs = {}
        for target, keys in aliases.items():
            for key in keys:
                if key in mapping:
                    kwargs[target] = mapping[key]
                    consumed.add(key)
                    break

        if "p_value" not in kwargs:
            raise KeyError(
                "StatResult.from_mapping requires a p-value; none of "
                f"{aliases['p_value']} found in keys {sorted(mapping)}."
            )

        # A CI split across two scalar keys is the other common producer shape.
        if "ci" not in kwargs and {"ci_lower", "ci_upper"} <= set(mapping):
            kwargs["ci"] = (mapping["ci_lower"], mapping["ci_upper"])
            consumed |= {"ci_lower", "ci_upper"}

        unmapped = set(mapping) - consumed
        if unmapped:
            kwargs["extras"] = {key: mapping[key] for key in sorted(unmapped)}

        if kwargs.get("ci") is not None:
            kwargs["ci"] = tuple(kwargs["ci"])
        return cls(**kwargs)


# EOF
