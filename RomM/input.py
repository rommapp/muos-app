import os
import time
from threading import Lock
from typing import Any, Dict, Optional

import sdl2


class Input:
    _instance: Optional["Input"] = None

    _key_mapping = {
        sdl2.SDL_CONTROLLER_BUTTON_A: "A",
        sdl2.SDL_CONTROLLER_BUTTON_B: "B",
        sdl2.SDL_CONTROLLER_BUTTON_X: "X",
        sdl2.SDL_CONTROLLER_BUTTON_Y: "Y",
        sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER: "L1",
        sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER: "R1",
        sdl2.SDL_CONTROLLER_BUTTON_LEFTSTICK: "L3",
        sdl2.SDL_CONTROLLER_BUTTON_RIGHTSTICK: "R3",
        sdl2.SDL_CONTROLLER_BUTTON_BACK: "SELECT",
        sdl2.SDL_CONTROLLER_BUTTON_START: "START",
        sdl2.SDL_CONTROLLER_BUTTON_GUIDE: "MENUF",
        sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP: "DY-",
        sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN: "DY+",
        sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT: "DX-",
        sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT: "DX+",
    }

    _axis_mapping = {
        sdl2.SDL_CONTROLLER_AXIS_LEFTX: "DX",
        sdl2.SDL_CONTROLLER_AXIS_LEFTY: "DY",
        sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT: "L2",
        sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT: "R2",
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

        # Enable controller events
        self._load_controller_mappings()
        sdl2.SDL_GameControllerEventState(sdl2.SDL_ENABLE)
        sdl2.SDL_JoystickEventState(sdl2.SDL_ENABLE)

        # Open controllers
        self.controllers: list[Any] = []

        num_controllers = sdl2.SDL_NumJoysticks()
        print(f"Found {num_controllers} controller(s)")

        for i in range(num_controllers):
            if sdl2.SDL_IsGameController(i):
                controller = sdl2.SDL_GameControllerOpen(i)
                if controller:
                    name = sdl2.SDL_GameControllerName(controller).decode("utf-8")
                    self.controllers.append(controller)
                    print(f"Found game controller {i}: {name}")
            else:
                print(f"Joystick {i} is not a recognized game controller")

        if not self.controllers:
            print("No game controllers found.")
            raise RuntimeError("No game controllers found.")

    def _load_controller_mappings(self) -> None:
        """Load controller mappings from environment variable or fallback file."""
        config_path = sdl2.SDL_getenv(b"SDL_GAMECONTROLLERCONFIG")
        if config_path:
            config_str = config_path.decode("utf-8")

            if "," in config_str and not config_str.endswith((".txt", ".cfg")):
                # Treat as mapping string - encode to bytes
                mapping_bytes = config_str.encode("utf-8")
                result = sdl2.SDL_GameControllerAddMapping(mapping_bytes)
                if result == -1:
                    print(
                        f"Warning: Failed to load mapping from environment: {sdl2.SDL_GetError().decode()}"
                    )
                else:
                    print("Loaded controller mapping from environment")
            else:
                # Treat as file path - encode to bytes for SDL function
                if os.path.exists(config_str):
                    file_path_bytes = config_str.encode("utf-8")
                    result = sdl2.SDL_GameControllerAddMappingsFromFile(file_path_bytes)
                    if result == -1:
                        print(
                            f"Warning: Could not load file {config_str}: {sdl2.SDL_GetError().decode()}"
                        )
                    else:
                        print(
                            f"Loaded {result} controller mappings from file {config_str}"
                        )
                else:
                    print(f"Warning: Controller config file {config_str} not found")
        else:
            print("No controller mappings loaded - using SDL defaults")

    def _add_key_pressed(self, key_name: str) -> None:
        """Add a key to the pressed set"""
        with self._input_lock:
            self._keys_pressed.add(key_name)
            self._keys_held.add(key_name)
            self._keys_held_start_time[key_name] = time.time()

    def _remove_key_held(self, key_name: str) -> None:
        """Remove a key from the pressed set"""
        with self._input_lock:
            self._keys_held.discard(key_name)
            self._keys_held_start_time.pop(key_name, None)

    def check_event(self, event=None) -> bool:
        """
        Check for input events and update key states
        Returns if an event was processed
        """
        if event:
            # Controller button press
            if event.type == sdl2.SDL_CONTROLLERBUTTONDOWN:
                button = event.cbutton.button
                # Map button to key name using the _key_mapping dictionary
                if button in self._key_mapping:
                    key_name = self._key_mapping[button]
                    self._add_key_pressed(key_name)
                    return True

            # Controller button release
            elif event.type == sdl2.SDL_CONTROLLERBUTTONUP:
                button = event.cbutton.button

                # Clear the key if it was pressed
                if button in self._key_mapping:
                    key_name = self._key_mapping[button]
                    self._remove_key_held(key_name)

            # Controller axis motion
            elif event.type == sdl2.SDL_CONTROLLERAXISMOTION:
                axis = event.caxis.axis
                value = event.caxis.value

                if axis in self._axis_mapping:
                    key_name = self._axis_mapping[axis]

                    # Only process significant movements (ignore small values)
                    if abs(value) > 10000:
                        dir = "+" if value > 0 else "-"
                        self._add_key_pressed(f"{key_name}{dir}")
                        return True

                    # Reset when axis returns to center
                    elif abs(value) < 5000:
                        self._remove_key_held(f"{key_name}+")
                        self._remove_key_held(f"{key_name}-")

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

    def clear_pressed(self) -> None:
        """Clear the pressed keys"""
        with self._input_lock:
            self._keys_pressed.clear()

    def cleanup(self) -> None:
        """Clean up SDL resources"""
        with self._input_lock:
            for controller in self.controllers:
                sdl2.SDL_GameControllerClose(controller)

            self.controllers = []  # Clear the list of controllers
            self._keys_pressed = set()
            self._keys_held = set()
            self._keys_held_start_time = {}

        sdl2.SDL_QuitSubSystem(sdl2.SDL_INIT_GAMECONTROLLER)
