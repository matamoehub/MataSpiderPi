#!/usr/bin/env python3
from __future__ import annotations

import builtins
from typing import Any


def get_process_singleton(key: str, default: Any = None) -> Any:
    return getattr(builtins, key, default)


def set_process_singleton(key: str, value: Any) -> Any:
    setattr(builtins, key, value)
    return value


def clear_process_singleton(key: str) -> None:
    if hasattr(builtins, key):
        delattr(builtins, key)
