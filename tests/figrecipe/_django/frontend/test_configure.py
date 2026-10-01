"""Normal npm preparation uses the installed public SDK package contract."""

import json

import pytest

from figrecipe._django.frontend.configure import configure


def _fixtures(tmp_path, *, name="@scitex/sdk", version="0.3.0", bridge=True):
    frontend = tmp_path / "frontend"
    owner = tmp_path / "sdk-owner"
    frontend.mkdir()
    owner.mkdir()
    package = {"dependencies": {"@scitex/sdk": "file:old"}, "scitexSdk": {"version": "0.3.0"}}
    (frontend / "package.json").write_text(json.dumps(package))
    exports = {"./ui/react/app/bridge": "./ui/bridge.ts"} if bridge else {}
    (owner / "package.json").write_text(json.dumps({"name": name, "version": version, "exports": exports}))
    return frontend, owner


def test_configure_uses_the_owning_installed_package_without_symlinks(tmp_path):
    frontend, owner = _fixtures(tmp_path)
    configure(frontend, owner)
    package = json.loads((frontend / "package.json").read_text())
    assert package["dependencies"]["@scitex/sdk"] == "file:" + str(owner.resolve())
    assert not any(p.is_symlink() for p in frontend.iterdir())


@pytest.mark.parametrize("fields", [{"name": "@scitex/ui"}, {"version": "0.2.1"}, {"bridge": False}])
def test_configure_refuses_wrong_or_incomplete_owner_without_changing_manifest(tmp_path, fields):
    frontend, owner = _fixtures(tmp_path, **fields)
    manifest = frontend / "package.json"
    before = manifest.read_bytes()
    with pytest.raises(ValueError):
        configure(frontend, owner)
    assert manifest.read_bytes() == before
