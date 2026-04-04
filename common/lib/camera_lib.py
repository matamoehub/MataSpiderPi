#!/usr/bin/env python3
from __future__ import annotations

import time
from typing import Optional

from spiderpi_support import get_board
from arm_lib import LOOK, get_arm

HEAD_PITCH = 0
HEAD_DEFAULT_SECONDS = 0.00375
HEAD_MOTION_SECONDS = 0.32
HEAD_TILT_SERVO_ID = 24
HEAD_TILT_CENTER = 330
HEAD_TILT_DELTA = 90
HEAD_TILT_MIN = 80
HEAD_TILT_MAX = 700
HEAD_TURN_SERVO_ID = 21
HEAD_TURN_CENTER = 500
HEAD_TURN_DELTA = 90
HEAD_TURN_MIN = 200
HEAD_TURN_MAX = 800


class Camera:
    """
    SpiderPi "head" helper driven by the arm.

    The camera is fixed to the top of the arm, so camera movement-style methods
    are translated into expressive arm poses.
    """

    def __init__(self):
        self._arm = get_arm()
        self._board = get_board()
        self._turn_pulse = HEAD_TURN_CENTER
        self._tilt_pulse = HEAD_TILT_CENTER

    def _require_arm(self):
        if self._arm is None:
            raise RuntimeError("SpiderPi arm camera control unavailable")
        return self._arm

    def _require_board(self):
        if self._board is None:
            raise RuntimeError("SpiderPi board unavailable")
        return self._board

    def _move_head(self, x: float, y: float, z: float, seconds: float = HEAD_DEFAULT_SECONDS, pitch: float = HEAD_PITCH):
        arm = self._require_arm()
        return arm.move_to(x, y, z, pitch=pitch, movetime_ms=int(float(seconds) * 1000))

    def _set_servo(self, servo_id: int, pulse: int, seconds: float):
        board = self._require_board()
        board.bus_servo_set_position(float(seconds), [[int(servo_id), int(pulse)]])
        return {"servo": int(servo_id), "pulse": int(pulse), "seconds": float(seconds)}

    def _set_turn(self, pulse: int, seconds: float = HEAD_MOTION_SECONDS):
        self._turn_pulse = max(HEAD_TURN_MIN, min(HEAD_TURN_MAX, int(pulse)))
        return self._set_servo(HEAD_TURN_SERVO_ID, self._turn_pulse, seconds)

    def _set_tilt(self, pulse: int, seconds: float = HEAD_MOTION_SECONDS):
        self._tilt_pulse = max(HEAD_TILT_MIN, min(HEAD_TILT_MAX, int(pulse)))
        return self._set_servo(HEAD_TILT_SERVO_ID, self._tilt_pulse, seconds)

    def _yaw_delta(self, pos: int, center: int = 1500, max_delta: float = 16.0) -> float:
        ratio = max(-1.0, min(1.0, (float(pos) - float(center)) / 500.0))
        return ratio * max_delta

    def _pitch_delta(self, pos: int, center: int = 1500, max_delta: float = 18.0) -> float:
        ratio = max(-1.0, min(1.0, (float(pos) - float(center)) / 500.0))
        return ratio * max_delta

    def center_all(self, speed_s: Optional[float] = None):
        seconds = HEAD_DEFAULT_SECONDS if speed_s is None else float(speed_s)
        if seconds <= 0:
            result = self._require_arm().look_pose()
        else:
            result = self._move_head(*LOOK, seconds=seconds)
        self._set_turn(HEAD_TURN_CENTER, seconds=max(seconds, HEAD_MOTION_SECONDS))
        self._set_tilt(HEAD_TILT_CENTER, seconds=max(seconds, HEAD_MOTION_SECONDS))
        return result

    def set_pitch(self, pos: int, speed_s: Optional[float] = None):
        seconds = HEAD_DEFAULT_SECONDS if speed_s is None else float(speed_s)
        delta = int(self._pitch_delta(pos) * 8)
        return self._set_tilt(HEAD_TILT_CENTER + delta, seconds=max(seconds, HEAD_MOTION_SECONDS))

    def set_yaw(self, pos: int, speed_s: Optional[float] = None):
        seconds = HEAD_DEFAULT_SECONDS if speed_s is None else float(speed_s)
        delta = int(self._yaw_delta(pos) * 8)
        return self._set_turn(HEAD_TURN_CENTER + delta, seconds=max(seconds, HEAD_MOTION_SECONDS))

    def nod(self, depth: int = 300, speed_s: Optional[float] = None):
        seconds = HEAD_MOTION_SECONDS if speed_s is None else float(speed_s)
        delta = max(40, min(140, int(float(depth) / 3.0)))
        self._set_tilt(HEAD_TILT_CENTER + delta, seconds=seconds)
        self._set_tilt(HEAD_TILT_CENTER - delta, seconds=seconds)
        return self._set_tilt(HEAD_TILT_CENTER, seconds=seconds)

    def shake(self, width: int = 300, speed_s: Optional[float] = None):
        seconds = HEAD_MOTION_SECONDS if speed_s is None else float(speed_s)
        delta = max(40, min(140, int(float(width) / 3.0)))
        self._set_turn(HEAD_TURN_CENTER + delta, seconds=seconds)
        self._set_turn(HEAD_TURN_CENTER - delta, seconds=seconds)
        return self._set_turn(HEAD_TURN_CENTER, seconds=seconds)

    def wiggle(self, cycles: int = 2, amplitude: int = 200, speed_s: Optional[float] = None):
        seconds = max(0.04, HEAD_MOTION_SECONDS / 3.0) if speed_s is None else float(speed_s)
        delta = max(220, min(320, int(float(amplitude) * 4.5)))
        for _ in range(max(1, int(cycles))):
            self._set_turn(HEAD_TURN_CENTER + delta, seconds=seconds)
            self._set_turn(HEAD_TURN_CENTER - delta, seconds=seconds)
        return self._set_turn(HEAD_TURN_CENTER, seconds=seconds)

    def tiny_wiggle(self, seconds: float = 2.0, amplitude: int = 90, speed_s: float = 0.12):
        delta = max(20, min(80, int(float(amplitude))))
        step_s = max(0.08, float(speed_s))
        end = time.time() + float(seconds)
        while time.time() < end:
            self._set_turn(HEAD_TURN_CENTER + delta, seconds=step_s)
            self._set_turn(HEAD_TURN_CENTER - delta, seconds=step_s)
        return self._set_turn(HEAD_TURN_CENTER, seconds=step_s)

    def glance_left(self, amplitude: int = 250, hold_s: float = 0.15):
        delta = max(40, min(210, int(float(amplitude) * 0.75)))
        self._set_turn(HEAD_TURN_CENTER + delta, seconds=HEAD_MOTION_SECONDS)
        time.sleep(float(hold_s))
        return self._set_turn(HEAD_TURN_CENTER, seconds=HEAD_MOTION_SECONDS)

    def glance_right(self, amplitude: int = 250, hold_s: float = 0.15):
        delta = max(40, min(210, int(float(amplitude) * 0.75)))
        self._set_turn(HEAD_TURN_CENTER - delta, seconds=HEAD_MOTION_SECONDS)
        time.sleep(float(hold_s))
        return self._set_turn(HEAD_TURN_CENTER, seconds=HEAD_MOTION_SECONDS)

    def look_up(self, amplitude: int = 250, hold_s: float = 0.15):
        delta = max(40, min(140, int(float(amplitude) / 2.0)))
        self._set_tilt(HEAD_TILT_CENTER + delta, seconds=HEAD_MOTION_SECONDS)
        time.sleep(float(hold_s))
        return self._set_tilt(HEAD_TILT_CENTER, seconds=HEAD_MOTION_SECONDS)

    def look_down(self, amplitude: int = 250, hold_s: float = 0.15):
        delta = max(40, min(140, int(float(amplitude) / 2.0)))
        self._set_tilt(HEAD_TILT_CENTER - delta, seconds=HEAD_MOTION_SECONDS)
        time.sleep(float(hold_s))
        return self._set_tilt(HEAD_TILT_CENTER, seconds=HEAD_MOTION_SECONDS)


_CAM_SINGLETON: Optional[Camera] = None


def get_camera() -> Camera:
    global _CAM_SINGLETON
    if _CAM_SINGLETON is None:
        _CAM_SINGLETON = Camera()
    return _CAM_SINGLETON
