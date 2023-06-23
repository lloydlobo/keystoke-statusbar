#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Keystrokes

Inspiration: https://github.com/petternett/railway-statusbar
"""

from collections import deque
from time import time
from threading import Event
from typing import Deque, List, Union
from pynput import keyboard
from keybindings import keyboard_mappings

WIDTH: int = 16
BG_CHAR: str = '•'
WPM_KEYS_PER_ROUND: int = 200
WPM_AVERAGE_WORD_LEN: int = 5
LINUX_MODIFIER_KEYS = {
    "space": "␣",  # Space key
    "enter": "⏎",  # Enter key
    "shift": "⇧",  # Shift key
    "backspace": "<<",  # Control key
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


def get_wpm(len_entries, time_start, time_end) -> float:
    if time_start is not None and time_end is not None:
        elapsed_time = time_end - time_start
        minutes = elapsed_time / 60
        words = len_entries / WPM_AVERAGE_WORD_LEN
        return round(words / minutes, 2)
    else:
        raise ValueError("Invalid `timer_start` or `timer_end` values.\
                         Expected `float` found `None`.")


def get_mod_key_symbol(mod_key: str):
    key = mod_key.lower()
    if key in LINUX_MODIFIER_KEYS:
        return LINUX_MODIFIER_KEYS[key]
    else:
        return mod_key


class App:
    def __init__(self):
        # Key-related members.
        self.curr_key: Union[str, None] = None
        self.key_pressed: bool = False
        self.key_released: bool = False
        self.released_key: Union[str, None] = None
        self.key_count: int = 0
        self.new_key_event: Union[Event, None] = None
        self.listener_paused: bool = False
        self.should_reset = False
        self.repeat_blinker = 0

        # Time-related members.
        self.wpm_timer_start: Union[float, None] = None
        self.wpm_timer_end: Union[float, None] = None  # For 200 key releases.
        self.curr_round_wpm: float = 0.0

        # Text-related members.
        self.key_history: Deque[str] = deque(maxlen=WPM_KEYS_PER_ROUND)
        self.key_history_cache: Deque[Deque[str]] = deque(maxlen=3)
        self.debug_text: Union[str, None] = None

        # World-related members.
        self.foreground: deque[Union[str, None]] = deque(
            [None] * WIDTH, maxlen=WIDTH)
        self.background: deque[Union[str, None]] = deque([None] * WIDTH)

    def render(self) -> None:
        """
        - Merge background and foreground to compose world (`List[str]`).
          - `self.foreground[i]` is assigned to `world[i]` if not None.
          - else, assign `self.background[i]` if not None else `RAIL_CHAR`.
        - Track, and record keypress count for each round to calculate wpm.
        - Concatenate a single buffer with message modules and print the frame.
        """

        world = [fg or bg or BG_CHAR for (fg, bg) in zip(
            self.foreground, self.background)]

        if self.wpm_timer_start is None and self.key_count > 0:
            self.wpm_timer_start = time()

        if self.key_count >= WPM_KEYS_PER_ROUND:
            self.wpm_timer_end = time()
            self.key_history_cache.append(self.key_history)
            self.key_history.clear()
            self.key_count = 0

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

            scene.append("".join(world))

        scene.append(f"{self.key_count:<3}")
        scene.append(f"{self.curr_round_wpm:.2f}wpm"
                     if self.curr_round_wpm is not None else "0.00wpm")

        if self.debug_text:
            print(f"DEBUG: {self.debug_text}", end=" ")

        print(" ".join(scene))  # Print current frame's buffer.

    def on_press(self, key) -> None:
        if self.new_key_event is not None:
            self.new_key_event.set()

        self.key_pressed = True  # False if using on_press.
        try:
            self.curr_key = f"{key.char}"
        except AttributeError:
            self.curr_key = f"{key}".replace("Key.", "")

        self.key_history.append(self.curr_key)

        if self.key_released:
            self.key_count += 1
            self.key_released = False
        else:
            self.foreground[0] = None
            match self.repeat_blinker:
                case 0:
                    self.background[0] = '░'
                case 1:
                    self.background[0] = '▓'
                case 2:
                    self.background[0] = '█'
            self.repeat_blinker = (self.repeat_blinker + 1) % 3

    def on_release(self, key) -> None:
        if self.new_key_event is not None:
            self.new_key_event.set()

        self.key_released = True

        try:
            self.released_key = f"{key.char}"
        except AttributeError:
            self.released_key = f"{key}".replace("Key.", "")

    def debug(self, text: str) -> None:
        self.debug_text = text

    def on_activate_h(self):
        print('ctrl-alt-h pressed: Halt ')
        self.listener_paused = not self.listener_paused

    def on_activate_i(self):
        print('ctrl-alt-i pressed: Resetting')
        self.should_reset = not (self.should_reset)

    def run(self) -> None:
        global_hot_keys = keyboard.GlobalHotKeys({
            '<ctrl>+<alt>+h': self.on_activate_h,
            '<ctrl>+<alt>+i': self.on_activate_i,  # reset
        })
        global_hot_keys.start()

        # Non-Blocking: Collect events until released.
        self.new_key_event = Event()
        listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release)
        listener.start()

        # Initial rendering.
        self.render()

        # Process input -> Update world, physics -> Render output -> Sleep.
        while not self.should_reset:
            if self.key_pressed:
                # self.foreground.popleft()
                curr = self.curr_key if self.curr_key is not None else ""
                # FIXME: if curr_key is not English it can have len > 1
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

            if n_events == 0:
                self.new_key_event.wait()
                self.new_key_event.clear()

            self.render()


def main():
    animation = App()
    animation.run()


if __name__ == "__main__":
    main()
