#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Keystrokes

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
FRAME_DELAY = 1.0 / FPS
MAX_SPEED = 1
FRICTION_CONST = 0.8

RAIL_CHAR = '..'
PLAYER_CHAR = "#"
FIRE_CHAR = "`"
CACTUS_CHAR = "|"
HILL_CHAR = "~"

MAX_HILL_COUNT = 3
PARA_CONST = 9
MAX_PARA_ELEMENTS = 2

WPM_CHARS_PER_ROUND = 200
WPM_AVERAGE_WORD_LEN = 5


class App:
    def __init__(self):
        self.velocity = 0.0
        self.total_km = 0.0
        self.curr_key = None
        self.typed_history = []
        self.typed_history_cache = []
        self.fire_disp = 0
        self.hill_count = 0
        self.new_press_event = None
        self.key_pressed = False
        self.listener_paused = False
        self.start_time_wpm = time.time()
        self.char_count_wpm = 0
        self.wpm_timer_start = None
        self.wpm_timer_end = None  # For 200 entries or key press
        self.curr_round_wpm = 0.0
        self.debug_text = None

        self.world = [None] * WIDTH
        self.foreground = [None] * WIDTH
        self.background = [None] * WIDTH

    def get_wpm(self, len_entries):
        if self.wpm_timer_start is not None and self.wpm_timer_end is not None:
            elapsed_time = self.wpm_timer_end - self.wpm_timer_start
            minutes = elapsed_time / 60
            words = len_entries / WPM_AVERAGE_WORD_LEN
            return round(words / minutes, 2)
        else:
            raise ValueError(
                """
                Invalid `wpm_timer_start` or `wpm_timer_end` values.
                Expected `float` found `None`.
                """
            )

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
    def render(self):
        # Compose text world.
        self.world = [
            x if x is not None else RAIL_CHAR for x in self.background]
        for i, value in enumerate(self.foreground):
            if value is not None:
                self.world[i] = value
            elif self.world[i] is None:
                self.world[i] = RAIL_CHAR

        self.world[PLAYER_POSITION] = PLAYER_CHAR
        if self.velocity > 0.9:
            self.world[PLAYER_POSITION - 1] = FIRE_CHAR
            if self.fire_disp % 3 == 0 or self.fire_disp % 2 == 0:
                self.world[PLAYER_POSITION - 2] = FIRE_CHAR
            self.fire_disp += 1

        if self.listener_paused:
            print('Escape to resume')
            return

        # Build the output string buffer.
        output_buffer = ""

        # for i in range(0, WIDTH - 1):
        #   # print(self.world[i], end="")

        # print(f"{self.total_km:.2f}km/", end="")

        len_total = len(self.typed_history)
        if self.wpm_timer_start is None and len_total > 0:
            self.wpm_timer_start = time.time()

        if len_total >= WPM_CHARS_PER_ROUND:
            if len(self.typed_history_cache) >= 5:
                self.typed_history_cache.clear()
            self.typed_history_cache.append(self.typed_history)
            self.typed_history.clear()
            self.wpm_timer_end = time.time()

        # if self.curr_round_wpm is not None:
        #     print(f"{self.curr_round_wpm}wpm/{len_total:3}", end="")
        # else:
        #     no_wpm = 0
        #     # FIXME: Use Same buffer template pattern.
        #     print(f"{no_wpm:.2f}wpm/{len_total:3}/", end="")
        #     # print(f"{no_wpm:.2f}wpm", end="")

        if self.wpm_timer_end is not None:
            self.wpm_timer_end = time.time()
            self.curr_round_wpm = self.get_wpm(WPM_CHARS_PER_ROUND)

            # print(f"{self.curr_round_wpm}wpm/{len_total:3}", end="")
            self.wpm_timer_start = None
            self.wpm_timer_end = None

        # DEBUG
        # print(f"{self.curr_key} ", end="")
        # output_buffer += f"{self.curr_key} " if self.curr_key is not None else ""

        # Construct output string.
        output_buffer += "{:<{width}}".format("".join(
            self.world[:WIDTH-1]), width=(2*WIDTH)
        )
        output_buffer += "{:<{width}}".format(
            f"{self.curr_key} " if self.curr_key is not None else "",
            width=5,
        )  # 9 chars max <Backspace> 5 for <shift>
        output_buffer += "{:.2f}km/".format(self.total_km)
        output_buffer += "{:<4}".format(
            "{}wpm/".format(self.curr_round_wpm)
            if self.curr_round_wpm is not None else "0.00wpm"
        )
        output_buffer += "{:<3}\n".format(len_total)

        # print()  # New line for next frame.
        print(output_buffer)  # Print current frame's buffer.

        if self.debug_text:
            print(f"DEBUG: {self.debug_text}")

    def debug(self, text):
        self.debug_text = text

    def pause_listener(self,):
        self.listener_paused = True

    def resume_listener(self,):
        self.listener_paused = False

    # def on_press(key):
    #     if not listener_paused:
    #         try:
    #             key_pressed = True  # 'alphanumeric key {0} pressed'
    #             # print('{0}'.format(key.char), end='', flush=True)
    #         except AttributeError:
    #             key_pressed = True  # 'special key {0} pressed'
    #             # print('{0}'.format(key), end='', flush=True)

    def on_release(self, key):
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

    def run(self):
        ax = 0.0
        counter = 0.0
        para = 0

        self.new_press_event = threading.Event()
        # Non-Blocking: Collect events until released.
        listener = keyboard.Listener(on_release=self.on_release)
        listener.start()

        self.render()  # Initial rendering.

        # App loop:
        # - Process input.
        # - Update world, physics.
        # - Render output.
        # - Sleep.
        while True:
            # For when we need >1 events per tick.
            n_events = 0
            # Process user input. If key event happens during tick:
            if (self.key_pressed):
                n_events += 1
                self.key_pressed = False
            elif n_events > 0:
                n_events -= 1

            if n_events > 0:
                ax += 0.02
            elif self.velocity > 0:
                ax -= 0.005
            elif self.velocity <= 0:
                ax = 0
                self.velocity = 0

            # debug(f"velocity: {velocity}, ax: {ax}")
            self.velocity += ax - self.velocity * FRICTION_CONST
            self.velocity = min(self.velocity, MAX_SPEED)

            if self.velocity == 0:
                self.new_press_event.wait()
                self.new_press_event.clear()

            curr_time = time.time()
            counter += self.velocity

            if counter >= 1:
                self.foreground.pop(0)
                # NOTE: get upper-bound(largest integer) floor division result.
                if random.randint(0, FPS // 2) == 1:
                    self.foreground.append(CACTUS_CHAR)
                else:
                    self.foreground.append(None)

                if para == 0:
                    if self.background[0] == HILL_CHAR:
                        self.hill_count -= 1

                    self.background.pop(0)
                    if random.randint(0, 2) == 1 and self.hill_count < MAX_HILL_COUNT:
                        self.background.append(HILL_CHAR)
                        self.hill_count += 1
                    else:
                        self.background.append(None)

                para += 1
                para %= PARA_CONST
                counter -= 1
                self.total_km += 0.01

            self.render()

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

"""
