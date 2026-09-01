"""Unit tests for the encryption helpers used to protect secrets at rest."""

import pytest

from app.core.security import EncryptionError, decrypt_json, encrypt_json


def test_encrypt_json_round_trips() -> None:
    data = {"token": "super-secret", "nested": {"a": 1}}

    token = encrypt_json(data)

    assert isinstance(token, str)
    assert "super-secret" not in token
    assert decrypt_json(token) == data


def test_decrypt_json_rejects_tampered_token() -> None:
    token = encrypt_json({"a": 1})

    with pytest.raises(EncryptionError):
        decrypt_json(token[:-1] + ("A" if token[-1] != "A" else "B"))
