"""Shared keyword vocabularies and matching for heuristic auditors.

Capability/side-effect inference is intentionally simple keyword matching,
not NLP or an LLM call: it must be deterministic (same input -> same
output, always) so audits are reproducible, per the project's testing
standards. It is a best-effort signal to surface tools for human review -
not proof of a tool's actual behavior, consistent with the principle that
tool metadata is untrusted input.
"""

import re

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize(text: str) -> str:
    """Lowercase and replace any run of non-alphanumeric characters with a
    single space, so compound identifiers like ``shell_command`` or
    ``api-key`` tokenize the same as a natural-language phrase."""
    return _NON_ALNUM.sub(" ", text.lower())


def find_matches(haystack: str, keywords: frozenset[str]) -> list[str]:
    """Return the subset of ``keywords`` present as whole tokens/phrases in
    ``haystack``. ``haystack`` must already be normalize()-d."""
    padded = f" {haystack} "
    return sorted(keyword for keyword in keywords if f" {keyword} " in padded)


SHELL_EXECUTION_KEYWORDS = frozenset(
    {
        "shell",
        "exec",
        "execute",
        "subprocess",
        "bash",
        "powershell",
        "cmd",
        "command",
        "eval",
        "script",
    }
)

NETWORK_KEYWORDS = frozenset(
    {
        "http",
        "https",
        "url",
        "fetch",
        "download",
        "upload",
        "request",
        "api",
        "webhook",
        "socket",
        "network",
        "email",
        "sms",
        "notify",
        "notification",
    }
)

FILE_SYSTEM_KEYWORDS = frozenset({"file", "path", "directory", "folder", "filesystem", "disk"})

DATABASE_KEYWORDS = frozenset(
    {
        "sql",
        "database",
        "query",
        "db",
        "table",
        "postgres",
        "postgresql",
        "mysql",
        "mongodb",
        "mongo",
    }
)

SECRETS_KEYWORDS = frozenset(
    {
        "secret",
        "password",
        "token",
        "credential",
        "api key",
        "apikey",
        "private key",
    }
)

IDENTITY_KEYWORDS = frozenset(
    {"user", "identity", "login", "account", "permission", "role", "iam", "session"}
)

INFRASTRUCTURE_KEYWORDS = frozenset(
    {
        "deploy",
        "infrastructure",
        "server",
        "servers",
        "cluster",
        "clusters",
        "provision",
        "instance",
        "instances",
        "container",
        "containers",
        "kubernetes",
        "terraform",
        "cloud",
        "resource",
        "resources",
    }
)

DESTRUCTIVE_KEYWORDS = frozenset(
    {
        "delete",
        "remove",
        "destroy",
        "drop",
        "terminate",
        "purge",
        "wipe",
        "erase",
        "uninstall",
    }
)

WRITE_KEYWORDS = frozenset(
    {
        "create",
        "update",
        "insert",
        "write",
        "modify",
        "save",
        "add",
        "set",
        "edit",
        "send",
        "notify",
        "publish",
        "post",
    }
)

READ_ONLY_KEYWORDS = frozenset(
    {
        "get",
        "list",
        "search",
        "read",
        "fetch",
        "query",
        "view",
        "lookup",
        "find",
        "describe",
        "show",
    }
)
