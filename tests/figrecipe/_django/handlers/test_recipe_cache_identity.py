"""New/switch target cache entries without replacing another recipe's record."""
import json
import os
import time
import pytest
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "figrecipe._django.settings")

@pytest.fixture
def recipes(tmp_path):
    import django
    django.setup()
    import figrecipe as fr
    from figrecipe._django.services import _editor_cache
    before = set(_editor_cache)
    for stem, values in (("first", [2, 4]), ("second", [30, 40])):
        fig, ax = fr.subplots()
        ax.plot([1, 2], values)
        fr.save(fig, tmp_path / f"{stem}.yaml", validate=False, verbose=False)
    yield tmp_path
    for key in set(_editor_cache) - before:
        _editor_cache.pop(key, None)


def _original(root):
    from django.test import RequestFactory
    from figrecipe._django._project_access import editor_key
    from figrecipe._django.services import get_or_create_editor
    request = RequestFactory().get("/preview", {"working_dir": str(root)})
    path = root / "first.yaml"
    original = get_or_create_editor(editor_key(request, path), str(path))
    original.working_dir = root
    original.imported_table = {"names": ["keep"], "rows": [[7]]}
    return request, original


def test_new_figure_does_not_overwrite_original_cache_or_imported_data(recipes):
    from django.test import RequestFactory
    from figrecipe._django._project_access import editor_key
    from figrecipe._django.handlers.files import handle_api_new
    from figrecipe._django.services import _editor_cache
    request, original = _original(recipes)
    original_fig = original.fig
    post = RequestFactory().post(f"/api/new?working_dir={recipes}", data="{}", content_type="application/json")
    response = handle_api_new(post, original)
    assert response.status_code == 200, response.content
    created = recipes / json.loads(response.content)["file"]
    assert original.recipe_path == recipes / "first.yaml"
    assert original.fig is original_fig
    assert original.imported_table["rows"] == [[7]]
    assert _editor_cache[editor_key(request, created)][0] is not original
    assert _editor_cache[editor_key(request, original.recipe_path)][0] is original


def test_switch_does_not_replace_previous_recipe_cache(recipes):
    from django.test import RequestFactory
    from figrecipe._django._project_access import editor_key
    from figrecipe._django.handlers.files import handle_api_switch
    from figrecipe._django.services import _editor_cache
    request, original = _original(recipes)
    original_fig = original.fig
    post = RequestFactory().post(f"/api/switch?working_dir={recipes}", data=json.dumps({"path":"second.yaml"}), content_type="application/json")
    response = handle_api_switch(post, original)
    assert response.status_code == 200, response.content
    assert original.recipe_path == recipes / "first.yaml"
    assert original.fig is original_fig
    assert original.imported_table["rows"] == [[7]]
    target = _editor_cache[editor_key(request, recipes / "second.yaml")][0]
    assert target is not original
    assert target.recipe_path == recipes / "second.yaml"


def test_read_repairs_legacy_cache_key_pointing_to_another_recipe(recipes):
    from figrecipe._django._project_access import editor_key
    from figrecipe._django.services import _editor_cache, get_or_create_editor
    request, original = _original(recipes)
    target = get_or_create_editor(editor_key(request, recipes / "second.yaml"), str(recipes / "second.yaml"))
    key = editor_key(request, original.recipe_path)
    _editor_cache[key] = (target, time.time())
    restored = get_or_create_editor(key, str(recipes / "first.yaml"))
    assert restored is not target
    assert restored.recipe_path == recipes / "first.yaml"
