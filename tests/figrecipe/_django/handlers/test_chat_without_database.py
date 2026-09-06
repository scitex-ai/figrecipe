#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The chat endpoints must not 500 when the editor has no database.

The standalone editor runs with no DATABASES entry -- Django's dummy backend --
because figrecipe stores nothing of its own. But INSTALLED_APPS registers
ScitexAppChatConfig (scitex_app._chat), whose views issue real ORM queries, and
the handler registry routes api/chat/* to them. Measured on develop d90cea4
(2026-09-06, reported by scitex-app):

    GET /api/chat/sessions/ -> 500
    {"error": "settings.DATABASES is improperly configured. Please supply the
      ENGINE value. Check settings documentation for more details."}

Every call, and with a Django settings diagnostic in the response body.

The handlers now check for a usable database first. The control that matters is
the last test: a gate that switched the feature off everywhere would satisfy
all the others perfectly, and would silently break the hosted editor, where
these same handlers run against a real database.
"""

import pytest

pytest.importorskip("django")


@pytest.fixture
def client():
    """A test client whose host is allowed -- SCOPED, not assigned.

    Assigning settings.ALLOWED_HOSTS directly leaks into every later test in
    the session: it broke the four test_settings.py cases that assert a bad
    host IS refused, because by the time they ran every host was allowed.
    override_settings restores on exit.
    """
    from django.test import Client, override_settings

    with override_settings(ALLOWED_HOSTS=["*"]):
        yield Client()


def test_import__django_handlers_module():
    # Arrange
    module_path = "figrecipe._django.handlers"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


# ── standalone: the endpoints answer, they do not fail ───────────────────────


def test_session_list_does_not_return_an_unhandled_500(client):
    """500 was the bug. 501 is the deliberate answer -- and is also 5xx.

    This test first read `status_code < 500`, which contradicted the 501 test
    two functions down: no response could satisfy both. Naming the actual
    defect (an unhandled 500 from the ORM) instead of a code range fixes it.
    """
    # Arrange
    path = "/api/chat/sessions/"
    # Act
    response = client.get(path)
    # Assert
    assert response.status_code != 500


def test_session_list_reports_not_implemented(client):
    """501: the endpoint exists in the API, this deployment does not serve it."""
    # Arrange
    path = "/api/chat/sessions/"
    # Act
    response = client.get(path)
    # Assert
    assert response.status_code == 501


@pytest.mark.parametrize("leak", ["DATABASES", "ENGINE", "ImproperlyConfigured"])
def test_response_body_carries_no_django_internals(client, leak):
    """A 500 leaked the settings diagnostic to the browser. Never again."""
    # Arrange
    path = "/api/chat/sessions/"
    # Act
    body = client.get(path).content.decode("utf-8", "replace")
    # Assert
    assert leak not in body


def test_chat_stream_is_NOT_gated(client):
    """The control against an over-broad gate: streaming needs no database.

    The first version of this fix guarded all four chat handlers, which turned
    a working endpoint into a 501. Measured on develop with no DATABASES
    configured: POST here with a prompt returns 200 and streams, failing only
    on a missing API key. scitex-app predicted it from the import chain
    (_chat/_django.py -> ._sse, ._stream carry zero ORM references) and the
    measurement agreed. Only the SESSION handlers touch the ORM.

    A gate is supposed to disable what cannot work, not what it sits next to.
    """
    # Arrange
    import json

    path = "/api/chat/stream"
    # Act
    response = client.post(
        path, data=json.dumps({}), content_type="application/json"
    )
    # Assert
    assert response.status_code != 501


def test_the_message_names_the_feature_not_the_mechanism(client):
    # Arrange
    path = "/api/chat/sessions/"
    # Act
    body = client.get(path).content.decode("utf-8", "replace")
    # Assert
    assert "chat history is not available" in body


# ── the control: the gate must NOT fire where a database exists ──────────────


def test_the_gate_stands_down_when_a_database_is_configured():
    """Without this, a gate that disables the feature everywhere still passes."""
    # Arrange
    from django.test import override_settings

    from figrecipe._django.handlers import _database_is_configured

    real_db = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "never_connected_to",
        }
    }
    # Act
    with override_settings(DATABASES=real_db):
        gated = not _database_is_configured()
    # Assert
    assert gated is False


def test_the_gate_fires_on_the_dummy_backend():
    # Arrange
    from django.test import override_settings

    from figrecipe._django.handlers import _database_is_configured

    dummy = {"default": {"ENGINE": "django.db.backends.dummy"}}
    # Act
    with override_settings(DATABASES=dummy):
        configured = _database_is_configured()
    # Assert
    assert configured is False


# EOF
