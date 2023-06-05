#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Keystrokes

Inspiration: https://github.com/petternett/railway-statusbar
"""

import threading
import time
import random

from typing import List, Union  # Literal, Optional

from pynput import keyboard  # from emoji import emojize

WIDTH: int = 12
PLAYER_POSITION: int = 3  # [..][..][..][v.][RAIL_CHAR]....

FPS: int = 30
FRAME_DELAY: float = 1.0 / FPS
MAX_SPEED: int = 1
FRICTION_CONST: float = 0.8

RAIL_CHAR: str = '..'
PLAYER_CHAR: str = '#'
FIRE_CHAR: str = '`'
TREE_CHAR: str = '|'
HILL_CHAR: str = '~'

MAX_HILL_COUNT: int = 3
PARA_CONST: int = 9
MAX_PARA_ELEMENTS: int = 2

WPM_CHARS_PER_ROUND: int = 200
WPM_AVERAGE_WORD_LEN: int = 5


def get_wpm(len_entries, time_start, time_end) -> float:
    if time_start is not None and time_end is not None:
        elapsed_time = time_end - time_start
        minutes = elapsed_time / 60
        words = len_entries / WPM_AVERAGE_WORD_LEN
        return round(words / minutes, 2)
    else:
        raise ValueError("Invalid `wpm_timer_start` or `wpm_timer_end` \
                         values. Expected `float` found `None`.")


class App:
    def __init__(self):
        # Numeric members.
        self.velocity: float = 0.0
        self.total_km: float = 0.0
        self.fire_disp: int = 0
        self.hill_count: int = 0
        self.char_count_wpm: int = 0

        # Key-related members.
        self.curr_key: Union[str, None] = None
        self.key_pressed: bool = False
        self.new_press_event: Union[threading.Event, None] = None
        self.listener_paused: bool = False

        # Time-related members.
        self.start_time_wpm: float = time.time()
        self.wpm_timer_start: Union[float, None] = None
        self.wpm_timer_end: Union[float, None] = None  # For 200 key releases.
        self.curr_round_wpm: float = 0.0

        # Text-related members.
        self.typed_history: List[str] = []
        self.typed_history_cache: List[List[str]] = []
        self.debug_text: Union[str, None] = None

        # World-related members.
        self.world: List[Union[str, None]] = [None] * WIDTH
        self.foreground: List[Union[str, None]] = [None] * WIDTH
        self.background: List[Union[str, None]] = [None] * WIDTH

    # - Merge background and foreground to compose world.
    #   - Assign values from self.background. Assign `RAIL_CHAR` if None.
    #   - Assign values from self.foreground. Keeps existing if None.
    # - Collect data to calculate wpm.
    # - Concatenate a single buffer with message modules and print per frame.
    def render(self) -> None:
        # PERF: self.world is used inside `render()` scope only. Consider
        # using local variable.
        self.world = [bg if bg is not None else RAIL_CHAR
                      for bg in self.background]
        self.world = [fg if fg is not None else self.world[i]
                      for i, fg in enumerate(self.foreground)]
        self.world[PLAYER_POSITION] = PLAYER_CHAR

        if self.velocity > 0.9:
            self.world[PLAYER_POSITION - 1] = FIRE_CHAR
            if self.fire_disp % 3 == 0 or self.fire_disp % 2 == 0:
                self.world[PLAYER_POSITION - 2] = FIRE_CHAR
            self.fire_disp += 1

        len_total = len(self.typed_history)
        if self.wpm_timer_start is None and len_total > 0:
            self.wpm_timer_start = time.time()

        if len_total >= WPM_CHARS_PER_ROUND:
            if len(self.typed_history_cache) >= 5:
                self.typed_history_cache.clear()
            self.typed_history_cache.append(self.typed_history)
            self.typed_history.clear()
            self.wpm_timer_end = time.time()

        if self.wpm_timer_end is not None:
            # self.wpm_timer_end = time.time() # HACK: Set timer twice?
            self.curr_round_wpm = get_wpm(
                WPM_CHARS_PER_ROUND, self.wpm_timer_start, self.wpm_timer_end)
            self.wpm_timer_start = None
            self.wpm_timer_end = None

        # Prepare the output modules for final string buffer.
        output_module = []

        # Construct [output-] [-module] to join into [-string] later.
        filtered_world = [item for item in self.world if item is not None]
        # output_buffer += "{:<{width}}".format(
        # "".join(filtered_world), width=(2*WIDTH))
        output_module.append("{:<{width}}".format(
            "".join(filtered_world), width=(2*WIDTH)))
        if self.listener_paused:
            output_module.append("<Esc>: Toggle keys ")
        else:
            # 9 chars max <Backspace> 5 for <shift>
            output_module.append("{:<{width}}".format(
                f"{self.curr_key} "
                if self.curr_key is not None else "", width=5,))
        output_module.append("{:.2f}km/".format(self.total_km))
        output_module.append("{:<4}".format(
            "{}wpm/".format(self.curr_round_wpm)
            if self.curr_round_wpm is not None else "0.00wpm"))
        output_module.append("{:<3}\n".format(len_total))

        print("".join(output_module))  # Print current frame's buffer.

        if self.debug_text:
            print(f"DEBUG: {self.debug_text}")

    def on_release(self, key) -> None:
        assert isinstance(
            self.new_press_event, threading.Event
        ) or (
            self.new_press_event is None,
            "new_press_event must be an instance of Event or None"
        )

        if self.new_press_event is not None:
            self.new_press_event.set()

        self.key_pressed = True  # False if using on_press.

        try:
            self.curr_key = format(key.char)
        except AttributeError:
            key_char = str(key).replace("Key.", "")
            self.curr_key = format(key_char)

        self.typed_history.append(self.curr_key)

        if key == keyboard.Key.esc:
            self.listener_paused = not self.listener_paused
            # return False # Stop listener.

    def debug(self, text: str) -> None:
        self.debug_text = text

    def pause_listener(self) -> None:
        self.listener_paused = True

    def resume_listener(self) -> None:
        self.listener_paused = False

    def run(self) -> None:
        accelaration = 0.0
        counter = 0.0
        para = 0

        # Non-Blocking: Collect events until released.
        self.new_press_event = threading.Event()
        listener = keyboard.Listener(on_release=self.on_release)
        listener.start()

        self.render()  # Initial rendering.

        # App loop: (while 1 is faster than while True)
        # Process input -> Update world, physics -> Render output -> Sleep.
        while 1:
            # For when we need >1 events per tick.
            n_events = 0
            # Process user input. If key event happens during tick:
            if (self.key_pressed):
                n_events += 1
                self.key_pressed = False
            elif n_events > 0:
                n_events -= 1

            if n_events > 0:
                accelaration += 0.02
            elif self.velocity > 0:
                accelaration -= 0.005
            elif self.velocity <= 0:
                accelaration = 0
                self.velocity = 0

            # debug(f"velocity: {velocity}, ax: {ax}")
            self.velocity += accelaration - self.velocity * FRICTION_CONST
            self.velocity = min(self.velocity, MAX_SPEED)

            if self.velocity == 0:
                self.new_press_event.wait()
                self.new_press_event.clear()

            curr_time = time.time()
            counter += self.velocity

            if counter >= 1:
                self.foreground.pop(0)
                # `//` gets upper-bound(largest integer) floor division result.
                if random.randint(0, FPS // 2) == 1:
                    self.foreground.append(TREE_CHAR)
                else:
                    self.foreground.append(None)

                if para == 0:
                    if self.background[0] == HILL_CHAR:
                        self.hill_count -= 1

                    self.background.pop(0)

                    if (random.randint(0, 2) == 1
                            and self.hill_count < MAX_HILL_COUNT):
                        self.background.append(HILL_CHAR)
                        self.hill_count += 1
                    else:
                        self.background.append(None)

                para += 1
                para %= PARA_CONST

                counter -= 1
                self.total_km += 0.01

            self.render()

            # PERF: BONUS speed up animation if velocity is high.
            # Now, User has to wait for all frames to render or catch up.
            time.sleep(curr_time + FRAME_DELAY - time.time())


if __name__ == "__main__":
    animation = App()
    animation.run()


"""
    # frame_start_time = time.monotonic()
    ...
    # NOTE: DO NOT USE THIS, as no delay leads to appending
    # multiple chars to `world` background foreground.
    # frame_elapsed_time = time.monotonic() - frame_start_time
    # if frame_elapsed_time < FRAME_DELAY: time.sleep(FRAME_DELAY
                                                      - frame_elapsed_time)

    # def on_press(key):
    #     if not listener_paused:
    #         try:
    #             key_pressed = True  # 'alphanumeric key {0} pressed'
    #             # print('{0}'.format(key.char), end='', flush=True)
    #         except AttributeError:
    #             key_pressed = True  # 'special key {0} pressed'
    #             # print('{0}'.format(key), end='', flush=True)


    # world = [x for x in self.background]  # Compose text world.
    # for i in range(0, WIDTH):
    #    if self.foreground[i] is not None:
    #        world[i] = self.foreground[i]
    #    elif world[i] is None:
    #        world[i] = RAIL_CHAR
    # OR
    # Clone and apply RAIL tracks if empty.
    # world = [x if x is not None else RAIL_CHAR for x in self.background]
    # world = [value if value is not None else world[i] for i, value
    #          in enumerate(self.foreground)]

"""
