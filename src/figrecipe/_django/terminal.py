#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local terminal WebSocket server using pty.

Spawns a bash shell and bridges I/O over WebSocket.
Used by figrecipe's standalone GUI for the terminal panel.

Protocol:
  - Client sends raw text → written to pty master
  - Client sends "resize:ROWS:COLS" → pty resized via TIOCSWINSZ
  - Server sends raw text ← read from pty master
"""

import asyncio
import fcntl
import logging
import os
import pty
import struct
import termios
import threading

logger = logging.getLogger(__name__)


async def terminal_ws_handler(websocket, path=None):
    """Handle a single terminal WebSocket connection."""
    pid, master_fd = pty.fork()

    if pid == 0:
        # Child: exec bash
        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        os.execvpe("bash", ["bash", "--login"], env)

    # Parent: bridge master_fd <-> WebSocket
    flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
    fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    closed = False

    async def read_pty():
        while not closed:
            try:
                data = os.read(master_fd, 4096)
                if data:
                    await websocket.send(data.decode("utf-8", errors="replace"))
            except BlockingIOError:
                await asyncio.sleep(0.02)
            except OSError:
                break

    read_task = asyncio.create_task(read_pty())

    try:
        async for message in websocket:
            if isinstance(message, str):
                if message.startswith("resize:"):
                    parts = message.split(":")
                    if len(parts) == 3:
                        try:
                            rows, cols = int(parts[1]), int(parts[2])
                            winsize = struct.pack("HHHH", rows, cols, 0, 0)
                            fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
                        except (ValueError, OSError):
                            pass
                else:
                    os.write(master_fd, message.encode("utf-8"))
            elif isinstance(message, bytes):
                os.write(master_fd, message)
    except Exception:
        pass
    finally:
        closed = True
        read_task.cancel()
        os.close(master_fd)
        try:
            os.kill(pid, 9)
            os.waitpid(pid, 0)
        except OSError:
            pass


def _repair_connection_header(request):
    """Make a non-strict WebSocket upgrade request acceptable.

    Some browsers and (more often) reverse proxies send a request that is
    clearly a WebSocket upgrade -- it carries ``Upgrade: websocket`` and a
    ``Sec-WebSocket-Key`` -- but whose ``Connection`` header does not contain
    an ``Upgrade`` token (e.g. ``Connection: keep-alive``). Since
    ``websockets`` >= 14 the handshake parser strictly requires an ``Upgrade``
    token in ``Connection`` and otherwise rejects the handshake with
    HTTP 426 (``InvalidUpgrade: invalid Connection header``).

    This runs as a ``process_request`` hook, *before* the strict ``accept()``
    validation, and appends ``Upgrade`` to the ``Connection`` header only when
    the request is unambiguously a WebSocket upgrade. It never fabricates an
    upgrade for plain HTTP requests, so normal (already-correct) clients are
    unaffected.

    Returns ``None`` so the handshake continues normally.
    """
    try:
        headers = request.headers
        upgrade_values = ",".join(headers.get_all("Upgrade")).lower()
        is_ws_upgrade = (
            "websocket" in upgrade_values
            and headers.get("Sec-WebSocket-Key") is not None
        )
        if not is_ws_upgrade:
            return None

        connection_tokens = []
        for value in headers.get_all("Connection"):
            connection_tokens.extend(
                tok.strip() for tok in value.split(",") if tok.strip()
            )
        has_upgrade_token = any(tok.lower() == "upgrade" for tok in connection_tokens)
        if not has_upgrade_token:
            # Replace the Connection header with a clean, RFC-compliant value
            # that preserves any existing tokens and adds "Upgrade".
            del headers["Connection"]
            connection_tokens.append("Upgrade")
            headers["Connection"] = ", ".join(connection_tokens)
            logger.debug("Repaired non-strict Connection header for WebSocket upgrade")
    except Exception as exc:  # never block the handshake on a repair failure
        logger.debug("Connection header repair skipped: %s", exc)
    return None


def _process_request(connection, request):
    """``process_request`` hook for the modern ``websockets.asyncio`` server.

    Signature is ``(connection, request)``; ``request`` exposes a mutable
    ``headers`` mapping. Returning ``None`` lets the handshake proceed.
    """
    _repair_connection_header(request)
    return None


def start_terminal_server(port: int = 5051):
    """Start standalone WebSocket terminal server."""
    try:
        import websockets
    except ImportError:
        logger.warning(
            "websockets package not installed. Terminal disabled. "
            "Install with: pip install websockets"
        )
        return None

    async def serve():
        async with websockets.serve(
            terminal_ws_handler,
            "127.0.0.1",
            port,
            process_request=_process_request,
        ):
            logger.info("Terminal server on ws://127.0.0.1:%d", port)
            await asyncio.Future()

    thread = threading.Thread(target=lambda: asyncio.run(serve()), daemon=True)
    thread.start()
    return thread
