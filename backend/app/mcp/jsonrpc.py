"""Minimal JSON-RPC 2.0 helpers for the MCP wire protocol.

Only what MCP discovery needs: building requests/notifications and parsing
responses. Not a general-purpose JSON-RPC library.
"""

import itertools
from typing import Any

from app.mcp.exceptions import MCPProtocolError

_id_counter = itertools.count(1)


def next_request_id() -> int:
    return next(_id_counter)


def build_request(method: str, params: dict[str, Any] | None, request_id: int) -> dict:
    message: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        message["params"] = params
    return message


def build_notification(method: str, params: dict[str, Any] | None) -> dict:
    message: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        message["params"] = params
    return message


def parse_response(message: dict, *, expected_id: int) -> dict:
    """Validate a JSON-RPC response envelope and return its ``result``.

    Raises ``MCPProtocolError`` if the message is malformed, mismatched, or
    itself a JSON-RPC error response.
    """
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        raise MCPProtocolError("Server sent a message that is not valid JSON-RPC 2.0.")

    if message.get("id") != expected_id:
        raise MCPProtocolError(
            f"Response id {message.get('id')!r} did not match request id {expected_id!r}."
        )

    if "error" in message:
        error = message["error"] or {}
        code = error.get("code", "unknown")
        error_message = error.get("message", "no message provided")
        raise MCPProtocolError(f"Server returned JSON-RPC error {code}: {error_message}")

    if "result" not in message:
        raise MCPProtocolError("Server response contained neither 'result' nor 'error'.")

    result = message["result"]
    if not isinstance(result, dict):
        raise MCPProtocolError("Server response 'result' was not a JSON object.")
    return result
