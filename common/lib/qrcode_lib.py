#!/usr/bin/env python3
from __future__ import annotations

"""
QR code reading for MataSpiderPi.

Decodes real QR codes (text/URL payloads) from the camera using OpenCV's
built-in QRCodeDetector — no ROS2 service and no compiled native library
required, unlike the vendored AprilTag wrapper
(vendor/hiwonder_spiderpi/spiderpi_sdk/common_sdk/common/apriltag.py), which
needs a compiled libapriltag.so that isn't shipped in this repo.

Note: this reads QR codes, not the vendor's AprilTag-based "tag" recognition
(spider_vision_lib.find_tag() is a separate, still-stubbed feature).
"""
__version__ = "1.0.0"

from typing import Any, Dict, List, Optional

import vision_lib as _vision_lib


def _require_runtime():
    try:
        import cv2  # type: ignore
    except Exception as e:  # pragma: no cover - depends on robot runtime
        raise RuntimeError(
            "qrcode_lib requires OpenCV on the robot image. "
            f"Import failed: {e}"
        ) from e
    return cv2


def read_qr_codes(
    show: bool = True,
    save_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Detect and decode every QR code visible in a captured frame.

    Returns dict with:
        found    bool
        count    int
        codes    list of {data, points, cx, cy} — points is the 4-corner
                 polygon in pixel coords, cx/cy is the polygon centre
        path     saved/displayed image path or None
    """
    cv2 = _require_runtime()
    vision = _vision_lib.get_vision()
    frame = vision.capture_frame()

    detector = cv2.QRCodeDetector()
    ok, decoded_texts, points, _straight = detector.detectAndDecodeMulti(frame)

    codes: List[Dict[str, Any]] = []
    annotated = frame.copy()
    if ok and points is not None:
        for text, quad in zip(decoded_texts, points):
            if not text:
                continue  # a located-but-undecodable code — skip it
            pts = [(float(x), float(y)) for x, y in quad]
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            codes.append({
                "data": text,
                "points": pts,
                "cx": int(cx),
                "cy": int(cy),
            })
            quad_int = [(int(x), int(y)) for x, y in pts]
            for i in range(len(quad_int)):
                cv2.line(annotated, quad_int[i], quad_int[(i + 1) % len(quad_int)], (0, 255, 0), 2)
            cv2.putText(
                annotated,
                text[:40],
                (quad_int[0][0], max(18, quad_int[0][1] - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 0),
                2,
            )

    path = None
    if show:
        info = vision.show_image(annotated, save_path=save_path,
                                 title=f"QR codes found: {len(codes)}")
        path = info["path"]
    elif save_path:
        path = vision.save_image(annotated, save_path=save_path)

    return {
        "found": bool(codes),
        "count": len(codes),
        "codes": codes,
        "path": path,
    }


def find_qr_code(show: bool = True, save_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Return the first decoded QR code, or None if none was found."""
    result = read_qr_codes(show=show, save_path=save_path)
    codes = result.get("codes") or []
    return codes[0] if codes else None
