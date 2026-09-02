"""MCP client for the ``HTTP`` source type (Streamable HTTP transport).

Supports both a plain JSON response and a single Server-Sent Events
response per request, since the spec allows either. Accepts an injectable
``httpx`` transport so tests never need a real network connection.
"""

import json

import httpx

from app.mcp.base import MCPClient, MCPDiscoveryResult
from app.mcp.exceptions import MCPConnectionError, MCPProtocolError, MCPTimeoutError
from app.mcp.jsonrpc import build_notification, build_request, next_request_id, parse_response
from app.mcp.wire_models import INITIALIZE_PARAMS, parse_tools

_MAX_PAGES = 20
_ACCEPT_HEADER = "application/json, text/event-stream"


class HttpMCPClient(MCPClient):
    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._url = url
        self._headers = headers or {}
        self._timeout = timeout
        # Injectable for tests; None means "use the real network".
        self._transport = transport

    def discover(self) -> MCPDiscoveryResult:
        try:
            with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
                return self._discover(client)
        except httpx.TimeoutException as exc:
            raise MCPTimeoutError(
                f"Timed out after {self._timeout}s connecting to {self._url}."
            ) from exc
        except httpx.HTTPError as exc:
            raise MCPConnectionError(f"Could not connect to {self._url}: {exc}") from exc

    def _discover(self, client: httpx.Client) -> MCPDiscoveryResult:
        protocol_version = None

        init_id = next_request_id()
        init_body = self._post(
            client, build_request("initialize", INITIALIZE_PARAMS, init_id), None
        )
        init_result = parse_response(init_body, expected_id=init_id)
        protocol_version = init_result.get("protocolVersion")

        self._post_notification(
            client, build_notification("notifications/initialized", None), protocol_version
        )

        tools = []
        cursor = None
        for _ in range(_MAX_PAGES):
            list_id = next_request_id()
            params = {"cursor": cursor} if cursor else None
            body = self._post(
                client, build_request("tools/list", params, list_id), protocol_version
            )
            result = parse_response(body, expected_id=list_id)
            tools.extend(parse_tools(result.get("tools", [])))
            cursor = result.get("nextCursor")
            if not cursor:
                break

        server_info = init_result.get("serverInfo", {})
        return MCPDiscoveryResult(
            server_name=server_info.get("name"),
            server_version=server_info.get("version"),
            protocol_version=protocol_version,
            tools=tools,
        )

    def _build_headers(self, protocol_version: str | None) -> dict[str, str]:
        headers = {
            **self._headers,
            "Accept": _ACCEPT_HEADER,
            "Content-Type": "application/json",
        }
        # Per spec, required on all requests after version negotiation.
        if protocol_version:
            headers["MCP-Protocol-Version"] = protocol_version
        return headers

    def _post(self, client: httpx.Client, message: dict, protocol_version: str | None) -> dict:
        response = client.post(
            self._url, json=message, headers=self._build_headers(protocol_version)
        )
        response.raise_for_status()
        return _parse_body(response)

    def _post_notification(
        self, client: httpx.Client, message: dict, protocol_version: str | None
    ) -> None:
        response = client.post(
            self._url, json=message, headers=self._build_headers(protocol_version)
        )
        # Per spec, servers respond 202 Accepted with no body to a notification.
        response.raise_for_status()


def _parse_body(response: httpx.Response) -> dict:
    content_type = response.headers.get("content-type", "")
    if "text/event-stream" in content_type:
        return _parse_sse(response.text)
    try:
        return response.json()
    except ValueError as exc:
        raise MCPProtocolError(f"Server response was not valid JSON: {exc}") from exc


def _parse_sse(body: str) -> dict:
    """Extract the JSON-RPC message from a single-event SSE response body."""
    events = [event for event in body.strip().split("\n\n") if event.strip()]
    if not events:
        raise MCPProtocolError("SSE response was empty.")

    data_lines = [
        line[len("data:") :].strip() for line in events[-1].splitlines() if line.startswith("data:")
    ]
    if not data_lines:
        raise MCPProtocolError("SSE response did not contain any 'data:' lines.")

    try:
        return json.loads("\n".join(data_lines))
    except json.JSONDecodeError as exc:
        raise MCPProtocolError(f"SSE 'data:' payload was not valid JSON: {exc}") from exc
