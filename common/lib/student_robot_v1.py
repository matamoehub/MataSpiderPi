"""Compatibility wrapper for v1-style imports.

The SpiderPi classroom API now lives in student_robot_v2, but this keeps
legacy imports available with the same bot object.
"""

from student_robot_v2 import RobotV2, bot, spider

__all__ = ["RobotV2", "bot", "spider"]
