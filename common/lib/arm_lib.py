#!/usr/bin/env python3
from __future__ import annotations

from spiderpi_support import get_arm_ik, get_board

GRIPPER_OPEN = 120
GRIPPER_MID = 360
GRIPPER_CLOSED = 600
# Default SpiderPi arm poses tuned against the real robot:
# - HOME should be a compact centered rest position
# - LOOK should keep the camera centered and more upright
# - CARRY/PLACE should remain lower utility poses for pick-and-place
HOME = (0, 12, 22)
LOOK = (0, 10, 34)
CARRY = (0, 15, 14)
PLACE = (8, 16, 5)
POSE_MOVETIME_MS = 125


class Arm:
    def __init__(self):
        self._ik = get_arm_ik()
        self._board = get_board()

    def _require_ik(self):
        if self._ik is None:
            raise RuntimeError('SpiderPi arm IK unavailable')
        return self._ik

    def _set_gripper(self, pulse: int, movetime_ms: int = 500):
        if self._board is None:
            raise RuntimeError('SpiderPi board unavailable')
        self._board.bus_servo_set_position(float(movetime_ms) / 1000.0, [[25, int(pulse)]])

    def open_gripper(self):
        self._set_gripper(GRIPPER_OPEN)
        return {"gripper": "open"}

    def set_gripper(self, pulse: int, movetime_ms: int = 500):
        pulse = max(GRIPPER_OPEN, min(GRIPPER_CLOSED, int(pulse)))
        self._set_gripper(pulse, movetime_ms=movetime_ms)
        return {"gripper": "custom", "pulse": pulse}

    def half_open_gripper(self):
        return self.set_gripper(GRIPPER_MID)

    def close_gripper(self):
        self._set_gripper(GRIPPER_CLOSED)
        return {"gripper": "closed"}

    def move_to(self, x: float, y: float, z: float, pitch: float = -90, min_pitch: float = -90, max_pitch: float = 100, movetime_ms: int = 1000):
        ik = self._require_ik()
        return ik.setPitchRangeMoving((float(x), float(y), float(z)), float(pitch), float(min_pitch), float(max_pitch), int(movetime_ms))

    def move(self, x: float, y: float, z: float, seconds: float = 1.0):
        return self.move_to(x, y, z, movetime_ms=int(float(seconds) * 1000))

    def home(self):
        return self.move_to(*HOME, movetime_ms=POSE_MOVETIME_MS)

    def look_pose(self):
        return self.move_to(*LOOK, pitch=0, movetime_ms=POSE_MOVETIME_MS)

    def carry_pose(self):
        return self.move_to(*CARRY, movetime_ms=POSE_MOVETIME_MS)

    def place_pose(self):
        return self.move_to(*PLACE, movetime_ms=POSE_MOVETIME_MS)

    def ready(self):
        return self.home()

    def open(self):
        return self.open_gripper()

    def close(self):
        return self.close_gripper()

    def set_grip(self, pulse: int, seconds: float = 0.5):
        return self.set_gripper(pulse, movetime_ms=int(float(seconds) * 1000))

    def half_open(self):
        return self.half_open_gripper()

    def look(self):
        return self.look_pose()

    def carry(self):
        return self.carry_pose()

    def place(self):
        return self.place_pose()

    def lift(self, height: float = 6.0):
        x, y, z = CARRY
        return self.move_to(x, y, z + float(height))

    def lower(self, height: float = 3.0):
        x, y, z = PLACE
        return self.move_to(x, y, max(0.0, z - float(height)))

    def pick(self, x: float, y: float, z: float):
        self.open_gripper()
        self.move_to(x, y, z + 4)
        self.move_to(x, y, z)
        self.close_gripper()
        return self.move_to(x, y, z + 6)

    def grab_at(self, x: float, y: float, z: float):
        return self.pick(x, y, z)


def get_arm() -> Arm:
    return Arm()
