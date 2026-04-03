# MataSpiderPi

MataSpiderPi is the Matamoe lesson and library repo for the Hiwonder SpiderPi Pro.

The repo keeps the same broad classroom shape as the other Mata robot repos, but the content here is SpiderPi-specific:
- hexapod movement helpers
- action group wrappers
- arm and gripper control
- SpiderPi-oriented vision helpers
- simulator shims for browser and notebook workflows
- lessons mapped to the SpiderPi Pro tutorial topics

## Python Setup

This project targets Python 3.11.2.

For local lesson and simulator work, create a Python 3.11.2 virtual environment and install the notebook and vision packages the lessons use:

```bash
python3.11 --version
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install jupyterlab notebook ipykernel numpy opencv-python mediapipe pillow
```

If `python3.11` is not installed yet, one common option on macOS is `pyenv`:

```bash
brew install pyenv
pyenv install 3.11.2
pyenv local 3.11.2
python -m venv .venv
source .venv/bin/activate
```

## Running Lessons Locally

The lesson notebooks bootstrap themselves from this repo. For local simulator-style runs, start Jupyter with simulator mode enabled:

```bash
source .venv/bin/activate
export MATA_BACKEND=sim
export MATA_SIM=1
jupyter lab
```

Then open a notebook such as `lessons/lesson01/level_1/Lesson01.ipynb`.

Notes:
- The local lessons use `common/lib`, the lesson loader, and the simulator shims in this repo.
- Real robot control depends on the robot image, ROS setup, and Hiwonder hardware services being available.
- Lesson 13 uses MediaPipe hand recognition, so `mediapipe` must be installed in the active environment.
- The local simulator app also uses `tkinter`, which is usually included with Python installers but may need extra setup on some `pyenv` builds.

## SpiderPi Content Areas

Lessons and libraries are organised around the SpiderPi Pro capability set:
- body movement and posture control
- arm inverse kinematics and gripping
- colour vision, tracking, tags, and face tools
- obstacle avoidance and transport challenges
- picking, sorting, kicking, and mission design

## Lessons Overview

1. Lesson 1 - Robot Demo: Introduces SpiderPi movement basics and includes a demo notebook showing major robot features.
2. Lesson 2 - Hexapod Movement: Teaches gait-style movement and side-stepping with reusable movement helpers.
3. Lesson 3 - Action Groups: Uses prebuilt motion sequences such as wave, dance, attack, and kick.
4. Lesson 4 - Robotic Arm Basics: Covers arm movement, gripper control, and simple object placement.
5. Lesson 5 - Camera and Colour Vision: Captures images and detects coloured targets with the camera.
6. Lesson 6 - Tracking and Tags: Connects vision data to behaviour with tracking and AprilTag-based responses.
7. Lesson 7 - Face, Shape, and Line Tools: Explores face detection, shape recognition, and patrol-style logic.
8. Lesson 8 - Obstacle Avoidance: Uses sonar sensing and movement together to avoid obstacles safely.
9. Lesson 9 - Block Picking: Combines vision, arm control, and gripping to pick up and place blocks.
10. Lesson 10 - Sorting Challenge: Builds a full pick-and-place workflow for sorting coloured objects into zones.
11. Lesson 11 - Kick and Carry: Tests multi-step transport and kicking behaviours.
12. Lesson 12 - Creative Mission: Brings movement, arm control, and vision together in an open-ended mission.
13. Lesson 13 - Rock Paper Scissors Vision: Uses MediaPipe hand recognition so SpiderPi can detect gestures and play rock, paper, scissors.

## Upstream Vendor Source

The original Hiwonder code is kept under `vendor/hiwonder_spiderpi/` so the SDKs, action groups, and advanced examples are available alongside the Matamoe wrappers.
