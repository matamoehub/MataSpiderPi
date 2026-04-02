from __future__ import annotations

from simulator.core.sim_state import load_state, save_state


class Lights:
    def _set(self, target: str, r: int, g: int, b: int):
        state = load_state()
        state.setdefault("lights", {})[target] = [int(r), int(g), int(b)]
        state["last_command"] = f"lights:{target}"
        save_state(state)
        return {"target": target, "rgb": [int(r), int(g), int(b)]}

    def robot(self, r: int, g: int, b: int):
        return self._set("robot", r, g, b)

    def sonar(self, r: int, g: int, b: int):
        return self._set("sonar", r, g, b)

    def all(self, r: int, g: int, b: int):
        return {"robot": self.robot(r, g, b), "sonar": self.sonar(r, g, b), "rgb": [int(r), int(g), int(b)]}

    def off(self):
        return self.all(0, 0, 0)

    def red(self):
        return self.all(255, 0, 0)

    def green(self):
        return self.all(0, 255, 0)

    def blue(self):
        return self.all(0, 0, 255)

    def yellow(self):
        return self.all(255, 200, 0)

    def purple(self):
        return self.all(180, 0, 255)


def get_lights() -> Lights:
    return Lights()
