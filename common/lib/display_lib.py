#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import os
import subprocess
import time

from spiderpi_support import ensure_vendor_paths, get_board

ensure_vendor_paths()

try:
    import sensor.dot_matrix_sensor as dot_matrix_sensor
    _DOT_MATRIX_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover
    dot_matrix_sensor = None  # type: ignore[assignment]
    _DOT_MATRIX_IMPORT_ERROR = exc


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
    "test_left": [
        "1111111100000000",
        "1111111100000000",
        "1111111100000000",
        "1111111100000000",
        "1111111100000000",
        "1111111100000000",
        "1111111100000000",
        "1111111100000000",
    ],
    "test_right": [
        "0000000011111111",
        "0000000011111111",
        "0000000011111111",
        "0000000011111111",
        "0000000011111111",
        "0000000011111111",
        "0000000011111111",
        "0000000011111111",
    ],
    "test_top": [
        "1111111111111111",
        "1111111111111111",
        "1111111111111111",
        "1111111111111111",
        "0000000000000000",
        "0000000000000000",
        "0000000000000000",
        "0000000000000000",
    ],
    "test_bottom": [
        "0000000000000000",
        "0000000000000000",
        "0000000000000000",
        "0000000000000000",
        "1111111111111111",
        "1111111111111111",
        "1111111111111111",
        "1111111111111111",
    ],
    "test_diag_down": [
        "1000000000000000",
        "0100000000000000",
        "0010000000000000",
        "0001000000000000",
        "0000100000000000",
        "0000010000000000",
        "0000001000000000",
        "0000000100000000",
    ],
    "test_diag_up": [
        "0000000100000000",
        "0000001000000000",
        "0000010000000000",
        "0000100000000000",
        "0001000000000000",
        "0010000000000000",
        "0100000000000000",
        "1000000000000000",
    ],
}

_TM1640_CMD1 = 64
_TM1640_CMD2 = 192
_TM1640_CMD3 = 128
_TM1640_DSP_ON = 8
_TM1640_DELAY_US = 10
_SYSTEM_PYTHON = os.environ.get("MATA_SYSTEM_PYTHON", "/usr/bin/python3")
_VENDOR_SENSOR_SDK = os.environ.get("MATA_SPIDERPI_SENSOR_SDK", "/home/pi/spiderpi/spiderpi_sdk/sensor_sdk")


def _sleep_us(value: int):
    time.sleep(float(value) / 1_000_000.0)


def _normalize_vertical_buf(buf):
    rows = [str(item).strip() for item in buf]
    if not rows:
        return ["0" * 16] * 16
    width = max(len(row) for row in rows)
    if width <= 8:
        # The TM1640 buffer is 16 columns wide on SpiderPi. Center smaller
        # 8-column classroom icons so they do not render only on the left side.
        width = 16
    width = max(1, width)
    normalized = []
    for row in rows:
        bits = "".join("1" if ch == "1" else "0" for ch in row)
        if len(bits) > width:
            bits = bits[:width]
        pad_total = width - len(bits)
        pad_left = pad_total // 2
        pad_right = pad_total - pad_left
        normalized.append(("0" * pad_left) + bits + ("0" * pad_right))
    return normalized


def _matrix_subprocess(action: str, payload) -> dict:
    script = """
import json, os, sys
sys.path.insert(0, os.environ["MATA_SPIDERPI_SENSOR_SDK"])
import sensor.dot_matrix_sensor as DMS

tm = DMS.TM1640(dio=7, clk=8)
action = os.environ["MATA_MATRIX_ACTION"]
payload = json.loads(os.environ["MATA_MATRIX_PAYLOAD"])
tm.clear()
if action == "shape":
    tm.set_buf_vertical(payload)
elif action == "number":
    tm.set_number(payload)
elif action == "clear":
    tm.clear()
else:
    raise RuntimeError(f"Unknown matrix action: {action}")
if action != "clear":
    tm.update_display()
print(json.dumps({"ok": True, "action": action}))
"""
    proc = subprocess.run(
        [_SYSTEM_PYTHON, "-c", script],
        env={
            **os.environ,
            "PYTHONUNBUFFERED": "1",
            "MATA_SPIDERPI_SENSOR_SDK": _VENDOR_SENSOR_SDK,
            "MATA_MATRIX_ACTION": str(action),
            "MATA_MATRIX_PAYLOAD": json.dumps(payload),
        },
        input="",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd="/tmp",
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "matrix subprocess failed")
    out = (proc.stdout or "").strip().splitlines()
    if not out:
        return {"ok": True, "action": action}
    try:
        return json.loads(out[-1])
    except Exception:
        return {"ok": True, "action": action, "stdout": proc.stdout.strip()}


def _coerce_hold_seconds(seconds) -> float:
    if seconds is None:
        return 0.0
    return max(0.0, float(seconds))


class _MatrixDisplayCompat:
    digit_dict = {
        "0": 0x3F,
        "1": 0x06,
        "2": 0x5B,
        "3": 0x4F,
        "4": 0x66,
        "5": 0x6D,
        "6": 0x7D,
        "7": 0x07,
        "8": 0x7F,
        "9": 0x6F,
        ".": 0x80,
        "-": 0x40,
    }

    def __init__(self, clk: int, dio: int, brightness: int = 7):
        import gpiod  # type: ignore

        self.display_buf = [0] * 16
        self._brightness = max(0, min(7, int(brightness)))

        chip = None
        last_error = None
        candidates = [str(path) for path in sorted(Path("/dev").glob("gpiochip*"))]
        candidates.extend([path.split("/")[-1] for path in candidates])
        seen = set()
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            try:
                maybe_chip = self._open_chip(gpiod, candidate)
                maybe_clk = self._get_line(gpiod, maybe_chip, int(clk))
                maybe_dio = self._get_line(gpiod, maybe_chip, int(dio))
                self._request_output(gpiod, maybe_clk, "tm1640-clk")
                self._request_output(gpiod, maybe_dio, "tm1640-dio")
                self._chip = maybe_chip
                self.clk = maybe_clk
                self.dio = maybe_dio
                chip = maybe_chip
                break
            except Exception as exc:  # pragma: no cover - hardware-specific
                last_error = exc
                try:
                    maybe_clk.release()
                except Exception:
                    pass
                try:
                    maybe_dio.release()
                except Exception:
                    pass
                continue
        if chip is None:
            raise RuntimeError(
                "SpiderPi dot matrix display could not find a usable gpiochip device"
                + (f": {last_error}" if last_error else "")
            )

        self.clk.set_value(0)
        self.dio.set_value(0)
        _sleep_us(_TM1640_DELAY_US)
        self._write_data_cmd()
        self._write_dsp_ctrl()

    @staticmethod
    def _open_chip(gpiod, candidate: str):
        if hasattr(gpiod, "Chip"):
            return gpiod.Chip(candidate)
        if hasattr(gpiod, "chip"):
            # The older 1.x python gpiod API typically expects a chip name like
            # "gpiochip4" rather than a /dev path.
            if str(candidate).startswith("/dev/"):
                try:
                    return gpiod.chip(Path(candidate).name)
                except Exception:
                    pass
            return gpiod.chip(candidate)
        raise RuntimeError("Unsupported gpiod API: no Chip/chip constructor")

    @staticmethod
    def _get_line(gpiod, chip, offset: int):
        if hasattr(chip, "get_line"):
            return chip.get_line(int(offset))
        raise RuntimeError("Unsupported gpiod API: chip has no get_line()")

    @staticmethod
    def _request_output(gpiod, line, consumer: str):
        if hasattr(gpiod, "LINE_REQ_DIR_OUT"):
            line.request(consumer=str(consumer), type=gpiod.LINE_REQ_DIR_OUT)
            return
        if hasattr(gpiod, "line_request"):
            request = gpiod.line_request()
            request.consumer = str(consumer)
            request.request_type = gpiod.line_request.DIRECTION_OUTPUT
            line.request(request)
            return
        raise RuntimeError("Unsupported gpiod API: no output request mode available")

    def _start(self):
        self.dio.set_value(0)
        _sleep_us(_TM1640_DELAY_US)
        self.clk.set_value(0)
        _sleep_us(_TM1640_DELAY_US)

    def _stop(self):
        self.dio.set_value(0)
        _sleep_us(_TM1640_DELAY_US)
        self.clk.set_value(1)
        _sleep_us(_TM1640_DELAY_US)
        self.dio.set_value(1)

    def _write_byte(self, value: int):
        for i in range(8):
            self.dio.set_value((int(value) >> i) & 1)
            _sleep_us(_TM1640_DELAY_US)
            self.clk.set_value(1)
            _sleep_us(_TM1640_DELAY_US)
            self.clk.set_value(0)
            _sleep_us(_TM1640_DELAY_US)

    def _write_data_cmd(self):
        self._start()
        self._write_byte(_TM1640_CMD1)
        self._stop()

    def _write_dsp_ctrl(self):
        self._start()
        self._write_byte(_TM1640_CMD3 | _TM1640_DSP_ON | self._brightness)
        self._stop()

    def write(self, rows, pos: int = 0):
        self._write_data_cmd()
        self._start()
        self._write_byte(_TM1640_CMD2 | int(pos))
        for row in rows:
            self._write_byte(int(row))
        self._stop()
        self._write_dsp_ctrl()

    def clear(self):
        self.display_buf = [0] * 16
        self.update_display()

    def set_number(self, number):
        self.display_buf = [self.digit_dict["0"]] * 4
        num = list(str(number))
        num.reverse()
        for i in range(len(num)):
            self.display_buf[-i - 1] = self.digit_dict[num[i]]
            if num[i] == ".":
                self.display_buf[-i - 2] = self.digit_dict[num[i - 1]] + self.digit_dict["."]

    def set_buf_vertical(self, buf):
        self.display_buf = [int(item, 2) for item in buf]

    def update_display(self):
        self.write(self.display_buf)


class Display:
    """
    Friendly text and dot-matrix display helper.
    """

    def __init__(self):
        self._board = get_board()
        self._matrix = None
        self._last_matrix_fallback = None

    def _require_board(self):
        if self._board is None:
            raise RuntimeError("SpiderPi OLED display is unavailable")
        return self._board

    def _oled_write(self, line: int, text: str):
        board = self._require_board()
        # Vendor SDK comments indicate the OLED payload length should include
        # the string terminator, so send one explicitly.
        board.set_oled_text(int(line), str(text)[:20] + "\0")

    def _matrix_display(self):
        if self._matrix is None:
            errors = []
            if dot_matrix_sensor is not None:
                try:
                    self._matrix = dot_matrix_sensor.TM1640(dio=7, clk=8)
                    return self._matrix
                except Exception as exc:
                    errors.append(f"vendor TM1640 failed: {exc}")
            else:
                if _DOT_MATRIX_IMPORT_ERROR:
                    errors.append(str(_DOT_MATRIX_IMPORT_ERROR))
            try:
                self._matrix = _MatrixDisplayCompat(dio=7, clk=8)
            except Exception as exc:
                errors.append(f"compat TM1640 failed: {exc}")
                raise RuntimeError(
                    "SpiderPi dot matrix display is unavailable"
                    + (": " + " | ".join(errors) if errors else "")
                ) from exc
        return self._matrix

    def _matrix_fallback_text(self, *lines: str):
        board = self._require_board()
        padded = list(lines[:4]) + [""] * max(0, 4 - len(lines))
        for index, text in enumerate(padded[:4], start=1):
            self._oled_write(index, str(text)[:20])
        self._last_matrix_fallback = [str(item)[:20] for item in padded[:4]]
        return {
            "fallback": "oled_text",
            "lines": self._last_matrix_fallback,
            "dot_matrix_available": False,
            "dot_matrix_error": str(_DOT_MATRIX_IMPORT_ERROR) if _DOT_MATRIX_IMPORT_ERROR else None,
        }

    def _console_echo(self, *lines: str):
        rendered = [str(item)[:20] for item in list(lines[:4]) + [""] * max(0, 4 - len(lines))]
        print("[display]", " | ".join(x for x in rendered if x))
        return rendered

    def text(self, line1: str = "", line2: str = "", line3: str = "", line4: str = ""):
        lines = [line1, line2, line3, line4]
        echoed = self._console_echo(*lines)
        try:
            for index, text in enumerate(lines, start=1):
                self._oled_write(index, str(text)[:20])
            return {"lines": lines, "console_echo": echoed}
        except Exception as exc:
            return {"lines": lines, "console_echo": echoed, "display_error": str(exc)}

    def line(self, line_number: int, text: str):
        rendered = self._console_echo(f"Line {int(line_number)}", str(text)[:20])
        try:
            self._oled_write(int(line_number), str(text)[:20])
            return {"line": int(line_number), "text": str(text)[:20], "console_echo": rendered}
        except Exception as exc:
            return {"line": int(line_number), "text": str(text)[:20], "console_echo": rendered, "display_error": str(exc)}

    def number(self, value: int | float, seconds: float | None = None):
        try:
            print(f"[display] matrix number -> value={value!r} seconds={seconds!r} via system-python")
            result = _matrix_subprocess("number", value)
            result["number"] = value
            hold_s = _coerce_hold_seconds(seconds)
            if hold_s > 0:
                time.sleep(hold_s)
                _matrix_subprocess("clear", None)
                result["hold_seconds"] = hold_s
            return result
        except Exception as exc:
            print(f"[display] matrix number fallback -> value={value!r} error={exc}")
            result = self._matrix_fallback_text("Number", str(value), "", "")
            result["number"] = value
            result["dot_matrix_error"] = str(exc)
            return result

    def clear_matrix(self):
        try:
            print("[display] matrix clear via system-python")
            return _matrix_subprocess("clear", None)
        except Exception as exc:
            print(f"[display] matrix clear fallback -> error={exc}")
            result = self._matrix_fallback_text("", "", "", "")
            result["matrix"] = "cleared_via_oled"
            result["dot_matrix_error"] = str(exc)
            return result

    def shape(self, name: str = "smile", seconds: float | None = None):
        key = str(name).strip().lower()
        if key not in _SHAPES:
            raise ValueError(f"Unknown shape: {name}")
        try:
            print(f"[display] matrix shape -> name={key!r} seconds={seconds!r} via system-python")
            result = _matrix_subprocess("shape", _normalize_vertical_buf(_SHAPES[key]))
            result["shape"] = key
            hold_s = _coerce_hold_seconds(seconds)
            if hold_s > 0:
                time.sleep(hold_s)
                _matrix_subprocess("clear", None)
                result["hold_seconds"] = hold_s
            return result
        except Exception as exc:
            print(f"[display] matrix shape fallback -> name={key!r} error={exc}")
            result = self._matrix_fallback_text("Shape", key.title(), "", "")
            result["shape"] = key
            result["dot_matrix_error"] = str(exc)
            return result

    def smile(self, seconds: float | None = None):
        return self.shape("smile", seconds=seconds)

    def triangle(self, seconds: float | None = None):
        return self.shape("triangle", seconds=seconds)

    def square(self, seconds: float | None = None):
        return self.shape("square", seconds=seconds)

    def diamond(self, seconds: float | None = None):
        return self.shape("diamond", seconds=seconds)


def get_display() -> Display:
    return Display()
