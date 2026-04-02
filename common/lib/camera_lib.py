#!/usr/bin/env python3
from __future__ import annotations

import time
from typing import Optional

from spiderpi_support import get_board


class Camera:
    """
    SpiderPi camera pan/tilt helper using the vendor board SDK.

    PWM servo ids:
    - 1: pitch
    - 2: yaw
    """

    def __init__(
        self,
        pitch_id: int = 1,
        yaw_id: int = 2,
        center: int = 1500,
        speed_s: float = 0.20,
        min_pos: int = 1000,
        max_pos: int = 2000,
    ):
        self._board = get_board()
        self.pitch_id = int(pitch_id)
        self.yaw_id = int(yaw_id)
        self.center = int(center)
        self.speed_s = float(speed_s)
        self.min_pos = int(min_pos)
        self.max_pos = int(max_pos)

    def _require_board(self):
        if self._board is None:
            raise RuntimeError("SpiderPi board camera control unavailable")
        return self._board

    def _clamp(self, pos: int) -> int:
        return max(self.min_pos, min(self.max_pos, int(pos)))

    def _send(self, sid: int, pos: int, speed_s: Optional[float] = None):
        board = self._require_board()
        duration = float(self.speed_s if speed_s is None else speed_s)
        board.pwm_servo_set_position(duration, [[int(sid), self._clamp(pos)]])
        time.sleep(duration + 0.02)

    def center_all(self, speed_s: Optional[float] = None):
        self._send(self.pitch_id, self.center, speed_s)
        self._send(self.yaw_id, self.center, speed_s)

    def set_pitch(self, pos: int, speed_s: Optional[float] = None):
        self._send(self.pitch_id, pos, speed_s)

    def set_yaw(self, pos: int, speed_s: Optional[float] = None):
        self._send(self.yaw_id, pos, speed_s)

    def nod(self, depth: int = 300, speed_s: Optional[float] = None):
        c = self.center
        self.set_pitch(c + depth, speed_s)
        self.set_pitch(c - depth, speed_s)
        self.set_pitch(c, speed_s)

    def shake(self, width: int = 300, speed_s: Optional[float] = None):
        c = self.center
        self.set_yaw(c - width, speed_s)
        self.set_yaw(c + width, speed_s)
        self.set_yaw(c, speed_s)

    def wiggle(self, cycles: int = 2, amplitude: int = 200, speed_s: Optional[float] = None):
        c = self.center
        left = c - int(amplitude)
        right = c + int(amplitude)
        for _ in range(int(cycles)):
            self.set_yaw(left, speed_s)
            self.set_yaw(right, speed_s)
        self.set_yaw(c, speed_s)

    def tiny_wiggle(self, seconds: float = 2.0, amplitude: int = 90, speed_s: float = 0.12):
        end = time.time() + float(seconds)
        c = self.center
        left = c - int(amplitude)
        right = c + int(amplitude)
        while time.time() < end:
            self.set_yaw(left, speed_s)
            self.set_yaw(right, speed_s)
        self.set_yaw(c, speed_s)

    def glance_left(self, amplitude: int = 250, hold_s: float = 0.15):
        c = self.center
        self.set_yaw(c - int(amplitude))
        time.sleep(hold_s)
        self.set_yaw(c)

    def glance_right(self, amplitude: int = 250, hold_s: float = 0.15):
        c = self.center
        self.set_yaw(c + int(amplitude))
        time.sleep(hold_s)
        self.set_yaw(c)

    def look_up(self, amplitude: int = 250, hold_s: float = 0.15):
        c = self.center
        self.set_pitch(c + int(amplitude))
        time.sleep(hold_s)
        self.set_pitch(c)

    def look_down(self, amplitude: int = 250, hold_s: float = 0.15):
        c = self.center
        self.set_pitch(c - int(amplitude))
        time.sleep(hold_s)
        self.set_pitch(c)


_CAM_SINGLETON: Optional[Camera] = None


def get_camera() -> Camera:
    global _CAM_SINGLETON
    if _CAM_SINGLETON is None:
        _CAM_SINGLETON = Camera()
    return _CAM_SINGLETON
