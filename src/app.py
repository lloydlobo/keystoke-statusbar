#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Inspiration: https://github.com/petternett/railway-statusbar
"""

from pynput import keyboard
import threading
import time
import random
# from emoji import emojize

WIDTH = 10
PLAYER_POSITION = 3

FPS = 30
DELAY = 1.0 / FPS
MAX_SPEED = 1
FRICTION_CONST = 0.8
velocity = 0.0
total_km = 0.0
curr_key = None
typed_history = []
typed_history_cache = []

RAIL_CHAR = '..'
PLAYER_CHAR = "#"
FIRE_CHAR = "`"
CACTUS_CHAR = "|"
HILL_CHAR = "~"

world = [None] * WIDTH
foreground = [None] * WIDTH
background = [None] * WIDTH
PARA_CONST = 9
MAX_PARA_ELEMENTS = 2

fire_disp = 0
hill_count = 0
MAX_HILL_COUNT = 3

new_press_event = None
key_pressed = False

listener_paused = False

debug_text = None


start_time_wpm = time.time()
char_count_wpm = 0
wpm_timer_start = None
wpm_timer_end = None  # For 200 entries or key press
curr_round_wpm = 0.0


def calculate_wpm(char_count, elapsed_time):
    AVERAGE_WORD_LEN = 5
    words = char_count/AVERAGE_WORD_LEN
    minutes = elapsed_time / 60
    wpm = words / minutes
    return round(wpm/1000, 2)


def get_wpm(len_entries, wpm_timer_start, wpm_timer_end):
    AVERAGE_WORD_LEN = 5
    elapsed_time = wpm_timer_end - wpm_timer_start
    words = len_entries / AVERAGE_WORD_LEN
    minutes = elapsed_time / 60
    wpm = words/minutes
    return round(wpm, 2)


def render():
    global fire_disp, curr_key, typed_history, typed_history_cache
    global wpm_timer_start, wpm_timer_end, curr_round_wpm

    # DEBUG
    # print(f"{curr_key} ", end="")

    # Compose text world.
    world = [x for x in background]

    for i in range(0, WIDTH):
        if foreground[i] is not None:
            world[i] = foreground[i]
        elif world[i] is None:
            world[i] = RAIL_CHAR

    world[PLAYER_POSITION] = PLAYER_CHAR
    if velocity > 0.9:
        world[PLAYER_POSITION - 1] = FIRE_CHAR
        if fire_disp % 3 == 0 or fire_disp % 2 == 0:
            world[PLAYER_POSITION - 2] = FIRE_CHAR
        fire_disp += 1

    global listener_paused

    if listener_paused:
        print('Escape to resume')
        return

    for i in range(0, WIDTH - 1):
        print(world[i], end="")
    print(f"{total_km:.2f}km/", end="")

    if wpm_timer_start is None and len(typed_history) > 0:
        wpm_timer_start = time.time()

    if len(typed_history) >= 200:
        if len(typed_history_cache) >= 5:
            typed_history_cache.clear()
        typed_history_cache.append(typed_history)
        typed_history.clear()
        wpm_timer_end = time.time()

    if curr_round_wpm is not None:
        print(
            f"{curr_round_wpm}wpm", end="")
    else:
        no_wpm = 0
        # print(f"{no_wpm:.2f}wpm/{len(typed_history):3}/", end="")
        print(f"{no_wpm:.2f}wpm", end="")

    if wpm_timer_end is not None:
        wpm_timer_end = time.time()
        len_entries = 200
        curr_round_wpm = get_wpm(
            len_entries, wpm_timer_start, wpm_timer_end)
        print(
            f"{curr_round_wpm}wpm", end="")
        wpm_timer_start = None
        wpm_timer_end = None
    # print(f"Total km: {total_km:.2f} ", end="")
    print()

    if debug_text:
        print(f"DEBUG: {debug_text}")


def debug(text):
    global debug_text
    debug_text = text


def pause_listener():
    global listener_paused
    listener_paused = True


def resume_listener():
    global listener_paused
    listener_paused = False


# def on_press(key):
#     global key_pressed, char_counter
#     if not listener_paused:
#         char_counter += 1
#         try:
#             key_pressed = True  # 'alphanumeric key {0} pressed'
#             # print('{0}'.format(key.char),)
#             # print('{0}'.format(key.char), end='', flush=True)
#         except AttributeError:
#             key_pressed = True  # 'special key {0} pressed'
#             # print('{0}'.format(key), )
#             # print('{0}'.format(key), end='', flush=True)


def on_release(key):
    global typed_history, new_press_event, key_pressed, listener_paused, curr_key
    new_press_event.set()
    key_pressed = True  # False if using on_press.
    try:
        curr_key = format(key.char)
        typed_history.append(curr_key)
    except AttributeError:
        key_char = str(key).replace("Key.", "")
        curr_key = format(key_char)
        typed_history.append(curr_key)

    if key == keyboard.Key.esc:
        if not listener_paused:
            listener_paused = True
        else:
            listener_paused = False
        # return False # Stop listener.


def run():
    global foreground, background, new_press_event, key_pressed, total_km, velocity, hill_count

    ax = 0.0
    counter = 0.0
    para = 0

    new_press_event = threading.Event()
    # Non-Blocking: Collect events until released.
    listener = keyboard.Listener(on_release=on_release)
    listener.start()

    render()  # Initial rendering.

    # App loop:
    # - Process input.
    # - Update world, physics.
    # - Render output.
    # - Sleep.
    while True:
        # For when we need >1 events per tick.
        n_events = 0
        # Process user input. If key event happens during tick:
        if (key_pressed):
            n_events += 1
            key_pressed = False
            # last_activity_time = time.time()
        elif n_events > 0:
            n_events -= 1

        if n_events > 0:
            ax += 0.02
        elif velocity > 0:
            ax -= 0.005
        elif velocity <= 0:
            ax = 0
            velocity = 0

        # debug(f"velocity: {velocity}, ax: {ax}")
        velocity += ax - velocity * FRICTION_CONST
        velocity = min(velocity, MAX_SPEED)
        if velocity == 0:
            new_press_event.wait()
            new_press_event.clear()

        curr_time = time.time()

        counter += velocity

        if counter >= 1:
            foreground.pop(0)
            if random.randint(0, FPS/2) == 1:
                foreground.append(CACTUS_CHAR)
            else:
                foreground.append(None)

            if para == 0:
                if background[0] == HILL_CHAR:
                    hill_count -= 1

                background.pop(0)
                if random.randint(0, 2) == 1 and hill_count < MAX_HILL_COUNT:
                    background.append(HILL_CHAR)
                    hill_count += 1
                else:
                    background.append(None)

            para += 1
            para %= PARA_CONST
            counter -= 1
            total_km += 0.01

        render()

        time.sleep(curr_time + DELAY - time.time())


if __name__ == "__main__":
    run()


"""

"""
