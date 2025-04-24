import os
import re

color_btn_a = "#ad3c6b"
color_btn_b = "#bb7200"
color_btn_x = "#3b80aa"
color_btn_y = "#41aa3b"
color_btn_shoulder = "#383838"

# Default button configurations
BUTTON_CONFIGS = {
    "nintendo": [
        {"key": "A", "btn": "A", "color": color_btn_a},  # East
        {"key": "B", "btn": "B", "color": color_btn_b},  # South
        {"key": "X", "btn": "X", "color": color_btn_x},  # North
        {"key": "Y", "btn": "Y", "color": color_btn_y},  # West
        {"key": "L1", "btn": "L1", "color": color_btn_shoulder},
        {"key": "R1", "btn": "R1", "color": color_btn_shoulder},
    ],
    "xbox": [
        {"key": "B", "btn": "A", "color": color_btn_b},  # South
        {"key": "A", "btn": "B", "color": color_btn_a},  # East
        {"key": "Y", "btn": "X", "color": color_btn_y},  # West
        {"key": "X", "btn": "Y", "color": color_btn_x},  # North
        {"key": "L1", "btn": "L1", "color": color_btn_shoulder},
        {"key": "R1", "btn": "R1", "color": color_btn_shoulder},
    ],
}

CONTROLLER_LAYOUT = os.getenv("CONTROLLER_LAYOUT", "nintendo")


def get_controller_layout():
    return BUTTON_CONFIGS.get(CONTROLLER_LAYOUT, BUTTON_CONFIGS["nintendo"])


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
