from __future__ import annotations

from simulator.core.sim_state import load_state, record_event, save_state

_ACTIONS = ['attack', 'dance', 'kick', 'twist', 'wave', 'wave_and_grip']


def list_actions() -> list[str]:
    return list(_ACTIONS)


def run_action(name: str, times: int = 1) -> None:
    state = load_state()
    state.setdefault('pose', {})['name'] = str(name)
    state.setdefault('action', {})['name'] = str(name)
    state['last_command'] = f'action:{name}'
    record_event(state, 'action_group', name=str(name), times=int(times))
    save_state(state)


class ActionGroups:
    def list(self) -> list[str]:
        return list_actions()

    def run(self, name: str, times: int = 1) -> None:
        run_action(name, times=times)

    def wave(self):
        run_action('wave')

    def dance(self):
        run_action('dance')

    def attack(self):
        run_action('attack')

    def kick(self):
        run_action('kick')

    def twist(self):
        run_action('twist')


def get_actions() -> ActionGroups:
    return ActionGroups()
