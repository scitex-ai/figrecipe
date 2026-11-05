#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the standalone GUI terminal WebSocket server.

Regression coverage for the HTTP 426 handshake bug: with strict
``websockets`` (>= 14) the opening handshake was rejected when a client or
proxy sent a ``Connection`` header that did not contain an ``Upgrade`` token
(e.g. ``Connection: keep-alive``). The ``_process_request`` hook repairs such
non-strict-but-unambiguous WebSocket upgrade requests so the handshake
succeeds, while leaving genuine non-WebSocket requests rejected.
"""

import socket
import time

import pytest

from figrecipe._django import terminal


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _wait_for_port(port, *, deadline=15.0):
    """Block until something accepts on port (slow-runner readiness probe).

    The terminal server starts in a daemon thread; a fixed sleep flakes when
    the runner is loaded (card figrecipe-terminal-test-readiness-harden-20261029).
    Fail loud with the elapsed wait instead of a bare ConnectionRefused.
    """
    start = time.monotonic()
    while True:
        try:
            socket.create_connection(("127.0.0.1", port), timeout=2).close()
            return
        except OSError:
            if time.monotonic() - start >= deadline:
                raise AssertionError(
                    f"terminal server never listened on 127.0.0.1:{port} "
                    f"within {deadline}s"
                )
            time.sleep(0.2)


def _send_handshake(port, connection_header, *, ws_upgrade=True, retries=1):
    """Send a raw handshake and return the HTTP status line."""
    s = None
    for attempt in range(retries + 1):
        try:
            s = socket.create_connection(("127.0.0.1", port), timeout=5)
            break
        except ConnectionRefusedError:
            if attempt >= retries:
                raise
    assert s is not None  # range() is never empty; narrows the type
    try:
        lines = ["GET / HTTP/1.1", f"Host: 127.0.0.1:{port}"]
        if ws_upgrade:
            lines += [
                "Upgrade: websocket",
                "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==",
                "Sec-WebSocket-Version: 13",
            ]
        lines.append(f"Connection: {connection_header}")
        req = "\r\n".join(lines) + "\r\n\r\n"
        s.sendall(req.encode())
        time.sleep(0.4)
        data = s.recv(4096).decode("utf-8", "replace")
    finally:
        s.close()
    return data.splitlines()[0] if data else ""


class _FakeHeaders(dict):
    def get_all(self, name):
        v = self.get(name)
        return [v] if v is not None else []


def _fake_request(headers):
    return type("Req", (), {"headers": _FakeHeaders(headers)})()


@pytest.fixture(scope="module")
def terminal_port():
    pytest.importorskip("websockets")
    port = _free_port()
    thread = terminal.start_terminal_server(port=port)
    assert thread is not None
    _wait_for_port(port)
    yield port


@pytest.mark.parametrize(
    "connection_header",
    [
        "Upgrade",
        "keep-alive, Upgrade",
        "keep-alive",  # the original failing case (no Upgrade token)
        "Keep-Alive",
        "close",
    ],
)
def test_websocket_upgrade_handshake_succeeds(terminal_port, connection_header):
    # Arrange
    port = terminal_port
    # Act
    status = _send_handshake(port, connection_header)
    # Assert
    assert "101" in status


def test_plain_http_request_is_not_upgraded(terminal_port):
    # Arrange
    port = terminal_port
    # Act: no Upgrade/Sec-WebSocket-Key headers present
    status = _send_handshake(port, "keep-alive", ws_upgrade=False)
    # Assert
    assert "101" not in status


def test_repair_adds_upgrade_token_when_missing():
    # Arrange
    req = _fake_request(
        {
            "Upgrade": "websocket",
            "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
            "Connection": "keep-alive",
        }
    )
    # Act
    terminal._repair_connection_header(req)
    # Assert
    assert "upgrade" in req.headers["Connection"].lower()


def test_repair_preserves_existing_connection_tokens():
    # Arrange
    req = _fake_request(
        {
            "Upgrade": "websocket",
            "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
            "Connection": "keep-alive",
        }
    )
    # Act
    terminal._repair_connection_header(req)
    # Assert
    assert "keep-alive" in req.headers["Connection"].lower()


def test_repair_leaves_non_websocket_request_untouched():
    # Arrange
    req = _fake_request({"Connection": "keep-alive"})
    # Act
    terminal._repair_connection_header(req)
    # Assert
    assert req.headers["Connection"] == "keep-alive"
