"""Validation helpers for experiment payloads.

Prevents storage of arbitrarily large or deeply nested JSON.
"""

from __future__ import annotations

import json
from typing import Any

MAX_PAYLOAD_SIZE = 100 * 1024  # 100 KB
MAX_PAYLOAD_DEPTH = 10


class PayloadTooLargeError(ValueError):
    """Payload exceeds size limit."""


class PayloadTooDeepError(ValueError):
    """Payload nesting exceeds depth limit."""


class PayloadNotJsonError(ValueError):
    """Payload cannot be serialized as JSON."""


def _check_depth(obj: Any, depth: int = 0) -> None:
    """Recursively check nesting depth."""
    if depth > MAX_PAYLOAD_DEPTH:
        raise PayloadTooDeepError(f"payload nesting depth exceeds {MAX_PAYLOAD_DEPTH}")
    if isinstance(obj, dict):
        for v in obj.values():
            _check_depth(v, depth + 1)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _check_depth(item, depth + 1)


def _check_null_bytes(obj: Any) -> None:
    """Recursively check for null bytes in strings (dict keys and values)."""
    if isinstance(obj, str):
        if "\x00" in obj:
            raise PayloadNotJsonError("payload contains null byte")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            _check_null_bytes(k)
            _check_null_bytes(v)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _check_null_bytes(item)


def validate_payload(payload: dict) -> dict:
    """Validate experiment payload.

    Rules:
    - JSON-serializable (no custom types)
    - Size <= 100 KB
    - Nesting depth <= 10
    - No null bytes in strings

    Returns:
        The same payload if valid.

    Raises:
        PayloadTooLargeError: size > 100 KB
        PayloadTooDeepError: nesting > 10
        PayloadNotJsonError: not JSON-serializable or contains null byte
    """
    try:
        serialized = json.dumps(payload, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        raise PayloadNotJsonError(f"payload is not JSON-serializable: {e}") from e

    size = len(serialized.encode("utf-8"))
    if size > MAX_PAYLOAD_SIZE:
        raise PayloadTooLargeError(f"payload size {size} bytes exceeds limit {MAX_PAYLOAD_SIZE}")

    _check_null_bytes(payload)
    _check_depth(payload)

    return payload
