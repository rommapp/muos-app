import os
import sys

portmaster_base = "/storage/roms/ports/PortMaster"
pylibs_path = os.path.join(portmaster_base, "pylibs")
exlibs_path = os.path.join(portmaster_base, "exlibs")
sys.path.append(pylibs_path)
sys.path.append(exlibs_path)

try:
    import sdl2
    import sdl2.ext
    import sdl2.sdlimage
except ModuleNotFoundError as e:
    print(f"Failed to import sdl2: {e}")
    sys.exit(1)

from threading import Lock
from typing import Optional

class Input:
    _instance: Optional["Input"] = None
    _key_mapping = {
        sdl2.SDLK_UP: "DY",
        sdl2.SDLK_DOWN: "DY",
        sdl2.SDLK_LEFT: "DX",
        sdl2.SDLK_RIGHT: "DX",
        sdl2.SDLK_a: "A",
        sdl2.SDLK_b: "B",
        sdl2.SDLK_y: "Y",
        sdl2.SDLK_x: "X",
        sdl2.SDLK_l: "L1",
        sdl2.SDLK_r: "R1",
        sdl2.SDLK_q: "L2",
        sdl2.SDLK_e: "R2",
        sdl2.SDLK_ESCAPE: "SELECT",
        sdl2.SDLK_RETURN: "START",
        sdl2.SDLK_m: "MENUF",
        sdl2.SDLK_PLUS: "V+",
        sdl2.SDLK_MINUS: "V-",
    }

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Input, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self._key_code = 0
        self._key_name = ""
        self._key_value = 0
        self._input_lock = Lock()

    def check(self, event=None) -> None:
        if event:
            if event.type == sdl2.SDL_KEYDOWN:
                key = event.key.keysym.sym
                if key in self._key_mapping:
                    with self._input_lock:
                        self._key_code = key
                        self._key_name = self._key_mapping[key]
                        if self._key_name == "DY":
                            self._key_value = -1 if key == sdl2.SDLK_UP else 1
                        elif self._key_name == "DX":
                            self._key_value = -1 if key == sdl2.SDLK_LEFT else 1
                        else:
                            self._key_value = 1
            elif event.type == sdl2.SDL_KEYUP:
                key = event.key.keysym.sym
                if key in self._key_mapping and self._key_code == key:
                    self.reset_input()

    def key(self, _key_name: str, _key_value: int = 99) -> bool:
        if self._key_name == _key_name:
            if _key_value != 99:
                return self._key_value == _key_value
            return True
        return False

    def handle_navigation(
        self, selected_position: int, items_per_page: int, total_items: int
    ) -> int:
        if self.key("DY"):
            if self._key_value == 1:
                if selected_position == total_items - 1:
                    selected_position = 0
                elif selected_position < total_items - 1:
                    selected_position += 1
            elif self._key_value == -1:
                if selected_position == 0:
                    selected_position = total_items - 1
                elif selected_position > 0:
                    selected_position -= 1
            self.reset_input()
        elif self.key("DX"):
            if self._key_value == 1:
                if selected_position < total_items - 1:
                    if selected_position + items_per_page <= total_items - 1:
                        selected_position = selected_position + items_per_page
                    else:
                        selected_position = total_items - 1
            elif self._key_value == -1:
                if selected_position > 0:
                    if selected_position - items_per_page >= 0:
                        selected_position = selected_position - items_per_page
                    else:
                        selected_position = 0
            self.reset_input()
        elif self.key("L1"):
            if selected_position > 0:
                if selected_position - items_per_page >= 0:
                    selected_position = selected_position - items_per_page
                else:
                    selected_position = 0
            self.reset_input()
        elif self.key("R1"):
            if selected_position < total_items - 1:
                if selected_position + items_per_page <= total_items - 1:
                    selected_position = selected_position + items_per_page
                else:
                    selected_position = total_items - 1
            self.reset_input()
        elif self.key("L2"):
            if selected_position > 0:
                if selected_position - 100 >= 0:
                    selected_position = selected_position - 100
                else:
                    selected_position = 0
            self.reset_input()
        elif self.key("R2"):
            if selected_position < total_items - 1:
                if selected_position + 100 <= total_items - 1:
                    selected_position = selected_position + 100
                else:
                    selected_position = total_items - 1
            self.reset_input()
        return selected_position

    def reset_input(self) -> None:
        with self._input_lock:
            self._key_name = ""
            self._key_value = 0
            self._key_code = 0

    def cleanup(self):
        print("Input cleanup (no controller to close).")
