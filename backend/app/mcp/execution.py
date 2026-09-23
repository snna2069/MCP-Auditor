"""Isolated MCP process execution with bounded lifecycle and output."""

from __future__ import annotations

import logging
import os
import subprocess
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExecutionPolicy:
    timeout_seconds: float
    memory_limit: str
    cpu_limit: float
    pids_limit: int
    max_output_bytes: int
    sandbox_image: str


@dataclass
class ExecutionRecord:
    execution_id: uuid.UUID
    audit_id: uuid.UUID
    started_at: datetime
    ended_at: datetime | None = None
    status: str = "STARTING"
    exit_code: int | None = None
    error: str | None = None
    output_bytes: int = 0


class ExecutionProcess(Protocol):
    stdin: object
    stdout: object
    stderr: object

    def poll(self) -> int | None: ...

    def terminate(self) -> None: ...

    def kill(self) -> None: ...

    def wait(self, timeout: float | None = None) -> int: ...


class _DockerProcess:
    def __init__(self, process: subprocess.Popen, container_name: str) -> None:
        self._process = process
        self.container_name = container_name
        self.stdin = process.stdin
        self.stdout = process.stdout
        self.stderr = process.stderr

    def poll(self) -> int | None:
        return self._process.poll()

    def terminate(self) -> None:
        self._process.terminate()

    def kill(self) -> None:
        self._process.kill()

    def wait(self, timeout: float | None = None) -> int:
        return self._process.wait(timeout=timeout)


class ExecutionBackend(Protocol):
    def start(
        self,
        command: str,
        args: list[str],
        env: dict[str, str],
        execution: ExecutionRecord,
        policy: ExecutionPolicy,
    ) -> ExecutionProcess: ...

    def cleanup(self, process: ExecutionProcess, execution: ExecutionRecord) -> None: ...


def execution_policy() -> ExecutionPolicy:
    settings = get_settings()
    return ExecutionPolicy(
        timeout_seconds=settings.mcp_discovery_timeout_seconds,
        memory_limit=settings.mcp_execution_memory_limit,
        cpu_limit=settings.mcp_execution_cpu_limit,
        pids_limit=settings.mcp_execution_pids_limit,
        max_output_bytes=settings.mcp_execution_max_output_bytes,
        sandbox_image=settings.mcp_sandbox_image,
    )


class DockerSandboxBackend:
    """Launches each MCP process in a disposable, least-privilege container."""

    def start(
        self,
        command: str,
        args: list[str],
        env: dict[str, str],
        execution: ExecutionRecord,
        policy: ExecutionPolicy,
    ) -> ExecutionProcess:
        container_name = f"mcp-auditor-{execution.execution_id.hex}"
        docker_args = [
            "docker",
            "run",
            "--rm",
            "--name",
            container_name,
            "-i",
            "--network",
            "none",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=16m",
            "--cap-drop=ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--memory",
            policy.memory_limit,
            "--cpus",
            str(policy.cpu_limit),
            "--pids-limit",
            str(policy.pids_limit),
        ]
        safe_env = {
            key: value
            for key, value in {
                "PATH": os.environ.get("PATH", ""),
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
                **_restricted_environment(env),
            }.items()
            if value
        }
        for key, value in safe_env.items():
            docker_args.extend(["--env", f"{key}={value}"])
        docker_args.extend([policy.sandbox_image, command, *args])
        try:
            process = subprocess.Popen(
                docker_args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=safe_env,
            )
        except OSError as exc:
            raise RuntimeError("Could not start the MCP sandbox runtime.") from exc
        execution.status = "RUNNING"
        _log_execution(execution, "started")
        return _DockerProcess(process, container_name)

    def cleanup(self, process: ExecutionProcess, execution: ExecutionRecord) -> None:
        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=2)
            except (subprocess.TimeoutExpired, OSError):
                try:
                    process.kill()
                    process.wait(timeout=2)
                except (OSError, subprocess.TimeoutExpired):
                    pass
        container_name = getattr(process, "container_name", None)
        if container_name:
            try:
                subprocess.run(
                    ["docker", "rm", "--force", container_name],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                )
            except (OSError, subprocess.TimeoutExpired):
                execution.error = execution.error or "sandbox_cleanup_failed"
        execution.ended_at = datetime.now(UTC)
        if execution.status == "RUNNING":
            execution.status = "COMPLETED" if execution.exit_code == 0 else "FAILED"
        _log_execution(execution, "finished")


class SubprocessBackend:
    """Test-only backend; never selected by production configuration."""

    def start(
        self,
        command: str,
        args: list[str],
        env: dict[str, str],
        execution: ExecutionRecord,
        policy: ExecutionPolicy,
    ) -> ExecutionProcess:
        process = subprocess.Popen(
            [command, *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            start_new_session=(os.name != "nt"),
            env=_restricted_environment(env),
        )
        execution.status = "RUNNING"
        return process

    def cleanup(self, process: ExecutionProcess, execution: ExecutionRecord) -> None:
        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=2)
            except (subprocess.TimeoutExpired, OSError):
                try:
                    process.kill()
                    process.wait(timeout=2)
                except (OSError, subprocess.TimeoutExpired):
                    pass
        execution.ended_at = datetime.now(UTC)
        execution.status = "COMPLETED" if execution.exit_code == 0 else "FAILED"


def _restricted_environment(configured: dict[str, str]) -> dict[str, str]:
    sensitive_markers = ("PASSWORD", "SECRET", "TOKEN", "API_KEY", "CREDENTIAL", "PRIVATE_KEY")
    return {
        key: value
        for key, value in configured.items()
        if not any(marker in key.upper() for marker in sensitive_markers)
    }


def _log_execution(execution: ExecutionRecord, event: str) -> None:
    logger.info(
        "mcp execution %s",
        event,
        extra={
            "execution_id": str(execution.execution_id),
            "audit_id": str(execution.audit_id),
            "started_at": execution.started_at.isoformat(),
            "ended_at": execution.ended_at.isoformat() if execution.ended_at else None,
            "status": execution.status,
            "exit_code": execution.exit_code,
            "output_bytes": execution.output_bytes,
        },
    )
