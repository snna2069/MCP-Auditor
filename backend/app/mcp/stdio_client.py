"""MCP client for the ``LOCAL_COMMAND`` source type.

Launches the configured command as a subprocess and speaks line-delimited
JSON-RPC over its stdin/stdout, per the MCP stdio transport spec. Uses a
background reader thread + queue (rather than ``select``) so timeouts work
on Windows, where ``select`` does not support pipe file descriptors.

This module only *reads* tool metadata during discovery; it never invokes
tools, per the project's security principle of treating discovered
servers as untrusted until an audit explicitly calls a tool.
"""

import json
import os
import queue
import subprocess
import threading

from app.mcp.base import MCPClient, MCPDiscoveryResult
from app.mcp.exceptions import MCPConnectionError, MCPProtocolError, MCPTimeoutError
from app.mcp.jsonrpc import build_notification, build_request, next_request_id, parse_response
from app.mcp.wire_models import INITIALIZE_PARAMS, parse_tools

# Safety cap on tools/list pagination so a misbehaving server can't force an
# unbounded loop.
_MAX_PAGES = 20


class StdioMCPClient(MCPClient):
    def __init__(
        self,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: float = 15.0,
    ) -> None:
        self._command = command
        self._args = args or []
        self._env = env or {}
        self._timeout = timeout

    def discover(self) -> MCPDiscoveryResult:
        # Merge with the parent environment (e.g. so PATH resolves the
        # command) then apply user-provided overrides. Never log self._env -
        # it may contain secrets the user configured for the command.
        merged_env = {**os.environ, **self._env}
        try:
            process = subprocess.Popen(  # noqa: S603 - command is user-configured by design
                [self._command, *self._args],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=merged_env,
            )
        except OSError as exc:
            raise MCPConnectionError(
                f"Could not launch local command '{self._command}': {exc}"
            ) from exc

        stdout_queue: queue.Queue[str | None] = queue.Queue()
        reader = threading.Thread(
            target=_pump_lines, args=(process.stdout, stdout_queue), daemon=True
        )
        reader.start()

        try:
            return self._run_handshake(process, stdout_queue)
        finally:
            _terminate(process)

    def _run_handshake(
        self, process: subprocess.Popen, stdout_queue: "queue.Queue[str | None]"
    ) -> MCPDiscoveryResult:
        init_id = next_request_id()
        self._send(process, build_request("initialize", INITIALIZE_PARAMS, init_id))
        init_result = parse_response(self._recv(process, stdout_queue), expected_id=init_id)

        self._send(process, build_notification("notifications/initialized", None))

        tools = []
        cursor = None
        for _ in range(_MAX_PAGES):
            list_id = next_request_id()
            params = {"cursor": cursor} if cursor else None
            self._send(process, build_request("tools/list", params, list_id))
            result = parse_response(self._recv(process, stdout_queue), expected_id=list_id)
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

    def _send(self, process: subprocess.Popen, message: dict) -> None:
        if process.poll() is not None:
            raise MCPConnectionError(
                f"Process exited before request could be sent "
                f"(code {process.returncode}).{_stderr_suffix(process)}"
            )
        try:
            process.stdin.write(json.dumps(message) + "\n")
            process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise MCPConnectionError(f"Failed to write to process stdin: {exc}") from exc

    def _recv(self, process: subprocess.Popen, stdout_queue: "queue.Queue[str | None]") -> dict:
        try:
            line = stdout_queue.get(timeout=self._timeout)
        except queue.Empty as exc:
            raise MCPTimeoutError(
                f"Timed out after {self._timeout}s waiting for a response."
            ) from exc

        if line is None:
            raise MCPConnectionError(
                f"Process closed stdout before responding.{_stderr_suffix(process)}"
            )

        try:
            return json.loads(line)
        except json.JSONDecodeError as exc:
            raise MCPProtocolError(f"Received non-JSON line from process: {exc}") from exc


def _pump_lines(stream, out_queue: "queue.Queue[str | None]") -> None:
    try:
        for line in iter(stream.readline, ""):
            stripped = line.strip()
            if stripped:
                out_queue.put(stripped)
    except ValueError:
        pass  # Stream closed while reading (process terminated concurrently).
    finally:
        out_queue.put(None)


def _stderr_suffix(process: subprocess.Popen) -> str:
    # Only safe to read stderr to EOF once the process has actually exited;
    # otherwise .read() could block indefinitely.
    if process.poll() is None or process.stderr is None:
        return ""
    try:
        tail = process.stderr.read().strip()
    except OSError:
        return ""
    return f" stderr: {tail}" if tail else ""


def _terminate(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
    except OSError:
        pass
