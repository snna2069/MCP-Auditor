"""Encryption helpers for sensitive fields stored at rest.

MCPServer.connection_config may contain secrets (API tokens, auth headers,
local command environment variables). We never persist that JSON in
plaintext; it is encrypted with Fernet (AES-128-CBC + HMAC) before being
written to the database and decrypted only when read back through the
service layer.
"""

import json
from functools import lru_cache
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


class EncryptionError(Exception):
    """Raised when data cannot be encrypted or decrypted."""


@lru_cache
def _get_fernet() -> Fernet:
    settings = get_settings()
    key = settings.encryption_key
    if not key:
        # Fail fast rather than silently generating a throwaway key: an
        # ephemeral key would make previously-encrypted data unreadable
        # after every restart.
        raise EncryptionError(
            "ENCRYPTION_KEY is not set. Generate one with "
            '`python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"` and set it in .env.'
        )
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as exc:
        raise EncryptionError("ENCRYPTION_KEY is not a valid Fernet key.") from exc


def encrypt_json(data: dict[str, Any]) -> str:
    """Serialize ``data`` to JSON and encrypt it, returning a token string."""
    payload = json.dumps(data).encode("utf-8")
    return _get_fernet().encrypt(payload).decode("utf-8")


def decrypt_json(token: str) -> dict[str, Any]:
    """Decrypt a token produced by ``encrypt_json`` back into a dict."""
    try:
        payload = _get_fernet().decrypt(token.encode("utf-8"))
    except InvalidToken as exc:
        raise EncryptionError("Stored data could not be decrypted.") from exc
    return json.loads(payload.decode("utf-8"))
