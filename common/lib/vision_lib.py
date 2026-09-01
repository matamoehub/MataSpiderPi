#!/usr/bin/env python3
from __future__ import annotations

"""
Notebook-friendly colour vision helper.

Uses the OpenCV pattern already taught in Lesson 3 and wraps it in a
singleton-safe library that can:
- capture a camera image
- detect red / green / blue objects
- run MediaPipe hand analysis for gesture-based lessons
- display the annotated image inline in Jupyter
- calibrate colour HSV ranges from the notebook
- undistort frames and report angular offset / lateral cm using the
  vendored SpiderPi camera calibration
- run YOLO26 nano object detection
"""
__version__ = "1.3.0"

import copy
import math
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ros_service_client import clear_process_singleton, get_process_singleton, set_process_singleton
from spiderpi_support import ensure_vendor_paths

# YOLO model — yolo26n nano, pre-installed on the robot at a fixed path.
# Students never need to choose or specify a model.
# Override with YOLO_MODEL env var for advanced use.
_YOLO_MODEL_NAME = "yolo26n.pt"
_YOLO_MODEL_SEARCH_PATHS = [
    Path("/opt/robot/models/yolo26n.pt"),          # pre-installed by ops
    Path(__file__).resolve().parent.parent / "models" / "yolo26n.pt",  # repo copy
    Path.home() / ".config" / "Ultralytics" / "yolo26n.pt",  # ultralytics cache
]
_DEFAULT_YOLO_MODEL = os.environ.get("YOLO_MODEL", _YOLO_MODEL_NAME)

# Camera calibration search paths (checked in order). The repo copy is the
# Hiwonder-vendored SpiderPi intrinsics (vendor/hiwonder_spiderpi/spiderpi_sdk/
# camera_calibration_sdk/calibration/calibration_param.npz), copied in as-is.
_CALIBRATION_SEARCH_PATHS = [
    Path("/opt/robot/calibration/camera_calibration.npz"),
    Path(__file__).resolve().parent.parent / "calibration" / "camera_calibration.npz",  # repo copy
    Path.home() / "camera_calibration.npz",
]

# The vendored calibration_param.npz stores only mtx_array/dist_array — no
# frame size. CollectCalibrationPicture.py opens the camera with
# cv2.VideoCapture(-1) and never sets an explicit resolution, so the
# calibration images were captured at the camera driver's default, which for
# this camera/SDK generation is 640x480. This constant records that
# assumption; load_calibration() scales the intrinsics to whatever
# resolution frames are actually captured at.
_CALIBRATION_NATIVE_SIZE = (640, 480)


HSVRange = Tuple[Tuple[int, int, int], Tuple[int, int, int]]


DEFAULT_COLOR_PROFILES: Dict[str, List[HSVRange]] = {
    "red": [
        ((0, 120, 50), (10, 255, 255)),
        ((170, 120, 50), (179, 255, 255)),
    ],
    "green": [
        ((35, 80, 40), (85, 255, 255)),
    ],
    "blue": [
        ((90, 80, 40), (135, 255, 255)),
    ],
}

ensure_vendor_paths()


def _normalize_color_name(color: str) -> str:
    value = str(color or "").strip().lower()
    aliases = {
        "r": "red",
        "g": "green",
        "b": "blue",
    }
    return aliases.get(value, value)


def _require_runtime():
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except Exception as e:  # pragma: no cover - depends on robot runtime
        msg = str(e)
        hint = ""
        if (
            "numpy.core.multiarray failed to import" in msg
            or "_ARRAY_API not found" in msg
            or "compiled using NumPy 1.x" in msg
        ):
            hint = (
                " This usually means OpenCV was installed against NumPy 1.x but the "
                "environment now has NumPy 2.x. In the robot/Jupyter environment, run: "
                "python -m pip install --force-reinstall --no-cache-dir "
                "'numpy<2' 'opencv-python<4.11'."
            )
        raise RuntimeError(
            "vision_lib requires OpenCV and NumPy on the robot image. "
            f"Import failed: {e}.{hint}"
        ) from e
    return cv2, np


def _require_mediapipe_runtime():
    try:
        import mediapipe as mp  # type: ignore
    except Exception as e:  # pragma: no cover - depends on robot runtime
        raise RuntimeError(
            "vision_lib MediaPipe features require the mediapipe package on the robot image. "
            f"Import failed: {e}"
        ) from e
    return mp


def _display_png_bytes(png_bytes: bytes) -> bool:
    try:  # pragma: no cover - notebook-only behavior
        from IPython.display import Image, display
    except Exception:
        return False
    display(Image(data=png_bytes))
    return True


def _coerce_range(lower: Sequence[int], upper: Sequence[int]) -> HSVRange:
    low = tuple(int(v) for v in lower)
    high = tuple(int(v) for v in upper)
    if len(low) != 3 or len(high) != 3:
        raise ValueError("HSV ranges must contain exactly 3 values")
    return low, high


def _expand_hue_wrap(lower: Tuple[int, int, int], upper: Tuple[int, int, int]) -> List[HSVRange]:
    lh, ls, lv = lower
    uh, us, uv = upper
    if lh < 0:
        return [
            ((0, ls, lv), (uh, us, uv)),
            ((180 + lh, ls, lv), (179, us, uv)),
        ]
    if uh > 179:
        return [
            ((lh, ls, lv), (179, us, uv)),
            ((0, ls, lv), (uh - 180, us, uv)),
        ]
    return [((max(0, lh), ls, lv), (min(179, uh), us, uv))]


def _clamp_pixel(value: float, maximum: int) -> int:
    return max(0, min(int(round(value)), maximum))


def _hand_landmark_xy(landmarks, index: int) -> Tuple[float, float]:
    point = landmarks[index]
    return float(point.x), float(point.y)


def _classify_hand_gesture(landmarks, handedness: str) -> Tuple[str, Dict[str, bool]]:
    wrist_x, wrist_y = _hand_landmark_xy(landmarks, 0)
    thumb_tip_x, thumb_tip_y = _hand_landmark_xy(landmarks, 4)
    thumb_ip_x, thumb_ip_y = _hand_landmark_xy(landmarks, 3)
    index_tip_y = _hand_landmark_xy(landmarks, 8)[1]
    index_pip_y = _hand_landmark_xy(landmarks, 6)[1]
    middle_tip_y = _hand_landmark_xy(landmarks, 12)[1]
    middle_pip_y = _hand_landmark_xy(landmarks, 10)[1]
    ring_tip_y = _hand_landmark_xy(landmarks, 16)[1]
    ring_pip_y = _hand_landmark_xy(landmarks, 14)[1]
    pinky_tip_y = _hand_landmark_xy(landmarks, 20)[1]
    pinky_pip_y = _hand_landmark_xy(landmarks, 18)[1]

    fingers = {
        "thumb": (thumb_tip_x < thumb_ip_x) if handedness.lower().startswith("right") else (thumb_tip_x > thumb_ip_x),
        "index": index_tip_y < index_pip_y,
        "middle": middle_tip_y < middle_pip_y,
        "ring": ring_tip_y < ring_pip_y,
        "pinky": pinky_tip_y < pinky_pip_y,
    }

    if all(fingers.values()):
        return "paper", fingers
    if not any(fingers.values()):
        return "rock", fingers
    if fingers["index"] and fingers["middle"] and not fingers["ring"] and not fingers["pinky"]:
        return "scissors", fingers
    if fingers["index"] and not fingers["middle"] and not fingers["ring"] and not fingers["pinky"]:
        return "point", fingers
    if fingers["thumb"] and not fingers["index"] and not fingers["middle"] and not fingers["ring"] and not fingers["pinky"]:
        if thumb_tip_y < wrist_y and thumb_ip_y < wrist_y:
            return "thumbs_up", fingers
        return "thumb_out", fingers
    if fingers["index"] and fingers["pinky"] and not fingers["middle"] and not fingers["ring"]:
        return "rock_sign", fingers
    return "unknown", fingers


def _classify_pose(landmarks) -> str:
    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]
    left_wrist = landmarks[15]
    right_wrist = landmarks[16]
    left_elbow = landmarks[13]
    right_elbow = landmarks[14]
    nose = landmarks[0]

    wrists_above_shoulders = left_wrist.y < left_shoulder.y and right_wrist.y < right_shoulder.y
    wrists_out_wide = abs(left_wrist.y - left_shoulder.y) < 0.10 and abs(right_wrist.y - right_shoulder.y) < 0.10
    elbows_out_wide = abs(left_elbow.y - left_shoulder.y) < 0.12 and abs(right_elbow.y - right_shoulder.y) < 0.12

    if wrists_above_shoulders:
        return "hands_up"
    if wrists_out_wide and elbows_out_wide:
        return "t_pose"
    if left_wrist.y < nose.y and right_wrist.y >= right_shoulder.y:
        return "left_hand_up"
    if right_wrist.y < nose.y and left_wrist.y >= left_shoulder.y:
        return "right_hand_up"
    return "neutral"


class Vision:
    def __init__(
        self,
        camera_index: Optional[int] = None,
        width: int = 320,
        height: int = 240,
        warmup_s: float = 0.15,
        min_area: int = 350,
    ):
        self.camera_index = int(os.environ.get("CAM_INDEX", camera_index if camera_index is not None else 0))
        self.width = int(width)
        self.height = int(height)
        self.warmup_s = float(warmup_s)
        self.min_area = int(min_area)
        self._profiles: Dict[str, List[HSVRange]] = copy.deepcopy(DEFAULT_COLOR_PROFILES)
        self._yolo_model: Optional[Any] = None  # loaded YOLO model (lazy)
        self._cal_K: Optional[Any] = None      # camera matrix, scaled to self.width/self.height
        self._cal_D: Optional[Any] = None      # distortion coefficients
        self._cal_map1: Optional[Any] = None   # precomputed undistort map1
        self._cal_map2: Optional[Any] = None   # precomputed undistort map2

    def set_color_profile(
        self,
        color: str,
        lower_hsv: Sequence[int] | Sequence[Sequence[int]],
        upper_hsv: Optional[Sequence[int]] = None,
    ) -> Dict[str, Any]:
        name = _normalize_color_name(color)
        if upper_hsv is None:
            ranges = []
            for pair in lower_hsv:  # type: ignore[assignment]
                if len(pair) != 2:
                    raise ValueError("Expected [(lower, upper), ...] when upper_hsv is omitted")
                ranges.append(_coerce_range(pair[0], pair[1]))  # type: ignore[index]
        else:
            ranges = [_coerce_range(lower_hsv, upper_hsv)]  # type: ignore[arg-type]
        self._profiles[name] = ranges
        return {"color": name, "ranges": ranges}

    def get_color_profile(self, color: str) -> List[HSVRange]:
        name = _normalize_color_name(color)
        if name not in self._profiles:
            raise KeyError(f"Unknown colour profile: {color}")
        return copy.deepcopy(self._profiles[name])

    def show_profiles(self) -> Dict[str, List[HSVRange]]:
        for name in sorted(self._profiles):
            print(f"{name}: {self._profiles[name]}")
        return copy.deepcopy(self._profiles)

    def _open_capture(self):
        cv2, _np = _require_runtime()
        candidates: list[int] = []
        for value in (self.camera_index, -1, 0, 1):
            if value not in candidates:
                candidates.append(value)

        last_error = None
        for index in candidates:
            cap = None
            try:
                cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
            except Exception:
                cap = cv2.VideoCapture(index)
            if not cap or not cap.isOpened():
                if cap is not None:
                    cap.release()
                last_error = f"index {index} did not open"
                continue

            try:
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc("Y", "U", "Y", "V"))
            except Exception:
                pass
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            try:
                cap.set(cv2.CAP_PROP_FPS, 30)
                cap.set(cv2.CAP_PROP_SATURATION, 40)
            except Exception:
                pass
            if self.warmup_s > 0:
                time.sleep(self.warmup_s)
            return cap

        raise RuntimeError(
            f"Camera failed to open on indices {candidates}. "
            f"Last result: {last_error}. Try setting CAM_INDEX for this robot."
        )

    def capture_frame(self):
        cap = self._open_capture()
        try:
            ok, frame = cap.read()
        finally:
            cap.release()
        if not ok or frame is None:
            raise RuntimeError("Camera opened, but no image frame was captured")
        return frame

    def _write_image(self, frame_bgr, save_path: Optional[str] = None) -> str:
        cv2, _np = _require_runtime()
        target = Path(save_path) if save_path else Path(tempfile.gettempdir()) / f"vision_capture_{int(time.time() * 1000)}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        ok = cv2.imwrite(str(target), frame_bgr)
        if not ok:
            raise RuntimeError(f"Failed to write image to {target}")
        return str(target)

    def save_image(self, frame_bgr, save_path: Optional[str] = None) -> str:
        """Write a frame to disk without displaying it. Returns the saved path."""
        return self._write_image(frame_bgr, save_path=save_path)

    def show_image(self, frame_bgr, save_path: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Any]:
        cv2, _np = _require_runtime()
        ok, encoded = cv2.imencode(".png", frame_bgr)
        if not ok:
            raise RuntimeError("Failed to encode image for notebook display")
        displayed = _display_png_bytes(encoded.tobytes())
        path = self._write_image(frame_bgr, save_path=save_path)
        if title:
            print(title)
        if not displayed:
            print(f"Image saved: {path}")
        return {"displayed": displayed, "path": path}

    def capture(self, show: bool = True, save_path: Optional[str] = None, title: str = "Camera Capture") -> Dict[str, Any]:
        frame = self.capture_frame()
        info = self.show_image(frame, save_path=save_path, title=title) if show else {"displayed": False, "path": self._write_image(frame, save_path=save_path)}
        return {"frame_bgr": frame, **info}

    def _capture_rgb_frame(self):
        cv2, _np = _require_runtime()
        frame_bgr = self.capture_frame()
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return frame_bgr, frame_rgb

    def _combined_mask(self, hsv_frame, ranges: Sequence[HSVRange]):
        cv2, np = _require_runtime()
        mask = None
        for lower, upper in ranges:
            part = cv2.inRange(hsv_frame, np.array(lower), np.array(upper))
            mask = part if mask is None else cv2.bitwise_or(mask, part)
        mask = cv2.erode(mask, None, iterations=1)
        mask = cv2.dilate(mask, None, iterations=2)
        return mask

    def find_color_objects(
        self,
        color: str,
        show: bool = True,
        save_path: Optional[str] = None,
        min_area: Optional[int] = None,
    ) -> Dict[str, Any]:
        cv2, _np = _require_runtime()
        name = _normalize_color_name(color)
        ranges = self.get_color_profile(name)
        frame = self.capture_frame()
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = self._combined_mask(hsv, ranges)

        contours, _hier = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        threshold = int(self.min_area if min_area is None else min_area)
        objects = []
        annotated = frame.copy()
        frame_h, frame_w = frame.shape[:2]

        for contour in contours:
            area = float(cv2.contourArea(contour))
            if area < threshold:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            m = cv2.moments(contour)
            if m["m00"] == 0:
                continue
            cx = int(m["m10"] / m["m00"])
            cy = int(m["m01"] / m["m00"])
            objects.append({
                "x": int(x),
                "y": int(y),
                "w": int(w),
                "h": int(h),
                "cx": cx,
                "cy": cy,
                "area": area,
            })

        objects.sort(key=lambda item: item["cx"])
        for idx, item in enumerate(objects, start=1):
            item["index"] = idx
            cv2.rectangle(
                annotated,
                (item["x"], item["y"]),
                (item["x"] + item["w"], item["y"] + item["h"]),
                (0, 255, 255),
                2,
            )
            cv2.putText(
                annotated,
                f"{name} #{idx}",
                (item["x"], max(18, item["y"] - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 255),
                2,
            )

        path = None
        if show:
            info = self.show_image(annotated, save_path=save_path, title=f"Detected {name} objects: {len(objects)}")
            path = info["path"]
        elif save_path:
            path = self._write_image(annotated, save_path=save_path)

        return {
            "color": name,
            "found": bool(objects),
            "count": len(objects),
            "objects": objects,
            "path": path,
            "ranges": ranges,
            "width": int(frame_w),
            "height": int(frame_h),
            "center_x": int(frame_w // 2),
        }

    def show_color(self, color: str, show: bool = True, save_path: Optional[str] = None, min_area: Optional[int] = None) -> Dict[str, Any]:
        return self.find_color_objects(color=color, show=show, save_path=save_path, min_area=min_area)

    def which_object(self, color: str, show: bool = True, save_path: Optional[str] = None, min_area: Optional[int] = None) -> int:
        result = self.find_color_objects(color=color, show=show, save_path=save_path, min_area=min_area)
        if not result["objects"]:
            return 0
        largest = max(result["objects"], key=lambda item: item["area"])
        print(f"{result['color']} object index: {largest['index']}")
        return int(largest["index"])

    def calibrate_color(
        self,
        color: str,
        box_size: int = 80,
        hue_pad: int = 12,
        sat_pad: int = 70,
        val_pad: int = 70,
        show: bool = True,
        save_path: Optional[str] = None,
        persist: bool = True,
    ) -> Dict[str, Any]:
        cv2, np = _require_runtime()
        name = _normalize_color_name(color)
        frame = self.capture_frame()
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        h, w = frame.shape[:2]
        half = max(10, int(box_size) // 2)
        cx = w // 2
        cy = h // 2
        x0 = max(0, cx - half)
        y0 = max(0, cy - half)
        x1 = min(w, cx + half)
        y1 = min(h, cy + half)
        roi = hsv[y0:y1, x0:x1]
        if roi.size == 0:
            raise RuntimeError("Calibration ROI was empty")

        median = np.median(roi.reshape(-1, 3), axis=0)
        mh, ms, mv = [int(round(v)) for v in median]
        lower = (
            mh - int(hue_pad),
            max(0, ms - int(sat_pad)),
            max(0, mv - int(val_pad)),
        )
        upper = (
            mh + int(hue_pad),
            min(255, ms + int(sat_pad)),
            min(255, mv + int(val_pad)),
        )
        ranges = _expand_hue_wrap(lower, upper)
        if persist:
            self._profiles[name] = ranges

        annotated = frame.copy()
        cv2.rectangle(annotated, (x0, y0), (x1, y1), (255, 255, 255), 2)
        cv2.putText(
            annotated,
            f"{name} HSV~{(mh, ms, mv)}",
            (10, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
        )
        path = None
        if show:
            info = self.show_image(annotated, save_path=save_path, title=f"Calibrated {name}: {ranges}")
            path = info["path"]
        elif save_path:
            path = self._write_image(annotated, save_path=save_path)

        result = {
            "color": name,
            "sample_hsv": (mh, ms, mv),
            "ranges": ranges,
            "path": path,
            "persisted": bool(persist),
        }
        print(result)
        return result

    # ── Camera calibration ────────────────────────────────────────────────────

    def load_calibration(self, path: Optional[str] = None) -> bool:
        """Load camera calibration from an npz file (camera_calibration.npz).

        Searches default paths if path is not given:
          /opt/robot/calibration/camera_calibration.npz
          common/calibration/camera_calibration.npz  (repo — vendored SpiderPi
          intrinsics, copied from vendor/hiwonder_spiderpi/spiderpi_sdk/
          camera_calibration_sdk/calibration/calibration_param.npz)
          ~/camera_calibration.npz

        The vendored file stores mtx_array/dist_array only (no frame size),
        calibrated at the camera's default driver resolution
        (_CALIBRATION_NATIVE_SIZE). The intrinsics are scaled here to match
        self.width/self.height so angle/distance math stays correct even
        though this class captures at 320x240 by default.

        Returns True if calibration was loaded successfully.
        """
        cv2, np = _require_runtime()
        candidates = [Path(path)] if path else _CALIBRATION_SEARCH_PATHS
        for p in candidates:
            if not p.exists():
                continue
            try:
                data = np.load(str(p))
                K = data["mtx_array"] if "mtx_array" in data.files else data["k_array"]
                D = (data["dist_array"] if "dist_array" in data.files else data["d_array"]).flatten()
                if "dim_array" in data.files:
                    native_w, native_h = (int(v) for v in data["dim_array"])
                else:
                    native_w, native_h = _CALIBRATION_NATIVE_SIZE

                scale_x = self.width / float(native_w)
                scale_y = self.height / float(native_h)
                K = K.copy()
                K[0, 0] *= scale_x  # fx
                K[1, 1] *= scale_y  # fy
                K[0, 2] *= scale_x  # cx
                K[1, 2] *= scale_y  # cy

                w, h = self.width, self.height
                new_K, _ = cv2.getOptimalNewCameraMatrix(K, D, (w, h), 1, (w, h))
                map1, map2 = cv2.initUndistortRectifyMap(
                    K, D, None, new_K, (w, h), cv2.CV_16SC2
                )
                self._cal_K   = new_K
                self._cal_D   = D
                self._cal_map1 = map1
                self._cal_map2 = map2
                print(f"[vision_lib] calibration loaded: {p.name}  "
                      f"fx={new_K[0,0]:.1f} fy={new_K[1,1]:.1f} "
                      f"cx={new_K[0,2]:.1f} cy={new_K[1,2]:.1f}  "
                      f"(scaled from {native_w}x{native_h} to {w}x{h})")
                return True
            except Exception as e:
                print(f"[vision_lib] calibration load failed ({p}): {e}")
        print("[vision_lib] no calibration file found — angular offset will use frame-centre estimate")
        return False

    def _ensure_calibration(self) -> bool:
        """Load calibration from default paths if not already loaded."""
        if self._cal_K is not None:
            return True
        return self.load_calibration()

    def undistort_frame(self, frame: Any) -> Any:
        """Undistort a frame using the loaded camera calibration.

        Loads calibration automatically from default paths if needed.
        Returns the original frame unchanged if calibration is unavailable.
        """
        if not self._ensure_calibration():
            return frame
        cv2, _np = _require_runtime()
        return cv2.remap(frame, self._cal_map1, self._cal_map2, cv2.INTER_LINEAR)

    def pixel_to_angle(self, pixel_x: float, pixel_y: Optional[float] = None) -> Dict[str, float]:
        """Convert pixel coordinates to angular offset from camera centre.

        Uses camera calibration when available, otherwise falls back to a
        reasonable estimate based on frame size.

        Returns {"angle_x_deg": float, "angle_y_deg": float}
          Positive angle_x = object is to the RIGHT of centre.
          Positive angle_y = object is BELOW centre.
        """
        if self._ensure_calibration() and self._cal_K is not None:
            fx = float(self._cal_K[0, 0])
            fy = float(self._cal_K[1, 1])
            cx = float(self._cal_K[0, 2])
            cy = float(self._cal_K[1, 2])
        else:
            # Fallback: assume ~60° FOV for a typical USB webcam.
            fx = fy = self.width / (2 * math.tan(math.radians(30)))
            cx = self.width / 2.0
            cy = self.height / 2.0

        angle_x = math.degrees(math.atan2(float(pixel_x) - cx, fx))
        angle_y = math.degrees(math.atan2(float(pixel_y) - cy, fy)) if pixel_y is not None else 0.0
        return {"angle_x_deg": round(angle_x, 2), "angle_y_deg": round(angle_y, 2)}

    def estimate_lateral_cm(
        self,
        pixel_cx: float,
        pixel_width: float,
        object_diameter_cm: float = 6.5,
    ) -> Optional[float]:
        """Estimate lateral distance (cm) of an object from camera centre.

        Uses the known real-world diameter of the object and its pixel width to
        estimate depth, then converts the pixel offset to cm.

        pixel_cx         — object centre x in the frame
        pixel_width      — object bounding-box width in pixels
        object_diameter_cm — real diameter in cm (default 6.5 cm for a standard football)

        Returns lateral cm (positive = right, negative = left), or None if
        calibration is unavailable or pixel_width is zero.
        """
        if pixel_width <= 0:
            return None
        if not self._ensure_calibration() or self._cal_K is None:
            return None
        fx = float(self._cal_K[0, 0])
        cx = float(self._cal_K[0, 2])
        # Depth from apparent size: Z = fx * D_real / D_pixels
        depth_cm = fx * float(object_diameter_cm) / float(pixel_width)
        # Lateral distance: X = (px - cx) / fx * Z
        lateral_cm = (float(pixel_cx) - cx) / fx * depth_cm
        return round(lateral_cm, 1)

    def target_position(
        self,
        color: str,
        target_x: Optional[int] = None,
        deadzone: int = 50,
        show: bool = True,
        min_area: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Find the largest colour object and return its direction from centre.

        For angular offset and lateral cm use locate_object() instead.

        Returns: found, direction ("left"|"center"|"right"|"lost"),
                 error (pixels from centre), target_x, deadzone, object, result.
        """
        result = self.find_color_objects(color=color, show=show, min_area=min_area)
        objects = result["objects"]
        centre_x = int(result["center_x"] if target_x is None else target_x)
        threshold = abs(int(deadzone))

        if not objects:
            return {
                "color":     result["color"],
                "found":     False,
                "direction": "lost",
                "error":     None,
                "target_x":  centre_x,
                "deadzone":  threshold,
                "object":    None,
                "result":    result,
            }

        target = max(objects, key=lambda item: item["area"])
        error = int(target["cx"] - centre_x)
        if abs(error) <= threshold:
            direction = "center"
        elif error < 0:
            direction = "left"
        else:
            direction = "right"

        return {
            "color":     result["color"],
            "found":     True,
            "direction": direction,
            "error":     error,
            "target_x":  centre_x,
            "deadzone":  threshold,
            "object":    target,
            "result":    result,
        }

    def locate_object(
        self,
        color: str,
        target_x: Optional[int] = None,
        deadzone: int = 50,
        show: bool = True,
        min_area: Optional[int] = None,
        object_diameter_cm: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Find the largest colour object with real-world position data.

        Enhanced version of target_position() — adds angular offset and
        optional lateral distance. Uses camera calibration automatically.

        Args:
            color:               Colour name to detect ("red", "green", "blue").
            deadzone:            Pixel half-width of the "center" zone.
            object_diameter_cm:  Real diameter of the object in cm.
                                 If given, lateral_cm is estimated from
                                 the object's pixel width + calibration.
                                 e.g. 6.5 for a standard football.

        Returns:
            direction     "left" | "center" | "right" | "lost"  (same as target_position)
            found         bool
            error         pixel offset from centre (+ = right, - = left)
            error_norm    normalised -1.0..1.0 (resolution-independent, no depth needed)
            angle_x_deg   lateral angle in degrees — positive = right of centre
                          Uses calibration when loaded; falls back to FOV estimate.
            lateral_cm    lateral distance in cm — only if object_diameter_cm given
                          AND calibration is loaded; otherwise None.
            object        largest detected object dict (x, y, w, h, cx, cy, area)
        """
        result = self.find_color_objects(color=color, show=show, min_area=min_area)
        objects = result["objects"]
        centre_x = int(result["center_x"] if target_x is None else target_x)
        threshold = abs(int(deadzone))

        if not objects:
            return {
                "color":       result["color"],
                "found":       False,
                "direction":   "lost",
                "error":       None,
                "error_norm":  None,
                "angle_x_deg": None,
                "lateral_cm":  None,
                "target_x":    centre_x,
                "deadzone":    threshold,
                "object":      None,
                "result":      result,
            }

        target = max(objects, key=lambda item: item["area"])
        error = int(target["cx"] - centre_x)

        # Normalised: -1.0 (far left) to +1.0 (far right)
        frame_w = result.get("width", self.width) or self.width
        error_norm = round(error / max(1, frame_w / 2), 3)

        # Angular offset — uses calibration if available
        angles = self.pixel_to_angle(target["cx"], target["cy"])
        angle_x_deg = angles["angle_x_deg"]

        # Lateral cm — only when real object size is known
        lateral_cm: Optional[float] = None
        if object_diameter_cm is not None:
            lateral_cm = self.estimate_lateral_cm(
                target["cx"],
                target.get("w", 0),
                object_diameter_cm,
            )

        if abs(error) <= threshold:
            direction = "center"
        elif error < 0:
            direction = "left"
        else:
            direction = "right"

        return {
            "color":       result["color"],
            "found":       True,
            "direction":   direction,
            "error":       error,
            "error_norm":  error_norm,
            "angle_x_deg": angle_x_deg,
            "lateral_cm":  lateral_cm,
            "target_x":    centre_x,
            "deadzone":    threshold,
            "object":      target,
            "result":      result,
        }

    def recognize_hands(
        self,
        show: bool = True,
        save_path: Optional[str] = None,
        max_hands: int = 2,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> Dict[str, Any]:
        cv2, _np = _require_runtime()
        mp = _require_mediapipe_runtime()
        frame_bgr, frame_rgb = self._capture_rgb_frame()
        annotated = frame_bgr.copy()
        h, w = annotated.shape[:2]
        hands_found: List[Dict[str, Any]] = []

        with mp.solutions.hands.Hands(
            static_image_mode=True,
            max_num_hands=int(max_hands),
            min_detection_confidence=float(min_detection_confidence),
            min_tracking_confidence=float(min_tracking_confidence),
        ) as detector:
            result = detector.process(frame_rgb)

        multi_landmarks = getattr(result, "multi_hand_landmarks", None) or []
        multi_handedness = getattr(result, "multi_handedness", None) or []
        for idx, landmarks in enumerate(multi_landmarks, start=1):
            handedness_label = "unknown"
            if idx - 1 < len(multi_handedness):
                try:
                    handedness_label = multi_handedness[idx - 1].classification[0].label
                except Exception:
                    handedness_label = "unknown"

            xs = [_clamp_pixel(pt.x * w, w - 1) for pt in landmarks.landmark]
            ys = [_clamp_pixel(pt.y * h, h - 1) for pt in landmarks.landmark]
            gesture, fingers = _classify_hand_gesture(landmarks.landmark, handedness_label)
            hand = {
                "index": idx,
                "handedness": handedness_label,
                "gesture": gesture,
                "fingers": fingers,
                "bbox": {
                    "x": min(xs),
                    "y": min(ys),
                    "w": max(xs) - min(xs),
                    "h": max(ys) - min(ys),
                },
            }
            hands_found.append(hand)

            mp.solutions.drawing_utils.draw_landmarks(
                annotated,
                landmarks,
                mp.solutions.hands.HAND_CONNECTIONS,
            )
            cv2.putText(
                annotated,
                f"{handedness_label} {gesture}",
                (hand["bbox"]["x"], max(18, hand["bbox"]["y"] - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 0),
                2,
            )

        path = None
        if show:
            info = self.show_image(annotated, save_path=save_path, title=f"Detected hands: {len(hands_found)}")
            path = info["path"]
        elif save_path:
            path = self._write_image(annotated, save_path=save_path)

        return {
            "found": bool(hands_found),
            "count": len(hands_found),
            "hands": hands_found,
            "path": path,
            "game_moves": [hand["gesture"] for hand in hands_found if hand.get("gesture") in ("rock", "paper", "scissors")],
        }

    def detect_faces(
        self,
        show: bool = True,
        save_path: Optional[str] = None,
        model_selection: int = 0,
        min_detection_confidence: float = 0.5,
    ) -> Dict[str, Any]:
        cv2, _np = _require_runtime()
        mp = _require_mediapipe_runtime()
        frame_bgr, frame_rgb = self._capture_rgb_frame()
        annotated = frame_bgr.copy()
        h, w = annotated.shape[:2]
        faces_found: List[Dict[str, Any]] = []

        with mp.solutions.face_detection.FaceDetection(
            model_selection=int(model_selection),
            min_detection_confidence=float(min_detection_confidence),
        ) as detector:
            result = detector.process(frame_rgb)

        detections = getattr(result, "detections", None) or []
        for idx, detection in enumerate(detections, start=1):
            bbox_rel = detection.location_data.relative_bounding_box
            x = _clamp_pixel(bbox_rel.xmin * w, w - 1)
            y = _clamp_pixel(bbox_rel.ymin * h, h - 1)
            bw = max(1, _clamp_pixel(bbox_rel.width * w, w))
            bh = max(1, _clamp_pixel(bbox_rel.height * h, h))
            score = 0.0
            try:
                score = float(detection.score[0])
            except Exception:
                score = 0.0

            face = {
                "index": idx,
                "score": score,
                "bbox": {"x": x, "y": y, "w": bw, "h": bh},
            }
            faces_found.append(face)

            cv2.rectangle(annotated, (x, y), (min(w - 1, x + bw), min(h - 1, y + bh)), (0, 255, 0), 2)
            cv2.putText(
                annotated,
                f"Face {idx} {score:.2f}",
                (x, max(18, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 0),
                2,
            )

        path = None
        if show:
            info = self.show_image(annotated, save_path=save_path, title=f"Detected faces: {len(faces_found)}")
            path = info["path"]
        elif save_path:
            path = self._write_image(annotated, save_path=save_path)

        return {
            "found": bool(faces_found),
            "count": len(faces_found),
            "faces": faces_found,
            "path": path,
        }

    def show_faces(
        self,
        show: bool = True,
        save_path: Optional[str] = None,
        model_selection: int = 0,
        min_detection_confidence: float = 0.5,
    ) -> Dict[str, Any]:
        return self.detect_faces(
            show=show,
            save_path=save_path,
            model_selection=model_selection,
            min_detection_confidence=min_detection_confidence,
        )

    def show_hands(
        self,
        show: bool = True,
        save_path: Optional[str] = None,
        max_hands: int = 2,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> Dict[str, Any]:
        return self.recognize_hands(
            show=show,
            save_path=save_path,
            max_hands=max_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def detect_pose(
        self,
        show: bool = True,
        save_path: Optional[str] = None,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> Dict[str, Any]:
        cv2, _np = _require_runtime()
        mp = _require_mediapipe_runtime()
        frame_bgr, frame_rgb = self._capture_rgb_frame()
        annotated = frame_bgr.copy()

        with mp.solutions.pose.Pose(
            static_image_mode=True,
            min_detection_confidence=float(min_detection_confidence),
            min_tracking_confidence=float(min_tracking_confidence),
        ) as detector:
            result = detector.process(frame_rgb)

        pose_landmarks = getattr(result, "pose_landmarks", None)
        pose = {
            "found": bool(pose_landmarks),
            "label": "none",
            "landmarks": {},
        }
        if pose_landmarks is not None:
            mp.solutions.drawing_utils.draw_landmarks(
                annotated,
                pose_landmarks,
                mp.solutions.pose.POSE_CONNECTIONS,
            )
            key_names = {
                "nose": 0,
                "left_shoulder": 11,
                "right_shoulder": 12,
                "left_elbow": 13,
                "right_elbow": 14,
                "left_wrist": 15,
                "right_wrist": 16,
                "left_hip": 23,
                "right_hip": 24,
            }
            for name, idx in key_names.items():
                point = pose_landmarks.landmark[idx]
                pose["landmarks"][name] = {
                    "x": float(point.x),
                    "y": float(point.y),
                    "z": float(point.z),
                    "visibility": float(point.visibility),
                }
            pose["label"] = _classify_pose(pose_landmarks.landmark)
            cv2.putText(
                annotated,
                f"pose: {pose['label']}",
                (10, 24),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 255),
                2,
            )

        path = None
        if show:
            info = self.show_image(annotated, save_path=save_path, title=f"Pose: {pose['label']}")
            path = info["path"]
        elif save_path:
            path = self._write_image(annotated, save_path=save_path)
        pose["path"] = path
        return pose

    def show_pose(
        self,
        show: bool = True,
        save_path: Optional[str] = None,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        return self.detect_pose(
            show=show,
            save_path=save_path,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def recognize_pose(
        self,
        show: bool = True,
        save_path: Optional[str] = None,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        return self.detect_pose(
            show=show,
            save_path=save_path,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    # ── YOLO object detection ─────────────────────────────────────────────────

    def _ensure_yolo(self) -> Any:
        """Load YOLO26 nano model lazily.

        Checks pre-installed paths first (/opt/robot/models/yolo26n.pt),
        then falls back to ultralytics auto-download.
        Students never need to specify a model — it is always yolo26n.
        """
        if self._yolo_model is not None:
            return self._yolo_model
        # ultralytics imports matplotlib.pyplot on load which triggers the
        # Jupyter inline backend and crashes with a version mismatch:
        #   AttributeError: 'RcParams' object has no attribute '_get'
        # Force a non-interactive backend before the import to avoid this.
        try:
            import matplotlib
            matplotlib.use("Agg")
        except Exception:
            pass
        try:
            from ultralytics import YOLO  # type: ignore
        except ImportError:
            raise RuntimeError(
                "YOLO requires the ultralytics package. "
                "Ask ops to run: pip install ultralytics"
            )
        # Use pre-installed model file if available — avoids internet dependency
        for p in _YOLO_MODEL_SEARCH_PATHS:
            if p.exists():
                self._yolo_model = YOLO(str(p))
                print(f"[vision_lib] YOLO26 nano loaded from {p}")
                return self._yolo_model
        # Not pre-installed — download (requires internet, first run only)
        print(f"[vision_lib] downloading {_YOLO_MODEL_NAME} (first use only)...")
        self._yolo_model = YOLO(_YOLO_MODEL_NAME)
        print("[vision_lib] YOLO26 nano ready")
        return self._yolo_model

    def detect_objects_yolo(
        self,
        conf: float = 0.5,
        show: bool = True,
        save_path: Optional[str] = None,
        classes: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Run YOLO26 nano object detection on a captured frame.

        Always uses the pre-installed yolo26n model — students do not
        need to choose or download a model.

        Args:
            conf:      Confidence threshold 0-1. Lower = more detections.
            show:      Display annotated frame in Jupyter.
            save_path: Optional path to save annotated image.
            classes:   Filter to specific COCO class IDs (None = all).
                       e.g. classes=[32] for sports ball only.

        Returns dict with:
            found       bool
            count       int
            objects     list of {label, confidence, x, y, w, h, cx, cy}
            path        saved image path or None
        """
        cv2, _np = _require_runtime()
        yolo = self._ensure_yolo()
        frame = self.capture_frame()

        results = yolo(frame, conf=conf, classes=classes, verbose=False)

        objects = []
        annotated = frame.copy()
        for result in results:
            # Use YOLO's built-in plot() for professional annotated frame
            # (per-class colours, background labels, proper styling)
            annotated = result.plot()
            for box in result.boxes:
                x1, y1, x2, y2 = (int(v) for v in box.xyxy[0])
                w, h = x2 - x1, y2 - y1
                objects.append({
                    "label": result.names[int(box.cls[0])],
                    "confidence": float(box.conf[0]),
                    "x": x1, "y": y1, "w": w, "h": h,
                    "cx": x1 + w // 2, "cy": y1 + h // 2,
                })

        path = None
        if show:
            info = self.show_image(annotated, save_path=save_path,
                                   title=f"YOLO: {len(objects)} objects detected")
            path = info["path"]
        elif save_path:
            path = self._write_image(annotated, save_path=save_path)

        return {
            "found": bool(objects),
            "count": len(objects),
            "objects": objects,
            "path": path,
        }

    def yolo_class_names(self) -> List[str]:
        """Return all 80 COCO class names YOLO26n can detect."""
        model = self._ensure_yolo()
        return list(model.names.values())


def get_vision(
    camera_index: Optional[int] = None,
    width: int = 320,
    height: int = 240,
    warmup_s: float = 0.15,
    min_area: int = 350,
) -> Vision:
    key = "vision_lib:vision"
    inst = get_process_singleton(key)
    if inst is None:
        inst = set_process_singleton(
            key,
            Vision(
                camera_index=camera_index,
                width=width,
                height=height,
                warmup_s=warmup_s,
                min_area=min_area,
            ),
        )
    return inst


def reset_vision() -> None:
    clear_process_singleton("vision_lib:vision")


def capture(*args, **kwargs):
    return get_vision().capture(*args, **kwargs)


def show_color(*args, **kwargs):
    return get_vision().show_color(*args, **kwargs)


def find_color_objects(*args, **kwargs):
    return get_vision().find_color_objects(*args, **kwargs)


def which_object(*args, **kwargs):
    return get_vision().which_object(*args, **kwargs)


def calibrate_color(*args, **kwargs):
    return get_vision().calibrate_color(*args, **kwargs)


def set_color_profile(*args, **kwargs):
    return get_vision().set_color_profile(*args, **kwargs)


def get_color_profile(*args, **kwargs):
    return get_vision().get_color_profile(*args, **kwargs)


def detect_faces(*args, **kwargs):
    return get_vision().detect_faces(*args, **kwargs)


def show_faces(*args, **kwargs):
    return get_vision().show_faces(*args, **kwargs)


def show_profiles():
    return get_vision().show_profiles()


def recognize_hands(*args, **kwargs):
    return get_vision().recognize_hands(*args, **kwargs)


def show_hands(*args, **kwargs):
    return get_vision().show_hands(*args, **kwargs)


def detect_objects_yolo(*args, **kwargs):
    return get_vision().detect_objects_yolo(*args, **kwargs)


def yolo_class_names():
    return get_vision().yolo_class_names()


def detect_pose(*args, **kwargs):
    return get_vision().detect_pose(*args, **kwargs)


def show_pose(*args, **kwargs):
    return get_vision().show_pose(*args, **kwargs)


def recognize_pose(*args, **kwargs):
    return get_vision().recognize_pose(*args, **kwargs)


def load_calibration(*args, **kwargs):
    return get_vision().load_calibration(*args, **kwargs)


def undistort_frame(*args, **kwargs):
    return get_vision().undistort_frame(*args, **kwargs)


def pixel_to_angle(*args, **kwargs):
    return get_vision().pixel_to_angle(*args, **kwargs)


def estimate_lateral_cm(*args, **kwargs):
    return get_vision().estimate_lateral_cm(*args, **kwargs)


def target_position(*args, **kwargs):
    return get_vision().target_position(*args, **kwargs)


def locate_object(*args, **kwargs):
    return get_vision().locate_object(*args, **kwargs)


def save_image(*args, **kwargs):
    return get_vision().save_image(*args, **kwargs)
