#!/usr/bin/env python3
from __future__ import annotations

from spiderpi_support import ensure_vendor_paths, get_board

ensure_vendor_paths()

try:
    import sensor.dot_matrix_sensor as dot_matrix_sensor
except Exception:  # pragma: no cover
    dot_matrix_sensor = None  # type: ignore[assignment]


_SHAPES = {
    "triangle": [
        "0000000010000000",
        "0000000111000000",
        "0000001111100000",
        "0000011111110000",
        "0000111111111000",
        "0001111111111100",
        "0011111111111110",
        "0111111111111111",
    ],
    "square": [
        "11111111",
        "10000001",
        "10000001",
        "10000001",
        "10000001",
        "10000001",
        "10000001",
        "11111111",
    ],
    "diamond": [
        "00011000",
        "00111100",
        "01111110",
        "11111111",
        "11111111",
        "01111110",
        "00111100",
        "00011000",
    ],
    "smile": [
        "00111100",
        "01000010",
        "10100101",
        "10000001",
        "10100101",
        "10011001",
        "01000010",
        "00111100",
    ],
}


class Display:
    """
    Friendly text and dot-matrix display helper.
    """

    def __init__(self):
        self._board = get_board()
        self._matrix = None

    def _require_board(self):
        if self._board is None:
            raise RuntimeError("SpiderPi OLED display is unavailable")
        return self._board

    def _matrix_display(self):
        if self._matrix is None:
            if dot_matrix_sensor is None:
                raise RuntimeError("SpiderPi dot matrix display is unavailable")
            self._matrix = dot_matrix_sensor.TM1640(dio=7, clk=8)
        return self._matrix

    def text(self, line1: str = "", line2: str = "", line3: str = "", line4: str = ""):
        board = self._require_board()
        lines = [line1, line2, line3, line4]
        for index, text in enumerate(lines, start=1):
            board.set_oled_text(index, str(text)[:20])
        return {"lines": lines}

    def line(self, line_number: int, text: str):
        board = self._require_board()
        board.set_oled_text(int(line_number), str(text)[:20])
        return {"line": int(line_number), "text": str(text)[:20]}

    def number(self, value: int | float):
        display = self._matrix_display()
        display.set_number(value)
        display.update_display()
        return {"number": value}

    def clear_matrix(self):
        display = self._matrix_display()
        display.clear()
        return {"matrix": "cleared"}

    def shape(self, name: str = "smile"):
        key = str(name).strip().lower()
        if key not in _SHAPES:
            raise ValueError(f"Unknown shape: {name}")
        display = self._matrix_display()
        display.set_buf_vertical(_SHAPES[key])
        display.update_display()
        return {"shape": key}

    def smile(self):
        return self.shape("smile")

    def triangle(self):
        return self.shape("triangle")

    def square(self):
        return self.shape("square")

    def diamond(self):
        return self.shape("diamond")


def get_display() -> Display:
    return Display()
