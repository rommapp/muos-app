import time
from struct import unpack
from threading import Lock
from typing import Optional


class Input:
    _instance: Optional["Input"] = None
    _key_mapping = {
        304: "A",
        305: "B",
        306: "Y",
        307: "X",
        308: "L1",
        309: "R1",
        314: "L2",
        315: "R2",
        17: "DY",
        16: "DX",
        310: "SELECT",
        311: "START",
        312: "MENUF",
        114: "V+",
        115: "V-",
    }

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Input, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self._key_code = 0
        self._key_name = ""
        self._key_value = 0  # 0: Released, 1: Pressed, -1: Held
        self._input_lock = Lock()  # Lock to protect input state
        self._last_scroll_time = 0.0  # Last time a scroll was performed
        self._key_states: dict[str, int] = {}  # Track the state of each key

        self._key_hold_start_time: dict[str, float] = (
            {}
        )  # Track when a key was first pressed
        self._initial_delay = 0.25  # Initial delay between scrolls (slower)
        self._min_delay = 0.05  # Minimum delay after acceleration (faster)
        self._acceleration_time = 1.0  # Time in seconds to reach maximum speed

    def check(self) -> None:
        with open("/dev/input/event1", "rb") as f:
            while True:
                event = f.read(24)
                if event:
                    (_, _, _, kcode, kvalue) = unpack("llHHI", event)
                    key_name = self._key_mapping.get(kcode, str(kcode))

                    # Update key state in our tracking dictionary
                    if kvalue == 0:  # Key released
                        self._key_states[key_name] = 0
                        # Reset hold time when key is released
                        if key_name in self._key_hold_start_time:
                            del self._key_hold_start_time[key_name]
                    else:  # Key pressed
                        if kvalue != 1:
                            kvalue = -1
                        self._key_states[key_name] = kvalue

                        # Record the time when key was first pressed
                        if key_name not in self._key_hold_start_time:
                            self._key_hold_start_time[key_name] = time.time()

                    with self._input_lock:
                        self._key_code = kcode
                        self._key_name = key_name
                        self._key_value = kvalue

    def key(self, _key_name: str, _key_value: int = 99) -> bool:
        # Check if the key is currently pressed based on our tracking dictionary
        current_value = self._key_states.get(_key_name, 0)

        if current_value != 0:
            if _key_value != 99:
                return current_value == _key_value
            return True
        return False

    def _get_current_scroll_delay(self, key_name: str) -> float:
        """Calculate the current scroll delay based on how long the key has been held."""
        if key_name not in self._key_hold_start_time:
            return self._initial_delay

        hold_duration = time.time() - self._key_hold_start_time[key_name]

        # Calculate a delay that decreases over time (accelerating scroll speed)
        if hold_duration >= self._acceleration_time:
            return self._min_delay
        else:
            # Linear interpolation between initial and minimum delay
            progress = hold_duration / self._acceleration_time
            return self._initial_delay - progress * (
                self._initial_delay - self._min_delay
            )

    def handle_navigation(
        self, selected_position: int, items_per_page: int, total_items: int
    ) -> int:
        current_time = time.time()

        if self.key("DY"):
            # Get the current scroll delay based on how long the key has been held
            current_delay = self._get_current_scroll_delay("DY")
            if current_time - self._last_scroll_time >= current_delay:
                self._last_scroll_time = current_time

                if self._key_states.get("DY") == 1:
                    if selected_position == total_items - 1:
                        selected_position = 0
                    elif selected_position < total_items - 1:
                        selected_position += 1
                elif self._key_states.get("DY") == -1:
                    if selected_position == 0:
                        selected_position = total_items - 1
                    elif selected_position > 0:
                        selected_position -= 1

        elif self.key("DX"):
            # Get the current scroll delay based on how long the key has been held
            current_delay = self._get_current_scroll_delay("DX")
            if current_time - self._last_scroll_time >= current_delay:
                self._last_scroll_time = current_time

                if self._key_states.get("DX") == 1:
                    if selected_position < total_items - 1:
                        if selected_position + items_per_page <= total_items - 1:
                            selected_position = selected_position + items_per_page
                        else:
                            selected_position = total_items - 1
                elif self._key_states.get("DX") == -1:
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
            self._key_states["L1"] = 0
        elif self.key("R1"):
            if selected_position < total_items - 1:
                if selected_position + items_per_page <= total_items - 1:
                    selected_position = selected_position + items_per_page
                else:
                    selected_position = total_items - 1
            self._key_states["R1"] = 0
        elif self.key("L2"):
            if selected_position > 0:
                if selected_position - 100 >= 0:
                    selected_position = selected_position - 100
                else:
                    selected_position = 0
            self._key_states["L2"] = 0
        elif self.key("R2"):
            if selected_position < total_items - 1:
                if selected_position + 100 <= total_items - 1:
                    selected_position = selected_position + 100
                else:
                    selected_position = total_items - 1
            self._key_states["R2"] = 0

        return selected_position

    def reset_input(self) -> None:
        with self._input_lock:
            self._key_name = ""
            self._key_value = 0
            self._key_code = 0
            self._key_states = {}
            self._key_hold_start_time = {}
