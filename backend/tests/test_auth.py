import hashlib

import pytest

from app.config import settings
from app.services.auth import generate_api_key, hash_key


def test_hash_key_is_sha256() -> None:
    raw = "sk-agent-testkey123"
    result = hash_key(raw)
    expected = hashlib.sha256(raw.encode()).hexdigest()
    assert result == expected


def test_hash_key_deterministic() -> None:
    raw = "sk-agent-abc"
    assert hash_key(raw) == hash_key(raw)


def test_generate_api_key_format() -> None:
    raw_key, key_hash = generate_api_key()
    assert raw_key.startswith(settings.API_KEY_PREFIX)
    assert len(raw_key) > len(settings.API_KEY_PREFIX)


def test_generate_api_key_hash_matches() -> None:
    raw_key, key_hash = generate_api_key()
    assert hash_key(raw_key) == key_hash


def test_generate_api_key_unique() -> None:
    key1, _ = generate_api_key()
    key2, _ = generate_api_key()
    assert key1 != key2
