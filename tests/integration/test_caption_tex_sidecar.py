"""End-to-end: caption-only .tex sidecar emit + composed panel-caption carry-forward.

No mocks — real figures saved to ``tmp_path`` and the emitted artifacts read back.
"""

import matplotlib

matplotlib.use("Agg")

import figrecipe as fr


def _panel(tmp_path, name, caption):
    fig, ax = fr.subplots()
    ax.plot([1, 2, 3], [1, 2, 3], id="line")
    fr.add_figure_caption(fig, caption)
    path = str(tmp_path / name)
    fr.save(fig, path)
    return path


def test_single_figure_emits_caption_only_tex_sidecar(tmp_path):
    # Arrange
    fr.set_manuscript_mode(False)
    # Act
    _panel(tmp_path, "fig.yaml", "Latency comparison (n=3).")
    tex = (tmp_path / "fig.tex").read_text()
    # Assert
    assert tex == "\\caption{Latency comparison (n=3).}\n\\label{fig:fig}\n"


def test_manuscript_mode_sidecar_omits_label(tmp_path):
    # Arrange
    fr.set_manuscript_mode(False)
    # Act: in manuscript mode the .tex is symlinked under another filename and
    # scitex-writer auto-labels by that stem -> our \label must be omitted.
    try:
        with fr.manuscript_mode():
            _panel(tmp_path, "ms.yaml", "Manuscript caption.")
        tex = (tmp_path / "ms.tex").read_text()
    finally:
        fr.set_manuscript_mode(False)
    # Assert
    assert tex == "\\caption{Manuscript caption.}\n"


def test_no_caption_emits_no_tex_sidecar(tmp_path):
    # Arrange
    fr.set_manuscript_mode(False)
    fig, ax = fr.subplots()
    ax.plot([1, 2], [1, 2], id="line")
    # Act
    fr.save(fig, str(tmp_path / "plain.yaml"))
    # Assert
    assert not (tmp_path / "plain.tex").exists()


def test_compose_carries_source_panel_captions_into_sidecar(tmp_path):
    # Arrange: two panels, each with its own caption, no panel_captions passed.
    fr.set_manuscript_mode(False)
    a = _panel(tmp_path, "a.yaml", "Throughput per condition.")
    b = _panel(tmp_path, "b.yaml", "Error rate per condition.")
    # Act
    cfig, _ = fr.compose(layout=(1, 2), sources={(0, 0): a, (0, 1): b})
    fr.save(cfig, str(tmp_path / "composed.yaml"))
    # Assert: source panel captions auto-pulled + folded as (A)/(B) into the .tex.
    assert (tmp_path / "composed.tex").read_text() == (
        "\\caption{(A) Throughput per condition. (B) Error rate per condition.}\n"
        "\\label{fig:composed}\n"
    )


def test_explicit_panel_captions_override_source_carry_forward(tmp_path):
    # Arrange
    fr.set_manuscript_mode(False)
    a = _panel(tmp_path, "a2.yaml", "Source A caption.")
    b = _panel(tmp_path, "b2.yaml", "Source B caption.")
    # Act: caller passes panel_captions explicitly -> those win.
    cfig, _ = fr.compose(
        layout=(1, 2),
        sources={(0, 0): a, (0, 1): b},
        panel_captions=["Override A", "Override B"],
    )
    # Assert
    assert cfig.record.figure_panel_captions == ["Override A", "Override B"]
