# Never silently discard what the author set

A styler that drops a property the author explicitly set — without saying so —
produces a figure that is **wrong in the picture and right in every assertion**.
That is not a theoretical risk. It shipped a comodulogram to human review with
its frequency axis blank.

## The incident

`apply_imshow_axes_visibility` suppressed heatmap chrome with:

```python
ax.set_xticks([])
ax.set_xticklabels([])   # <- the bug
```

`set_xticklabels([])` pins a **`NullFormatter`** on the axis. A formatter lives
on the *axis*, not on the handle you reach it through, so **every tick set
afterwards renders blank** — through the figrecipe wrapper, through the raw
`ax._ax`, through an explicit `set_xticklabels(...)`. There was **no code
workaround**; only upgrading fixed it.

What made it dangerous was not the blanking. It was the silence:

```python
ax.set_xticks([0, 1])
ax.get_xticks()          # [0, 1]   <- the author's own values. Looks correct.
# ...but the drawn labels are ['', '']
```

Every object-level assertion passed. The figure reached print with no numbers on
an axis whose numbers *were the content*. Which frequencies couple **is** the
finding in a comodulogram.

## The rules

**1. Suppress reversibly.** Clear tick *locations*; never install a formatter.

```python
# GOOD - reversible; a later set_xticks() renders
ax.set_xticks([])

# BAD - pins a NullFormatter; nothing can undo it
ax.set_xticks([])
ax.set_xticklabels([])
```

To hide labels while *keeping* tick marks, toggle visibility — it is a flag, not
a formatter, so it can be turned back on:

```python
ax.tick_params(labelbottom=False)   # reversible
ax.tick_params(labelbottom=True)    # genuinely restores
```

**2. If you must discard an explicit choice, say so.** A `FixedLocator` is
matplotlib's fingerprint of an author's `set_xticks(...)`. Overriding one is a
decision the author did not make — warn, and name the axis and the escape hatch.

**3. Assert on what RENDERS, not on the object graph.** This is the rule that
actually protects people. An axis-object assertion is *structurally blind* to
this class of corruption, because the object state is exactly what was asked for.

```python
# BLIND - passed throughout the incident
assert list(ax.get_xticks()) == [0, 1]

# SEES IT - reads the drawn text
ax.figure.canvas.draw()
assert [t.get_text() for t in ax.get_xticklabels()] == ["0", "1"]
```

## A silent failure also hides whatever is behind it

This is the part most people miss. The blank labels were not just *a* bug — they
were a **mask over two more**, both found the moment the labels rendered:

- A **layout** bug: with numbers finally drawn, the colorbar was seen colliding
  with the xlabel. The silence had concealed a real defect in the figure code.
- A **wrong computation**: the family-center tick positions had been computed
  assuming contiguous feature families, but the features were *interleaved*, so
  every label collapsed onto the axis centre. The labels were never merely
  missing — they were **nonsense**, and nobody could tell while they were blank.

So a silent failure is not one bug, it is a bug plus everything it conceals. The
drawn-label assertion catches the *renderer*; only looking at the pixels caught
the *computation behind it*. Both layers needed the pixels.

## Where this generalises

Any figrecipe path that can silently diverge from an explicit instruction owes
the author a warning: stylers that override, recorders that cannot faithfully
replay something drawn, solvers that quietly fall back. A figure that looks
plausible and is wrong is worse than one that fails — the failure gets fixed;
the plausible one gets published, and takes its hidden defects with it.

See also: `05_styles.md`, `27_six-stat-annotation-doctrine.md` (readable
heatmaps), `25_figure-prep-checklist.md`.
