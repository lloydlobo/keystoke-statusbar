#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Inspiration: https://github.com/petternett/railway-statusbar/blob/main/src/railway.py
"""

from pynput import keyboard
import threading

new_press_event = None
key_pressed = False
listener_paused = False

debug_text = None


def render():
    print("Hello, world!")


def pause_listener():
    global listener_paused
    listener_paused = True


def resume_listener():
    global listener_paused
    listener_paused = False


def on_press(key):
    global key_pressed
    if not listener_paused:
        try:
            key_pressed = True  # 'alphanumeric key {0} pressed'
            print('°'+'{0}'.format(key.char))
        except AttributeError:
            key_pressed = True  # 'special key {0} pressed'
            print('°'+'{0}'.format(key))
        pass
    pass


def on_release(key):
    global new_press_event, key_pressed, listener_paused
    if (new_press_event is not None):
        new_press_event.set()
    key_pressed = False

    if not listener_paused:
        try:
            print('{0}'.format(key.char))
        except AttributeError:
            print('{0}'.format(key))
        pass
    else:
        print('Escape to resume')

    if key == keyboard.Key.esc:
        if not listener_paused:
            listener_paused = True
        else:
            listener_paused = False
        # return False # Stop listener.
    pass


def run():
    global new_press_event, key_pressed

    new_press_event = threading.Event()

    # Non-Blocking: Collect events until released.
    listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release,
    )
    listener.start()

    render()  # Initial rendering.

    # App loop.
    while True:
        # For when we need >1 events per tick.
        n_events = 0
        # Process user input. If key event happens during tick:
        if (key_pressed):
            n_events += 1
            key_pressed = False
        elif n_events > 0:
            n_events -= 1
        pass

    pass


if __name__ == "__main__":
    run()
