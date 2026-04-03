#!/usr/bin/env python3
from __future__ import annotations

"""
MataSpiderPi student library.

This is the main library students should use.

Preferred import:
    from student_robot_v2 import bot

Then use the robot through one clear API:
    bot.body.forward(1)
    bot.arm.open()
    bot.lights.green()
    bot.display.text("Hello")
    bot.vision.find_color("red")
    bot.speech.say("SpiderPi ready")
    bot.distance.cm()
"""

import robot_moves as robot_moves_module
from action_group_lib import get_actions
from arm_lib import get_arm
from buzzer_lib import get_buzzer
from camera_lib import get_camera
from display_lib import get_display
from lights_lib import get_lights
from sonar_lib import get_sonar
from spider_vision_lib import get_spider_vision
import tts_lib


class Body:
    def __init__(self):
        self._actions = get_actions()

    def forward(self, seconds: float = 0.6):
        return robot_moves_module.forward(seconds=seconds)

    def backward(self, seconds: float = 0.6):
        return robot_moves_module.backward(seconds=seconds)

    def left(self, seconds: float = 0.6):
        return robot_moves_module.left(seconds=seconds)

    def right(self, seconds: float = 0.6):
        return robot_moves_module.right(seconds=seconds)

    def turn_left(self, seconds: float = 0.5):
        return robot_moves_module.turn_left(seconds=seconds)

    def turn_right(self, seconds: float = 0.5):
        return robot_moves_module.turn_right(seconds=seconds)

    def stop(self):
        return robot_moves_module.stop()

    def dance(self):
        return self._actions.dance()

    def wave(self):
        return self._actions.wave()

    def attack(self):
        return self._actions.attack()

    def kick(self):
        return self._actions.kick()

    def twist(self):
        return self._actions.twist()


class Arm:
    def __init__(self):
        self._arm = get_arm()

    def home(self):
        return self._arm.home()

    def ready(self):
        return self._arm.ready()

    def move(self, x: float, y: float, z: float, seconds: float = 1.0):
        return self._arm.move(x, y, z, seconds=seconds)

    def look(self):
        return self._arm.look()

    def open(self):
        return self._arm.open()

    def half_open(self):
        return self._arm.half_open()

    def close(self):
        return self._arm.close()

    def set_grip(self, pulse: int, seconds: float = 0.5):
        return self._arm.set_grip(pulse, seconds=seconds)

    def turn_left(self):
        return self._arm.turn_left()

    def turn_right(self):
        return self._arm.turn_right()

    def center_turn(self):
        return self._arm.center_turn()

    def lift(self, height: float = 6.0):
        return self._arm.lift(height=height)

    def lower(self, height: float = 3.0):
        return self._arm.lower(height=height)

    def grab_at(self, x: float, y: float, z: float):
        return self._arm.grab_at(x, y, z)

    def pick(self, x: float, y: float, z: float):
        return self._arm.pick(x, y, z)

    def carry(self):
        return self._arm.carry()

    def place(self):
        return self._arm.place()


class Vision:
    def __init__(self):
        self._vision = get_spider_vision()

    def snapshot(self, show: bool = True):
        return self._vision.snapshot(show=show)

    def capture(self, show: bool = True):
        return self.snapshot(show=show)

    def find_color(self, color: str = "red", show: bool = True):
        return self._vision.find_color(color=color, show=show)

    def show_color(self, color: str = "red", show: bool = True):
        return self.find_color(color=color, show=show)

    def can_see(self, color: str = "red", show: bool = False) -> bool:
        return self._vision.can_see(color=color, show=show)

    def count_color(self, color: str = "red", show: bool = False) -> int:
        return self._vision.count_color(color=color, show=show)

    def color_position(self, color: str = "red", show: bool = False):
        return self._vision.color_position(color=color, show=show)

    def detect_faces(self, show: bool = True):
        return self._vision.detect_faces(show=show)

    def show_faces(self, show: bool = True):
        return self._vision.show_faces(show=show)

    def recognize_faces(self, show: bool = True):
        return self._vision.recognize_faces(show=show)

    def find_face(self):
        return self.detect_faces(show=True)

    def recognize_hands(self, show: bool = True):
        return self._vision.recognize_hands(show=show)

    def show_hands(self, show: bool = True):
        return self._vision.show_hands(show=show)

    def detect_hands(self, show: bool = True):
        return self._vision.show_hands(show=show)

    def detect_pose(self, show: bool = True):
        return self._vision.detect_pose(show=show)

    def show_pose(self, show: bool = True):
        return self._vision.show_pose(show=show)

    def recognize_pose(self, show: bool = True):
        return self._vision.recognize_pose(show=show)

    def find_tag(self):
        return self._vision.find_tag()

    def find_shapes(self):
        return self._vision.find_shapes()


class Sound:
    def __init__(self):
        self._buzzer = get_buzzer()

    def say(self, text: str, block: bool = True):
        return tts_lib.say(text, block=block)

    def beep(self, freq: int = 2000, seconds: float = 0.2):
        return self._buzzer.beep(freq=freq, duration_s=seconds)

    def melody(self, score: str, bpm: int = 120):
        return self._buzzer.play_notes_music_mode(score, bpm=bpm)


class Speech:
    """
    Explicit Piper TTS helper.
    """

    def say(self, text: str, block: bool = True):
        return tts_lib.say(text, block=block)


class DistanceSensor:
    def __init__(self):
        self._sonar = None
        self._init_error: Exception | None = None

    def _require_sonar(self):
        if self._sonar is not None:
            return self._sonar
        if self._init_error is not None:
            raise RuntimeError(f"SpiderPi distance sensor unavailable: {self._init_error}")
        try:
            self._sonar = get_sonar()
            return self._sonar
        except Exception as exc:
            self._init_error = exc
            raise RuntimeError(f"SpiderPi distance sensor unavailable: {exc}") from exc

    def cm(self) -> int:
        return self._require_sonar().get_distance_cm(filtered=True)

    def mm(self) -> int:
        return self._require_sonar().get_distance_mm(filtered=True)

    def is_close(self, threshold_cm: float = 20.0) -> bool:
        return self._require_sonar().is_closer_than(threshold_cm, filtered=True)


class RobotV2:
    """
    Student-friendly SpiderPi API.

    Preferred namespaces:
    - bot.body.forward(1)
    - bot.arm.open()
    - bot.lights.green()
    - bot.display.text("Hello")
    - bot.vision.find_color("red")
    - bot.speech.say("hello")
    - bot.distance.cm()
    """

    def __init__(self):
        self.body = Body()
        self.arm = Arm()
        self.vision = Vision()
        self.sound = Sound()
        self.speech = Speech()
        self.distance = DistanceSensor()
        self.camera = get_camera()
        self.lights = get_lights()
        self.display = get_display()

        # Compatibility aliases for older notebooks.
        self.move = self.body
        self.voice = self.sound
        self.buzzer = get_buzzer()
        self.sonar = self.distance
        self.actions = get_actions()

    def say(self, text: str, block: bool = True):
        return self.sound.say(text, block=block)

    def beep(self, freq: int = 2000, seconds: float = 0.2):
        return self.sound.beep(freq=freq, seconds=seconds)

    def stop(self):
        return self.body.stop()

    def help(self) -> dict[str, list[str]]:
        return {
            "body": ["forward", "backward", "left", "right", "turn_left", "turn_right", "stop", "dance", "wave", "attack", "kick", "twist"],
            "arm": ["home", "ready", "move", "look", "open", "half_open", "close", "set_grip", "turn_left", "turn_right", "center_turn", "lift", "lower", "grab_at", "pick", "carry", "place"],
            "vision": ["snapshot", "capture", "find_color", "show_color", "can_see", "count_color", "color_position", "detect_faces", "show_faces", "recognize_faces", "find_face", "recognize_hands", "show_hands", "detect_hands", "detect_pose", "show_pose", "recognize_pose", "find_tag", "find_shapes"],
            "sound": ["say", "beep", "melody"],
            "speech": ["say"],
            "distance": ["cm", "mm", "is_close"],
            "lights": ["robot", "sonar", "all", "off", "red", "green", "blue", "yellow", "purple"],
            "display": ["text", "line", "number", "clear_matrix", "shape", "smile", "triangle", "square", "diamond"],
            "camera": ["center_all", "set_yaw", "set_pitch", "glance_left", "glance_right", "look_up", "look_down", "nod", "shake", "wiggle", "tiny_wiggle"],
        }


bot = RobotV2()
spider = bot

__all__ = ["RobotV2", "bot", "spider"]
