#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Keystrokes

Inspiration: https://github.com/petternett/railway-statusbar
"""

from collections import deque
from random import randint
from time import time, sleep, perf_counter
from threading import Event, Thread
from typing import List, Union  # Literal, Optional

from pynput import keyboard  # from emoji import emojize

from keybindings import keyboard_mappings

WIDTH: int = 16
PLAYER_POSITION: int = 3  # [__][__][__][PLAYER_CHAR_][RAIL_CHAR]....

FPS: int = 30
FRAME_DELAY: float = 1.0 / FPS
MAX_SPEED: int = 1
FRICTION_CONST: float = 0.8

RAIL_CHAR: str = '_'
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


linux_modifier_keys = {
    "space": "␣",  # Space key
    "enter": "⏎",  # Enter key
    "shift": "⇧",  # Shift key
    "ctrl": "⌃",  # Control key
    "ctrl_r": "⌃",  # Control key
    "alt": "⌥",  # Option (Alt) key
    "cmd": "⌘",  # Command (Apple) key
    "cmd_r": "⌘",  # Command (Apple) key
    "menu": "menu",  # Command (Apple) key
    "caps_lock": "⇪",  # Caps Lock key
    "tab": "⇥",  # Tab key
    "delete": "⌫",  # Delete (Backspace) key
    "esc": "⎋",  # Escape key
    "f1": "f1",  # Function (Fn) key
}


def get_mod_key_symbol(mod_key: str):
    key = mod_key.lower()
    if key in linux_modifier_keys:
        return linux_modifier_keys[key]
    else:
        return ""


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
        self.should_reset = False

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

        is_enabled = False
        if is_enabled:
            world = [fg or bg or RAIL_CHAR for (fg, bg) in zip(
                self.foreground, self.background)]
            world[PLAYER_POSITION] = PLAYER_CHAR
            if self.velocity > 0.9:
                world[PLAYER_POSITION-1] = FIRE_CHAR
                if self.fire_disp % 3 == 0 or self.fire_disp % 2 == 0:
                    world[PLAYER_POSITION-2] = FIRE_CHAR
                self.fire_disp += 1

        keytar = [fg or bg or RAIL_CHAR for (fg, bg) in zip(
            self.foreground, self.background)]

        # TODO: calculate key_count outside on key_release event. Loop runs
        # 6x times for each keypress, or increment counter at each key press.
        key_count = len(self.key_history)

        if self.wpm_timer_start is None and key_count > 0:
            self.wpm_timer_start = time()
        if key_count >= WPM_KEYS_PER_ROUND:
            self.wpm_timer_end = time()
            # TODO: Use a more efficient approach to handle the self
            # .key_history_cache list. Instead of clearing the list
            # and appending elements each time, you can use a deque with
            # a maximum length to maintain a sliding window of the last
            # three key history lists:
            # self.key_history_cache = deque(self.key_history_cache, maxlen=3)
            # self.key_history_cache.append(self.key_history.copy())

            if len(self.key_history_cache) >= 3:
                self.key_history_cache.clear()
            self.key_history_cache.append(self.key_history)
            self.key_history.clear()
        if self.wpm_timer_end is not None:
            self.curr_round_wpm = get_wpm(
                WPM_KEYS_PER_ROUND, self.wpm_timer_start, self.wpm_timer_end,)
            self.wpm_timer_start = self.wpm_timer_end = None

        scene: List[str] = []
        if self.listener_paused:
            scene.append("ctrl+alt+h to resume")
        else:
            is_enabled = False
            if is_enabled:
                pressed = self.curr_key if self.curr_key is not None else ""
                maps = keyboard_mappings.get(pressed)
                map_str = str(maps)
                map_of_map = keyboard_mappings.get(map_str)
                scene.append(
                    f"{pressed}|{map_str}|{map_of_map}")

            # scene.append("".join(world))
            scene.append("".join(keytar))

        scene.append(f"{self.total_km:.2f}km")
        scene.append(f"{self.curr_round_wpm:.2f}wpm"
                     if self.curr_round_wpm is not None else "0.00wpm")
        scene.append(f"{key_count:<3}")

        if self.debug_text:
            print(f"DEBUG: {self.debug_text}", end=" ")

        print(" ".join(scene))  # Print current frame's buffer.

    def on_activate_h(self):
        print('ctrl-alt-h pressed: Halt ')
        self.listener_paused = not self.listener_paused

    def on_activate_i(self):
        print('ctrl-alt-i pressed: Reseting')
        self.should_reset = not (self.should_reset)

    def on_release(self, key) -> None:
        assert isinstance(self.new_key_event, Event) or (
            self.new_key_event is None, "should be an Event on key release")
        if self.new_key_event is not None:
            self.new_key_event.set()

        self.key_pressed = True  # False if using on_press.
        try:
            self.curr_key = f"{key.char}"
        except AttributeError:
            self.curr_key = f"{key}".replace("Key.", "")

        self.key_history.append(self.curr_key)

        # if key == keyboard.Key.esc:
        #     self.listener_paused = not self.listener_paused
        #     # return False # Stop listener.

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

        global_hot_keys = keyboard.GlobalHotKeys({
            '<ctrl>+<alt>+h': self.on_activate_h,
            '<ctrl>+<alt>+i': self.on_activate_i,  # reset
        })
        global_hot_keys.start()

        # Non-Blocking: Collect events until released.
        self.new_key_event = Event()
        listener = keyboard.Listener(on_release=self.on_release)
        listener.start()

        # Initial rendering.
        self.render()

        # App loop: (while 1 is faster than while True)
        # Process input -> Update world, physics -> Render output -> Sleep.
        while 1 and not self.should_reset:
            if self.key_pressed:
                self.foreground.popleft()
                curr = self.curr_key if self.curr_key is not None else ""
                if len(curr) == 1:
                    self.foreground.append(curr)
                elif len(curr) > 1:
                    symbol = get_mod_key_symbol(mod_key=curr)
                    self.foreground.append(symbol)

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

            curr_time = perf_counter()
            counter += self.velocity

            if counter >= 1:
                is_enabled = False
                if is_enabled:
                    frame_has_tree = randint(0, WIDTH) == 1  # floor max int.
                    self.foreground.popleft()
                    self.foreground.append(
                        TREE_CHAR if frame_has_tree else None)

                    if para == 0:
                        should_cloud_disappear = self.background[0] == CLOUD_CHAR
                        self.cloud_count -= 1 if should_cloud_disappear else 0
                        can_rain = (self.cloud_count < MAX_CLOUDS
                                    and randint(0, 2) == 1)
                        self.background.popleft()
                        self.background.append(
                            CLOUD_CHAR if can_rain else None)
                        self.cloud_count += 1 if can_rain else 0

                para += 1
                para %= PARA_CONST  # Reset periodically.

                counter -= 1
                self.total_km += 0.01

            self.render()

            elapsed_time = perf_counter() - curr_time
            if elapsed_time < FRAME_DELAY:
                sleep(FRAME_DELAY - elapsed_time)

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
            sleep(FRAME_DELAY)


def main():
    animation = App()
    animation.run()


if __name__ == "__main__":
    main()
