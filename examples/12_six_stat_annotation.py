#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
12_six_stat_annotation.py

Statistical annotations that satisfy the six-stat doctrine without hand-typing
mathtext.

The doctrine (skill 27) requires every statistical annotation on a figure to carry
all six of n / CI / method / p-value / effect size / test statistic, with italic
statistical symbols. Until ``StatResult`` existed, the only way to comply was to
type the mathtext by hand::

    ax.add_stat_annotation(x1=0, x2=1, text=r"$\\it{N}$=12, $\\it{n}$=340, ...")

which is tedious, easy to typo, and — worst — impossible to check: a forgotten
field looks exactly like a complete one. ``StatResult`` is the display-side port
for a computed test result. A producer (scitex-stats, scipy, a stored results
table) fills in the fields; figrecipe renders them. Neither imports the other.

Every number in this figure is COMPUTED from the generated data below and passed
through ``StatResult`` — nothing is hand-typed.

Also demonstrates, from the same release line:
- ``ax.stx_annotate_n(...)`` — sample-size labels that dodge existing ink.
- ``ax.comma_format(...)`` — thousands-separator tick labels.
- The heatmap colorbar requirement (doctrine rule 2): colorbar + label + units.
"""

from pathlib import Path

import numpy as np
import scitex as stx
from scipy import stats

import figrecipe as fr


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    """Standardised mean difference, pooled SD."""
    n_a, n_b = len(a), len(b)
    pooled_var = ((n_a - 1) * a.var(ddof=1) + (n_b - 1) * b.var(ddof=1)) / (
        n_a + n_b - 2
    )
    return (b.mean() - a.mean()) / np.sqrt(pooled_var)


def cohens_d_ci(d: float, n_a: int, n_b: int, level: float = 0.95) -> tuple:
    """Confidence interval on Cohen's d itself.

    The CI must bracket the effect size it is reported next to. A CI on the raw
    mean *difference* printed beside a standardised *d* reads as a contradiction
    (the interval does not contain the number it appears to qualify), so compute
    the interval on d.
    """
    se = np.sqrt((n_a + n_b) / (n_a * n_b) + d**2 / (2 * (n_a + n_b)))
    crit = stats.norm.ppf(1 - (1 - level) / 2)
    return (d - crit * se, d + crit * se)


@stx.session
def main(
    CONFIG=stx.session.INJECTED,
    logger=stx.session.INJECTED,
):
    """Render the six-stat annotation demo figure."""
    OUT = Path(CONFIG.SDIR_OUT)
    rng = np.random.default_rng(42)

    fig, axes = fr.subplots(1, 3, figsize=(180 / 25.4, 55 / 25.4))

    # === Panel A: two-group comparison, six-stat annotation ==================
    # The data. n_subjects (N) and per-subject windows (n) are kept distinct —
    # collapsing them hides the unit of statistical independence.
    n_subjects, windows_per_subject = 12, 30
    control = rng.normal(2.1, 0.8, n_subjects * windows_per_subject)
    treated = rng.normal(3.0, 0.9, n_subjects * windows_per_subject)

    # The statistics: computed, never typed. Treated first, so a positive t and a
    # positive d describe the same direction of effect.
    welch = stats.ttest_ind(treated, control, equal_var=False)
    effect = cohens_d(control, treated)
    result = fr.StatResult(
        p_value=float(welch.pvalue),
        method="Welch's t-test",
        statistic=float(welch.statistic),
        statistic_name="t",
        dof=float(welch.df),
        effect_size=effect,
        effect_name="d",
        ci=cohens_d_ci(effect, len(control), len(treated)),
        n=len(control) + len(treated),
        n_subjects=n_subjects,
        n_unit="windows",
        n_subjects_unit="patients",
    )
    logger.info(f"Panel A missing fields: {result.missing_fields()}")  # -> []

    ax = axes[0]
    means = [control.mean(), treated.mean()]
    errors = [control.std(ddof=1), treated.std(ddof=1)]
    ax.bar([0, 1], means, yerr=errors, capsize=2.3, id="bars_a")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Control", "Treated"])
    ax.set_ylabel("Firing rate [Hz]")
    ax.set_ylim(0, 7.4)

    # Per-group sample sizes, printed inside the bars. avoid_overlap is OFF here on
    # purpose: it dodges existing ink, and the bar *is* the ink -- leaving it on
    # would push a white label off the bar and onto the white background.
    for position, group in zip((0, 1), (control, treated)):
        ax.stx_annotate_n(
            position, 0.5, len(group), color="white", avoid_overlap=False, ha="center"
        )

    # One call renders the bracket, the stars, AND all six fields in italic. The
    # stars never replace the p-value -- the exact number is right underneath them.
    ax.add_stat_annotation(0, 1, stat=result, y=4.6, sep=",\n", stars=True, id="stat_a")

    # === Panel B: correlation over many samples, comma ticks + n label =======
    n_windows = 24_000
    x = rng.normal(12_000, 4_000, n_windows)
    y = 0.42 * (x - x.mean()) / x.std() + rng.normal(0, 1, n_windows)

    pearson = stats.pearsonr(x, y)
    correlation = fr.StatResult(
        p_value=float(pearson.pvalue),
        method="Pearson correlation",
        statistic=float(
            pearson.statistic
            * np.sqrt((n_windows - 2))
            / np.sqrt(1 - pearson.statistic**2)
        ),
        statistic_name="t",
        dof=n_windows - 2,
        effect_size=float(pearson.statistic),
        effect_name="r",
        ci=tuple(pearson.confidence_interval()),
        n=n_windows,
        n_unit="windows",
        n_subjects=n_subjects,
        n_subjects_unit="patients",
    )

    ax = axes[1]
    ax.scatter(x, y, s=0.5, alpha=0.15, id="scatter_b")
    ax.set_xlabel("Stimulus intensity [a.u.]")
    ax.set_ylabel("Normalised response [z]")
    # Thousands separators, so "24000" reads as "24,000".
    ax.comma_format(x=True)
    # The full six-stat line, rendered from the computed correlation. (No separate
    # n label here -- the annotation already carries N and n; repeating them would
    # be redundant ink.)
    ax.text(
        0.02,
        0.02,
        correlation.annotation(sep=",\n"),
        transform=ax.transAxes,
        fontsize=5,
        va="bottom",
    )

    # === Panel C: heatmap — colorbar with label AND units (doctrine rule 2) ==
    ax = axes[2]
    time = np.linspace(0, 1, 60)
    freq = np.linspace(4, 80, 40)
    power = np.exp(-((freq[:, None] - 40) ** 2) / 300) * np.exp(
        -((time[None, :] - 0.5) ** 2) / 0.05
    )
    image = ax.imshow(
        power,
        aspect="auto",
        origin="lower",
        extent=[time[0], time[-1], freq[0], freq[-1]],
        cmap="viridis",
        id="heatmap_c",
    )
    # The SCITEX style suppresses axis chrome on imshow (right for a picture, where
    # ticks are noise). A heatmap's axes carry physical meaning, so tick them back.
    ax.set_xticks([0.0, 0.5, 1.0])
    ax.set_yticks([20, 40, 60, 80])
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Frequency [Hz]")
    # Doctrine rule 2: a heatmap needs a colorbar, with a label AND units.
    fig.colorbar(image, ax=ax._ax, label="Power [dB]")

    fig.add_panel_labels(["A", "B", "C"])
    fr.save(fig, OUT / "six_stat_annotation.png", validate=False)
    logger.info(f"Output: {OUT / 'six_stat_annotation.png'}")
    return 0


if __name__ == "__main__":
    main()
