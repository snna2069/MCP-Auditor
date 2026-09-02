"""Tests for StdioMCPClient against a real subprocess (fake fixture server)."""

import json
import sys
from pathlib import Path

import pytest

from app.mcp.exceptions import MCPConnectionError, MCPTimeoutError
from app.mcp.stdio_client import StdioMCPClient

FAKE_SERVER_PATH = str(Path(__file__).parent / "fixtures" / "fake_stdio_server.py")

SAMPLE_TOOL = {
    "name": "get_weather",
    "title": "Weather Information Provider",
    "description": "Get current weather information for a location",
    "inputSchema": {
        "type": "object",
        "properties": {"location": {"type": "string"}},
        "required": ["location"],
    },
    "annotations": {"readOnlyHint": True, "openWorldHint": True},
}


def _client(scenario: dict, timeout: float = 5.0) -> StdioMCPClient:
    return StdioMCPClient(
        command=sys.executable,
        args=[FAKE_SERVER_PATH],
        env={"FAKE_MCP_SCENARIO": json.dumps(scenario)},
        timeout=timeout,
    )


def test_discover_returns_normalized_tools() -> None:
    client = _client({"tools": [SAMPLE_TOOL]})

    result = client.discover()

    assert result.server_name == "fake-server"
    assert result.protocol_version == "2025-06-18"
    assert len(result.tools) == 1
    tool = result.tools[0]
    assert tool.name == "get_weather"
    assert tool.annotations.read_only_hint is True


def test_discover_with_no_tools() -> None:
    client = _client({"tools": []})

    result = client.discover()

    assert result.tools == []


def test_discover_raises_on_crashed_process() -> None:
    client = _client({"exit_after_init": True})

    with pytest.raises(MCPConnectionError):
        client.discover()


def test_discover_raises_on_timeout() -> None:
    client = _client({"delay_seconds": 2}, timeout=0.2)

    with pytest.raises(MCPTimeoutError):
        client.discover()


def test_discover_raises_on_missing_command() -> None:
    client = StdioMCPClient(command="this-command-does-not-exist-anywhere", timeout=2.0)

    with pytest.raises(MCPConnectionError):
        client.discover()
