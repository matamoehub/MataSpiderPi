#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

try:
    import vision_lib as _base_vision
except Exception:  # pragma: no cover
    _base_vision = None

try:
    import qrcode_lib as _qrcode_lib
except Exception:  # pragma: no cover
    _qrcode_lib = None


def _require_base():
    if _base_vision is None:
        raise RuntimeError("vision_lib is not available")
    return _base_vision


def _require_qrcode():
    if _qrcode_lib is None:
        raise RuntimeError("qrcode_lib is not available")
    return _qrcode_lib


def _camera_error_result(activity: str, exc: Exception, show: bool = True) -> dict[str, Any]:
    return {
        "ok": False,
        "activity": activity,
        "show": bool(show),
        "camera_available": False,
        "error": str(exc),
        "message": "SpiderPi camera is unavailable. Reconnect the USB camera or check CAM_INDEX.",
    }


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
        try:
            raw = base.capture(show=show, save_path=save_path, title="SpiderPi Camera")
        except RuntimeError as exc:
            return _camera_error_result("snapshot", exc, show=show)
        return {"ok": True, "activity": "snapshot", "camera_available": True, **raw}

    def find_color(self, color: str = "red", show: bool = True, save_path: str | None = None) -> dict[str, Any]:
        base = _require_base()
        try:
            raw = base.find_color_objects(color=color, show=show, save_path=save_path)
        except RuntimeError as exc:
            result = _camera_error_result("find_color", exc, show=show)
            result["color"] = str(color)
            result["count"] = 0
            result["found"] = False
            result["objects"] = []
            result["first"] = None
            result["path"] = None
            return result
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

    def target_position(
        self,
        color: str = "red",
        target_x: int | None = None,
        deadzone: int = 50,
        show: bool = False,
        min_area: int | None = None,
    ) -> dict[str, Any]:
        base = _require_base()
        try:
            return base.target_position(
                color=color, target_x=target_x, deadzone=deadzone, show=show, min_area=min_area,
            )
        except RuntimeError as exc:
            result = _camera_error_result("target_position", exc, show=show)
            result["color"] = str(color)
            result["direction"] = "lost"
            result["found"] = False
            result["object"] = None
            return result

    def locate_object(
        self,
        color: str = "red",
        target_x: int | None = None,
        deadzone: int = 50,
        show: bool = False,
        min_area: int | None = None,
        object_diameter_cm: float | None = None,
    ) -> dict[str, Any]:
        base = _require_base()
        try:
            return base.locate_object(
                color=color, target_x=target_x, deadzone=deadzone, show=show,
                min_area=min_area, object_diameter_cm=object_diameter_cm,
            )
        except RuntimeError as exc:
            result = _camera_error_result("locate_object", exc, show=show)
            result["color"] = str(color)
            result["direction"] = "lost"
            result["found"] = False
            result["angle_x_deg"] = None
            result["lateral_cm"] = None
            result["object"] = None
            return result

    def calibrate_color(
        self,
        color: str,
        box_size: int = 80,
        show: bool = True,
        save_path: str | None = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        base = _require_base()
        try:
            return base.calibrate_color(
                color=color, box_size=box_size, show=show, save_path=save_path, persist=persist,
            )
        except RuntimeError as exc:
            result = _camera_error_result("calibrate_color", exc, show=show)
            result["color"] = str(color)
            result["persisted"] = False
            return result

    def which_object(self, color: str = "red", show: bool = True, min_area: int | None = None) -> int:
        base = _require_base()
        try:
            return base.which_object(color=color, show=show, min_area=min_area)
        except RuntimeError:
            return 0

    def track_color(self, color: str = "red") -> dict[str, Any]:
        return {
            "ok": True,
            "activity": "track_color",
            "color": color,
            "message": f"Tracking mode for {color} is available in the advanced SpiderPi demos.",
        }

    def detect_faces(self, show: bool = True) -> dict[str, Any]:
        base = _require_base()
        try:
            raw = base.detect_faces(show=show)
        except RuntimeError as exc:
            result = _camera_error_result("face_detection", exc, show=show)
            result["engine"] = "mediapipe"
            result["vendor_demo"] = "functions/face_detect.py"
            result["found"] = False
            result["count"] = 0
            result["faces"] = []
            result["path"] = None
            return result
        return {
            "ok": True,
            "activity": "face_detection",
            "engine": "mediapipe",
            "vendor_demo": "functions/face_detect.py",
            "show": bool(show),
            "found": bool(raw.get("found")),
            "count": int(raw.get("count", 0)),
            "faces": list(raw.get("faces") or []),
            "path": raw.get("path"),
            "message": "Face detection uses the MataSpiderPi MediaPipe helper and can display an annotated frame.",
        }

    def show_faces(self, show: bool = True) -> dict[str, Any]:
        return self.detect_faces(show=show)

    def recognize_faces(self, show: bool = True) -> dict[str, Any]:
        return self.detect_faces(show=show)

    def find_face(self) -> dict[str, Any]:
        return self.detect_faces(show=True)

    def recognize_hands(self, show: bool = True) -> dict[str, Any]:
        base = _require_base()
        try:
            raw = base.recognize_hands(show=show)
        except RuntimeError as exc:
            result = _camera_error_result("hand_recognition", exc, show=show)
            result["engine"] = "mediapipe"
            result["found"] = False
            result["count"] = 0
            result["hands"] = []
            result["game_moves"] = []
            result["path"] = None
            return result
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

    def detect_objects(self, confidence: float = 0.5, show: bool = True) -> dict[str, Any]:
        base = _require_base()
        try:
            raw = base.detect_objects_yolo(conf=confidence, show=show)
        except RuntimeError as exc:
            result = _camera_error_result("object_detection", exc, show=show)
            result["engine"] = "yolo26n"
            result["found"] = False
            result["count"] = 0
            result["objects"] = []
            result["path"] = None
            return result
        return {
            "ok": True,
            "activity": "object_detection",
            "engine": "yolo26n",
            "show": bool(show),
            "found": bool(raw.get("found")),
            "count": int(raw.get("count", 0)),
            "objects": list(raw.get("objects") or []),
            "path": raw.get("path"),
            "message": "Object detection uses YOLO26 nano and can display an annotated frame.",
        }

    def find_object(self, name: str, confidence: float = 0.5, show: bool = True) -> dict[str, Any]:
        result = self.detect_objects(confidence=confidence, show=show)
        target = str(name).strip().lower()
        matches = [obj for obj in result.get("objects", []) if str(obj.get("label", "")).lower() == target]
        best = max(matches, key=lambda obj: obj.get("confidence", 0.0)) if matches else None
        return {
            **result,
            "activity": "find_object",
            "name": target,
            "found": bool(best),
            "match": best,
        }

    def object_classes(self) -> list[str]:
        base = _require_base()
        try:
            return base.yolo_class_names()
        except RuntimeError:
            return []

    def detect_pose(self, show: bool = True) -> dict[str, Any]:
        base = _require_base()
        try:
            raw = base.detect_pose(show=show)
        except RuntimeError as exc:
            result = _camera_error_result("pose_detection", exc, show=show)
            result["engine"] = "mediapipe"
            result["found"] = False
            result["label"] = "none"
            result["landmarks"] = {}
            result["path"] = None
            return result
        return {
            "ok": True,
            "activity": "pose_detection",
            "engine": "mediapipe",
            "show": bool(show),
            "found": bool(raw.get("found")),
            "label": raw.get("label", "none"),
            "landmarks": dict(raw.get("landmarks") or {}),
            "path": raw.get("path"),
            "message": "Pose detection uses the shared MediaPipe Pose helper (same as MataTurboPi) and classifies hands_up/t_pose/left_hand_up/right_hand_up/neutral.",
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

    def read_qr_codes(self, show: bool = True) -> dict[str, Any]:
        try:
            qr = _require_qrcode()
            raw = qr.read_qr_codes(show=show)
        except RuntimeError as exc:
            result = _camera_error_result("qr_code", exc, show=show)
            result["engine"] = "opencv"
            result["found"] = False
            result["count"] = 0
            result["codes"] = []
            result["path"] = None
            return result
        return {
            "ok": True,
            "activity": "qr_code",
            "engine": "opencv",
            "show": bool(show),
            "found": bool(raw.get("found")),
            "count": int(raw.get("count", 0)),
            "codes": list(raw.get("codes") or []),
            "path": raw.get("path"),
            "message": "QR code reading uses OpenCV's built-in QRCodeDetector — real QR text/URL payloads, not AprilTags.",
        }

    def find_qr_code(self, show: bool = True) -> dict[str, Any] | None:
        result = self.read_qr_codes(show=show)
        codes = result.get("codes") or []
        return codes[0] if codes else None

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
