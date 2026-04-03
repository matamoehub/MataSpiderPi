#!/usr/bin/env python3
from __future__ import annotations

import time
from typing import List, Optional, Tuple

from spiderpi_support import get_board

DEFAULT_BPM = 120
DEFAULT_FREQ = 2400

_SEMITONES = {
    "C": 0,
    "C#": 1,
    "DB": 1,
    "D": 2,
    "D#": 3,
    "EB": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "GB": 6,
    "G": 7,
    "G#": 8,
    "AB": 8,
    "A": 9,
    "A#": 10,
    "BB": 10,
    "B": 11,
}


def note_to_freq(note: str) -> int:
    token = str(note).strip().upper()
    if token in ("R", "REST", "PAUSE", "SILENCE"):
        return 0
    if len(token) < 2:
        raise ValueError(f"Invalid note: {note}")
    if token[1] in ("#", "B"):
        key = token[:2]
        octave_txt = token[2:]
    else:
        key = token[:1]
        octave_txt = token[1:]
    if key not in _SEMITONES or not octave_txt:
        raise ValueError(f"Invalid note: {note}")
    octave = int(octave_txt)
    midi = (octave + 1) * 12 + _SEMITONES[key]
    hz = 440.0 * (2.0 ** ((midi - 69) / 12.0))
    return int(round(max(1.0, hz)))


class Buzzer:
    def __init__(self):
        self._board = get_board()

    def _require_board(self):
        if self._board is None:
            raise RuntimeError("SpiderPi buzzer control unavailable")
        return self._board

    def beep(self, freq: int = DEFAULT_FREQ, duration_s: float = 0.2, gap_s: float = 0.05, note: str | None = None) -> None:
        board = self._require_board()
        if note is not None:
            freq = note_to_freq(note)
        duration_s = max(0.0, float(duration_s))
        if duration_s <= 0.0:
            return
        if int(freq) <= 0:
            time.sleep(duration_s)
            return
        gap_s = max(0.0, float(gap_s))
        try:
            # The SpiderPi controller expects an explicit off window; using 0 here
            # can leave the buzzer latched on some robot images.
            board.set_buzzer(int(freq), duration_s, gap_s, 1)
            time.sleep(duration_s + gap_s)
        finally:
            self.off()

    def off(self) -> None:
        try:
            self._require_board().set_buzzer(0, 0.0, 0.0, 1)
        except Exception:
            pass

    def play_note(self, note: str, beats: float = 1.0, bpm: int = DEFAULT_BPM) -> None:
        beat_s = 60.0 / float(max(1, int(bpm)))
        total_s = max(0.0, float(beats) * beat_s)
        freq = note_to_freq(note)
        if freq <= 0:
            time.sleep(total_s)
            return
        self.beep(freq=freq, duration_s=total_s)

    def play_notes(self, score: str, bpm: int = DEFAULT_BPM) -> None:
        tokens = [t for t in str(score).split() if t.strip()]
        try:
            for token in tokens:
                if ":" in token:
                    note, beats_txt = token.split(":", 1)
                    beats = float(beats_txt)
                else:
                    note, beats = token, 1.0
                self.play_note(note, beats=beats, bpm=bpm)
        finally:
            self.off()

    def play_notes_music_mode(self, score: str, bpm: int = DEFAULT_BPM) -> None:
        self.play_notes(score, bpm=bpm)

    def play_melody(self, notes: List[Tuple[str, float]], bpm: int = DEFAULT_BPM) -> None:
        for note, beats in notes:
            self.play_note(note, beats=beats, bpm=bpm)


_BUZZER_SINGLETON: Optional[Buzzer] = None


def get_buzzer() -> Buzzer:
    global _BUZZER_SINGLETON
    if _BUZZER_SINGLETON is None:
        _BUZZER_SINGLETON = Buzzer()
    return _BUZZER_SINGLETON
