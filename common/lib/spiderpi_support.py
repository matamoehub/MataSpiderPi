#!/usr/bin/env python3
from __future__ import annotations

import importlib
import logging
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)


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
    robot_repo_dir = str(os.environ.get("ROBOT_LIB_REPO_DIR", "")).strip()
    if robot_repo_dir:
        candidates.append(Path(robot_repo_dir).expanduser() / "vendor" / "hiwonder_spiderpi")
    candidates.extend(
        [
            Path("/opt/robot/MataSpiderPi/vendor/hiwonder_spiderpi"),
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


_board_error: Exception | None = None


def get_board_error() -> Exception | None:
    """Return the exception raised by the last failed get_board() attempt.

    None means the board is either not yet initialised or initialised fine.
    Callers that got a None board back from get_board() can use this to
    build a clearer message than the generic "unavailable" string, e.g.
    distinguishing "another process already has the serial port open" from
    other init failures.
    """
    return _board_error


def board_unavailable_reason(default: str = "SpiderPi board unavailable") -> str:
    """Human-readable reason the board is unavailable, for error messages."""
    exc = _board_error
    if exc is None:
        return default
    message = str(exc)
    lowered = message.lower()
    if isinstance(exc, PermissionError) or "could not exclusively lock" in lowered or (
        "exclusive" in lowered and "lock" in lowered
    ):
        return (
            f"{default}: robot already in use by another process "
            f"(serial port could not be locked: {message})"
        )
    return f"{default}: {message}"


@lru_cache(maxsize=1)
def get_board() -> Any:
    global _board_error
    ensure_vendor_paths()
    try:
        from common.ros_robot_controller_sdk import Board
        board = Board()
        _log.debug("spiderpi_support: Board initialised")
        _board_error = None
        return board
    except Exception as e:
        _board_error = e
        _log.warning("spiderpi_support: could not initialise Board: %s", e)
        return None


@lru_cache(maxsize=1)
def get_action_controller() -> Any:
    ensure_vendor_paths()
    board = get_board()
    if board is None:
        return None
    try:
        from common.action_group_controller import ActionGroupController
        ctrl = ActionGroupController(board, action_path=str(resolve_vendor_root()))
        _log.debug("spiderpi_support: ActionGroupController initialised")
        return ctrl
    except Exception as e:
        _log.warning("spiderpi_support: could not initialise ActionGroupController: %s", e)
        return None


@lru_cache(maxsize=1)
def get_arm_ik() -> Any:
    ensure_vendor_paths()
    try:
        from arm_ik.arm_move_ik import ArmIK
        ik = ArmIK()
        _log.debug("spiderpi_support: ArmIK initialised")
        return ik
    except Exception as e:
        _log.warning("spiderpi_support: could not initialise ArmIK: %s", e)
        return None


def in_simulator() -> bool:
    mode = str(os.environ.get('MATA_BACKEND', '')).strip().lower()
    return mode == 'sim' or os.environ.get('MATA_SIM', '').strip() == '1'
