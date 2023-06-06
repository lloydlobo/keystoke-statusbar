#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Keystrokes

Inspiration: https://github.com/petternett/railway-statusbar
"""

from collections import deque
from random import randint
from time import time, sleep
from threading import Event, Thread
from typing import List, Union  # Literal, Optional

from pynput import keyboard  # from emoji import emojize

WIDTH: int = 16
PLAYER_POSITION: int = 3  # [..][..][..][v.][RAIL_CHAR]....

FPS: int = 30
FRAME_DELAY: float = 1.0 / FPS
MAX_SPEED: int = 1
FRICTION_CONST: float = 0.8

RAIL_CHAR: str = '__'
PLAYER_CHAR: str = ''
FIRE_CHAR: str = '='
CLOUD_CHAR: str = ''
TREE_CHAR: str = ''

MAX_CLOUDS: int = 3
PARA_CONST: int = 9
MAX_PARA_ELEMENTS: int = 2

WPM_KEYS_PER_ROUND: int = 200
WPM_AVERAGE_WORD_LEN: int = 5


def get_wpm(len_entries, time_start, time_end) -> float:
    if time_start is not None and time_end is not None:
        elapsed_time = time_end - time_start
        minutes = elapsed_time / 60
        words = len_entries / WPM_AVERAGE_WORD_LEN
        return round(words / minutes, 2)
    else:
        raise ValueError("Invalid `timer_start` or `timer_end` values.\
                         Expected `float` found `None`.")


class App:
    def __init__(self):
        # Numeric members.
        self.velocity: float = 0.0
        self.total_km: float = 0.0
        self.fire_disp: int = 0
        self.cloud_count: int = 0

        # Key-related members.
        self.curr_key: Union[str, None] = None
        self.key_pressed: bool = False
        self.new_key_event: Union[Event, None] = None
        self.listener_paused: bool = False

        # Time-related members.
        self.wpm_timer_start: Union[float, None] = None
        self.wpm_timer_end: Union[float, None] = None  # For 200 key releases.
        self.curr_round_wpm: float = 0.0

        # Text-related members.
        self.key_history: List[str] = []
        self.key_history_cache: List[List[str]] = []
        self.debug_text: Union[str, None] = None

        # World-related members.
        self.foreground: deque[Union[str, None]] = deque([None] * WIDTH)
        self.background: deque[Union[str, None]] = deque([None] * WIDTH)

    def render(self) -> None:
        """
        - Merge background and foreground to compose world (`List[str]`).
          - `self.foreground[i]` is assigned to `world[i]` if not None.
          - else, assign `self.background[i]` if not None else `RAIL_CHAR`.
        - Track, and record keypress count for each round to calculate wpm.
        - Concatenate a single buffer with message modules and print the frame.
        """

        world = [fg or bg or RAIL_CHAR for (fg, bg) in zip(
            self.foreground, self.background)]
        world[PLAYER_POSITION] = PLAYER_CHAR
        if self.velocity > 0.9:
            world[PLAYER_POSITION-1] = FIRE_CHAR
            if self.fire_disp % 3 == 0 or self.fire_disp % 2 == 0:
                world[PLAYER_POSITION-2] = FIRE_CHAR
            self.fire_disp += 1

        key_count = len(self.key_history)
        if self.wpm_timer_start is None and key_count > 0:
            self.wpm_timer_start = time()
        if key_count >= WPM_KEYS_PER_ROUND:
            self.wpm_timer_end = time()
            if len(self.key_history_cache) >= 3:
                self.key_history_cache.clear()
            self.key_history_cache.append(self.key_history)
            self.key_history.clear()
        if self.wpm_timer_end is not None:
            self.curr_round_wpm = get_wpm(
                WPM_KEYS_PER_ROUND, self.wpm_timer_start, self.wpm_timer_end,)
            self.wpm_timer_start = None
            self.wpm_timer_end = None

        scene = []
        scene.append("".join(world))
        scene.append(f"{self.curr_key:<5}"
                     if not self.listener_paused and self.curr_key is not None
                     else "Escape to resume")
        scene.append(f"{self.total_km:.2f}km")
        scene.append(f"{self.curr_round_wpm:.2f}wpm"
                     if self.curr_round_wpm is not None else "0.00wpm")
        scene.append(f"{key_count:<3}")

        if self.debug_text:
            print(f"DEBUG: {self.debug_text}", end=" ")

        print(" ".join(scene))  # Print current frame's buffer.

    def on_release(self, key) -> None:
        assert isinstance(self.new_key_event, Event) or (
            self.new_key_event is None, "should be an Event on key release")
        if self.new_key_event is not None:
            self.new_key_event.set()

        self.key_pressed = True  # False if using on_press.
        try:
            self.curr_key = format(key.char)
        except AttributeError:
            key_char = str(key).replace("Key.", "")
            self.curr_key = format(key_char)

        self.key_history.append(self.curr_key)

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
        self.new_key_event = Event()
        listener = keyboard.Listener(on_release=self.on_release)
        listener.start()

        self.render()  # Initial rendering.

        # App loop: (while 1 is faster than while True)
        # Process input -> Update world, physics -> Render output -> Sleep.
        while 1:
            n_events = 0  # For when we need >1 events per tick.
            if (self.key_pressed):
                n_events += 1  # Key press event. poll tick.
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
                self.new_key_event.wait()
                self.new_key_event.clear()

            curr_time = time()
            counter += self.velocity

            if counter >= 1:
                frame_has_tree = randint(0, FPS // 2) == 1  # floor max int.
                # self.foreground.pop(0)
                self.foreground.popleft()
                self.foreground.append(TREE_CHAR if frame_has_tree else None)

                if para == 0:
                    should_cloud_disappear = self.background[0] == CLOUD_CHAR
                    self.cloud_count -= 1 if should_cloud_disappear else 0
                    can_rain = (self.cloud_count < MAX_CLOUDS
                                and randint(0, 2) == 1)
                    # self.background.pop(0)
                    self.background.popleft()
                    self.background.append(CLOUD_CHAR if can_rain else None)
                    self.cloud_count += 1 if can_rain else 0

                para += 1
                para %= PARA_CONST  # Reset periodically.

                counter -= 1
                self.total_km += 0.01

            self.render()
            sleep(curr_time + FRAME_DELAY - time())

    # TODO: for neorun. user controlled pauses.
    def update(self, frame_delay) -> None:
        pass

    # TODO: for neorun. user controlled pauses.
    def neorun(self) -> None:
        def keyboard_listener() -> None:
            with keyboard.Listener(on_release=self.on_release) as listener:
                listener.join()

        listener_thread = Thread(target=keyboard_listener, daemon=True)
        listener_thread.start()

        while 1:
            if self.new_key_event is not None:
                self.new_key_event.wait()
                self.new_key_event.clear()

            if not self.listener_paused:
                self.update(FRAME_DELAY)
                self.render()

            time.sleep(FRAME_DELAY)


if __name__ == "__main__":
    animation = App()
    animation.run()


"""
    # frame_start_time = time.monotonic()
    ...
    # NOTE: DO NOT USE THIS, as no delay leads to appending
    # multiple chars to `world` background foreground.
    # frame_elapsed_time = time.monotonic() - frame_start_time
    # if frame_elapsed_time < FRAME_DELAY: sleep(FRAME_DELAY
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

    #   - Assign values from self.background. Assign `RAIL_CHAR` if None.
    #   - Assign values from self.foreground. Keeps existing if None.
    # self.world = [bg if bg is not None else RAIL_CHAR
    #               for bg in self.background]
    # self.world = [fg if fg is not None else self.world[i]
    #               for i, fg in enumerate(self.foreground)]

    # for i in range(0, WIDTH):
    #     if self.foreground[i] is not None:
    #         self.world[i] = self.foreground[i]
    #     elif self.world[i] is None:
    #         self.world[i] = RAIL_CHAR

    # world = [fg if fg is not None
    #          else (bg if bg is not None else RAIL_CHAR)
    #          for fg, bg in zip(self.foreground, self.background)]

    # World-related members.
    # self.foreground: List[Union[str, None]] = [None] * WIDTH
    # self.background: List[Union[str, None]] = [None] * WIDTH

    # https://stackoverflow.com/a/57438344
    # In answer to your question, deques are ever-so-slightly more efficient
    # for use as stacks than lists; if you're importing collections anyway, and
    # need a stack based structure, using a deque will get you a tiny benefit
    # (at # least on CPython, can't speak to other implementation). But it's
    # not # really worth micro-optimizing here the cost of
    # importing collections in # the first place, and the cost of
    # whatever useful code you execute based on this stack, likely
    # dwarfs whatever tiny difference you'll see between list and deque for
    # pops from the right. A simple ipython3 microbenchmark:

    # https://stackoverflow.com/a/50804541
    # deque object changes the start of the list pointer and "forgets" the
    # oldest item. it's faster and it's one of the usages it's been
    # designed for.

    # scene = []
    # scene.append("".join(world))
    # scene.append(f"<Esc>: Toggle keys" if self.listener_paused else f"{self
                                                             .curr_key: <5}")
    # scene.append(f"{self.total_km:.2f}km")
    # scene.append(f"{self.curr_round_wpm:.2f}wpm" if self.curr_round_wpm
                   is not None else "0.00wpm")
    # scene.append(f"{key_count:<3}")
    # scene.append(f"{self.curr_key:<5}" if not self.listener_paused and self
                   .curr_key is not None else "Escape to resume")

"""
