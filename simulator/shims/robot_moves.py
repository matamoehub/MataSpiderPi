from __future__ import annotations

import time
from typing import Optional

from simulator.core.sim_state import apply_robot_motion, load_state, record_event, reset_state, save_state

SPEED_TO_M_S = 1.0 / 1600.0
TURN_SPEED_TO_DEG_S = 0.55
SIM_STEP_DT = 0.02


def _move(vx: float, vy: float, omega: float, seconds: float, label: str):
    total = max(0.0, float(seconds))
    elapsed = 0.0
    while elapsed < total:
        step = min(SIM_STEP_DT, total - elapsed)
        state = load_state()
        apply_robot_motion(state, vx, vy, omega, step, label)
        state.setdefault('pose', {})['name'] = label
        save_state(state)
        time.sleep(step)
        elapsed += step
    state = load_state()
    state['robot']['vx'] = 0.0
    state['robot']['vy'] = 0.0
    state['robot']['omega_deg_s'] = 0.0
    state['last_command'] = label
    save_state(state)


def stop():
    state = load_state()
    state['robot']['vx'] = 0.0
    state['robot']['vy'] = 0.0
    state['robot']['omega_deg_s'] = 0.0
    state['last_command'] = 'stop'
    save_state(state)


def emergency_stop():
    stop()


def forward(seconds: float = 0.6, speed: Optional[float] = None):
    scale = 300 if speed is None else float(speed)
    _move(scale * SPEED_TO_M_S, 0.0, 0.0, seconds, 'forward')


def backward(seconds: float = 0.6, speed: Optional[float] = None):
    scale = 300 if speed is None else float(speed)
    _move(-scale * SPEED_TO_M_S, 0.0, 0.0, seconds, 'backward')


def left(seconds: float = 0.6, speed: Optional[float] = None):
    scale = 300 if speed is None else float(speed)
    _move(0.0, -scale * SPEED_TO_M_S, 0.0, seconds, 'left')


def right(seconds: float = 0.6, speed: Optional[float] = None):
    scale = 300 if speed is None else float(speed)
    _move(0.0, scale * SPEED_TO_M_S, 0.0, seconds, 'right')


def move_left(seconds: float = 0.6, speed: Optional[float] = None):
    left(seconds=seconds, speed=speed)


def move_right(seconds: float = 0.6, speed: Optional[float] = None):
    right(seconds=seconds, speed=speed)


def turn_left(seconds: float = 0.5, speed: Optional[float] = None):
    scale = 300 if speed is None else float(speed)
    _move(0.0, 0.0, scale * TURN_SPEED_TO_DEG_S, seconds, 'turn_left')


def turn_right(seconds: float = 0.5, speed: Optional[float] = None):
    scale = 300 if speed is None else float(speed)
    _move(0.0, 0.0, -scale * TURN_SPEED_TO_DEG_S, seconds, 'turn_right')


def diagonal_left(seconds: float = 0.8, speed: Optional[float] = None):
    scale = 300 if speed is None else float(speed)
    v = scale * SPEED_TO_M_S
    _move(v * 0.6, -v * 0.6, 0.0, seconds, 'diagonal_left')


def diagonal_right(seconds: float = 0.8, speed: Optional[float] = None):
    scale = 300 if speed is None else float(speed)
    v = scale * SPEED_TO_M_S
    _move(v * 0.6, v * 0.6, 0.0, seconds, 'diagonal_right')


def drift_left(seconds: float = 1.0, speed: Optional[float] = None, turn_blend: float = 0.55):
    scale = 300 if speed is None else float(speed)
    v = scale * SPEED_TO_M_S
    _move(v * 0.2, -v * 0.9, scale * TURN_SPEED_TO_DEG_S * float(turn_blend), seconds, 'drift_left')


def drift_right(seconds: float = 1.0, speed: Optional[float] = None, turn_blend: float = 0.55):
    scale = 300 if speed is None else float(speed)
    v = scale * SPEED_TO_M_S
    _move(v * 0.2, v * 0.9, -scale * TURN_SPEED_TO_DEG_S * float(turn_blend), seconds, 'drift_right')


def drive_for(vx: float, vy: float, seconds: float, speed: Optional[float] = None):
    scale = 300 if speed is None else float(speed)
    factor = scale * SPEED_TO_M_S
    _move(float(vx) * factor, float(vy) * factor, 0.0, seconds, 'drive_for')


def horn(*_args, **_kwargs):
    state = load_state()
    record_event(state, 'horn', name='simulated')
    state['last_command'] = 'horn'
    save_state(state)
    return True


def reset_simulator_state():
    reset_state()


class RobotMoves:
    def stop(self): stop()
    def emergency_stop(self): emergency_stop()
    def forward(self, seconds: float = 0.6, speed: Optional[float] = None): forward(seconds, speed)
    def backward(self, seconds: float = 0.6, speed: Optional[float] = None): backward(seconds, speed)
    def left(self, seconds: float = 0.6, speed: Optional[float] = None): left(seconds, speed)
    def right(self, seconds: float = 0.6, speed: Optional[float] = None): right(seconds, speed)
    def move_left(self, seconds: float = 0.6, speed: Optional[float] = None): move_left(seconds, speed)
    def move_right(self, seconds: float = 0.6, speed: Optional[float] = None): move_right(seconds, speed)
    def turn_left(self, seconds: float = 0.5, speed: Optional[float] = None): turn_left(seconds, speed)
    def turn_right(self, seconds: float = 0.5, speed: Optional[float] = None): turn_right(seconds, speed)
    def diagonal_left(self, seconds: float = 0.8, speed: Optional[float] = None): diagonal_left(seconds, speed)
    def diagonal_right(self, seconds: float = 0.8, speed: Optional[float] = None): diagonal_right(seconds, speed)
    def drift_left(self, seconds: float = 1.0, speed: Optional[float] = None, turn_blend: float = 0.55): drift_left(seconds, speed, turn_blend)
    def drift_right(self, seconds: float = 1.0, speed: Optional[float] = None, turn_blend: float = 0.55): drift_right(seconds, speed, turn_blend)
    def drive_for(self, vx: float, vy: float, seconds: float, speed: Optional[float] = None): drive_for(vx, vy, seconds, speed)
    def horn(self, *args, **kwargs): return horn(*args, **kwargs)
