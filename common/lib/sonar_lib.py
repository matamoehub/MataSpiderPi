#!/usr/bin/env python3
from __future__ import annotations

import time
from collections import deque
from statistics import mean
from typing import Deque, Optional

from ros_service_client import clear_process_singleton, get_process_singleton, set_process_singleton
from spiderpi_support import ensure_vendor_paths

ensure_vendor_paths()

try:
    from sensor.ultrasonic_sensor import Ultrasonic
except Exception as exc:  # pragma: no cover
    Ultrasonic = None  # type: ignore[assignment]
    _ULTRASONIC_IMPORT_ERROR = exc
else:
    _ULTRASONIC_IMPORT_ERROR = None


class Sonar:
    def __init__(self, window: int = 5):
        if Ultrasonic is None:
            hint = ""
            if "smbus2" in str(_ULTRASONIC_IMPORT_ERROR):
                hint = (
                    " Install the I2C dependency in the robot/Jupyter environment with: "
                    "python -m pip install smbus2"
                )
            raise RuntimeError(
                f"SpiderPi ultrasonic sensor is unavailable: {_ULTRASONIC_IMPORT_ERROR}.{hint}"
            )
        self.window = max(1, int(window))
        self._sensor = Ultrasonic()
        self._samples: Deque[int] = deque(maxlen=self.window)
        self._last_mm: Optional[int] = None
        self._last_at: Optional[float] = None

    def _read_mm(self) -> int:
        value = int(self._sensor.getDistance())
        self._last_mm = value
        self._last_at = time.time()
        self._samples.append(value)
        return value

    def has_reading(self) -> bool:
        return self._last_mm is not None

    def wait_for_reading(self, timeout_s: float = 2.0) -> int:
        end = time.time() + float(timeout_s)
        while time.time() < end:
            value = self._read_mm()
            if value > 0:
                return value
            time.sleep(0.05)
        raise TimeoutError(f"No sonar reading received within {timeout_s}s")

    def get_distance_mm(self, filtered: bool = False) -> int:
        value = self._read_mm()
        if filtered and self._samples:
            return int(round(float(mean(self._samples))))
        return value

    def get_distance_cm(self, filtered: bool = False) -> int:
        value = self.get_distance_mm(filtered=filtered)
        return int(round(float(value) / 10.0))

    def is_closer_than(self, threshold_cm: float, filtered: bool = True) -> bool:
        value = self.get_distance_cm(filtered=filtered)
        return bool(value <= float(threshold_cm))

    @property
    def last_update_age_s(self) -> Optional[float]:
        if self._last_at is None:
            return None
        return max(0.0, time.time() - self._last_at)


def get_sonar(window: int = 5) -> Sonar:
    key = "sonar_lib:sonar"
    inst = get_process_singleton(key)
    if inst is None:
        inst = set_process_singleton(key, Sonar(window=window))
    return inst


def reset_sonar() -> None:
    clear_process_singleton("sonar_lib:sonar")
