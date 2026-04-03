#!/usr/bin/env python3
from __future__ import annotations

import importlib
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / 'lessons').is_dir() and (parent / 'vendor' / 'hiwonder_spiderpi').is_dir():
            return parent
    return here.parents[2]


@lru_cache(maxsize=1)
def resolve_vendor_root() -> Path:
    candidates: list[Path] = []

    for env_name in (
        "MATA_SPIDERPI_VENDOR_DIR",
        "SPIDERPI_VENDOR_DIR",
        "HIWONDER_SPIDERPI_DIR",
    ):
        value = str(os.environ.get(env_name, "")).strip()
        if value:
            candidates.append(Path(value).expanduser())

    repo_vendor = repo_root() / 'vendor' / 'hiwonder_spiderpi'
    candidates.extend(
        [
            Path("/home/pi/spiderpi"),
            Path("/home/pi/SpiderPi"),
            Path("/home/pi/hiwonder_spiderpi"),
            Path("/home/pi/SpiderPi/vendor/hiwonder_spiderpi"),
            repo_vendor,
        ]
    )

    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.resolve(strict=False))
        if key in seen:
            continue
        seen.add(key)
        if (candidate / "spiderpi_sdk").is_dir():
            return candidate

    return repo_vendor


def ensure_vendor_paths() -> Path:
    vendor = resolve_vendor_root()
    paths = [
        vendor,
        vendor / 'spiderpi_sdk' / 'common_sdk',
        vendor / 'spiderpi_sdk' / 'sensor_sdk',
        vendor / 'spiderpi_sdk' / 'arm_ik_sdk',
        vendor / 'spiderpi_sdk' / 'camera_calibration_sdk',
    ]
    for path in reversed(paths):
        value = str(path)
        if path.exists() and value not in sys.path:
            sys.path.insert(0, value)
    return vendor


def module_available(name: str) -> bool:
    try:
        importlib.import_module(name)
        return True
    except Exception:
        return False


@lru_cache(maxsize=1)
def get_board() -> Any:
    ensure_vendor_paths()
    try:
        from common.ros_robot_controller_sdk import Board
        return Board()
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_action_controller() -> Any:
    ensure_vendor_paths()
    board = get_board()
    if board is None:
        return None
    try:
        from common.action_group_controller import ActionGroupController
        return ActionGroupController(board, action_path=str(resolve_vendor_root()))
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_arm_ik() -> Any:
    ensure_vendor_paths()
    try:
        from arm_ik.arm_move_ik import ArmIK
        return ArmIK()
    except Exception:
        return None


def in_simulator() -> bool:
    mode = str(os.environ.get('MATA_BACKEND', '')).strip().lower()
    return mode == 'sim' or os.environ.get('MATA_SIM', '').strip() == '1'
