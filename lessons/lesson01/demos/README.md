# SpiderPi Demo Guide

This demo folder is the quickest way to show the full SpiderPi feature set with the current MataSpiderPi API.

## Start

Use the demo notebook:

- `Robot_Demo.ipynb`

It uses the student API:

```python
from lesson_loader import setup
setup()
from student_robot_v2 import bot
```

## Main Namespaces

- `bot.body`: walking and action-group body motion
- `bot.arm`: arm, gripper, and arm turn helpers
- `bot.camera`: head/camera style moves
- `bot.display`: matrix display text, shapes, and numbers
- `bot.lights`: RGB and sonar light control
- `bot.vision`: camera, color vision, face detection, and hand recognition
- `bot.sound`: buzzer and melody helpers
- `bot.speech`: text-to-speech
- `bot.distance`: ultrasonic distance sensor

## Body Moves

```python
bot.body.forward(0.6)
bot.body.backward(0.6)
bot.body.left(0.6)
bot.body.right(0.6)
bot.body.turn_left(0.5)
bot.body.turn_right(0.5)
bot.body.stop()
```

Action-group body moves:

```python
bot.body.dance()
bot.body.wave()
bot.body.attack()
bot.body.kick()
bot.body.twist()
```

## Arm Moves

Basic poses:

```python
bot.arm.home()
bot.arm.ready()
bot.arm.look()
bot.arm.carry()
bot.arm.place()
```

Direct positioning:

```python
bot.arm.move(0, 12, 22, seconds=0.4)
bot.arm.move(-4, 12, 22, seconds=0.4)
bot.arm.move(4, 12, 22, seconds=0.4)
```

Turn helpers:

```python
bot.arm.turn_left()
bot.arm.center_turn()
bot.arm.turn_right()
```

Arm height helpers:

```python
bot.arm.lift()
bot.arm.lower()
```

Gripper:

```python
bot.arm.open()
bot.arm.half_open()
bot.arm.close()
bot.arm.set_grip(300, seconds=0.2)
```

Pick helpers:

```python
bot.arm.grab_at(0, 15, 8)
bot.arm.pick(0, 15, 8)
```

## Camera Moves

Center pose:

```python
bot.camera.center_all()
```

Turn and tilt:

```python
bot.camera.glance_left()
bot.camera.glance_right()
bot.camera.look_up()
bot.camera.look_down()
```

Servo-style control:

```python
bot.camera.set_yaw(1500)
bot.camera.set_pitch(1500)
```

Expressive gestures:

```python
bot.camera.nod()
bot.camera.shake()
bot.camera.wiggle()
bot.camera.tiny_wiggle()
```

## Display

Text:

```python
bot.display.text("HELLO", "", "", "", seconds=2)
bot.display.line(1, "TEST", seconds=2)
```

Shapes and numbers:

```python
bot.display.smile(seconds=2)
bot.display.triangle(seconds=2)
bot.display.square(seconds=2)
bot.display.diamond(seconds=2)
bot.display.number(42, seconds=2)
bot.display.clear_matrix()
```

## Lights

```python
bot.lights.red()
bot.lights.green()
bot.lights.blue()
bot.lights.yellow()
bot.lights.purple()
bot.lights.off()
```

## Sound And Display

```python
bot.sound.beep(2200, 0.1)
bot.sound.melody("C4:0.5 E4:0.5 G4:1", bpm=180)
bot.display.text("Hello", "From SpiderPi", seconds=1.0)
```

## Vision

Snapshot:

```python
bot.vision.snapshot(show=True)
```

Color vision:

```python
bot.vision.find_color("red", show=True)
bot.vision.can_see("red")
bot.vision.count_color("red")
bot.vision.color_position("red")
```

Face detection:

```python
bot.vision.find_face()
bot.vision.show_faces(show=True)
```

Hand recognition:

```python
bot.vision.show_hands(show=True)
bot.vision.detect_hands(show=True)
```

## Distance

```python
bot.distance.cm()
bot.distance.mm()
bot.distance.is_close(25)
```

## Recommended Showcase Order

1. `bot.display.text("SpiderPi Show", "", "", "", seconds=1)`
2. `bot.lights.purple()`
3. `bot.body.forward(0.6)`
4. `bot.camera.center_all()`
5. `bot.camera.glance_left()`
6. `bot.camera.glance_right()`
7. `bot.arm.turn_left()`
8. `bot.arm.turn_right()`
9. `bot.vision.show_faces(show=True)`
10. `bot.vision.show_hands(show=True)`
11. `bot.body.dance()`

## Notes

- The SpiderPi display uses the front LED matrix for visible text and icons.
- Face and hand detection need the camera pointed at the person and enough light.
- The camera and arm are mechanically linked, so some camera-style moves also affect the arm posture.
