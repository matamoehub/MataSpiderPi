from __future__ import annotations

from simulator.core.sim_state import load_state, record_event, save_state

HOME = (0.0, 15.0, 18.0)
LOOK = (0.0, 15.0, 30.0)
CARRY = (0.0, 18.0, 10.0)
PLACE = (8.0, 18.0, 3.0)


class Arm:
    def _set_state(self, xyz, gripper=None, label='arm_move'):
        state = load_state()
        state.setdefault('arm', {})['x'] = float(xyz[0])
        state.setdefault('arm', {})['y'] = float(xyz[1])
        state.setdefault('arm', {})['z'] = float(xyz[2])
        if gripper is not None:
            state.setdefault('gripper', {})['open'] = bool(gripper)
        state['last_command'] = label
        record_event(state, label, x=float(xyz[0]), y=float(xyz[1]), z=float(xyz[2]))
        save_state(state)
        return dict(state['arm'])

    def move_to(self, x: float, y: float, z: float, pitch: float = -90, min_pitch: float = -90, max_pitch: float = 100, movetime_ms: int = 1000):
        del pitch, min_pitch, max_pitch, movetime_ms
        return self._set_state((x, y, z), label='arm_move')

    def open_gripper(self):
        return self._set_state(self.current_xyz(), gripper=True, label='gripper_open')

    def close_gripper(self):
        return self._set_state(self.current_xyz(), gripper=False, label='gripper_close')

    def current_xyz(self):
        state = load_state()
        arm = state.setdefault('arm', {'x': HOME[0], 'y': HOME[1], 'z': HOME[2]})
        return (arm['x'], arm['y'], arm['z'])

    def home(self):
        return self._set_state(HOME, label='arm_home')

    def look_pose(self):
        return self._set_state(LOOK, label='arm_look')

    def carry_pose(self):
        return self._set_state(CARRY, label='arm_carry')

    def place_pose(self):
        return self._set_state(PLACE, label='arm_place')

    def pick(self, x: float, y: float, z: float):
        self.open_gripper()
        self.move_to(x, y, z)
        self.close_gripper()
        return self.move_to(x, y, z + 5.0)


def get_arm() -> Arm:
    return Arm()
