# MataSpiderPi Library Overview

This document describes the current student-facing SpiderPi library, the main implementation layers behind it, and the major commits that shaped the current API.

## Purpose

This repo adapts the Hiwonder SpiderPi platform into a classroom-oriented Python library with:

- one clear student API
- stable lesson bootstrapping
- simplified robot motion and sensor helpers
- visible matrix display output
- camera, face, hand, and color vision
- buzzer, Piper TTS, and named WAV playback

The primary student entry point is:

```python
from student_robot_v2 import bot
```

## Main Student API

The main API is implemented in [common/lib/student_robot_v2.py](common/lib/student_robot_v2.py).

It exposes a single `bot` object with these namespaces:

- `bot.body`
- `bot.arm`
- `bot.camera`
- `bot.display`
- `bot.vision`
- `bot.sound`
- `bot.speech`
- `bot.distance`
- `bot.lights`

It also keeps some compatibility aliases:

- `bot.move`
- `bot.voice`
- `bot.buzzer`
- `bot.sonar`
- `bot.actions`

### `bot.body`

Locomotion and action-group helpers:

- `forward`
- `backward`
- `left`
- `right`
- `turn_left`
- `turn_right`
- `stop`
- `dance`
- `wave`
- `attack`
- `kick`
- `twist`

These are backed by [common/lib/robot_moves.py](common/lib/robot_moves.py) and [common/lib/action_group_lib.py](common/lib/action_group_lib.py).

### `bot.arm`

Arm positioning and gripper helpers:

- `home`
- `ready`
- `move`
- `look`
- `open`
- `half_open`
- `close`
- `set_grip`
- `turn_left`
- `turn_right`
- `center_turn`
- `lift`
- `lower`
- `grab_at`
- `pick`
- `carry`
- `place`

These are backed by [common/lib/arm_lib.py](common/lib/arm_lib.py).

The implementation has been tuned heavily for SpiderPi hardware geometry rather than assuming vendor defaults were correct.

### `bot.camera`

Head/camera gesture helpers:

- `center_all`
- `set_yaw`
- `set_pitch`
- `glance_left`
- `glance_right`
- `look_up`
- `look_down`
- `nod`
- `shake`
- `wiggle`
- `tiny_wiggle`

These are backed by [common/lib/camera_lib.py](common/lib/camera_lib.py).

Important implementation detail:

- `look_up` / `look_down` were remapped to the real top servo
- left/right glance and wiggle use the real arm-turn/head-turn path
- multiple commits adjusted range and speed based on real robot feedback

### `bot.display`

The display path is implemented in [common/lib/display_lib.py](common/lib/display_lib.py).

This library no longer assumes the original OLED text path is the primary visible output. On real SpiderPi hardware, the visible path is the matrix display, so the display layer was adapted around that.

Current display features:

- `text`
- `line`
- `number`
- `clear_matrix`
- `shape`
- `icon`
- `emoji`
- `icons`
- `rps`
- `eyes`
- `look_left`
- `look_right`
- `look_up`
- `look_down`
- `wink`
- `left_wink`
- `center_wink`
- `right_wink`
- `blink`
- `sleep`
- `shut_eyes`
- `wake_up`
- `sleepy_blink`
- `close_left_eye`
- `close_center_eye`
- `close_right_eye`
- `open_left_eye`
- `open_center_eye`
- `open_right_eye`
- `spider`
- `spider_walk`
- `web`
- `smile`
- `triangle`
- `square`
- `diamond`

#### Matrix text behavior

`display.text(...)` was reworked from a not-visibly-working OLED-style path into a matrix text sequencer.

Current behavior:

- each non-empty argument is treated as its own message
- messages are displayed in sequence
- `seconds` is the hold time for each message
- long text scrolls across the matrix

Example:

```python
bot.display.text("Looking", "Center", "Colors", "Snapshot", seconds=1.2)
```

This shows four messages one after the other instead of trying to render four simultaneous OLED lines.

#### Shapes, icons, emoji, and eyes

The display stack now supports:

- general pixel shapes
- a classroom icon set
- animated spider and web patterns
- expressive eye states
- independent three-eye patterns
- left/right rock-paper-scissors matchup rendering

#### RPS display

`bot.display.rps(spider_move, human_move, seconds=3.0)` shows:

- SpiderPi move on the left
- human move on the right

This is used by Lesson 13.

### `bot.vision`

Vision is wrapped through:

- [common/lib/spider_vision_lib.py](common/lib/spider_vision_lib.py)
- [common/lib/vision_lib.py](common/lib/vision_lib.py)

Student-facing methods include:

- `snapshot`
- `capture`
- `find_color`
- `show_color`
- `can_see`
- `count_color`
- `color_position`
- `detect_faces`
- `show_faces`
- `recognize_faces`
- `find_face`
- `recognize_hands`
- `show_hands`
- `detect_hands`
- `detect_pose`
- `show_pose`
- `recognize_pose`
- `find_tag`
- `find_shapes`

Important behavior:

- face detection uses the real MediaPipe-backed path
- hand gesture detection uses the real hand recognition path
- unplugged camera situations return a friendly result dictionary instead of crashing the notebook

### `bot.sound` and `bot.speech`

Sound and speech are backed by:

- [common/lib/buzzer_lib.py](common/lib/buzzer_lib.py)
- [common/lib/tts_lib.py](common/lib/tts_lib.py)

Current sound methods:

- `say`
- `play`
- `rocky`
- `sounds`
- `sound_info`
- `beep`
- `melody`

#### Piper TTS

Piper speech synthesis is wrapped in [common/lib/tts_lib.py](common/lib/tts_lib.py).

Features:

- synthesize text to WAV
- cache synthesized speech
- play generated speech with `aplay`
- queue speech jobs

#### Named WAV playback

Named WAV playback was added to support a Rocky-style soundboard.

Manifest:

- [sounds/rocky_sounds.json](sounds/rocky_sounds.json)

Runtime location expected on the robot:

- `/opt/robot/sounds/rocky_sounds.json`
- `/opt/robot/sounds/*.wav`

Example usage:

```python
bot.sound.play("rocky_fist_my_bump")
bot.sound.rocky("rocky_amaze")
bot.sound.sounds()
bot.sound.sound_info("robot_camera_question")
bot.play_sound("eng_tests_pass")
bot.rocky("rocky_good_good_good")
```

`bot.speech.play(...)` and `bot.speech.rocky(...)` expose the same named playback path.

### `bot.distance`

Distance helpers:

- `cm`
- `mm`
- `is_close`

Backed by [common/lib/sonar_lib.py](common/lib/sonar_lib.py).

The wrapper is lazy and fails with a readable message if sonar hardware is unavailable.

## Compatibility Modules

The repo now includes:

- [common/lib/student_spider.py](common/lib/student_spider.py)
- [common/lib/student_robot.py](common/lib/student_robot.py)
- [common/lib/student_robot_v1.py](common/lib/student_robot_v1.py)

These compatibility wrappers all re-export the same `bot` object from `student_robot_v2`.

## Lesson Integration

Lesson bootstrapping was standardized so lessons import the common library in a predictable way.

Notable lesson-level changes:

- lesson loaders were fixed and simplified
- `time` was exposed through lesson loaders
- lesson speech was largely replaced with `display.text(...)`
- Lesson 1 became a richer display/demo lesson
- Lesson 13 became a tuned rock-paper-scissors interaction with display, buzzer, and vision integration

## Major Engineering Themes in the Commit History

The following themes describe what changed over time.

### 1. Basic project and loader setup

Early commits established the project structure and fixed lesson import order:

- `a2aeef6` Initial commit
- `a892d36` Initial MataSpiderPi project
- `3c016f5` Fix lesson loader import order and document local setup
- `34153d9` Prefer workspace lesson libs and lazy-load SpiderPi sonar
- `ce1bebd` Prefer robot common libs and resolve SpiderPi vendor SDK

### 2. Hardware/runtime stabilization

These commits addressed runtime issues and hardware support:

- `9807a35` Fix SpiderPi runtime dependencies and hardware helpers
- `dd6f771` Stop lesson buzzer tones cleanly
- `455cfd7` Fix SpiderPi buzzer note release and stop behavior
- `e396d8d` Add gpiochip fallback for SpiderPi dot matrix display
- `162bd1b` Handle gpiod API variants and display fallback errors
- `7ac56f3` Pin gpiod to v1 API for SpiderPi display support
- `078b904` Use system Python for SpiderPi matrix display

### 3. Matrix display bring-up

This was a large block of work because the real display mapping differed from assumptions:

- `f83d70a` Normalize SpiderPi matrix display rendering
- `9546450` Add hold time support for SpiderPi display shapes
- `c3b03b2` Add SpiderPi matrix display test patterns
- `ec5c168` Add debug logs for SpiderPi display matrix actions
- `22642f7` Transpose SpiderPi matrix display shapes
- `e886d8a` Render SpiderPi display text on matrix
- `143b107` Scroll and flip SpiderPi matrix text
- `843645c` Sequence SpiderPi matrix text lines
- `0669833` Speed up SpiderPi text scrolling

This sequence moved the display layer from “mostly vendor expectation” to “known-good on real hardware.”

### 4. Arm and camera tuning

Many commits tuned speed, pose, and servo mapping based on physical testing:

- `9f35150` Tune SpiderPi arm home and look poses
- `5685508` Fix SpiderPi camera center pose pitch
- `5a0bda1` Speed up SpiderPi arm pose helpers
- `621cffc` Further speed up SpiderPi arm motions
- `68cdab2` Speed up SpiderPi camera center default
- `dd5c86b` Speed up SpiderPi arm and display defaults
- `0db480a` Further speed up SpiderPi camera motions
- `60e1a44` Fix SpiderPi smile orientation and arm speed
- `5ac3ff7` Further speed up SpiderPi defaults
- `74cfffe` Match SpiderPi arm pose speed to camera
- `ff6ef4a` Speed up SpiderPi direct arm moves
- `0fdf474` Accentuate SpiderPi camera gestures
- `72dd0e2` Add arm turn helpers and stronger camera moves
- `d0bdc2f` Drive SpiderPi camera moves with real servos
- `4d31969` Slow SpiderPi head and turn motions
- `f116e66` Slow SpiderPi camera gestures
- `59cf19a` Widen SpiderPi camera wiggle range
- `0dda4fb` Further widen SpiderPi camera wiggle
- `2571f19` Slow SpiderPi camera wiggle timing
- `87d80dc` Make SpiderPi camera wiggle wider and faster

The practical result is that `camera.center_all()`, glance, look, nod, shake, and wiggle now correspond more closely to the real hardware layout and speeds.

### 5. Vision and camera robustness

Vision capabilities were added and then hardened:

- `566b7c8` Add SpiderPi face detection and faster text
- `79d1c0e` Handle unplugged SpiderPi camera gracefully

The camera path now behaves better in both working and unplugged states.

### 6. Display expressions, icons, and animations

The display became much more expressive:

- `baec669` Add SpiderPi LED eye expressions
- `ef10a56` Refresh SpiderPi demo with eye expressions
- `f03d956` Add animated SpiderPi eye expressions
- `9fd5e26` Sync SpiderPi demo eye and sonar effects
- `7c3457d` Add three-eye SpiderPi LED expressions
- `9d70d3c` Add SpiderPi display icon pack
- `fb81a80` Animate SpiderPi spider display icon
- `640de0a` Add spider walk to lesson 1 display examples

### 7. Lesson API documentation and polish

- `133fe34` Document and expose full SpiderPi demo API
- `08069aa` Expose time from lesson loaders
- `2cb388d` Replace lesson speech with display text

### 8. Demo lesson expansion

The demo lesson was expanded into a real showcase:

- `dca14c5` Expand SpiderPi demo lesson showcase
- `ef10a56` Refresh SpiderPi demo with eye expressions
- `9fd5e26` Sync SpiderPi demo eye and sonar effects

### 9. Lesson 13 rock-paper-scissors flow

Lesson 13 had the largest focused lesson-level iteration:

- `0c5952a` Tune SpiderPi rock paper scissors countdown
- `03a5878` Add buzzer cues to SpiderPi RPS lesson
- `76e19ec` Show RPS matchup on SpiderPi matrix
- `ce03938` Clarify RPS left-right display in lesson 13
- `e161e2b` Tighten SpiderPi lesson 13 game flow
- `d1a5e69` Speed up SpiderPi RPS countdown
- `f8a4d7d` Hide SpiderPi move until hand capture
- `cbb49af` Make SpiderPi RPS countdown much faster
- `472fa24` Speed up SpiderPi RPS countdown flow

The final direction was:

- short display text
- countdown with arm motion and buzzer
- end at `camera.center_all()`
- capture player move first
- reveal robot move after capture
- show left/right matrix matchup
- announce result

### 10. Rocky sound playback

The most recent change added named Rocky-style sound support:

- `f9d1023` Add named Rocky sound playback

This added:

- a manifest file for named sounds
- library helpers to play sounds by key
- compatibility wrappers for v1-style imports

## Current Top-of-Tree Commit History

Newest first:

- `f9d1023` Add named Rocky sound playback
- `472fa24` Speed up SpiderPi RPS countdown flow
- `cbb49af` Make SpiderPi RPS countdown much faster
- `f8a4d7d` Hide SpiderPi move until hand capture
- `d1a5e69` Speed up SpiderPi RPS countdown
- `e161e2b` Tighten SpiderPi lesson 13 game flow
- `640de0a` Add spider walk to lesson 1 display examples
- `0669833` Speed up SpiderPi text scrolling
- `fb81a80` Animate SpiderPi spider display icon
- `ce03938` Clarify RPS left-right display in lesson 13
- `8a2746b` Add display icon examples to lesson 1
- `9d70d3c` Add SpiderPi display icon pack
- `76e19ec` Show RPS matchup on SpiderPi matrix
- `03a5878` Add buzzer cues to SpiderPi RPS lesson
- `0c5952a` Tune SpiderPi rock paper scissors countdown
- `2cb388d` Replace lesson speech with display text
- `843645c` Sequence SpiderPi matrix text lines
- `79d1c0e` Handle unplugged SpiderPi camera gracefully
- `7c3457d` Add three-eye SpiderPi LED expressions
- `9fd5e26` Sync SpiderPi demo eye and sonar effects
- `f03d956` Add animated SpiderPi eye expressions
- `ef10a56` Refresh SpiderPi demo with eye expressions
- `baec669` Add SpiderPi LED eye expressions
- `87d80dc` Make SpiderPi camera wiggle wider and faster
- `2571f19` Slow SpiderPi camera wiggle timing
- `0dda4fb` Further widen SpiderPi camera wiggle
- `e6185b4` Speed up SpiderPi display text again
- `59cf19a` Widen SpiderPi camera wiggle range
- `9bf1315` Slow SpiderPi default body moves
- `133fe34` Document and expose full SpiderPi demo API
- `dca14c5` Expand SpiderPi demo lesson showcase
- `566b7c8` Add SpiderPi face detection and faster text
- `f116e66` Slow SpiderPi camera gestures
- `4d31969` Slow SpiderPi head and turn motions
- `d0bdc2f` Drive SpiderPi camera moves with real servos
- `72dd0e2` Add arm turn helpers and stronger camera moves
- `0fdf474` Accentuate SpiderPi camera gestures
- `ff6ef4a` Speed up SpiderPi direct arm moves
- `08069aa` Expose time from lesson loaders
- `74cfffe` Match SpiderPi arm pose speed to camera
- `5ac3ff7` Further speed up SpiderPi defaults
- `60e1a44` Fix SpiderPi smile orientation and arm speed
- `0db480a` Further speed up SpiderPi camera motions
- `dd5c86b` Speed up SpiderPi arm and display defaults
- `68cdab2` Speed up SpiderPi camera center default
- `621cffc` Further speed up SpiderPi arm motions
- `5a0bda1` Speed up SpiderPi arm pose helpers
- `5685508` Fix SpiderPi camera center pose pitch
- `9f35150` Tune SpiderPi arm home and look poses
- `143b107` Scroll and flip SpiderPi matrix text
- `e886d8a` Render SpiderPi display text on matrix
- `22642f7` Transpose SpiderPi matrix display shapes
- `ec5c168` Add debug logs for SpiderPi display matrix actions
- `c3b03b2` Add SpiderPi matrix display test patterns
- `9546450` Add hold time support for SpiderPi display shapes
- `f83d70a` Normalize SpiderPi matrix display rendering
- `078b904` Use system Python for SpiderPi matrix display
- `7ac56f3` Pin gpiod to v1 API for SpiderPi display support
- `162bd1b` Handle gpiod API variants and display fallback errors
- `e396d8d` Add gpiochip fallback for SpiderPi dot matrix display
- `455cfd7` Fix SpiderPi buzzer note release and stop behavior
- `dd6f771` Stop lesson buzzer tones cleanly
- `9807a35` Fix SpiderPi runtime dependencies and hardware helpers
- `60f01d6` Fallback to OLED when SpiderPi matrix is unavailable
- `ce1bebd` Prefer robot common libs and resolve SpiderPi vendor SDK
- `34153d9` Prefer workspace lesson libs and lazy-load SpiderPi sonar
- `b6a45b0` Map SpiderPi head motions to arm and use home vendor path
- `3c016f5` Fix lesson loader import order and document local setup
- `515e003` Fix README merge conflict and add lesson summaries
- `aec62ee` Merge remote main into local MataSpiderPi
- `a892d36` Initial MataSpiderPi project
- `a2aeef6` Initial commit

## Suggested Reading Order

To understand the repo quickly, read these files in this order:

1. [common/lib/student_robot_v2.py](common/lib/student_robot_v2.py)
2. [common/lib/display_lib.py](common/lib/display_lib.py)
3. [common/lib/arm_lib.py](common/lib/arm_lib.py)
4. [common/lib/camera_lib.py](common/lib/camera_lib.py)
5. [common/lib/spider_vision_lib.py](common/lib/spider_vision_lib.py)
6. [common/lib/tts_lib.py](common/lib/tts_lib.py)
7. [sounds/rocky_sounds.json](sounds/rocky_sounds.json)
8. [lessons/lesson01/demos/Robot_Demo.ipynb](lessons/lesson01/demos/Robot_Demo.ipynb)
9. [lessons/lesson13/level_1/Lesson13.ipynb](lessons/lesson13/level_1/Lesson13.ipynb)
