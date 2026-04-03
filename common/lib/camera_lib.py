#!/usr/bin/env python3
from __future__ import annotations

import time
from typing import Optional

from arm_lib import LOOK, get_arm

HEAD_PITCH = 0
HEAD_DEFAULT_SECONDS = 0.03
HEAD_MOTION_SECONDS = 0.035


class Camera:
    """
    SpiderPi "head" helper driven by the arm.

    The camera is fixed to the top of the arm, so camera movement-style methods
    are translated into expressive arm poses.
    """

    def __init__(self):
        self._arm = get_arm()

    def _require_arm(self):
        if self._arm is None:
            raise RuntimeError("SpiderPi arm camera control unavailable")
        return self._arm

    def _move_head(self, x: float, y: float, z: float, seconds: float = HEAD_DEFAULT_SECONDS, pitch: float = HEAD_PITCH):
        arm = self._require_arm()
        return arm.move_to(x, y, z, pitch=pitch, movetime_ms=int(float(seconds) * 1000))

    def _yaw_delta(self, pos: int, center: int = 1500, max_delta: float = 6.0) -> float:
        ratio = max(-1.0, min(1.0, (float(pos) - float(center)) / 500.0))
        return ratio * max_delta

    def _pitch_delta(self, pos: int, center: int = 1500, max_delta: float = 8.0) -> float:
        ratio = max(-1.0, min(1.0, (float(pos) - float(center)) / 500.0))
        return ratio * max_delta

    def center_all(self, speed_s: Optional[float] = None):
        seconds = HEAD_DEFAULT_SECONDS if speed_s is None else float(speed_s)
        return self._require_arm().look_pose() if seconds <= 0 else self._move_head(*LOOK, seconds=seconds)

    def set_pitch(self, pos: int, speed_s: Optional[float] = None):
        x, y, z = LOOK
        dz = self._pitch_delta(pos)
        seconds = HEAD_DEFAULT_SECONDS if speed_s is None else float(speed_s)
        return self._move_head(x, y, z + dz, seconds=seconds)

    def set_yaw(self, pos: int, speed_s: Optional[float] = None):
        x, y, z = LOOK
        dx = self._yaw_delta(pos)
        seconds = HEAD_DEFAULT_SECONDS if speed_s is None else float(speed_s)
        return self._move_head(x + dx, y, z, seconds=seconds)

    def nod(self, depth: int = 300, speed_s: Optional[float] = None):
        x, y, z = LOOK
        dz = max(2.0, min(8.0, float(depth) / 60.0))
        seconds = HEAD_MOTION_SECONDS if speed_s is None else float(speed_s)
        self._move_head(x, y, z + dz, seconds=seconds)
        self._move_head(x, y, z - dz, seconds=seconds)
        return self._move_head(x, y, z, seconds=seconds)

    def shake(self, width: int = 300, speed_s: Optional[float] = None):
        x, y, z = LOOK
        dx = max(2.0, min(6.0, float(width) / 80.0))
        seconds = HEAD_MOTION_SECONDS if speed_s is None else float(speed_s)
        self._move_head(x - dx, y, z, seconds=seconds)
        self._move_head(x + dx, y, z, seconds=seconds)
        return self._move_head(x, y, z, seconds=seconds)

    def wiggle(self, cycles: int = 2, amplitude: int = 200, speed_s: Optional[float] = None):
        x, y, z = LOOK
        dx = max(1.5, min(5.0, float(amplitude) / 70.0))
        seconds = HEAD_MOTION_SECONDS if speed_s is None else float(speed_s)
        for _ in range(max(1, int(cycles))):
            self._move_head(x - dx, y, z, seconds=seconds)
            self._move_head(x + dx, y, z, seconds=seconds)
        return self._move_head(x, y, z, seconds=seconds)

    def tiny_wiggle(self, seconds: float = 2.0, amplitude: int = 90, speed_s: float = 0.12):
        x, y, z = LOOK
        dx = max(1.0, min(3.0, float(amplitude) / 80.0))
        step_s = max(0.08, float(speed_s))
        end = time.time() + float(seconds)
        while time.time() < end:
            self._move_head(x - dx, y, z, seconds=step_s)
            self._move_head(x + dx, y, z, seconds=step_s)
        return self._move_head(x, y, z, seconds=step_s)

    def glance_left(self, amplitude: int = 250, hold_s: float = 0.15):
        x, y, z = LOOK
        dx = max(2.0, min(6.0, float(amplitude) / 80.0))
        self._move_head(x - dx, y, z, seconds=HEAD_MOTION_SECONDS)
        time.sleep(float(hold_s))
        return self._move_head(x, y, z, seconds=HEAD_MOTION_SECONDS)

    def glance_right(self, amplitude: int = 250, hold_s: float = 0.15):
        x, y, z = LOOK
        dx = max(2.0, min(6.0, float(amplitude) / 80.0))
        self._move_head(x + dx, y, z, seconds=HEAD_MOTION_SECONDS)
        time.sleep(float(hold_s))
        return self._move_head(x, y, z, seconds=HEAD_MOTION_SECONDS)

    def look_up(self, amplitude: int = 250, hold_s: float = 0.15):
        x, y, z = LOOK
        dz = max(2.0, min(8.0, float(amplitude) / 70.0))
        self._move_head(x, y, z + dz, seconds=HEAD_MOTION_SECONDS)
        time.sleep(float(hold_s))
        return self._move_head(x, y, z, seconds=HEAD_MOTION_SECONDS)

    def look_down(self, amplitude: int = 250, hold_s: float = 0.15):
        x, y, z = LOOK
        dz = max(2.0, min(8.0, float(amplitude) / 70.0))
        self._move_head(x, y, z - dz, seconds=HEAD_MOTION_SECONDS)
        time.sleep(float(hold_s))
        return self._move_head(x, y, z, seconds=HEAD_MOTION_SECONDS)


_CAM_SINGLETON: Optional[Camera] = None


def get_camera() -> Camera:
    global _CAM_SINGLETON
    if _CAM_SINGLETON is None:
        _CAM_SINGLETON = Camera()
    return _CAM_SINGLETON
