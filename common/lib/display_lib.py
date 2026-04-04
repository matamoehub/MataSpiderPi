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


_EYE_SLOTS = (1, 6, 11)


def _plot_bits(rows: list[list[str]], row: int, start: int, bits: str) -> None:
    if row < 0 or row >= len(rows):
        return
    for offset, bit in enumerate(bits):
        col = start + offset
        if 0 <= col < len(rows[row]):
            rows[row][col] = bit


def _build_eye_rows(
    states: tuple[str, str, str],
    horizontal_shift: int = 0,
    vertical_shift: int = 0,
) -> list[str]:
    rows = [list("0" * 16) for _ in range(8)]
    open_pattern = ("010", "111", "111", "111", "010")
    closed_pattern = ("000", "000", "111", "000", "000")
    sleep_pattern = ("100", "010", "001")
    base_row = 1 + vertical_shift

    for eye_index, state in enumerate(states):
        start_col = _EYE_SLOTS[eye_index] + horizontal_shift
        if state == "open":
            for row_offset, bits in enumerate(open_pattern):
                _plot_bits(rows, base_row + row_offset, start_col, bits)
        elif state == "closed":
            for row_offset, bits in enumerate(closed_pattern):
                _plot_bits(rows, base_row + row_offset, start_col, bits)
        elif state == "sleep":
            for row_offset, bits in enumerate(sleep_pattern):
                _plot_bits(rows, base_row + 1 + row_offset, start_col, bits)

    return ["".join(row) for row in rows]


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
        "10011001",
        "10100101",
        "10000001",
        "10100101",
        "01000010",
        "00111100",
    ],
    "eyes": _build_eye_rows(("open", "open", "open")),
    "eyes_left": _build_eye_rows(("open", "open", "open"), horizontal_shift=-1),
    "eyes_right": _build_eye_rows(("open", "open", "open"), horizontal_shift=1),
    "eyes_up": _build_eye_rows(("open", "open", "open"), vertical_shift=-1),
    "eyes_down": _build_eye_rows(("open", "open", "open"), vertical_shift=1),
    "left_eye_closed": _build_eye_rows(("closed", "open", "open")),
    "center_eye_closed": _build_eye_rows(("open", "closed", "open")),
    "right_eye_closed": _build_eye_rows(("open", "open", "closed")),
    "left_eye_open": _build_eye_rows(("open", "closed", "closed")),
    "center_eye_open": _build_eye_rows(("closed", "open", "closed")),
    "right_eye_open": _build_eye_rows(("closed", "closed", "open")),
    "wink": _build_eye_rows(("closed", "open", "open")),
    "blink": _build_eye_rows(("closed", "closed", "closed")),
    "sleep": _build_eye_rows(("sleep", "sleep", "sleep")),
    "shut_eyes": _build_eye_rows(("closed", "closed", "closed")),
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

_FONT_3X5 = {
    " ": ["000", "000", "000", "000", "000"],
    "!": ["010", "010", "010", "000", "010"],
    "-": ["000", "000", "111", "000", "000"],
    ".": ["000", "000", "000", "000", "010"],
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"],
    "7": ["111", "001", "001", "001", "001"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
    "A": ["111", "101", "111", "101", "101"],
    "B": ["110", "101", "110", "101", "110"],
    "C": ["111", "100", "100", "100", "111"],
    "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "111", "100", "111"],
    "F": ["111", "100", "111", "100", "100"],
    "G": ["111", "100", "101", "101", "111"],
    "H": ["101", "101", "111", "101", "101"],
    "I": ["111", "010", "010", "010", "111"],
    "J": ["001", "001", "001", "101", "111"],
    "K": ["101", "101", "110", "101", "101"],
    "L": ["100", "100", "100", "100", "111"],
    "M": ["101", "111", "111", "101", "101"],
    "N": ["101", "111", "111", "111", "101"],
    "O": ["111", "101", "101", "101", "111"],
    "P": ["111", "101", "111", "100", "100"],
    "Q": ["111", "101", "101", "111", "001"],
    "R": ["110", "101", "110", "101", "101"],
    "S": ["111", "100", "111", "001", "111"],
    "T": ["111", "010", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "111"],
    "V": ["101", "101", "101", "101", "010"],
    "W": ["101", "101", "111", "111", "101"],
    "X": ["101", "101", "010", "101", "101"],
    "Y": ["101", "101", "010", "010", "010"],
    "Z": ["111", "001", "010", "100", "111"],
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
        return ["0" * 8] * 16
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
    # SpiderPi's TM1640 path expects a 16-column vertical buffer. Our classroom
    # shapes are authored as 8 rows x 16 columns, so transpose them into
    # 16 entries of 8 bits each before sending to set_buf_vertical().
    height = len(normalized)
    transposed = []
    for x in range(width):
        col = []
        for y in range(height):
            col.append(normalized[y][x])
        transposed.append("".join(col))
    return transposed


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


def _matrix_text_rows(text: str) -> list[str]:
    value = str(text or "").upper()
    chars = [ch for ch in value if ch in _FONT_3X5]
    if not chars:
        chars = [" "]
    rows5 = [""] * 5
    for idx, ch in enumerate(chars):
        glyph = _FONT_3X5.get(ch, _FONT_3X5[" "])
        for y in range(5):
            rows5[y] += glyph[y]
            if idx != len(chars) - 1:
                rows5[y] += "0"
    width = min(16, max(len(r) for r in rows5))
    rows8 = ["0" * width]
    for row in rows5:
        rows8.append(row[:width].ljust(width, "0"))
    rows8.extend(["0" * width, "0" * width])
    visible = [r[:16].ljust(16, "0") for r in rows8[:8]]
    # The SpiderPi matrix is vertically flipped relative to the simple 3x5 font.
    visible.reverse()
    return visible


def _matrix_text_frames(text: str) -> list[list[str]]:
    value = str(text or "").upper()
    chars = [ch for ch in value if ch in _FONT_3X5]
    if not chars:
        chars = [" "]
    rows5 = [""] * 5
    for idx, ch in enumerate(chars):
        glyph = _FONT_3X5.get(ch, _FONT_3X5[" "])
        for y in range(5):
            rows5[y] += glyph[y]
            rows5[y] += "0"
    padded = ["0" * 16 + row + "0" * 16 for row in rows5]
    frames = []
    total_width = max(len(row) for row in padded)
    for start in range(0, max(1, total_width - 16 + 1)):
        frame5 = [row[start:start + 16].ljust(16, "0") for row in padded]
        frame8 = ["0" * 16] + frame5 + ["0" * 16, "0" * 16]
        frame8.reverse()
        frames.append(frame8[:8])
    return frames


def _show_matrix_text(text: str, seconds: float | None = None) -> dict:
    hold_s = _coerce_hold_seconds(seconds)
    value = str(text or "").strip()
    if not value:
        return _matrix_subprocess("clear", None)
    chars = [ch for ch in value.upper() if ch in _FONT_3X5]
    if len(chars) <= 4:
        result = _matrix_subprocess("shape", _normalize_vertical_buf(_matrix_text_rows(value)))
        if hold_s > 0:
            time.sleep(hold_s)
            _matrix_subprocess("clear", None)
            result["hold_seconds"] = hold_s
        return result

    frames = _matrix_text_frames(value)
    frame_delay = 0.0225
    if hold_s > 0 and frames:
        frame_delay = max(0.01, hold_s / len(frames))
    for frame in frames:
        _matrix_subprocess("shape", _normalize_vertical_buf(frame))
        time.sleep(frame_delay)
    _matrix_subprocess("clear", None)
    return {"ok": True, "action": "text_scroll", "frames": len(frames), "frame_delay": frame_delay}


def _first_visible_text(lines) -> str:
    for line in lines:
        value = str(line or "").strip()
        if value:
            return value
    return ""


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

    def text(self, line1: str = "", line2: str = "", line3: str = "", line4: str = "", seconds: float | None = None):
        lines = [line1, line2, line3, line4]
        echoed = self._console_echo(*lines)
        visible = _first_visible_text(lines)
        matrix_result = None
        if visible:
            try:
                print(f"[display] matrix text -> text={visible!r} seconds={seconds!r} via system-python")
                matrix_result = _show_matrix_text(visible, seconds=seconds)
            except Exception as exc:
                print(f"[display] matrix text fallback -> text={visible!r} error={exc}")
                matrix_result = {"matrix_text_error": str(exc), "visible_text": visible}
        try:
            for index, text in enumerate(lines, start=1):
                self._oled_write(index, str(text)[:20])
            result = {"lines": lines, "console_echo": echoed}
            if matrix_result is not None:
                result["matrix"] = matrix_result
            return result
        except Exception as exc:
            result = {"lines": lines, "console_echo": echoed, "display_error": str(exc)}
            if matrix_result is not None:
                result["matrix"] = matrix_result
            return result

    def line(self, line_number: int, text: str, seconds: float | None = None):
        rendered = self._console_echo(f"Line {int(line_number)}", str(text)[:20])
        matrix_result = None
        value = str(text)[:20]
        if value.strip():
            try:
                print(f"[display] matrix line -> line={int(line_number)} text={value!r} seconds={seconds!r} via system-python")
                matrix_result = _show_matrix_text(value, seconds=seconds)
            except Exception as exc:
                print(f"[display] matrix line fallback -> line={int(line_number)} text={value!r} error={exc}")
                matrix_result = {"matrix_text_error": str(exc), "visible_text": value}
        try:
            self._oled_write(int(line_number), value)
            result = {"line": int(line_number), "text": value, "console_echo": rendered}
            if matrix_result is not None:
                result["matrix"] = matrix_result
            return result
        except Exception as exc:
            result = {"line": int(line_number), "text": value, "console_echo": rendered, "display_error": str(exc)}
            if matrix_result is not None:
                result["matrix"] = matrix_result
            return result

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

    def _play_shapes(
        self,
        names: list[str],
        frame_seconds: float = 0.18,
        final_hold_seconds: float = 0.0,
    ):
        result = None
        for index, name in enumerate(names):
            hold = frame_seconds
            if index == len(names) - 1 and final_hold_seconds > 0:
                hold = final_hold_seconds
            result = self.shape(name, seconds=hold)
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

    def eyes(self, seconds: float | None = None):
        return self.shape("eyes", seconds=seconds)

    def look_left(self, seconds: float | None = None):
        return self.shape("eyes_left", seconds=seconds)

    def look_right(self, seconds: float | None = None):
        return self.shape("eyes_right", seconds=seconds)

    def look_up(self, seconds: float | None = None):
        return self.shape("eyes_up", seconds=seconds)

    def look_down(self, seconds: float | None = None):
        return self.shape("eyes_down", seconds=seconds)

    def left_wink(self, seconds: float | None = None):
        hold_s = _coerce_hold_seconds(seconds)
        return self._play_shapes(["eyes", "left_eye_closed", "eyes"], frame_seconds=0.16, final_hold_seconds=hold_s)

    def center_wink(self, seconds: float | None = None):
        hold_s = _coerce_hold_seconds(seconds)
        return self._play_shapes(["eyes", "center_eye_closed", "eyes"], frame_seconds=0.16, final_hold_seconds=hold_s)

    def right_wink(self, seconds: float | None = None):
        hold_s = _coerce_hold_seconds(seconds)
        return self._play_shapes(["eyes", "right_eye_closed", "eyes"], frame_seconds=0.16, final_hold_seconds=hold_s)

    def close_left_eye(self, seconds: float | None = None):
        return self.shape("left_eye_closed", seconds=seconds)

    def close_center_eye(self, seconds: float | None = None):
        return self.shape("center_eye_closed", seconds=seconds)

    def close_right_eye(self, seconds: float | None = None):
        return self.shape("right_eye_closed", seconds=seconds)

    def open_left_eye(self, seconds: float | None = None):
        return self.shape("left_eye_open", seconds=seconds)

    def open_center_eye(self, seconds: float | None = None):
        return self.shape("center_eye_open", seconds=seconds)

    def open_right_eye(self, seconds: float | None = None):
        return self.shape("right_eye_open", seconds=seconds)

    def wink(self, seconds: float | None = None):
        return self.left_wink(seconds=seconds)

    def blink(self, seconds: float | None = None):
        hold_s = _coerce_hold_seconds(seconds)
        return self._play_shapes(["eyes", "blink", "eyes"], frame_seconds=0.12, final_hold_seconds=hold_s)

    def sleep(self, seconds: float | None = None):
        hold_s = _coerce_hold_seconds(seconds)
        return self._play_shapes(["eyes", "blink", "shut_eyes", "sleep"], frame_seconds=0.16, final_hold_seconds=hold_s or 0.5)

    def shut_eyes(self, seconds: float | None = None):
        return self.shape("shut_eyes", seconds=seconds)

    def wake_up(self, seconds: float | None = None):
        hold_s = _coerce_hold_seconds(seconds)
        return self._play_shapes(["sleep", "shut_eyes", "blink", "eyes"], frame_seconds=0.16, final_hold_seconds=hold_s or 0.4)

    def sleepy_blink(self, seconds: float | None = None):
        hold_s = _coerce_hold_seconds(seconds)
        return self._play_shapes(["eyes", "blink", "shut_eyes", "blink", "eyes"], frame_seconds=0.14, final_hold_seconds=hold_s)

    def triangle(self, seconds: float | None = None):
        return self.shape("triangle", seconds=seconds)

    def square(self, seconds: float | None = None):
        return self.shape("square", seconds=seconds)

    def diamond(self, seconds: float | None = None):
        return self.shape("diamond", seconds=seconds)


def get_display() -> Display:
    return Display()
