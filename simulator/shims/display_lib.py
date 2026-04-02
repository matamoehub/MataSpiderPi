from __future__ import annotations

from simulator.core.sim_state import load_state, save_state


class Display:
    def text(self, line1: str = "", line2: str = "", line3: str = "", line4: str = ""):
        state = load_state()
        state["display"] = {"lines": [line1, line2, line3, line4]}
        state["last_command"] = "display:text"
        save_state(state)
        return state["display"]

    def line(self, line_number: int, text: str):
        state = load_state()
        display = state.setdefault("display", {"lines": ["", "", "", ""]})
        lines = list(display.get("lines", ["", "", "", ""]))
        idx = max(1, min(4, int(line_number))) - 1
        while len(lines) < 4:
            lines.append("")
        lines[idx] = str(text)
        state["display"] = {"lines": lines}
        state["last_command"] = f"display:line:{idx + 1}"
        save_state(state)
        return {"line": idx + 1, "text": str(text)}

    def number(self, value):
        state = load_state()
        state["display"] = {"number": value}
        state["last_command"] = "display:number"
        save_state(state)
        return {"number": value}

    def clear_matrix(self):
        state = load_state()
        state["display"] = {"matrix": "cleared"}
        state["last_command"] = "display:clear"
        save_state(state)
        return {"matrix": "cleared"}

    def shape(self, name: str = "smile"):
        state = load_state()
        state["display"] = {"shape": str(name)}
        state["last_command"] = f"display:shape:{name}"
        save_state(state)
        return {"shape": str(name)}

    def smile(self):
        return self.shape("smile")

    def triangle(self):
        return self.shape("triangle")

    def square(self):
        return self.shape("square")

    def diamond(self):
        return self.shape("diamond")


def get_display() -> Display:
    return Display()
