#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from spiderpi_support import get_action_controller, resolve_vendor_root


def list_actions() -> list[str]:
    root = resolve_vendor_root() / 'action_groups'
    if not root.exists():
        return []
    return sorted(path.stem for path in root.glob('*.d6a'))


def run_action(name: str, times: int = 1) -> None:
    controller = get_action_controller()
    if controller is None:
        raise RuntimeError('SpiderPi action controller unavailable')
    controller.run_action_group(str(name), times=max(1, int(times)))


def stop() -> None:
    controller = get_action_controller()
    if controller is not None:
        try:
            controller.stop_servo()
        except Exception:
            pass


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
