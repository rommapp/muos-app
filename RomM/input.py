import time
from threading import Lock
from typing import Dict, Optional

import sdl2


class Input:
    _instance: Optional["Input"] = None
    _key_mapping = {
        # muOS
        3: "A",
        4: "B",
        5: "Y",
        6: "X",
        7: "L1",
        8: "R1",
        13: "L2",
        14: "R2",
        9: "SELECT",
        10: "START",
        16: "MENUF",
        # EmulationStation
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
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._input_lock = Lock()

        # Track the state of all keys
        self._keys_pressed: set[str] = set()
        self._keys_held: set[str] = set()
        self._keys_held_start_time: Dict[str, float] = {}

        # Key repeat settings
        self._initial_delay = 0.35

        # Enable joystick events
        sdl2.SDL_JoystickEventState(sdl2.SDL_ENABLE)

        # Open joysticks
        self.joysticks = []
        num_joysticks = sdl2.SDL_NumJoysticks()
        print(f"Found {num_joysticks} joystick(s)")

        for i in range(num_joysticks):
            joystick = sdl2.SDL_JoystickOpen(i)
            if joystick:
                name = sdl2.SDL_JoystickName(joystick).decode("utf-8")
                self.joysticks.append(joystick)

                axes = sdl2.SDL_JoystickNumAxes(joystick)
                buttons = sdl2.SDL_JoystickNumButtons(joystick)
                hats = sdl2.SDL_JoystickNumHats(joystick)

                print(f"Joystick {i}: {name}")
                print(f"  - Axes: {axes}")
                print(f"  - Buttons: {buttons}")
                print(f"  - Hats: {hats}")

    def _hat_value_to_string(self, value):
        """Convert hat value to human-readable direction"""
        if value == 0:
            return "CENTER"
        if value == 1:
            return "UP"
        if value == 2:
            return "RIGHT"
        if value == 3:
            return "UP+RIGHT"
        if value == 4:
            return "DOWN"
        if value == 6:
            return "DOWN+RIGHT"
        if value == 8:
            return "LEFT"
        if value == 9:
            return "UP+LEFT"
        if value == 12:
            return "DOWN+LEFT"
        return f"UNKNOWN({value})"

    def _add_key_pressed(self, key_name: str) -> None:
        """Add a key to the pressed set"""
        with self._input_lock:
            self._keys_pressed.add(key_name)
            self._keys_held.add(key_name)
            self._keys_held_start_time[key_name] = time.time()

    def _remove_key_pressed(self, key_name: str) -> None:
        """Remove a key from the pressed set"""
        with self._input_lock:
            self._keys_pressed.discard(key_name)
            self._keys_held.discard(key_name)
            self._keys_held_start_time.pop(key_name, None)

    def check(self, event=None) -> bool:
        """
        Check for input events and update key states
        Returns if an event was processed
        """
        if event:
            # Generic keydown event
            if event.type == sdl2.SDL_KEYDOWN:
                key = event.key.keysym.sym
                # Map key to button name using the _key_mapping dictionary
                if key in self._key_mapping:
                    key_name = self._key_mapping[key]
                    self._add_key_pressed(key_name)
                    print(f"Key pressed: {key_name}")
                    return True

            # Generic keyup event
            elif event.type == sdl2.SDL_KEYUP:
                key = event.key.keysym.sym
                # Map key to button name using the _key_mapping dictionary
                if key in self._key_mapping:
                    key_name = self._key_mapping[key]
                    self._remove_key_pressed(key_name)
                    print(f"Key released: {key_name}")

            # Joystick button press
            if event.type == sdl2.SDL_JOYBUTTONDOWN:
                button = event.jbutton.button
                # Map button to key name using the _key_mapping dictionary
                if button in self._key_mapping:
                    key_name = self._key_mapping[button]
                    self._add_key_pressed(key_name)
                    print(f"Button pressed: {key_name}")
                    return True

            # Joystick button release
            elif event.type == sdl2.SDL_JOYBUTTONUP:
                button = event.jbutton.button

                # Clear the key if it was pressed
                if button in self._key_mapping:
                    key_name = self._key_mapping[button]
                    self._remove_key_pressed(key_name)
                    print(f"Button released: {key_name}")

            # Joystick axis motion
            elif event.type == sdl2.SDL_JOYAXISMOTION:
                axis = event.jaxis.axis
                value = event.jaxis.value

                # Only process significant movements (ignore small values)
                if abs(value) > 10000:
                    key = "DX" if axis == 0 else "DY"
                    dir = "+" if value > 0 else "-"
                    self._add_key_pressed(f"{key}{dir}")
                    return True

                # Reset when axis returns to center
                elif abs(value) < 5000:
                    if axis == 0:
                        self._remove_key_pressed("DX+")
                        self._remove_key_pressed("DX-")
                    else:
                        self._remove_key_pressed("DY+")
                        self._remove_key_pressed("DY-")
                    print(f"Axis centered: {key_name}")

            # Joystick hat motion (D-pad)
            elif event.type == sdl2.SDL_JOYHATMOTION:
                hat = event.jhat.hat
                value = event.jhat.value
                direction = self._hat_value_to_string(value)
                print(f"Hat {hat} = {direction} ({value})")

                # Clear previous D-pad states
                for key in ["DX+", "DY+", "DX-", "DY-"]:
                    self._remove_key_pressed(key)

                # Set new D-pad states
                if value & 1:  # UP
                    self._add_key_pressed("DY-")
                    return True
                elif value & 4:  # DOWN
                    self._add_key_pressed("DY+")
                    return True

                if value & 2:  # RIGHT
                    self._add_key_pressed("DX+")
                    return True
                elif value & 8:  # LEFT
                    self._add_key_pressed("DX-")
                    return True

        return False

    def key(self, key_name: str) -> bool:
        """Check if a specific key is pressed with an optional value check"""
        with self._input_lock:
            is_pressed = key_name in self._keys_pressed
            self._keys_pressed.discard(key_name)

            if key_name in self._keys_held:
                # Check if the key is held down
                held_time = time.time() - self._keys_held_start_time[key_name]
                if held_time >= self._initial_delay:
                    is_pressed = True

            return is_pressed

    def handle_navigation(
        self, selected_position: int, items_per_page: int, total_items: int
    ) -> int:
        """Handle navigation based on pressed keys"""
        if self.key("DY+"):  # DOWN
            if selected_position == total_items - 1:
                selected_position = 0
            elif selected_position < total_items - 1:
                selected_position += 1
        elif self.key("DY-"):  # UP
            if selected_position == 0:
                selected_position = total_items - 1
            elif selected_position > 0:
                selected_position -= 1
        elif self.key("DX+"):  # RIGHT
            if selected_position < total_items - 1:
                if selected_position + items_per_page <= total_items - 1:
                    selected_position = selected_position + items_per_page
                else:
                    selected_position = total_items - 1
        elif self.key("DX-"):  # LEFT
            if selected_position > 0:
                if selected_position - items_per_page >= 0:
                    selected_position = selected_position - items_per_page
                else:
                    selected_position = 0
        elif self.key("L1"):
            if selected_position > 0:
                if selected_position - items_per_page >= 0:
                    selected_position = selected_position - items_per_page
                else:
                    selected_position = 0
        elif self.key("R1"):
            if selected_position < total_items - 1:
                if selected_position + items_per_page <= total_items - 1:
                    selected_position = selected_position + items_per_page
                else:
                    selected_position = total_items - 1
        elif self.key("L2"):
            if selected_position > 0:
                if selected_position - 100 >= 0:
                    selected_position = selected_position - 100
                else:
                    selected_position = 0
        elif self.key("R2"):
            if selected_position < total_items - 1:
                if selected_position + 100 <= total_items - 1:
                    selected_position = selected_position + 100
                else:
                    selected_position = total_items - 1

        return selected_position

    def cleanup(self) -> None:
        """Clean up SDL resources"""
        for joystick in self.joysticks:
            sdl2.SDL_JoystickClose(joystick)

        sdl2.SDL_QuitSubSystem(sdl2.SDL_INIT_JOYSTICK)
