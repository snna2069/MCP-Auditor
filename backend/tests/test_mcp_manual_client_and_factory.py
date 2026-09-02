"""Tests for ManualMCPClient and the client factory."""

import pytest

from app.mcp.exceptions import MCPClientError
from app.mcp.factory import build_mcp_client
from app.mcp.http_client import HttpMCPClient
from app.mcp.manual_client import ManualMCPClient
from app.mcp.stdio_client import StdioMCPClient
from app.models.enums import SourceType


def test_manual_client_normalizes_provided_tools() -> None:
    client = ManualMCPClient(
        {
            "details": {
                "tools": [
                    {
                        "name": "lookup_customer",
                        "description": "Looks up a customer record",
                        "inputSchema": {"type": "object"},
                    }
                ]
            }
        }
    )

    result = client.discover()

    assert len(result.tools) == 1
    assert result.tools[0].name == "lookup_customer"
    assert result.warnings == []


def test_manual_client_with_no_tools_succeeds_with_empty_list() -> None:
    client = ManualMCPClient({"details": {"description": "no tools yet"}})

    result = client.discover()

    assert result.tools == []


def test_manual_client_skips_malformed_tool_entries() -> None:
    client = ManualMCPClient(
        {
            "details": {
                "tools": [
                    {"description": "missing required name"},
                    {"name": "valid_tool", "inputSchema": {"type": "object"}},
                ]
            }
        }
    )

    result = client.discover()

    assert len(result.tools) == 1
    assert result.tools[0].name == "valid_tool"
    assert len(result.warnings) == 1


def test_factory_builds_stdio_client_for_local_command() -> None:
    client = build_mcp_client(
        SourceType.LOCAL_COMMAND, {"command": "python", "args": []}, timeout=5.0
    )
    assert isinstance(client, StdioMCPClient)


def test_factory_builds_http_client_for_http() -> None:
    client = build_mcp_client(SourceType.HTTP, {"url": "https://example.com/mcp"}, timeout=5.0)
    assert isinstance(client, HttpMCPClient)


def test_factory_builds_manual_client_for_manual_configuration() -> None:
    client = build_mcp_client(SourceType.MANUAL_CONFIGURATION, {}, timeout=5.0)
    assert isinstance(client, ManualMCPClient)


def test_factory_rejects_unsupported_source_type() -> None:
    with pytest.raises(MCPClientError):
        build_mcp_client(SourceType.SSE, {}, timeout=5.0)
