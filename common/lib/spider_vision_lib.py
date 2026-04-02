#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

try:
    import vision_lib as _base_vision
except Exception:  # pragma: no cover
    _base_vision = None


def _require_base():
    if _base_vision is None:
        raise RuntimeError("vision_lib is not available")
    return _base_vision


def _simple_color_result(color: str, raw: dict[str, Any]) -> dict[str, Any]:
    objects = list(raw.get("objects") or [])
    first = objects[0] if objects else None
    return {
        "found": bool(objects),
        "color": str(color),
        "count": len(objects),
        "first": first,
        "objects": objects,
        "path": raw.get("path"),
        "simulated": bool(raw.get("simulated", False)),
    }


class SpiderVision:
    """
    Student-friendly vision helper.

    Keep methods simple and outcome-focused:
    - snapshot()
    - find_color("red")
    - count_color("blue")
    - can_see("green")
    """

    def snapshot(self, show: bool = True, save_path: str | None = None):
        base = _require_base()
        return base.capture(show=show, save_path=save_path, title="SpiderPi Camera")

    def find_color(self, color: str = "red", show: bool = True, save_path: str | None = None) -> dict[str, Any]:
        base = _require_base()
        raw = base.find_color_objects(color=color, show=show, save_path=save_path)
        return _simple_color_result(color, raw)

    def count_color(self, color: str = "red", show: bool = False) -> int:
        return int(self.find_color(color=color, show=show).get("count", 0))

    def can_see(self, color: str = "red", show: bool = False) -> bool:
        return bool(self.find_color(color=color, show=show).get("found"))

    def color_position(self, color: str = "red", show: bool = False) -> dict[str, Any] | None:
        return self.find_color(color=color, show=show).get("first")

    def biggest_color(self, color: str = "red", show: bool = False) -> dict[str, Any] | None:
        objects = list(self.find_color(color=color, show=show).get("objects") or [])
        if not objects:
            return None
        return max(objects, key=lambda item: float(item.get("distance_m", 0.0)))

    def track_color(self, color: str = "red") -> dict[str, Any]:
        return {
            "ok": True,
            "activity": "track_color",
            "color": color,
            "message": f"Tracking mode for {color} is available in the advanced SpiderPi demos.",
        }

    def detect_faces(self, show: bool = True) -> dict[str, Any]:
        return {
            "ok": True,
            "found": None,
            "count": None,
            "activity": "face_detection",
            "engine": "mediapipe",
            "vendor_demo": "functions/face_detect.py",
            "show": bool(show),
            "message": "MediaPipe face detection is available in the upstream SpiderPi demos.",
        }

    def show_faces(self, show: bool = True) -> dict[str, Any]:
        return self.detect_faces(show=show)

    def recognize_faces(self, show: bool = True) -> dict[str, Any]:
        return self.detect_faces(show=show)

    def find_face(self) -> dict[str, Any]:
        return self.detect_faces(show=True)

    def recognize_hands(self, show: bool = True) -> dict[str, Any]:
        base = _require_base()
        raw = base.recognize_hands(show=show)
        return {
            "ok": True,
            "activity": "hand_recognition",
            "engine": "mediapipe",
            "found": bool(raw.get("found")),
            "count": int(raw.get("count", 0)),
            "hands": list(raw.get("hands") or []),
            "game_moves": list(raw.get("game_moves") or []),
            "path": raw.get("path"),
            "message": "Hand recognition uses the simplified MataSpiderPi MediaPipe helper.",
        }

    def show_hands(self, show: bool = True) -> dict[str, Any]:
        return self.recognize_hands(show=show)

    def detect_pose(self, show: bool = True) -> dict[str, Any]:
        return {
            "ok": False,
            "activity": "pose_detection",
            "engine": "mediapipe",
            "show": bool(show),
            "available": False,
            "message": "This MataSpiderPi API matches MataTurboPi naming, but I did not find an upstream SpiderPi MediaPipe pose-recognition demo in the vendored Hiwonder repo.",
        }

    def show_pose(self, show: bool = True) -> dict[str, Any]:
        return self.detect_pose(show=show)

    def recognize_pose(self, show: bool = True) -> dict[str, Any]:
        return self.detect_pose(show=show)

    def find_tag(self) -> dict[str, Any]:
        return {
            "ok": True,
            "activity": "apriltag_detection",
            "message": "AprilTag detection is available in the advanced SpiderPi demos.",
        }

    def follow_line(self) -> dict[str, Any]:
        return {
            "ok": True,
            "activity": "line_following",
            "message": "Line following is available in the advanced SpiderPi demos.",
        }

    def avoid_obstacles(self) -> dict[str, Any]:
        return {
            "ok": True,
            "activity": "obstacle_avoidance",
            "message": "Obstacle avoidance is available in the advanced SpiderPi demos.",
        }

    def find_shapes(self) -> dict[str, Any]:
        return {
            "ok": True,
            "activity": "shape_recognition",
            "message": "Shape recognition is available in the advanced SpiderPi demos.",
        }


def get_spider_vision() -> SpiderVision:
    return SpiderVision()
