#!/usr/bin/env python3
from __future__ import annotations

import time
from typing import Optional

from spiderpi_support import get_action_controller

BASE_SPEED = float(__import__('os').environ.get('BASE_SPEED', '300'))

_ACTIONS = {
    'forward': ('go_forward_low', 0.55),
    'backward': ('back_low', 0.55),
    'left': ('left_move', 0.55),
    'right': ('right_move', 0.55),
    'turn_left': ('turn_left_low', 0.45),
    'turn_right': ('turn_right_low', 0.45),
    'attack': ('attack', 1.0),
    'wave': ('wave', 1.0),
    'dance': ('dance', 1.6),
    'kick': ('kick', 1.0),
    'twist': ('twist', 1.0),
}


def _controller_or_error():
    controller = get_action_controller()
    if controller is None:
        raise RuntimeError('SpiderPi action controller unavailable')
    return controller


def _repeat_count(seconds: float, cycle_seconds: float) -> int:
    return max(1, int(round(max(0.1, float(seconds)) / max(0.1, float(cycle_seconds)))))


def _run_action(action_name: str, seconds: float) -> None:
    action_group, cycle = _ACTIONS[action_name]
    controller = _controller_or_error()
    repeats = _repeat_count(seconds, cycle)
    controller.run_action_group(action_group, times=repeats)


def stop() -> None:
    controller = get_action_controller()
    if controller is not None:
        try:
            controller.stop_servo()
        except Exception:
            pass


def emergency_stop() -> None:
    stop()


def forward(seconds: float = 0.6, speed: Optional[float] = None):
    del speed
    _run_action('forward', seconds)


def backward(seconds: float = 0.6, speed: Optional[float] = None):
    del speed
    _run_action('backward', seconds)


def left(seconds: float = 0.6, speed: Optional[float] = None):
    del speed
    _run_action('left', seconds)


def right(seconds: float = 0.6, speed: Optional[float] = None):
    del speed
    _run_action('right', seconds)


def move_left(seconds: float = 0.6, speed: Optional[float] = None):
    left(seconds=seconds, speed=speed)


def move_right(seconds: float = 0.6, speed: Optional[float] = None):
    right(seconds=seconds, speed=speed)


def turn_left(seconds: float = 0.5, speed: Optional[float] = None):
    del speed
    _run_action('turn_left', seconds)


def turn_right(seconds: float = 0.5, speed: Optional[float] = None):
    del speed
    _run_action('turn_right', seconds)


def diagonal_left(seconds: float = 0.8, speed: Optional[float] = None):
    left(seconds=seconds * 0.5, speed=speed)
    forward(seconds=seconds * 0.5, speed=speed)


def diagonal_right(seconds: float = 0.8, speed: Optional[float] = None):
    right(seconds=seconds * 0.5, speed=speed)
    forward(seconds=seconds * 0.5, speed=speed)


def drift_left(seconds: float = 1.0, speed: Optional[float] = None, turn_blend: float = 0.55):
    del speed, turn_blend
    left(seconds=seconds * 0.6)
    turn_left(seconds=seconds * 0.4)


def drift_right(seconds: float = 1.0, speed: Optional[float] = None, turn_blend: float = 0.55):
    del speed, turn_blend
    right(seconds=seconds * 0.6)
    turn_right(seconds=seconds * 0.4)


def drive_for(vx: float, vy: float, seconds: float, speed: Optional[float] = None):
    del speed
    if abs(vx) >= abs(vy):
        if vx >= 0:
            forward(seconds=seconds)
        else:
            backward(seconds=seconds)
    else:
        if vy >= 0:
            right(seconds=seconds)
        else:
            left(seconds=seconds)


def horn(*_args, **_kwargs) -> bool:
    print('SpiderPi horn placeholder: use buzzer or classroom sound output.')
    return True


class RobotMoves:
    def __init__(self, base_speed: float = None, rate_hz: float = None):
        del base_speed, rate_hz

    def stop(self): stop()
    def emergency_stop(self): emergency_stop()
    def forward(self, seconds: float = 0.6, speed: Optional[float] = None): forward(seconds, speed)
    def backward(self, seconds: float = 0.6, speed: Optional[float] = None): backward(seconds, speed)
    def left(self, seconds: float = 0.6, speed: Optional[float] = None): left(seconds, speed)
    def right(self, seconds: float = 0.6, speed: Optional[float] = None): right(seconds, speed)
    def move_left(self, seconds: float = 0.6, speed: Optional[float] = None): move_left(seconds, speed)
    def move_right(self, seconds: float = 0.6, speed: Optional[float] = None): move_right(seconds, speed)
    def turn_left(self, seconds: float = 0.5, speed: Optional[float] = None): turn_left(seconds, speed)
    def turn_right(self, seconds: float = 0.5, speed: Optional[float] = None): turn_right(seconds, speed)
    def diagonal_left(self, seconds: float = 0.8, speed: Optional[float] = None): diagonal_left(seconds, speed)
    def diagonal_right(self, seconds: float = 0.8, speed: Optional[float] = None): diagonal_right(seconds, speed)
    def drift_left(self, seconds: float = 1.0, speed: Optional[float] = None, turn_blend: float = 0.55): drift_left(seconds, speed, turn_blend)
    def drift_right(self, seconds: float = 1.0, speed: Optional[float] = None, turn_blend: float = 0.55): drift_right(seconds, speed, turn_blend)
    def drive_for(self, vx: float, vy: float, seconds: float, speed: Optional[float] = None): drive_for(vx, vy, seconds, speed)
    def horn(self, *args, **kwargs): return horn(*args, **kwargs)
