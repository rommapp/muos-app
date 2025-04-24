import os
import re
from typing import TypedDict

color_btn_a = "#ad3c6b"
color_btn_b = "#bb7200"
color_btn_x = "#3b80aa"
color_btn_y = "#41aa3b"
color_btn_shoulder = "#383838"


class Button(TypedDict):
    key: str
    btn: str
    color: str


class ButtonConfig(TypedDict):
    a: Button
    b: Button
    x: Button
    y: Button
    l1: Button
    r1: Button


class ButtonConfigs(TypedDict):
    nintendo: ButtonConfig
    xbox: ButtonConfig


# Default button configurations
BUTTON_CONFIGS: ButtonConfigs = {
    "nintendo": {
        "a": {"key": "A", "btn": "A", "color": color_btn_a},  # East
        "b": {"key": "B", "btn": "B", "color": color_btn_b},  # South
        "x": {"key": "X", "btn": "X", "color": color_btn_x},  # North
        "y": {"key": "Y", "btn": "Y", "color": color_btn_y},  # West
        "l1": {"key": "L1", "btn": "L1", "color": color_btn_shoulder},
        "r1": {"key": "R1", "btn": "R1", "color": color_btn_shoulder},
    },
    "xbox": {
        "a": {"key": "B", "btn": "A", "color": color_btn_a},  # East
        "b": {"key": "A", "btn": "B", "color": color_btn_b},  # South
        "x": {"key": "Y", "btn": "X", "color": color_btn_x},  # North
        "y": {"key": "X", "btn": "Y", "color": color_btn_y},  # West
        "l1": {"key": "L1", "btn": "L1", "color": color_btn_shoulder},
        "r1": {"key": "R1", "btn": "R1", "color": color_btn_shoulder},
    },
}

CONTROLLER_LAYOUT = os.getenv("CONTROLLER_LAYOUT", "nintendo").lower()


def get_controller_layout() -> ButtonConfig:
    """Return the current controller layout configuration."""
    if CONTROLLER_LAYOUT not in BUTTON_CONFIGS:
        raise ValueError(f"Invalid controller layout: {CONTROLLER_LAYOUT}")
    return BUTTON_CONFIGS[CONTROLLER_LAYOUT]  # trunk-ignore(mypy/literal-required)


def set_controller_layout(layout: str):
    global CONTROLLER_LAYOUT
    if layout in BUTTON_CONFIGS:
        CONTROLLER_LAYOUT = layout


def save_controller_layout(env_path=".env"):
    layout = f"CONTROLLER_LAYOUT={CONTROLLER_LAYOUT}\n"

    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
    else:
        lines = []

    for i, line in enumerate(lines):
        if re.match(r"^\s*CONTROLLER_LAYOUT\s*=", line, re.IGNORECASE):
            lines[i] = layout
            break
    else:
        lines.append(layout)

    with open(env_path, "w") as f:
        f.writelines(lines)
