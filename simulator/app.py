#!/usr/bin/env python3
"""Minimal local simulator launcher for MataSpiderPi."""

from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk

from simulator.core.sim_state import load_state, reset_state, save_state, state_path


class SimApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("MataSpiderPi Simulator")
        frame = ttk.Frame(root, padding=10)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="MataSpiderPi Simulator", font=("TkDefaultFont", 14, "bold")).pack(anchor="w")
        ttk.Label(frame, text="This lightweight window is mainly for debugging simulator state. The browser simulator in robot-classroom is the main student experience.", wraplength=520, justify="left").pack(anchor="w", pady=(6, 12))
        ttk.Button(frame, text="Reset State", command=self.reset_robot).pack(anchor="w")
        self.text = tk.Text(frame, width=80, height=26)
        self.text.pack(fill="both", expand=True, pady=(10, 0))
        self.draw()

    def reset_robot(self):
        st = reset_state()
        save_state(st)
        self.draw()

    def draw(self):
        state = load_state()
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, f"State file: {state_path()}\n\n")
        self.text.insert(tk.END, json.dumps(state, indent=2))
        self.root.after(500, self.draw)


def main():
    root = tk.Tk()
    SimApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
