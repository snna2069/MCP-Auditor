"""MCP stdio transport backed by an isolated execution backend."""

import json
import queue
import threading
import time
import uuid
from datetime import UTC, datetime

from app.mcp.base import MCPClient, MCPDiscoveryResult
from app.mcp.exceptions import MCPClientError, MCPConnectionError, MCPProtocolError, MCPTimeoutError
from app.mcp.execution import (
    DockerSandboxBackend,
    ExecutionBackend,
    ExecutionPolicy,
    ExecutionProcess,
    ExecutionRecord,
    execution_policy,
)
from app.mcp.jsonrpc import build_notification, build_request, next_request_id, parse_response
from app.mcp.wire_models import INITIALIZE_PARAMS, parse_tools

_MAX_PAGES = 20


class StdioMCPClient(MCPClient):
    def __init__(
        self,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: float = 15.0,
        audit_id: str | None = None,
        backend: ExecutionBackend | None = None,
        policy: ExecutionPolicy | None = None,
    ) -> None:
        self._command = command
        self._args = args or []
        self._env = env or {}
        self._timeout = timeout
        self._audit_id = uuid.UUID(audit_id) if audit_id else uuid.uuid4()
        self._backend = backend or DockerSandboxBackend()
        self._policy = policy or execution_policy()
        self._deadline = 0.0

    def discover(self) -> MCPDiscoveryResult:
        execution = ExecutionRecord(
            execution_id=uuid.uuid4(),
            audit_id=self._audit_id,
            started_at=datetime.now(UTC),
        )
        try:
            process = self._backend.start(
                self._command,
                self._args,
                self._env,
                execution,
                self._policy,
            )
        except (OSError, RuntimeError) as exc:
            execution.status = "FAILED"
            execution.error = type(exc).__name__
            execution.ended_at = datetime.now(UTC)
            raise MCPConnectionError("Could not start the MCP sandbox.") from exc

        output_queue: queue.Queue[object] = queue.Queue()
        output_bytes = [0]
        self._deadline = time.monotonic() + min(
            self._timeout, self._policy.timeout_seconds
        )
        reader = threading.Thread(
            target=_pump_lines,
            args=(process.stdout, output_queue, self._policy.max_output_bytes, output_bytes),
            daemon=True,
        )
        reader.start()
        try:
            result = self._run_handshake(process, output_queue)
            execution.status = "COMPLETED"
            return result
        except MCPTimeoutError:
            execution.status = "TIMEOUT"
            raise
        except MCPClientError as exc:
            execution.status = "FAILED"
            execution.error = type(exc).__name__
            raise
        finally:
            execution.exit_code = process.poll()
            execution.output_bytes = output_bytes[0]
            self._backend.cleanup(process, execution)

    def _run_handshake(
        self, process: ExecutionProcess, output_queue: "queue.Queue[object]"
    ) -> MCPDiscoveryResult:
        init_id = next_request_id()
        self._send(process, build_request("initialize", INITIALIZE_PARAMS, init_id))
        init_result = parse_response(self._recv(process, output_queue), expected_id=init_id)
        self._send(process, build_notification("notifications/initialized", None))

        tools = []
        cursor = None
        for _ in range(_MAX_PAGES):
            list_id = next_request_id()
            params = {"cursor": cursor} if cursor else None
            self._send(process, build_request("tools/list", params, list_id))
            result = parse_response(self._recv(process, output_queue), expected_id=list_id)
            tools.extend(parse_tools(result.get("tools", [])))
            cursor = result.get("nextCursor")
            if not cursor:
                break

        server_info = init_result.get("serverInfo", {})
        return MCPDiscoveryResult(
            server_name=server_info.get("name"),
            server_version=server_info.get("version"),
            protocol_version=init_result.get("protocolVersion"),
            tools=tools,
        )

    def _send(self, process: ExecutionProcess, message: dict) -> None:
        if process.poll() is not None:
            raise MCPConnectionError("MCP process exited before the request was sent.")
        try:
            process.stdin.write(json.dumps(message) + "\n")
            process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise MCPConnectionError("Failed to write to the MCP process.") from exc

    def _recv(self, process: ExecutionProcess, output_queue: "queue.Queue[object]") -> dict:
        remaining = self._deadline - time.monotonic()
        if remaining <= 0:
            raise MCPTimeoutError("MCP execution exceeded its timeout.")
        try:
            line = output_queue.get(timeout=min(self._timeout, remaining))
        except queue.Empty as exc:
            raise MCPTimeoutError(
                f"Timed out after {self._timeout}s waiting for an MCP response."
            ) from exc
        if line is None:
            raise MCPConnectionError("MCP process closed stdout before responding.")
        if isinstance(line, _OutputLimitExceeded):
            raise MCPProtocolError("MCP output exceeded the configured limit.")
        try:
            return json.loads(line)
        except (TypeError, json.JSONDecodeError) as exc:
            raise MCPProtocolError("MCP response was not valid JSON.") from exc


class _OutputLimitExceeded:
    pass


def _pump_lines(
    stream, output_queue: "queue.Queue[object]", maximum: int, output_count: list[int]
) -> None:
    try:
        for line in iter(stream.readline, ""):
            stripped = line.strip()
            if stripped:
                output_count[0] += len(stripped.encode("utf-8"))
                if output_count[0] > maximum:
                    output_queue.put(_OutputLimitExceeded())
                    return
                output_queue.put(stripped)
    except (OSError, ValueError):
        pass
    finally:
        output_queue.put(None)
