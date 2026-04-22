"""Compatibility wrapper for older lessons.

Prefer importing from student_robot_v2. This module keeps v1-style notebooks
working while exposing the same robot instance and named sound helpers.
"""

from student_robot_v2 import RobotV2, bot, spider

__all__ = ["RobotV2", "bot", "spider"]
