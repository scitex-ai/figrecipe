"""Real export bytes from disposable previews; never writes project files."""
import base64
import io
import json
import os

import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")


@pytest.fixture(scope="module", autouse=True)
def django_ready():
    import django
    django.setup()


@pytest.fixture
def preview():
    from PIL import Image
    data = io.BytesIO()
    Image.new("RGB", (12, 10), "red").save(data, "PNG")
    return {"path": "fixture.yaml", "x": -20, "y": -20,
            "width": 12, "height": 10,
            "image": base64.b64encode(data.getvalue()).decode()}


def test_negative_canvas_placement_exports_visible_pixels(preview):
    from PIL import Image
    from figrecipe._django.handlers.compose import _compose_pil
    # Arrange
    figures = [preview]
    # Act
    result = _compose_pil(figures, False)
    # Assert
    assert (result.size, result.getpixel((0, 0)), result.getpixel((11, 9))) == (
        (24, 24), (255, 0, 0, 255), (255, 0, 0, 255)
    )


@pytest.mark.parametrize("fmt,signature,mime", [
    ("png", b"\x89PNG", "image/png"),
    ("pdf", b"%PDF", "application/pdf"),
    ("svg", b"<svg", "image/svg+xml"),
])
def test_export_returns_real_download_with_descriptive_filename(preview, fmt, signature, mime):
    import django
    django.setup()
    from django.test import RequestFactory
    from figrecipe._django.handlers.compose import handle_compose_export
    # Arrange
    name = "fixture-Figure1-20261102T040506Z"
    request = RequestFactory().post(
        f"/api/compose/export/{fmt}",
        data=json.dumps({"figures": [preview], "filename": name}),
        content_type="application/json",
    )
    # Act
    response = handle_compose_export(request, None, fmt)
    # Assert
    assert (response.status_code, response.content.startswith(signature),
            response["Content-Type"], response["Content-Disposition"]) == (
        200, True, mime, f'attachment; filename="{name}.{fmt}"'
    )


def test_png_download_preserves_visible_pixels(preview):
    from PIL import Image
    from django.test import RequestFactory
    from figrecipe._django.handlers.compose import handle_compose_export
    # Arrange
    request = RequestFactory().post(
        "/api/compose/export/png", data=json.dumps({"figures": [preview]}),
        content_type="application/json",
    )
    # Act
    response = handle_compose_export(request, None, "png")
    # Assert
    assert Image.open(io.BytesIO(response.content)).getpixel((0, 0)) == (255, 0, 0)
