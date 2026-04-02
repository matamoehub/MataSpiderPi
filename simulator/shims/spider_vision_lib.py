from __future__ import annotations

from simulator.core.sim_state import load_state
import vision_lib as _base_vision


def _visible_objects():
    state = load_state()
    return list(state.get('course', {}).get('obstacles', []))


class SpiderVision:
    def capture(self, *args, **kwargs):
        return _base_vision.capture(*args, **kwargs)

    def detect_color(self, color: str = 'red', *args, **kwargs):
        return _base_vision.find_color_objects(color=color, *args, **kwargs)

    def track_color(self, color: str = 'red'):
        return {'ok': True, 'mode': 'track_color', 'color': color, 'targets': _visible_objects()}

    def detect_face(self):
        return {'ok': True, 'mode': 'face_detect', 'faces': [{'id': 'sim-face-1', 'confidence': 0.99}]}

    def detect_apriltag(self):
        return {'ok': True, 'mode': 'apriltag_detect', 'tags': [{'id': 1, 'distance_m': 0.75}]}

    def patrol_line(self):
        return {'ok': True, 'mode': 'visual_patrol', 'line_detected': True}

    def avoid_obstacles(self):
        return {'ok': True, 'mode': 'avoidance', 'obstacles': _visible_objects()}

    def recognize_shapes(self):
        return {'ok': True, 'mode': 'shape_recognition', 'shapes': [{'shape': 'circle', 'color': 'red'}]}

    def advanced_examples(self):
        return {
            'intelligent_fetch': 'simulated',
            'block_fetch': 'simulated',
            'color_sorting': 'simulated',
            'shape_recognition': 'simulated',
            'intelligent_kick': 'simulated',
            'cruise_carry': 'simulated',
            'ball_orientation': 'simulated',
        }


def get_spider_vision() -> SpiderVision:
    return SpiderVision()
