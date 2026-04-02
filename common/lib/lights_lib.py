#!/usr/bin/env python3
from __future__ import annotations

from spiderpi_support import ensure_vendor_paths, get_board

ensure_vendor_paths()

try:
    from sensor.ultrasonic_sensor import Ultrasonic
except Exception:  # pragma: no cover
    Ultrasonic = None  # type: ignore[assignment]


def _clamp(value: int) -> int:
    return max(0, min(255, int(value)))


class Lights:
    """
    Simple LED helper for SpiderPi.

    Supports:
    - the robot controller RGB LEDs
    - the ultrasonic module's two RGB eyes
    """

    def __init__(self):
        self._board = get_board()
        self._ultrasonic = Ultrasonic() if Ultrasonic is not None else None

    def _rgb(self, r: int, g: int, b: int) -> tuple[int, int, int]:
        return (_clamp(r), _clamp(g), _clamp(b))

    def robot(self, r: int, g: int, b: int):
        if self._board is None:
            raise RuntimeError("SpiderPi board RGB control unavailable")
        r, g, b = self._rgb(r, g, b)
        self._board.set_rgb([[1, r, g, b], [2, r, g, b]])
        return {"target": "robot", "rgb": [r, g, b]}

    def sonar(self, r: int, g: int, b: int):
        if self._ultrasonic is None:
            raise RuntimeError("SpiderPi ultrasonic RGB control unavailable")
        r, g, b = self._rgb(r, g, b)
        self._ultrasonic.setRGBMode(0)
        self._ultrasonic.setRGB(0, (r, g, b))
        self._ultrasonic.setRGB(1, (r, g, b))
        return {"target": "sonar", "rgb": [r, g, b]}

    def all(self, r: int, g: int, b: int):
        result = {"rgb": list(self._rgb(r, g, b))}
        try:
            result["robot"] = self.robot(r, g, b)
        except Exception as exc:
            result["robot_error"] = str(exc)
        try:
            result["sonar"] = self.sonar(r, g, b)
        except Exception as exc:
            result["sonar_error"] = str(exc)
        return result

    def off(self):
        return self.all(0, 0, 0)

    def red(self):
        return self.all(255, 0, 0)

    def green(self):
        return self.all(0, 255, 0)

    def blue(self):
        return self.all(0, 0, 255)

    def yellow(self):
        return self.all(255, 200, 0)

    def purple(self):
        return self.all(180, 0, 255)


def get_lights() -> Lights:
    return Lights()
