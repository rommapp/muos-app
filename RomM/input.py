import time
from threading import Lock
from typing import Dict, Optional, Set

import sdl2


class Input:
    _instance: Optional["Input"] = None
    _key_mapping = {
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
        self._keys_pressed: Dict[str, int] = {}
        self._key_hold_start_time: Dict[str, float] = {}

        # Track which keys have had their first event processed
        self._key_first_processed: Set[str] = set()

        # Key repeat settings
        self._initial_delay = 0.25  # Delay after first event before repeating
        self._min_delay = 0.05  # Minimum delay after acceleration (faster)
        self._acceleration_time = 1.0  # Time in seconds to reach maximum speed

        # Last processed time for key repeats
        self._last_repeat_time: Dict[str, float] = {}

        # Enable joystick events
        sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK)
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

    def check(self, event=None) -> None:
        current_time = time.time()

        if event:
            # Joystick button press
            if event.type == sdl2.SDL_JOYBUTTONDOWN:
                button = event.jbutton.button
                print(f"Button pressed: {button}")

                # Map button to key name using the _key_mapping dictionary
                if button in self._key_mapping:
                    key_name = self._key_mapping[button]
                    with self._input_lock:
                        self._keys_pressed[key_name] = 1
                        self._key_hold_start_time[key_name] = current_time
                        # First press is immediately processed
                        if key_name not in self._key_first_processed:
                            self._key_first_processed.add(key_name)
                            print(f"Key first press: {key_name}")
                        else:
                            print(f"Key held: {key_name}")

            # Joystick button release
            elif event.type == sdl2.SDL_JOYBUTTONUP:
                button = event.jbutton.button
                print(f"Button released: {button}")

                # Clear the key if it was pressed
                if button in self._key_mapping:
                    key_name = self._key_mapping[button]
                    with self._input_lock:
                        if key_name in self._keys_pressed:
                            del self._keys_pressed[key_name]
                        if key_name in self._key_hold_start_time:
                            del self._key_hold_start_time[key_name]
                        if key_name in self._last_repeat_time:
                            del self._last_repeat_time[key_name]
                        # Remove from first processed set
                        self._key_first_processed.discard(key_name)
                    print(f"Key released: {key_name}")

            # Joystick axis motion
            elif event.type == sdl2.SDL_JOYAXISMOTION:
                axis = event.jaxis.axis
                value = event.jaxis.value

                # Only process significant movements (ignore small values)
                if abs(value) > 10000:
                    normalized_value = 1 if value > 0 else -1

                    # Map axis 0 to DX (left/right)
                    if axis == 0:
                        key_name = "DX"
                        with self._input_lock:
                            # Check if this is a new direction or same direction
                            is_new_press = (
                                key_name not in self._keys_pressed
                                or self._keys_pressed[key_name] != normalized_value
                            )

                            self._keys_pressed[key_name] = normalized_value
                            self._key_hold_start_time[key_name] = current_time

                            # First movement in this direction is immediately processed
                            if is_new_press:
                                self._key_first_processed.add(key_name)
                                print(
                                    f"Axis first move: {key_name} = {normalized_value}"
                                )
                            else:
                                print(f"Axis held: {key_name} = {normalized_value}")

                    # Map axis 1 to DY (up/down)
                    elif axis == 1:
                        key_name = "DY"
                        with self._input_lock:
                            # Check if this is a new direction or same direction
                            is_new_press = (
                                key_name not in self._keys_pressed
                                or self._keys_pressed[key_name] != normalized_value
                            )

                            self._keys_pressed[key_name] = normalized_value
                            self._key_hold_start_time[key_name] = current_time

                            # First movement in this direction is immediately processed
                            if is_new_press:
                                self._key_first_processed.add(key_name)
                                print(
                                    f"Axis first move: {key_name} = {normalized_value}"
                                )
                            else:
                                print(f"Axis held: {key_name} = {normalized_value}")

                # Reset when axis returns to center
                elif abs(value) < 5000:
                    key_name = "DX" if axis == 0 else "DY"
                    with self._input_lock:
                        if key_name in self._keys_pressed:
                            del self._keys_pressed[key_name]
                        if key_name in self._key_hold_start_time:
                            del self._key_hold_start_time[key_name]
                        if key_name in self._last_repeat_time:
                            del self._last_repeat_time[key_name]
                        # Remove from first processed set
                        self._key_first_processed.discard(key_name)
                    print(f"Axis centered: {key_name}")

            # Joystick hat motion (D-pad)
            elif event.type == sdl2.SDL_JOYHATMOTION:
                hat = event.jhat.hat
                value = event.jhat.value
                direction = self._hat_value_to_string(value)
                print(f"Hat {hat} = {direction} ({value})")

                with self._input_lock:
                    # Track which keys were previously set
                    prev_dx = "DX" in self._keys_pressed
                    prev_dy = "DY" in self._keys_pressed
                    prev_dx_val = self._keys_pressed.get("DX", 0)
                    prev_dy_val = self._keys_pressed.get("DY", 0)

                    # Clear previous D-pad states
                    for key in ["DX", "DY"]:
                        if key in self._keys_pressed:
                            del self._keys_pressed[key]
                        if key in self._key_hold_start_time:
                            del self._key_hold_start_time[key]
                        if key in self._last_repeat_time:
                            del self._last_repeat_time[key]
                        # Don't remove from first processed yet

                    # Set new D-pad states
                    if value & 1:  # UP
                        self._keys_pressed["DY"] = -1
                        self._key_hold_start_time["DY"] = current_time
                        # Check if this is a new direction
                        if not prev_dy or prev_dy_val != -1:
                            self._key_first_processed.add("DY")
                    elif value & 4:  # DOWN
                        self._keys_pressed["DY"] = 1
                        self._key_hold_start_time["DY"] = current_time
                        # Check if this is a new direction
                        if not prev_dy or prev_dy_val != 1:
                            self._key_first_processed.add("DY")
                    else:
                        # No vertical movement
                        self._key_first_processed.discard("DY")

                    if value & 2:  # RIGHT
                        self._keys_pressed["DX"] = 1
                        self._key_hold_start_time["DX"] = current_time
                        # Check if this is a new direction
                        if not prev_dx or prev_dx_val != 1:
                            self._key_first_processed.add("DX")
                    elif value & 8:  # LEFT
                        self._keys_pressed["DX"] = -1
                        self._key_hold_start_time["DX"] = current_time
                        # Check if this is a new direction
                        if not prev_dx or prev_dx_val != -1:
                            self._key_first_processed.add("DX")
                    else:
                        # No horizontal movement
                        self._key_first_processed.discard("DX")

        # Process key repeats for held buttons
        with self._input_lock:
            keys_to_process = list(self._key_hold_start_time.keys())

            for key_name in keys_to_process:
                # Skip keys that haven't had their first event processed yet
                if key_name not in self._key_first_processed:
                    continue

                hold_time = current_time - self._key_hold_start_time[key_name]

                # First press is already processed immediately when the key is pressed
                # Now we only care about repeats

                # Calculate repeat rate based on how long the key has been held
                if hold_time > self._acceleration_time + self._initial_delay:
                    # At maximum speed
                    repeat_delay = self._min_delay
                elif hold_time > self._initial_delay:
                    # Gradually accelerate
                    progress = (
                        hold_time - self._initial_delay
                    ) / self._acceleration_time
                    repeat_delay = self._initial_delay - progress * (
                        self._initial_delay - self._min_delay
                    )
                    repeat_delay = max(
                        self._min_delay, repeat_delay
                    )  # Ensure we don't go below min delay
                else:
                    # Still in initial delay period
                    continue

                # Check if it's time for a repeat
                last_repeat = self._last_repeat_time.get(key_name, 0)
                if current_time - last_repeat >= repeat_delay:
                    # Update the last repeat time
                    self._last_repeat_time[key_name] = current_time
                    print(f"Key repeat: {key_name}")
                    # The key is already in _keys_pressed, so handle_navigation will see it

    def key(self, key_name: str, key_value: int = 99) -> bool:
        """Check if a specific key is pressed with an optional value check"""
        with self._input_lock:
            if key_name in self._keys_pressed:
                if key_value != 99:
                    return self._keys_pressed[key_name] == key_value
                return True
            return False

    def handle_navigation(
        self, selected_position: int, items_per_page: int, total_items: int
    ) -> int:
        """Handle navigation based on pressed keys"""
        original_position = selected_position

        if self.key("DY"):
            dy_value = self._keys_pressed.get("DY", 0)
            if dy_value == 1:  # DOWN
                if selected_position == total_items - 1:
                    selected_position = 0
                elif selected_position < total_items - 1:
                    selected_position += 1
            elif dy_value == -1:  # UP
                if selected_position == 0:
                    selected_position = total_items - 1
                elif selected_position > 0:
                    selected_position -= 1

        elif self.key("DX"):
            dx_value = self._keys_pressed.get("DX", 0)
            if dx_value == 1:  # RIGHT
                if selected_position < total_items - 1:
                    if selected_position + items_per_page <= total_items - 1:
                        selected_position = selected_position + items_per_page
                    else:
                        selected_position = total_items - 1
            elif dx_value == -1:  # LEFT
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

        # If position changed, mark keys as processed
        if selected_position != original_position:
            with self._input_lock:
                # Mark all active navigation keys as having their first event processed
                for key in ["DX", "DY", "L1", "R1", "L2", "R2"]:
                    if key in self._keys_pressed:
                        self._key_first_processed.add(key)

        return selected_position

    def reset_input(self) -> None:
        """Reset all input states"""
        with self._input_lock:
            self._keys_pressed.clear()
            self._key_hold_start_time.clear()
            self._last_repeat_time.clear()
            self._key_first_processed.clear()

    def cleanup(self) -> None:
        """Clean up SDL resources"""
        for joystick in self.joysticks:
            sdl2.SDL_JoystickClose(joystick)

        sdl2.SDL_QuitSubSystem(sdl2.SDL_INIT_JOYSTICK)
