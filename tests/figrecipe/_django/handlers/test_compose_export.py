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
    result = _compose_pil([preview], False)
    assert result.size == (24, 24)
    assert result.getpixel((0, 0)) == (255, 0, 0, 255)
    assert result.getpixel((11, 9)) == (255, 0, 0, 255)


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
    name = "fixture-Figure1-20261102T040506Z"
    request = RequestFactory().post(
        f"/api/compose/export/{fmt}",
        data=json.dumps({"figures": [preview], "filename": name}),
        content_type="application/json",
    )
    response = handle_compose_export(request, None, fmt)
    assert response.status_code == 200
    assert response.content.startswith(signature)
    assert response["Content-Type"] == mime
    assert response["Content-Disposition"] == f'attachment; filename="{name}.{fmt}"'
    if fmt == "png":
        from PIL import Image
        assert Image.open(io.BytesIO(response.content)).getpixel((0, 0)) == (255, 0, 0)
