"""Tests for HttpMCPClient using an injected httpx MockTransport (no network)."""

import json

import httpx
import pytest

from app.mcp.exceptions import MCPConnectionError, MCPProtocolError
from app.mcp.http_client import HttpMCPClient

SAMPLE_TOOL = {
    "name": "search_docs",
    "description": "Search internal documentation",
    "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}},
}


def _json_response(message: dict) -> httpx.Response:
    return httpx.Response(200, json=message, headers={"content-type": "application/json"})


def test_discover_over_plain_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if body["method"] == "initialize":
            return _json_response(
                {
                    "jsonrpc": "2.0",
                    "id": body["id"],
                    "result": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "http-fake", "version": "2.0.0"},
                    },
                }
            )
        if body["method"] == "notifications/initialized":
            return httpx.Response(202)
        if body["method"] == "tools/list":
            return _json_response(
                {"jsonrpc": "2.0", "id": body["id"], "result": {"tools": [SAMPLE_TOOL]}}
            )
        raise AssertionError(f"unexpected method {body['method']}")

    client = HttpMCPClient(url="https://example.test/mcp", transport=httpx.MockTransport(handler))

    result = client.discover()

    assert result.server_name == "http-fake"
    assert len(result.tools) == 1
    assert result.tools[0].name == "search_docs"


def test_discover_over_sse_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if body["method"] == "initialize":
            payload = {
                "jsonrpc": "2.0",
                "id": body["id"],
                "result": {
                    "protocolVersion": "2025-06-18",
                    "serverInfo": {"name": "sse-fake"},
                },
            }
            sse_body = f"data: {json.dumps(payload)}\n\n"
            return httpx.Response(200, text=sse_body, headers={"content-type": "text/event-stream"})
        if body["method"] == "notifications/initialized":
            return httpx.Response(202)
        if body["method"] == "tools/list":
            payload = {
                "jsonrpc": "2.0",
                "id": body["id"],
                "result": {"tools": [SAMPLE_TOOL]},
            }
            sse_body = f"data: {json.dumps(payload)}\n\n"
            return httpx.Response(200, text=sse_body, headers={"content-type": "text/event-stream"})
        raise AssertionError(f"unexpected method {body['method']}")

    client = HttpMCPClient(url="https://example.test/mcp", transport=httpx.MockTransport(handler))

    result = client.discover()

    assert result.server_name == "sse-fake"
    assert len(result.tools) == 1


def test_discover_paginates_tools_list() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if body["method"] == "initialize":
            return _json_response(
                {
                    "jsonrpc": "2.0",
                    "id": body["id"],
                    "result": {"protocolVersion": "2025-06-18", "serverInfo": {}},
                }
            )
        if body["method"] == "notifications/initialized":
            return httpx.Response(202)
        if body["method"] == "tools/list":
            cursor = (body.get("params") or {}).get("cursor")
            if cursor is None:
                return _json_response(
                    {
                        "jsonrpc": "2.0",
                        "id": body["id"],
                        "result": {"tools": [SAMPLE_TOOL], "nextCursor": "page-2"},
                    }
                )
            return _json_response(
                {"jsonrpc": "2.0", "id": body["id"], "result": {"tools": [SAMPLE_TOOL]}}
            )
        raise AssertionError(f"unexpected method {body['method']}")

    client = HttpMCPClient(url="https://example.test/mcp", transport=httpx.MockTransport(handler))

    result = client.discover()

    assert len(result.tools) == 2


def test_discover_raises_on_protocol_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        return _json_response(
            {
                "jsonrpc": "2.0",
                "id": body["id"],
                "error": {"code": -32000, "message": "boom"},
            }
        )

    client = HttpMCPClient(url="https://example.test/mcp", transport=httpx.MockTransport(handler))

    with pytest.raises(MCPProtocolError):
        client.discover()


def test_discover_raises_on_connection_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    client = HttpMCPClient(url="https://example.test/mcp", transport=httpx.MockTransport(handler))

    with pytest.raises(MCPConnectionError):
        client.discover()
